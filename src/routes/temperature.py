from dataclasses import asdict

from flask import Blueprint, jsonify

from src.services.temperature_service import get_latest_temperature_response


temperature_bp = Blueprint("temperature", __name__)


@temperature_bp.route("/temperature", methods=["GET"])
def temperature():
    """Return the current average temperature from all senseBoxes.

    Fetches temperature data from configured senseBoxes and returns
    the average value. Only includes data from the last hour.

    Returns:
        JSON response with average_temperature field, or error message.
    """
    response_payload = get_latest_temperature_response()
    if response_payload is None:
        return (
            jsonify(
                {
                    "error": "No temperature data available",
                    "message": (
                        "Unable to retrieve fresh temperature data from "
                        "senseBoxes. Data may be unavailable or older than 1 hour."
                    ),
                }
            ),
            503,
        )

    return jsonify(asdict(response_payload))


