import sys
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Histogram,
                               generate_latest)

from src.sensebox_service import get_average_temperature_for_fresh_data
from src.version import VERSION

app = Flask(__name__)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    duration = time.perf_counter() - g.start_time
    route = request.url_rule.rule if request.url_rule else "unmatched"
    labels = {
        "method": request.method,
        "path": route,
        "status": str(response.status_code),
    }
    HTTP_REQUESTS_TOTAL.labels(**labels).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(**labels).observe(duration)
    return response


@app.route('/metrics', methods=['GET'])
def metrics():
    """Expose Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/version', methods=['GET'])
def version():
    """Return the version of the deployed app.

    Returns:
        JSON response with version field containing the app version.
    """
    return jsonify({"version": VERSION})


def get_temperature_status(temperature: float) -> str:
    """Determine temperature status based on the average temperature.

    Args:
        temperature: The average temperature value.

    Returns:
        Status string: "Too Cold", "Good", or "Too Hot".
    """
    if temperature < 10:
        return "Too Cold"
    elif temperature <= 36:
        return "Good"
    else:
        return "Too Hot"


@app.route('/temperature', methods=['GET'])
def temperature():
    """Return the current average temperature from all senseBoxes.

    Fetches temperature data from configured senseBoxes and returns
    the average value. Only includes data from the last hour.

    Returns:
        JSON response with average_temperature field, or error message.
    """
    avg_temp = get_average_temperature_for_fresh_data()

    if avg_temp is None:
        return jsonify({
            "error": "No temperature data available",
            "message": (
                "Unable to retrieve fresh temperature data from "
                "senseBoxes. Data may be unavailable or older than 1 hour."
            )
        }), 503

    return jsonify({
        "average_temperature": round(avg_temp, 2),
        "status": get_temperature_status(avg_temp)
    })


def print_version() -> None:
    """Print the app version from `version.py` then exit.

    Exits with code 0 on success, 1 on failure.
    """
    if not VERSION:
        print("Error: VERSION not defined", file=sys.stderr)
        sys.exit(1)

    print(VERSION)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print_version()
    else:
        app.run(host='0.0.0.0', port=5000)
