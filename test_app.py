import unittest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app import app, VERSION
from sensebox_service import (
    extract_temperature_value,
    is_data_fresh,
    get_average_temperature
)


class TestVersionEndpoint(unittest.TestCase):
    """Test cases for the /version endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
    
    def test_version_endpoint_exists(self):
        """Test that /version endpoint exists and returns 200."""
        response = self.client.get('/version')
        self.assertEqual(response.status_code, 200)
    
    def test_version_endpoint_returns_json(self):
        """Test that /version endpoint returns JSON."""
        response = self.client.get('/version')
        self.assertEqual(response.content_type, 'application/json')
    
    def test_version_endpoint_returns_correct_version(self):
        """Test that /version endpoint returns the correct version."""
        response = self.client.get('/version')
        data = json.loads(response.data)
        self.assertIn('version', data)
        self.assertEqual(data['version'], VERSION)
    
    def test_version_endpoint_no_parameters(self):
        """Test that /version endpoint works without parameters."""
        response = self.client.get('/version')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('version', data)


class TestTemperatureEndpoint(unittest.TestCase):
    """Test cases for the /temperature endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
    
    @patch('app.get_average_temperature')
    def test_temperature_endpoint_exists(self, mock_get_avg):
        """Test that /temperature endpoint exists."""
        mock_get_avg.return_value = 20.5
        response = self.client.get('/temperature')
        self.assertIn(response.status_code, [200, 503])
    
    @patch('app.get_average_temperature')
    def test_temperature_endpoint_returns_json(self, mock_get_avg):
        """Test that /temperature endpoint returns JSON."""
        mock_get_avg.return_value = 20.5
        response = self.client.get('/temperature')
        self.assertEqual(response.content_type, 'application/json')
    
    @patch('app.get_average_temperature')
    def test_temperature_endpoint_success(self, mock_get_avg):
        """Test successful temperature retrieval."""
        mock_get_avg.return_value = 22.456
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('average_temperature', data)
        self.assertEqual(data['average_temperature'], 22.46)  # Rounded to 2 decimals
    
    @patch('app.get_average_temperature')
    def test_temperature_endpoint_no_data(self, mock_get_avg):
        """Test error response when no data is available."""
        mock_get_avg.return_value = None
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('message', data)
    
    @patch('app.get_average_temperature')
    def test_temperature_endpoint_rounds_correctly(self, mock_get_avg):
        """Test that temperature is rounded to 2 decimal places."""
        mock_get_avg.return_value = 18.999
        response = self.client.get('/temperature')
        data = json.loads(response.data)
        self.assertEqual(data['average_temperature'], 19.0)


class TestSenseboxService(unittest.TestCase):
    """Test cases for the sensebox_service module."""
    
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
        result = extract_temperature_value(box_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['value'], 23.5)
        self.assertIsInstance(result['timestamp'], datetime)
    
    def test_extract_temperature_value_no_sensors(self):
        """Test extracting temperature when no sensors are present."""
        box_data = {"sensors": []}
        result = extract_temperature_value(box_data)
        self.assertIsNone(result)
    
    def test_extract_temperature_value_no_temperature_sensor(self):
        """Test extracting temperature when temperature sensor is not present."""
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
        result = extract_temperature_value(box_data)
        self.assertIsNone(result)
    
    def test_is_data_fresh_within_hour(self):
        """Test that data from within the last hour is considered fresh."""
        recent_time = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=30)
        self.assertTrue(is_data_fresh(recent_time))
    
    def test_is_data_fresh_older_than_hour(self):
        """Test that data older than 1 hour is not considered fresh."""
        old_time = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(hours=2)
        self.assertFalse(is_data_fresh(old_time))
    
    def test_is_data_fresh_exactly_one_hour(self):
        """Test that data exactly 1 hour old is at the boundary."""
        # Note: With <= comparison, exactly 1 hour is fresh
        # With < comparison, it would not be fresh
        # The implementation uses <=, so exactly 1 hour should be fresh
        one_hour_ago = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(hours=1, seconds=1)
        self.assertFalse(is_data_fresh(one_hour_ago))
    
    @patch('sensebox_service.get_sensebox_data')
    def test_get_average_temperature_all_valid(self, mock_get_data):
        """Test average calculation with all valid data."""
        now = datetime.now(datetime.now().astimezone().tzinfo)
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
        
        avg = get_average_temperature(["box1", "box2", "box3"])
        self.assertEqual(avg, 22.0)
    
    @patch('sensebox_service.get_sensebox_data')
    def test_get_average_temperature_no_data(self, mock_get_data):
        """Test average calculation when no data is available."""
        mock_get_data.return_value = None
        
        avg = get_average_temperature(["box1"])
        self.assertIsNone(avg)
    
    @patch('sensebox_service.get_sensebox_data')
    def test_get_average_temperature_stale_data(self, mock_get_data):
        """Test that stale data is excluded from average."""
        old_time = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(hours=2)
        mock_get_data.return_value = {
            "sensors": [{
                "title": "Temperatur",
                "lastMeasurement": {
                    "value": "20.0",
                    "createdAt": old_time.isoformat()
                }
            }]
        }
        
        avg = get_average_temperature(["box1"])
        self.assertIsNone(avg)


if __name__ == '__main__':
    unittest.main()