from version import VERSION
import sys
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/version', methods=['GET'])
def version():
    """Return the version of the deployed app.
    
    Returns:
        JSON response with version field containing the app version.
    """
    return jsonify({"version": VERSION})


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
