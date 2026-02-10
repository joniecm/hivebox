from flask import Blueprint, jsonify

from src.version import VERSION

version_bp = Blueprint("version", __name__)


@version_bp.route("/version", methods=["GET"])
def version():
    """Return the version of the deployed app.

    Returns:
        JSON response with version field containing the app version.
    """
    return jsonify({"version": VERSION})
