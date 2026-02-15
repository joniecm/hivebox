"""Integration tests for /readyz endpoint - success cases."""
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
def test_readyz_returns_200_when_all_senseboxes_accessible(
    client, monkeypatch
):
    """Test /readyz returns 200 when all senseBoxes accessible."""

    def fake_get(url, timeout=None):  # noqa: ARG001
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

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ready"
    assert data["sensebox"]["accessible"] == 3
    assert data["sensebox"]["total"] == 3


@pytest.mark.integration
def test_readyz_returns_200_when_majority_inaccessible_but_cache_fresh(
    client, monkeypatch
):
    """Test /readyz returns 200 when >50% inaccessible but cache is fresh."""

    def fake_get(url, timeout=None):  # noqa: ARG001
        # All boxes fail
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    # Mock cache age to be fresh (less than 5 minutes)
    with patch("src.routes.readyz.get_cache_age_seconds", return_value=60):
        response = client.get("/readyz")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ready"
        assert data["sensebox"]["accessible"] == 0


@pytest.mark.integration
def test_readyz_returns_200_when_cache_old_but_boxes_accessible(
    client, monkeypatch
):
    """Test /readyz returns 200 when cache is old but boxes are accessible."""

    def fake_get(url, timeout=None):  # noqa: ARG001
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "sensors": [
                {
                    "title": TEMPERATURE_SENSOR_PHENOMENON,
                    "lastMeasurement": {
                        "value": "22.0",
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

    # Mock cache age to be old (more than 5 minutes)
    with patch("src.routes.readyz.get_cache_age_seconds", return_value=400):
        response = client.get("/readyz")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ready"


@pytest.mark.integration
def test_readyz_with_no_cache_available(client, monkeypatch):
    """Test /readyz when cache is not available (None)."""

    def fake_get(url, timeout=None):  # noqa: ARG001
        # All boxes fail
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(
        "src.services.sensebox_service.requests.get",
        fake_get,
    )

    # Mock cache age to be None (no cache)
    with patch("src.routes.readyz.get_cache_age_seconds", return_value=None):
        response = client.get("/readyz")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ready"
        # Cache age is None, so cache_too_old evaluates to False
        assert data["cache"]["age_seconds"] is None


@pytest.mark.integration
def test_readyz_with_partial_accessibility_fresh_cache(client, monkeypatch):
    """Test /readyz with 2/3 boxes accessible and fresh cache."""
    call_count = [0]

    def fake_get(url, timeout=None):  # noqa: ARG001
        call_count[0] += 1
        # First two boxes succeed, last fails
        if call_count[0] <= 2:
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

    with patch("src.routes.readyz.get_cache_age_seconds", return_value=60):
        response = client.get("/readyz")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ready"
        assert data["sensebox"]["accessible"] == 2
        assert data["sensebox"]["inaccessible"] == 1
