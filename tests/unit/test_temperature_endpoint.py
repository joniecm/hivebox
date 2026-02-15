import unittest
import json
from unittest.mock import patch

from src.app import app
from src.services.temperature_service import TemperatureResponse


class TestTemperatureEndpoint(unittest.TestCase):
    """Test cases for the /temperature endpoint."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_endpoint_exists(self, mock_get_response):
        """Test that /temperature endpoint exists."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=20.5,
            status="Good",
        )
        response = self.client.get('/temperature')
        self.assertIn(response.status_code, [200, 503])

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_endpoint_returns_json(self, mock_get_response):
        """Test that /temperature endpoint returns JSON."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=20.5,
            status="Good",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.content_type, 'application/json')

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_endpoint_success(self, mock_get_response):
        """Test successful temperature retrieval."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=22.46,
            status="Good",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('average_temperature', data)
        self.assertEqual(data['average_temperature'], 22.46)

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_endpoint_no_data(self, mock_get_response):
        """Test error response when no data is available."""
        mock_get_response.return_value = None
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('message', data)

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_endpoint_rounds_correctly(self, mock_get_response):
        """Test that temperature is rounded to 2 decimal places."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=19.0,
            status="Good",
        )
        response = self.client.get('/temperature')
        data = json.loads(response.data)
        self.assertEqual(data['average_temperature'], 19.0)

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_status_too_cold(self, mock_get_response):
        """Test status is 'Too Cold' when temperature is less than 10."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=5.0,
            status="Too Cold",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Too Cold')

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_status_good_lower_bound(self, mock_get_response):
        """Test status is 'Good' at lower boundary (10)."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=10.0,
            status="Good",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Good')

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_status_good_middle(self, mock_get_response):
        """Test status is 'Good' in the middle of range (20)."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=20.0,
            status="Good",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Good')

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_status_good_upper_bound(self, mock_get_response):
        """Test status is 'Good' at upper boundary (36)."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=36.0,
            status="Good",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Good')

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_status_too_hot(self, mock_get_response):
        """Test status is 'Too Hot' when temperature is more than 36."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=40.0,
            status="Too Hot",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Too Hot')

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_status_too_hot_boundary(self, mock_get_response):
        """Test status is 'Too Hot' at boundary (37, just above 36)."""
        mock_get_response.return_value = TemperatureResponse(
            average_temperature=37.0,
            status="Too Hot",
        )
        response = self.client.get('/temperature')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Too Hot')
