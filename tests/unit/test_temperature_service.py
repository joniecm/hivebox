import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src.services.minio_service import TemperatureRecord
from src.services.temperature_service import (
    TemperatureResponse,
    get_latest_temperature_response,
    get_temperature_status,
)


class TestTemperatureService(unittest.TestCase):
    """Test cases for temperature_service module."""

    def test_get_temperature_status_too_cold(self):
        self.assertEqual(get_temperature_status(5.0), "Too Cold")

    def test_get_temperature_status_good_range(self):
        self.assertEqual(get_temperature_status(10.0), "Good")
        self.assertEqual(get_temperature_status(20.0), "Good")
        self.assertEqual(get_temperature_status(36.0), "Good")

    def test_get_temperature_status_too_hot(self):
        self.assertEqual(get_temperature_status(36.1), "Too Hot")

    @patch("src.services.temperature_service.MinioService.from_env")
    @patch(
        "src.services.temperature_service."
        "sensebox_service.get_average_temperature_with_sources"
    )
    def test_get_latest_temperature_response_none(
        self,
        mock_get_average,
        mock_from_env,
    ):
        mock_get_average.return_value = (None, [], None)
        mock_from_env.return_value = None
        self.assertIsNone(get_latest_temperature_response())

    @patch("src.services.temperature_service.collect_temperature_record")
    @patch(
        "src.services.temperature_service."
        "sensebox_service.get_average_temperature_with_sources"
    )
    def test_get_latest_temperature_response_rounds(
        self,
        mock_get_average,
        mock_collect,
    ):
        mock_get_average.return_value = (22.456, ["box-1"], datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
        mock_collect.return_value = TemperatureRecord(
            average_temperature=22.456,
            timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_hivebox_ids=["box-1"],
        )
        response = get_latest_temperature_response()
        self.assertIsInstance(response, TemperatureResponse)
        self.assertEqual(response.average_temperature, 22.46)
        self.assertEqual(response.status, "Good")


if __name__ == "__main__":
    unittest.main()
