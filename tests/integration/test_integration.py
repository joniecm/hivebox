from datetime import datetime, timezone

import pytest
import requests

from app import app
from sensebox_service import SENSEBOX_IDS, TEMPERATURE_SENSOR_PHENOMENON


@pytest.fixture()
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.mark.integration
def test_temperature_endpoint_integration(client, monkeypatch):
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
