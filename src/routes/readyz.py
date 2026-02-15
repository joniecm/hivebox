"""Readiness endpoint blueprint."""

import logging
from typing import Optional

from flask import Blueprint, jsonify

from src.services.sensebox_service import SenseBoxService
from src.services.temperature_service import (
    CACHE_KEY_LATEST,
    CACHE_TTL_SECONDS,
    SENSEBOX_IDS,
)
from src.services.valkey_service import ValkeyService


readyz_bp = Blueprint("readyz", __name__)
logger = logging.getLogger(__name__)

sensebox_service = SenseBoxService(SENSEBOX_IDS)
valkey_service = ValkeyService.from_env()

CACHE_MAX_AGE_MINUTES = 5


def check_sensebox_accessibility() -> tuple[int, int]:
    """Check how many senseBoxes are accessible.

    Returns:
        Tuple of (accessible_count, total_count).
    """
    accessible = 0
    total = len(SENSEBOX_IDS)

    for box_id in SENSEBOX_IDS:
        if sensebox_service.is_box_accessible(box_id):
            accessible += 1

    return accessible, total


def get_cache_age_seconds() -> Optional[int]:
    """Get the age of the cached temperature data in seconds.

    Returns:
        Age in seconds, or None if cache is not available or not configured.
    """
    if valkey_service is None:
        return None

    ttl = valkey_service.ttl(CACHE_KEY_LATEST)
    if ttl is None:
        return None

    age = CACHE_TTL_SECONDS - ttl
    return max(0, age)


@readyz_bp.route("/readyz", methods=["GET"])
def readyz():
    """Return readiness status of the application.

    The endpoint returns HTTP 200 unless ALL of the following are true:
    - More than 50% (50% + 1) of the configured senseBoxes are not accessible.
    - The cached content is older than 5 minutes.

    If both conditions are met, returns HTTP 503 Service Unavailable.

    Returns:
        JSON response with status and diagnostic information.
    """
    accessible, total = check_sensebox_accessibility()
    cache_age_seconds = get_cache_age_seconds()

    inaccessible = total - accessible
    threshold = total // 2
    too_many_inaccessible = inaccessible > threshold

    cache_too_old = False
    if cache_age_seconds is not None:
        cache_too_old = cache_age_seconds > (CACHE_MAX_AGE_MINUTES * 60)

    response_data = {
        "status": "ready",
        "sensebox": {
            "accessible": accessible,
            "total": total,
            "inaccessible": inaccessible,
        },
        "cache": {
            "age_seconds": cache_age_seconds,
            "max_age_seconds": CACHE_MAX_AGE_MINUTES * 60,
        }
    }

    if too_many_inaccessible and cache_too_old:
        response_data["status"] = "not_ready"
        response_data["reason"] = (
            f"More than 50% of senseBoxes are inaccessible "
            f"({inaccessible}/{total}) and cached data is older than "
            f"{CACHE_MAX_AGE_MINUTES} minutes."
        )
        logger.warning(
            "Readiness check failed: %d/%d senseBoxes inaccessible, "
            "cache age %s seconds",
            inaccessible,
            total,
            cache_age_seconds,
        )
        return jsonify(response_data), 503

    return jsonify(response_data), 200
