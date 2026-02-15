"""Integration tests for /readyz endpoint - error cases."""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import requests

from src.services.sensebox_service import TEMPERATURE_SENSOR_PHENOMENON


class DummyResponse:
    """Dummy HTTP response for mocking requests."""

    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")

    def json(self):
        return self._payload


@pytest.mark.integration
def test_readyz_returns_503_when_majority_inaccessible_and_cache_old(
    client, monkeypatch
):
    """Test /readyz returns 503 when >50% inaccessible AND cache is old."""

    def fake_get(url, timeout=None):  # noqa: ARG001
        # All boxes fail
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    # Mock cache age to be old (more than 5 minutes)
    with patch("src.routes.readyz.get_cache_age_seconds", return_value=400):
        response = client.get("/readyz")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "not_ready"
        assert "reason" in data
        assert data["sensebox"]["accessible"] == 0
        assert data["sensebox"]["total"] == 3


@pytest.mark.integration
def test_readyz_returns_503_when_two_of_three_inaccessible_and_cache_old(
    client, monkeypatch
):
    """Test /readyz returns 503 when 2/3 inaccessible, cache old."""
    call_count = [0]

    def fake_get(url, timeout=None):  # noqa: ARG001
        call_count[0] += 1
        # First box succeeds, others fail
        if call_count[0] == 1:
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
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    # Mock cache age to be old
    with patch("src.routes.readyz.get_cache_age_seconds", return_value=400):
        response = client.get("/readyz")
        # 1 accessible, 2 inaccessible = 66.6% inaccessible (> 50%)
        # For 3 boxes, threshold = 3 // 2 = 1, inaccessible = 2, 2 > 1 is True
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "not_ready"
        assert "reason" in data
        assert data["sensebox"]["accessible"] == 1
        assert data["sensebox"]["inaccessible"] == 2
