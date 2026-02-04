from datetime import datetime, timezone

import pytest
import requests

from src.app import app
from src.sensebox_service import SENSEBOX_IDS, TEMPERATURE_SENSOR_PHENOMENON


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

    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"status={self.status_code}")

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
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

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get)

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

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get_timeout)

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
        "src.sensebox_service.requests.get",
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
        "src.sensebox_service.requests.get", fake_get_http_error
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
            pass

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
        # Return data without sensors field
        payload = {"name": "TestBox"}
        return DummyResponse(payload)

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get)

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
            pass

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
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

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get)

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
            pass

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
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

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_stale_data(client, monkeypatch):
    """Test the temperature endpoint rejects stale data older than 1 hour."""
    from datetime import timedelta

    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            pass

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
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

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
    assert "older than 1 hour" in payload["message"]


@pytest.mark.integration
def test_temperature_endpoint_mixed_valid_and_failed(client, monkeypatch):
    """Test temperature endpoint with mixed results.

    Some senseBoxes return valid data while others fail.
    """
    from datetime import timedelta

    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"status={self.status_code}")

        def json(self):
            return self._payload

    def fake_get(url, timeout=None):
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
                            # High value that would skew average
                            "value": "100.0",
                            "createdAt": old_time.isoformat(),
                        },
                    }
                ]
            }
            return DummyResponse(payload)

        # Third box: connection error
        else:
            raise requests.ConnectionError("Failed to connect")

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    # Should succeed with only the valid data from the first box
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["average_temperature"] == 20.0
    assert payload["status"] == "Good"


@pytest.mark.integration
def test_temperature_endpoint_mixed_all_failed(client, monkeypatch):
    """Test the temperature endpoint when all boxes fail in different ways."""
    from datetime import timedelta

    call_count = [0]

    def fake_get(url, timeout=None):
        box_id = url.rsplit("/", 1)[-1]
        call_count[0] += 1

        # First box: timeout
        if box_id == SENSEBOX_IDS[0]:
            raise requests.Timeout("Connection timeout")

        # Second box: stale data
        elif box_id == SENSEBOX_IDS[1]:
            old_time = datetime.now(timezone.utc) - timedelta(hours=3)

            class DummyResponse:
                status_code = 200

                def raise_for_status(self):
                    pass

                def json(self):
                    return {
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

            return DummyResponse()

        # Third box: missing sensor data
        else:
            class DummyResponse:
                status_code = 200

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"sensors": []}

            return DummyResponse()

    monkeypatch.setattr("src.sensebox_service.requests.get", fake_get)

    response = client.get("/temperature")
    # Should fail with 503 as no valid data is available
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
