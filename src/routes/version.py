"""Version endpoint blueprint."""

import logging

from flask import Blueprint, jsonify

from src.version import VERSION

version_bp = Blueprint("version", __name__)

logger = logging.getLogger(__name__)


@version_bp.route("/version", methods=["GET"])
def version():
    """Return the version of the deployed app.

    Returns:
        JSON response with version field containing the app version.
    """
    logger.debug("Serving /version.")
    return jsonify({"version": VERSION})
