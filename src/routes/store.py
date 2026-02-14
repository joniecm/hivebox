import logging

from flask import Blueprint, jsonify

from src.background.temperature_flusher import flush_temperature_records


store_bp = Blueprint("store", __name__)

logger = logging.getLogger(__name__)


@store_bp.route("/store", methods=["POST"])
def store_temperature_records():
    """Flush buffered temperature records to MinIO."""
    flushed, success = flush_temperature_records()
    if not success:
        logger.warning("MinIO not configured; store request rejected.")
        return (
            jsonify(
                {
                    "error": "MinIO not configured",
                    "message": "Unable to flush temperature data to MinIO.",
                }
            ),
            503,
        )
    logger.info("Flushed %s temperature record(s) to MinIO.", flushed)
    return jsonify({"flushed": flushed})
