import logging
from dataclasses import dataclass
from typing import Optional

from src.background.temperature_flusher import (
    collect_temperature_record
)
from src.services.minio_service import MinioService
from src.services.sensebox_service import sensebox_service


logger = logging.getLogger(__name__)

_minio_service: MinioService | None = None


@dataclass(frozen=True)
class TemperatureResponse:
    average_temperature: float
    status: str


def get_temperature_status(temperature: float) -> str:
    """Determine temperature status based on the average temperature.

    Args:
        temperature: The average temperature value.

    Returns:
        Status string: "Too Cold", "Good", or "Too Hot".
    """
    if temperature < 10:
        return "Too Cold"
    if temperature <= 36:
        return "Good"
    return "Too Hot"


def get_latest_temperature_response() -> Optional[TemperatureResponse]:
    """Return latest temperature response, preferring live senseBox data.

    Returns:
        TemperatureResponse or None if no data is available.
    """
    global _minio_service

    average_temperature, source_ids = (
        sensebox_service.get_average_temperature_with_sources()
    )
    if average_temperature is not None:
        record = collect_temperature_record(average_temperature, source_ids)
        status = get_temperature_status(record.average_temperature)
        logger.debug("Built live temperature response with status %s.", status)
        return TemperatureResponse(
            average_temperature=round(record.average_temperature, 2),
            status=status,
        )

    if _minio_service is None:
        _minio_service = MinioService.from_env()
    latest_record = None
    if _minio_service is not None:
        latest_record = _minio_service.get_latest_record()
    if latest_record is None:
        logger.debug("No temperature record available from MinIO.")
        return None
    status = get_temperature_status(latest_record.average_temperature)
    logger.debug("Built backup temperature response with status %s.", status)
    return TemperatureResponse(
        average_temperature=round(latest_record.average_temperature, 2),
        status=status,
    )
