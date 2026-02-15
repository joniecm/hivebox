from datetime import datetime, timezone

import pytest
import requests

from src.services.sensebox_service import TEMPERATURE_SENSOR_PHENOMENON
from src.services.temperature_service import SENSEBOX_IDS, TemperatureResponse
import src.services.temperature_service as temperature_service


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

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/temperature")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["average_temperature"] == 22.0
    assert payload["status"] == "Good"


class FakeValkeyService:
    def __init__(self):
        self.store = {}
        self.ttl_values = {}

    def get_json(self, key: str):
        return self.store.get(key)

    def set_json(self, key: str, payload: dict, ttl_seconds: int) -> None:
        self.store[key] = payload
        self.ttl_values[key] = ttl_seconds

    def ttl(self, key: str):
        return self.ttl_values.get(key)

    def acquire_lock(self, key: str, ttl_seconds: int) -> bool:
        return True

    def release_lock(self, key: str) -> None:
        return None


@pytest.mark.integration
def test_temperature_endpoint_uses_valkey_cache(client, monkeypatch):
    fake_valkey = FakeValkeyService()
    responses = iter([
        TemperatureResponse(average_temperature=20.0, status="Good"),
        TemperatureResponse(average_temperature=22.0, status="Good"),
    ])
    calls = {"count": 0}

    def fake_get_latest():
        calls["count"] += 1
        return next(responses)

    monkeypatch.setattr(temperature_service, "valkey_service", fake_valkey)
    monkeypatch.setattr(
        temperature_service,
        "get_latest_temperature_response",
        fake_get_latest,
    )

    response_first = client.get("/temperature")
    assert response_first.status_code == 200
    payload_first = response_first.get_json()
    assert payload_first["average_temperature"] == 20.0

    response_second = client.get("/temperature")
    assert response_second.status_code == 200
    payload_second = response_second.get_json()
    assert payload_second["average_temperature"] == 20.0
    assert calls["count"] == 1
