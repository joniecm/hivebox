from datetime import datetime, timezone, timedelta

import pytest
import requests

from src.services.sensebox_service import TEMPERATURE_SENSOR_PHENOMENON
from src.services.temperature_service import SENSEBOX_IDS


@pytest.mark.integration
def test_temperature_endpoint_mixed_valid_and_failed(client, monkeypatch):
    """Test temperature endpoint with mixed results.

    Some senseBoxes return valid data while others fail.
    """
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
        elif box_id == SENSEBOX_IDS[1]:
            old_time = datetime.now(timezone.utc) - timedelta(hours=2)
            payload = {
                "sensors": [
                    {
                        "title": TEMPERATURE_SENSOR_PHENOMENON,
                        "lastMeasurement": {
                            "value": "100.0",
                            "createdAt": old_time.isoformat(),
                        },
                    }
                ]
            }
            return DummyResponse(payload)
        else:
            raise requests.ConnectionError("Failed to connect")

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/temperature")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["average_temperature"] == 20.0
    assert payload["status"] == "Good"


@pytest.mark.integration
def test_temperature_endpoint_mixed_all_failed(client, monkeypatch):
    """Test the temperature endpoint when all boxes fail in different ways."""
    def fake_get(url, timeout=None):
        box_id = url.rsplit("/", 1)[-1]

        if box_id == SENSEBOX_IDS[0]:
            raise requests.Timeout("Connection timeout")
        elif box_id == SENSEBOX_IDS[1]:
            old_time = datetime.now(timezone.utc) - timedelta(hours=3)

            class DummyResponse:
                status_code = 200

                def raise_for_status(self):
                    return None

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
        else:
            class DummyResponse:
                status_code = 200

                def raise_for_status(self):
                    return None

                def json(self):
                    return {"sensors": []}

            return DummyResponse()

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
