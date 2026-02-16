"""Service module for temperature business logic."""

import logging
import threading
from dataclasses import dataclass
from typing import List, Optional

from src.background.temperature_flusher import collect_temperature_record
from src.services.minio_service import MinioService
from src.services.sensebox_service import SenseBoxService
from src.services.valkey_service import ValkeyService


# List of senseBox IDs to fetch temperature data from
SENSEBOX_IDS = [
    "5c647389a100840019eea656",
    "66268770eaca630008ec4f9e",
    "6570eb180db9850007f21abe",
]


class TemperatureService:
    """Business logic for temperature-related operations."""

    def __init__(self, sensebox_ids: Optional[List[str]] = None) -> None:
        self._sensebox_ids = (
            list(sensebox_ids)
            if sensebox_ids is not None
            else list(SENSEBOX_IDS)
        )

    def get_sensebox_ids(self) -> List[str]:
        """Return the senseBox IDs that should be used for temperature data."""
        return list(self._sensebox_ids)

    @staticmethod
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


logger = logging.getLogger(__name__)

CACHE_KEY_LATEST = "temperature:latest:v1"
CACHE_LOCK_KEY = "temperature:latest:lock"
CACHE_TTL_SECONDS = 60
CACHE_REFRESH_THRESHOLD_SECONDS = 10


@dataclass(frozen=True)
class TemperatureResponse:
    average_temperature: float
    status: str
    data_age_seconds: Optional[float] = None


sensebox_service = SenseBoxService(SENSEBOX_IDS)
valkey_service = ValkeyService.from_env()


def get_temperature_status(temperature: float) -> str:
    """Return the status label for the given temperature."""
    return TemperatureService.get_temperature_status(temperature)


def get_latest_temperature_response() -> Optional[TemperatureResponse]:
    """Fetch the latest temperature response.

    Prefers fresh data from senseBoxes. Falls back to the latest MinIO record
    when live data is unavailable.
    """
    average, sources, newest_timestamp = (
        sensebox_service.get_average_temperature_with_sources(SENSEBOX_IDS)
    )
    used_fallback = False
    data_age_seconds = None

    if average is None:
        logger.info("No live temperature data; trying MinIO fallback.")
        minio_service = MinioService.from_env()
        if minio_service is None:
            logger.warning("MinIO not configured; no fallback available.")
            return None
        latest_record = minio_service.get_latest_record()
        if latest_record is None:
            logger.warning("No stored temperature records found in MinIO.")
            return None
        average = latest_record.average_temperature
        sources = latest_record.source_hivebox_ids
        newest_timestamp = latest_record.timestamp
        used_fallback = True

    # Calculate data age if we have a timestamp
    if newest_timestamp is not None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        # Ensure both timestamps are timezone-aware
        if newest_timestamp.tzinfo is None:
            newest_timestamp = newest_timestamp.replace(tzinfo=timezone.utc)
        data_age_seconds = (now - newest_timestamp).total_seconds()

    rounded_average = round(average, 2)
    if not used_fallback:
        collect_temperature_record(rounded_average, sources)
    logger.info(
        "Latest temperature %.2f with status %s.",
        rounded_average,
        get_temperature_status(rounded_average),
    )

    return TemperatureResponse(
        average_temperature=rounded_average,
        status=get_temperature_status(rounded_average),
        data_age_seconds=data_age_seconds,
    )


def _serialize_temperature_response(
    response: TemperatureResponse,
) -> dict:
    return {
        "average_temperature": response.average_temperature,
        "status": response.status,
        "data_age_seconds": response.data_age_seconds,
    }


def _deserialize_temperature_response(
    payload: dict,
) -> Optional[TemperatureResponse]:
    try:
        data_age_value = payload.get("data_age_seconds")
        data_age_seconds = (
            float(data_age_value) if data_age_value is not None else None
        )

        return TemperatureResponse(
            average_temperature=float(payload["average_temperature"]),
            status=str(payload["status"]),
            data_age_seconds=data_age_seconds,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _refresh_cached_temperature_response() -> None:
    if valkey_service is None:
        return
    if not valkey_service.acquire_lock(CACHE_LOCK_KEY, ttl_seconds=5):
        return

    try:
        response = get_latest_temperature_response()
        if response is None:
            return
        valkey_service.set_json(
            CACHE_KEY_LATEST,
            _serialize_temperature_response(response),
            ttl_seconds=CACHE_TTL_SECONDS,
        )
    finally:
        valkey_service.release_lock(CACHE_LOCK_KEY)


def _refresh_cached_temperature_response_async() -> None:
    thread = threading.Thread(
        target=_refresh_cached_temperature_response,
        daemon=True,
    )
    thread.start()


def get_latest_temperature_response_cached() -> Optional[TemperatureResponse]:
    if valkey_service is None:
        return get_latest_temperature_response()

    cached_payload = valkey_service.get_json(CACHE_KEY_LATEST)
    if cached_payload:
        cached_response = _deserialize_temperature_response(cached_payload)
        if cached_response is not None:
            ttl = valkey_service.ttl(CACHE_KEY_LATEST)
            if ttl is not None and ttl <= CACHE_REFRESH_THRESHOLD_SECONDS:
                _refresh_cached_temperature_response_async()
            return cached_response

    response = get_latest_temperature_response()
    if response is None:
        return None
    valkey_service.set_json(
        CACHE_KEY_LATEST,
        _serialize_temperature_response(response),
        ttl_seconds=CACHE_TTL_SECONDS,
    )
    return response
