"""Service module for fetching and processing senseBox data.

This module handles interactions with the openSenseMap API.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


# List of senseBox IDs to fetch temperature data from
SENSEBOX_IDS = [
    "5c647389a100840019eea656",
    "66268770eaca630008ec4f9e",
    "6570eb180db9850007f21abe",
]

OPENSENSEMAP_API_BASE = "https://api.opensensemap.org"
# German name used in openSenseMap
TEMPERATURE_SENSOR_PHENOMENON = "Temperatur"

logger = logging.getLogger(__name__)


def _get_timeout_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class SenseBoxService:
    """Service for fetching and processing senseBox data."""

    def __init__(
        self,
        box_ids: Optional[List[str]] = None,
        api_base: str = OPENSENSEMAP_API_BASE,
        temperature_sensor_phenomenon: str = TEMPERATURE_SENSOR_PHENOMENON,
        timeout_seconds: int = 2,
        read_timeout_seconds: int = 5,
    ) -> None:
        self.box_ids = box_ids or list(SENSEBOX_IDS)
        self.api_base = api_base
        self.temperature_sensor_phenomenon = temperature_sensor_phenomenon
        self.timeout_seconds = timeout_seconds
        self.read_timeout_seconds = read_timeout_seconds

    def get_sensebox_data(self, box_id: str) -> Optional[Dict]:
        """Fetch data for a single senseBox.

        Args:
            box_id: The unique identifier of the senseBox.

        Returns:
            Dictionary containing senseBox data, or None if request fails.
        """
        try:
            url = f"{self.api_base}/boxes/{box_id}"
            logger.debug(
                "Requesting senseBox %s with timeouts connect=%ss read=%ss",
                box_id,
                self.timeout_seconds,
                self.read_timeout_seconds,
            )
            response = requests.get(
                url,
                timeout=(self.timeout_seconds, self.read_timeout_seconds),
            )
            response.raise_for_status()
            logger.debug(
                "Received senseBox %s response status=%s content_length=%s",
                box_id,
                response.status_code,
                response.headers.get("Content-Length", "unknown"),
            )
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Failed to fetch senseBox %s: %s", box_id, exc)
            return None

    def extract_temperature_value(self, box_data: Dict) -> Optional[Dict[str, Any]]:
        """Extract temperature sensor value and timestamp from senseBox data.

        Args:
            box_data: Dictionary containing senseBox data.

        Returns:
            Dictionary with 'value' (float) and 'timestamp' (datetime),
            or None if not found.
        """
        if not box_data or "sensors" not in box_data:
            logger.debug("senseBox payload missing sensors array.")
            return None

        for sensor in box_data.get("sensors", []):
            if sensor.get("title") == self.temperature_sensor_phenomenon:
                last_measurement = sensor.get("lastMeasurement")
                if last_measurement:
                    try:
                        value = float(last_measurement.get("value"))
                        timestamp_str = last_measurement.get("createdAt")
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                        logger.debug(
                            "Extracted temperature %.2f from senseBox.",
                            value,
                        )
                        return {"value": value, "timestamp": timestamp}
                    except (ValueError, TypeError, AttributeError):
                        pass

        return None

    def is_data_fresh(self, timestamp: datetime, max_age_hours: int = 1) -> bool:
        """Check if data timestamp is within the acceptable age.

        Args:
            timestamp: The timestamp of the measurement.
            max_age_hours: Maximum age in hours (default: 1).

        Returns:
            True if data is fresh, False otherwise.
        """
        now = datetime.now(timestamp.tzinfo)
        max_age = timedelta(hours=max_age_hours)
        is_fresh = (now - timestamp) <= max_age
        logger.debug(
            "senseBox data freshness=%s age_seconds=%.1f max_age_hours=%s",
            is_fresh,
            (now - timestamp).total_seconds(),
            max_age_hours,
        )
        return is_fresh

    def get_average_temperature_for_fresh_data(
        self,
        box_ids: Optional[List[str]] = None,
    ) -> Optional[float]:
        """Calculate average temperature from multiple senseBoxes.

        Fetches temperature data from all specified senseBoxes and returns
        the average value. Only includes data that is no older than 1 hour.

        Args:
            box_ids: List of senseBox IDs. If None, uses default box IDs.

        Returns:
            Average temperature as float, or None if no valid data is available.
        """
        selected_ids = box_ids or self.box_ids
        temperatures: List[float] = []

        for box_id in selected_ids:
            box_data = self.get_sensebox_data(box_id)
            if box_data:
                temp_data = self.extract_temperature_value(box_data)
                if temp_data and self.is_data_fresh(temp_data["timestamp"]):
                    temperatures.append(temp_data["value"])

        if not temperatures:
            logger.info("No fresh temperature data available from senseBoxes.")
            return None

        return sum(temperatures) / len(temperatures)

    def get_average_temperature_with_sources(
        self,
        box_ids: Optional[List[str]] = None,
    ) -> tuple[Optional[float], List[str]]:
        """Calculate average temperature and return contributing senseBox IDs.

        Args:
            box_ids: List of senseBox IDs. If None, uses default box IDs.

        Returns:
            Tuple of (average temperature or None, list of contributing box IDs).
        """
        selected_ids = box_ids or self.box_ids
        temperatures: List[float] = []
        used_ids: List[str] = []

        for box_id in selected_ids:
            box_data = self.get_sensebox_data(box_id)
            if box_data:
                temp_data = self.extract_temperature_value(box_data)
                if temp_data and self.is_data_fresh(temp_data["timestamp"]):
                    temperatures.append(temp_data["value"])
                    used_ids.append(box_id)
                else:
                    logger.debug(
                        "Skipping senseBox %s due to missing/stale temperature.",
                        box_id,
                    )
            else:
                logger.debug("No data returned for senseBox %s.", box_id)

        if not temperatures:
            logger.info("No fresh temperature data available from senseBoxes.")
            return None, []

        return sum(temperatures) / len(temperatures), used_ids

connect_timeout = _get_timeout_env("SENSEBOX_CONNECT_TIMEOUT", 2)
read_timeout = _get_timeout_env("SENSEBOX_READ_TIMEOUT", 5)
sensebox_service = SenseBoxService(
    timeout_seconds=connect_timeout,
    read_timeout_seconds=read_timeout,
)
