from datetime import datetime, timedelta, timezone

import pytest
import requests

from app import app
from sensebox_service import SENSEBOX_IDS, TEMPERATURE_SENSOR_PHENOMENON


class DummyResponse:
    """Mock HTTP response for testing."""
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")

    def json(self):
        return self._payload


@pytest.fixture()
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.mark.integration
def test_temperature_endpoint_integration(client, monkeypatch):
    """Test the temperature endpoint with successful data from all boxes."""
    values = {
        SENSEBOX_IDS[0]: 20.0,
        SENSEBOX_IDS[1]: 22.0,
        SENSEBOX_IDS[2]: 24.0,
    }

    def fake_get(url, timeout):
        box_id = url.rsplit("/", 1)[-1]
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "sensors": [
                {
                    "title": TEMPERATURE_SENSOR_PHENOMENON,
                    "lastMeasurement": {
                        "value": str(values[box_id]),
                        "createdAt": now,
                    },
                }
            ]
        }
        return DummyResponse(payload)

    monkeypatch.setattr("sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["average_temperature"] == 22.0
    assert payload["status"] == "Good"


@pytest.mark.integration
def test_temperature_endpoint_api_timeout(client, monkeypatch):
    """Test the temperature endpoint handles API timeout errors."""
    def fake_get_timeout(url, timeout):
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr("sensebox_service.requests.get", fake_get_timeout)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_connection_error(client, monkeypatch):
    """Test the temperature endpoint handles connection errors."""
    def fake_get_connection_error(url, timeout):
        raise requests.ConnectionError("Failed to connect")

    monkeypatch.setattr("sensebox_service.requests.get", fake_get_connection_error)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_http_error(client, monkeypatch):
    """Test the temperature endpoint handles HTTP error responses."""
    def fake_get_http_error(url, timeout):
        response = DummyResponse({}, status_code=500)
        return response

    monkeypatch.setattr("sensebox_service.requests.get", fake_get_http_error)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_missing_sensors(client, monkeypatch):
    """Test the temperature endpoint handles missing sensor data."""
    def fake_get(url, timeout):
        # Return data without sensors field
        payload = {"name": "TestBox"}
        return DummyResponse(payload)

    monkeypatch.setattr("sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_no_temperature_sensor(client, monkeypatch):
    """Test the temperature endpoint handles missing temperature sensor."""
    def fake_get(url, timeout):
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "sensors": [
                {
                    "title": "Humidity",  # Wrong sensor type
                    "lastMeasurement": {
                        "value": "65.0",
                        "createdAt": now,
                    },
                }
            ]
        }
        return DummyResponse(payload)

    monkeypatch.setattr("sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_invalid_temperature_value(client, monkeypatch):
    """Test the temperature endpoint handles invalid temperature values."""
    def fake_get(url, timeout):
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "sensors": [
                {
                    "title": TEMPERATURE_SENSOR_PHENOMENON,
                    "lastMeasurement": {
                        "value": "invalid",  # Non-numeric value
                        "createdAt": now,
                    },
                }
            ]
        }
        return DummyResponse(payload)

    monkeypatch.setattr("sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_stale_data(client, monkeypatch):
    """Test the temperature endpoint rejects stale data older than 1 hour."""
    def fake_get(url, timeout):
        # Data from 2 hours ago
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "sensors": [
                {
                    "title": TEMPERATURE_SENSOR_PHENOMENON,
                    "lastMeasurement": {
                        "value": "25.0",
                        "createdAt": old_time.isoformat(),
                    },
                }
            ]
        }
        return DummyResponse(payload)

    monkeypatch.setattr("sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
    assert "older than 1 hour" in payload["message"]


@pytest.mark.integration
def test_temperature_endpoint_mixed_valid_and_failed(client, monkeypatch):
    """Test the temperature endpoint with mixed results: some valid, some failed."""
    def fake_get(url, timeout):
        box_id = url.rsplit("/", 1)[-1]
        
        # First box: valid fresh data
        if box_id == SENSEBOX_IDS[0]:
            now = datetime.now(timezone.utc).isoformat()
            payload = {
                "sensors": [
                    {
                        "title": TEMPERATURE_SENSOR_PHENOMENON,
                        "lastMeasurement": {
                            "value": "20.0",
                            "createdAt": now,
                        },
                    }
                ]
            }
            return DummyResponse(payload)
        
        # Second box: stale data (should be ignored)
        elif box_id == SENSEBOX_IDS[1]:
            old_time = datetime.now(timezone.utc) - timedelta(hours=2)
            payload = {
                "sensors": [
                    {
                        "title": TEMPERATURE_SENSOR_PHENOMENON,
                        "lastMeasurement": {
                            "value": "100.0",  # High value that would skew average
                            "createdAt": old_time.isoformat(),
                        },
                    }
                ]
            }
            return DummyResponse(payload)
        
        # Third box: connection error
        else:
            raise requests.ConnectionError("Failed to connect")

    monkeypatch.setattr("sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    # Should succeed with only the valid data from the first box
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["average_temperature"] == 20.0
    assert payload["status"] == "Good"


@pytest.mark.integration
def test_temperature_endpoint_mixed_all_failed(client, monkeypatch):
    """Test the temperature endpoint when all boxes fail in different ways."""
    def fake_get(url, timeout):
        box_id = url.rsplit("/", 1)[-1]
        
        # First box: timeout
        if box_id == SENSEBOX_IDS[0]:
            raise requests.Timeout("Connection timeout")
        
        # Second box: stale data
        elif box_id == SENSEBOX_IDS[1]:
            old_time = datetime.now(timezone.utc) - timedelta(hours=3)
            payload = {
                "sensors": [
                    {
                        "title": TEMPERATURE_SENSOR_PHENOMENON,
                        "lastMeasurement": {
                            "value": "25.0",
                            "createdAt": old_time.isoformat(),
                        },
                    }
                ]
            }
            return DummyResponse(payload)
        
        # Third box: missing sensor data
        else:
            return DummyResponse({"sensors": []})

    monkeypatch.setattr("sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    # Should fail with 503 as no valid data is available
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
