from version import VERSION
import sys
from flask import Flask, jsonify
from sensebox_service import get_average_temperature_for_fresh_data

app = Flask(__name__)


@app.route('/version', methods=['GET'])
def version():
    """Return the version of the deployed app.
    
    Returns:
        JSON response with version field containing the app version.
    """
    return jsonify({"version": VERSION})


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
            "message": "Unable to retrieve fresh temperature data from senseBoxes. Data may be unavailable or older than 1 hour."
        }), 503
    
    return jsonify({"average_temperature": round(avg_temp, 2)})


def print_version() -> None:
    """Print the app version from `version.py` then exit.

    Exits with code 0 on success, 1 on failure.
    """
    if not VERSION:
        print("", file=sys.stderr)
        sys.exit(1)

    print(VERSION)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print_version()
    else:
        app.run(host='0.0.0.0', port=5000)
