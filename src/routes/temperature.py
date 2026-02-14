"""Temperature endpoint blueprint."""

import logging

from flask import Blueprint, jsonify

from src.background.temperature_flusher import collect_temperature_record
from src.services.minio_service import MinioService
from src.services.sensebox_service import SenseBoxService
from src.services.temperature_service import TemperatureService


temperature_bp = Blueprint("temperature", __name__)

logger = logging.getLogger(__name__)

sensebox_service = SenseBoxService()
temperature_service = TemperatureService()


@temperature_bp.route("/temperature", methods=["GET"])
def temperature():
    """Return the current average temperature from all senseBoxes.

    Fetches temperature data from configured senseBoxes and returns
    the average value. Only includes data from the last hour.

    Returns:
        JSON response with average_temperature field, or error message.
    """
    sensebox_ids = temperature_service.get_sensebox_ids()
    avg_temp = sensebox_service.get_average_temperature_for_fresh_data(
        box_ids=sensebox_ids
    )

    if avg_temp is None:
        logger.info("No fresh senseBox temperature data; trying MinIO.")
        minio_service = MinioService.from_env()
        if minio_service is not None:
            latest_record = minio_service.get_latest_record()
            if latest_record is not None:
                avg_temp = latest_record.average_temperature
                sensebox_ids = latest_record.source_hivebox_ids

    if avg_temp is None:
        logger.warning("No temperature data available from senseBox or MinIO.")
        return jsonify({
            "error": "No temperature data available",
            "message": (
                "Unable to retrieve fresh temperature data from "
                "senseBoxes. Data may be unavailable or older than 1 hour."
            )
        }), 503

    rounded_temp = round(avg_temp, 2)
    collect_temperature_record(rounded_temp, sensebox_ids)
    logger.info(
        "Returning temperature %.2f from %s source(s).",
        rounded_temp,
        len(sensebox_ids),
    )

    return jsonify({
        "average_temperature": rounded_temp,
        "status": temperature_service.get_temperature_status(rounded_temp)
    })
