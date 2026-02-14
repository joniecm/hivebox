import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from src.services.sensebox_service import SenseBoxService


class TestSenseboxService(unittest.TestCase):
    """Test cases for the sensebox_service module."""

    def setUp(self):
        self.service = SenseBoxService()

    @staticmethod
    def get_aware_now():
        """Helper method to get timezone-aware current datetime."""
        return datetime.now().astimezone()

    def test_extract_temperature_value_valid_data(self):
        """Test extracting temperature from valid senseBox data."""
        box_data = {
            "sensors": [
                {
                    "title": "Temperatur",
                    "lastMeasurement": {
                        "value": "23.5",
                        "createdAt": "2026-01-14T22:00:00.000Z"
                    }
                }
            ]
        }
        result = self.service._extract_temperature_value(box_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['value'], 23.5)
        self.assertIsInstance(result['timestamp'], datetime)

    def test_extract_temperature_value_no_sensors(self):
        """Test extracting temperature when no sensors are present."""
        box_data = {"sensors": []}
        result = self.service._extract_temperature_value(box_data)
        self.assertIsNone(result)

    def test_extract_temperature_value_no_temperature_sensor(self):
        """Test extracting temperature when no temperature sensor."""
        box_data = {
            "sensors": [
                {
                    "title": "Humidity",
                    "lastMeasurement": {
                        "value": "65.0",
                        "createdAt": "2026-01-14T22:00:00.000Z"
                    }
                }
            ]
        }
        result = self.service._extract_temperature_value(box_data)
        self.assertIsNone(result)

    def test_is_data_fresh_within_hour(self):
        """Test that data from within the last hour is considered fresh."""
        recent_time = self.get_aware_now() - timedelta(minutes=30)
        self.assertTrue(self.service._is_data_fresh(recent_time))

    def test_is_data_fresh_older_than_hour(self):
        """Test that data older than 1 hour is not considered fresh."""
        old_time = self.get_aware_now() - timedelta(hours=2)
        self.assertFalse(self.service._is_data_fresh(old_time))

    def test_is_data_fresh_exactly_one_hour(self):
        """Test that data exactly 1 hour old is at the boundary."""
        # The implementation uses <=, so exactly 1 hour should be fresh.
        fixed_now = datetime(2026, 1, 14, 22, 0, 0, tzinfo=timezone.utc)
        one_hour_ago = fixed_now - timedelta(hours=1)
        with patch("src.services.sensebox_service.datetime") as mock_datetime:
            mock_datetime.now.side_effect = lambda tz=None: fixed_now
            self.assertTrue(self.service._is_data_fresh(one_hour_ago))

    @patch.object(SenseBoxService, "_get_sensebox_data")
    def test_get_average_temperature_all_valid(self, mock_get_data):
        """Test average calculation with all valid data."""
        now = self.get_aware_now()
        mock_get_data.side_effect = [
            {
                "sensors": [{
                    "title": "Temperatur",
                    "lastMeasurement": {
                        "value": "20.0",
                        "createdAt": now.isoformat()
                    }
                }]
            },
            {
                "sensors": [{
                    "title": "Temperatur",
                    "lastMeasurement": {
                        "value": "22.0",
                        "createdAt": now.isoformat()
                    }
                }]
            },
            {
                "sensors": [{
                    "title": "Temperatur",
                    "lastMeasurement": {
                        "value": "24.0",
                        "createdAt": now.isoformat()
                    }
                }]
            }
        ]

        avg = self.service.get_average_temperature_for_fresh_data(
            ["box1", "box2", "box3"]
        )
        self.assertEqual(avg, 22.0)

    @patch.object(SenseBoxService, "_get_sensebox_data")
    def test_get_average_temperature_no_data(self, mock_get_data):
        """Test average calculation when no data is available."""
        mock_get_data.return_value = None

        avg = self.service.get_average_temperature_for_fresh_data(["box1"])
        self.assertIsNone(avg)

    @patch.object(SenseBoxService, "_get_sensebox_data")
    def test_get_average_temperature_stale_data(self, mock_get_data):
        """Test that stale data is excluded from average."""
        old_time = self.get_aware_now() - timedelta(hours=2)
        mock_get_data.return_value = {
            "sensors": [{
                "title": "Temperatur",
                "lastMeasurement": {
                    "value": "20.0",
                    "createdAt": old_time.isoformat()
                }
            }]
        }

        avg = self.service.get_average_temperature_for_fresh_data(["box1"])
        self.assertIsNone(avg)
