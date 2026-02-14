from datetime import datetime, timezone, timedelta

import pytest
import requests

from src.services.sensebox_service import TEMPERATURE_SENSOR_PHENOMENON


@pytest.mark.integration
def test_temperature_endpoint_api_timeout(client, monkeypatch):
    """Test the temperature endpoint handles API timeout errors."""
    def fake_get_timeout(url, timeout):
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get_timeout,
    )

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

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get_connection_error,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_http_error(client, monkeypatch):
    """Test the temperature endpoint handles HTTP error responses."""
    class DummyResponse:
        def __init__(self, status_code=500):
            self.status_code = status_code

        def raise_for_status(self):
            raise requests.HTTPError(f"HTTP {self.status_code}")

        def json(self):
            return {}

    def fake_get_http_error(url, timeout):
        return DummyResponse(status_code=500)

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get_http_error,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_missing_sensors(client, monkeypatch):
    """Test the temperature endpoint handles missing sensor data."""
    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
        payload = {"name": "TestBox"}
        return DummyResponse(payload)

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_no_temperature_sensor(client, monkeypatch):
    """Test the temperature endpoint handles missing temperature sensor."""
    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "sensors": [
                {
                    "title": "Humidity",
                    "lastMeasurement": {
                        "value": "65.0",
                        "createdAt": now,
                    },
                }
            ]
        }
        return DummyResponse(payload)

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_invalid_temperature_value(client, monkeypatch):
    """Test the temperature endpoint handles invalid temperature values."""
    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "sensors": [
                {
                    "title": TEMPERATURE_SENSOR_PHENOMENON,
                    "lastMeasurement": {
                        "value": "invalid",
                        "createdAt": now,
                    },
                }
            ]
        }
        return DummyResponse(payload)

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_stale_data(client, monkeypatch):
    """Test the temperature endpoint rejects stale data older than 1 hour."""
    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
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

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
    assert "older than 1 hour" in payload["message"]
