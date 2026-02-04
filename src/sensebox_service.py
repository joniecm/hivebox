"""Service module for fetching and processing senseBox data.

This module handles interactions with the openSenseMap API.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any


# List of senseBox IDs to fetch temperature data from
SENSEBOX_IDS = [
    "5c647389a100840019eea656",
    "66268770eaca630008ec4f9e",
    "6570eb180db9850007f21abe"
]

OPENSENSEMAP_API_BASE = "https://api.opensensemap.org"
# German name used in openSenseMap
TEMPERATURE_SENSOR_PHENOMENON = "Temperatur"


def get_sensebox_data(box_id: str) -> Optional[Dict]:
    """Fetch data for a single senseBox.

    Args:
        box_id: The unique identifier of the senseBox.

    Returns:
        Dictionary containing senseBox data, or None if request fails.
    """
    try:
        url = f"{OPENSENSEMAP_API_BASE}/boxes/{box_id}"
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def extract_temperature_value(box_data: Dict) -> Optional[Dict[str, Any]]:
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
        if sensor.get("title") == TEMPERATURE_SENSOR_PHENOMENON:
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


def is_data_fresh(timestamp: datetime, max_age_hours: int = 1) -> bool:
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
    box_ids: List[str] = None
) -> Optional[float]:
    """Calculate average temperature from multiple senseBoxes.

    Fetches temperature data from all specified senseBoxes and returns
    the average value. Only includes data that is no older than 1 hour.

    Args:
        box_ids: List of senseBox IDs. If None, uses default SENSEBOX_IDS.

    Returns:
        Average temperature as float, or None if no valid data is available.
    """
    if box_ids is None:
        box_ids = SENSEBOX_IDS

    temperatures = []

    for box_id in box_ids:
        box_data = get_sensebox_data(box_id)
        if box_data:
            temp_data = extract_temperature_value(box_data)
            if temp_data:
                if is_data_fresh(temp_data["timestamp"]):
                    temperatures.append(temp_data["value"])

    if not temperatures:
        return None

    return sum(temperatures) / len(temperatures)
