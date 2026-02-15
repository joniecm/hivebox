"""Temperature endpoint blueprint."""

import logging

from flask import Blueprint, jsonify

from src.services.temperature_service import (
    TemperatureService,
    get_latest_temperature_response_cached,
)


temperature_bp = Blueprint("temperature", __name__)

logger = logging.getLogger(__name__)

temperature_service = TemperatureService()


@temperature_bp.route("/temperature", methods=["GET"])
def temperature():
    """Return the current average temperature from all senseBoxes.

    Fetches temperature data from configured senseBoxes and returns
    the average value. Only includes data from the last hour.

    Returns:
        JSON response with average_temperature field, or error message.
    """
    response = get_latest_temperature_response_cached()
    if response is None:
        logger.warning("No temperature data available from senseBox or MinIO.")
        return jsonify({
            "error": "No temperature data available",
            "message": (
                "Unable to retrieve fresh temperature data from "
                "senseBoxes. Data may be unavailable or older than 1 hour."
            )
        }), 503

    return jsonify({
        "average_temperature": response.average_temperature,
        "status": response.status,
    })
