"""Service module for temperature business logic."""

from dataclasses import dataclass
from typing import List, Optional

from src.background.temperature_flusher import collect_temperature_record
from src.services.minio_service import MinioService
from src.services.sensebox_service import SenseBoxService


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


@dataclass(frozen=True)
class TemperatureResponse:
    average_temperature: float
    status: str


sensebox_service = SenseBoxService()


def get_temperature_status(temperature: float) -> str:
    """Return the status label for the given temperature."""
    return TemperatureService.get_temperature_status(temperature)


def get_latest_temperature_response() -> Optional[TemperatureResponse]:
    """Fetch the latest temperature response.

    Prefers fresh data from senseBoxes. Falls back to the latest MinIO record
    when live data is unavailable.
    """
    average, sources = sensebox_service.get_average_temperature_with_sources()
    used_fallback = False

    if average is None:
        minio_service = MinioService.from_env()
        if minio_service is None:
            return None
        latest_record = minio_service.get_latest_record()
        if latest_record is None:
            return None
        average = latest_record.average_temperature
        sources = latest_record.source_hivebox_ids
        used_fallback = True

    rounded_average = round(average, 2)
    if not used_fallback:
        collect_temperature_record(rounded_average, sources)

    return TemperatureResponse(
        average_temperature=rounded_average,
        status=get_temperature_status(rounded_average),
    )
