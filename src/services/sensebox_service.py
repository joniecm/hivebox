"""Service module for fetching and processing senseBox data.

This module handles interactions with the openSenseMap API.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any


OPENSENSEMAP_API_BASE = "https://api.opensensemap.org"
# German name used in openSenseMap
TEMPERATURE_SENSOR_PHENOMENON = "Temperatur"

logger = logging.getLogger(__name__)


class SenseBoxService:
    """Service for fetching and aggregating senseBox measurements."""

    def __init__(
        self,
        sensebox_ids: Optional[List[str]] = None,
        api_base: str = OPENSENSEMAP_API_BASE,
        temperature_sensor_phenomenon: str = TEMPERATURE_SENSOR_PHENOMENON,
    ) -> None:
        self.sensebox_ids = (
            list(sensebox_ids) if sensebox_ids is not None else []
        )
        self.api_base = api_base
        self.temperature_sensor_phenomenon = temperature_sensor_phenomenon

    def _get_sensebox_data(self, box_id: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a single senseBox.

        Args:
            box_id: The unique identifier of the senseBox.

        Returns:
            Dictionary containing senseBox data, or None if request fails.
        """
        try:
            url = f"{self.api_base}/boxes/{box_id}"
            response = requests.get(url, timeout=2)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning(
                "Failed to fetch senseBox %s data: %s",
                box_id,
                exc,
            )
            return None

    def _extract_temperature_value(
        self, box_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract temperature sensor value and timestamp from senseBox data.

        Args:
            box_data: Dictionary containing senseBox data.

        Returns:
            Dictionary with 'value' (float) and 'timestamp' (datetime),
            or None if not found.
        """
        if not box_data or "sensors" not in box_data:
            return None

        for sensor in box_data.get("sensors", []):
            if sensor.get("title") == self.temperature_sensor_phenomenon:
                last_measurement = sensor.get("lastMeasurement")
                if last_measurement:
                    try:
                        value = float(last_measurement.get("value"))
                        timestamp_str = last_measurement.get("createdAt")
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00"))
                        return {"value": value, "timestamp": timestamp}
                    except (ValueError, TypeError, AttributeError):
                        pass

        return None

    @staticmethod
    def _is_data_fresh(timestamp: datetime, max_age_hours: int = 1) -> bool:
        """Check if data timestamp is within the acceptable age.

        Args:
            timestamp: The timestamp of the measurement.
            max_age_hours: Maximum age in hours (default: 1).

        Returns:
            True if data is fresh, False otherwise.
        """
        now = datetime.now(timestamp.tzinfo)
        max_age = timedelta(hours=max_age_hours)
        return (now - timestamp) <= max_age

    def get_average_temperature_for_fresh_data(
        self, box_ids: Optional[List[str]] = None
    ) -> Optional[float]:
        """Calculate average temperature from multiple senseBoxes.

        Fetches temperature data from all specified senseBoxes and returns
        the average value. Only includes data that is no older than 1 hour.

        Args:
            box_ids: List of senseBox IDs. If None, uses configured IDs.

        Returns:
            Average temperature as float, or None if no valid data is
            available.
        """
        average, _ = self.get_average_temperature_with_sources(box_ids)
        return average

    def get_average_temperature_with_sources(
        self, box_ids: Optional[List[str]] = None
    ) -> tuple[Optional[float], list[str]]:
        """Calculate average temperature with contributing senseBox IDs.

        Args:
            box_ids: List of senseBox IDs. If None, uses configured IDs.

        Returns:
            Tuple of (average temperature, source box IDs).
        """
        if box_ids is None:
            box_ids = self.sensebox_ids

        temperatures = []
        sources = []

        for box_id in box_ids:
            box_data = self._get_sensebox_data(box_id)
            if box_data:
                temp_data = self._extract_temperature_value(box_data)
                if temp_data and self._is_data_fresh(temp_data["timestamp"]):
                    temperatures.append(temp_data["value"])
                    sources.append(box_id)

        if not temperatures:
            logger.info("No fresh temperature data found for senseBoxes.")
            return None, []

        return sum(temperatures) / len(temperatures), sources
