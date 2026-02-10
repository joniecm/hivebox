import pytest

from src.app import app
from src.services.temperature_service import TemperatureResponse


@pytest.fixture()
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def _record(value: float) -> TemperatureResponse:
    return TemperatureResponse(
        average_temperature=round(value, 2),
        status="Good" if 10 <= value <= 36 else ("Too Cold" if value < 10 else "Too Hot"),
    )


@pytest.mark.integration
def test_temperature_endpoint_integration(client, monkeypatch):
    """Test the temperature endpoint with a latest in-memory record."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: _record(22.0),
    )

    response = client.get("/temperature")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["average_temperature"] == 22.0
    assert payload["status"] == "Good"


@pytest.mark.integration
def test_temperature_endpoint_api_timeout(client, monkeypatch):
    """Test the temperature endpoint handles missing data (timeout equivalent)."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_connection_error(client, monkeypatch):
    """Test the temperature endpoint handles missing data (connection error equivalent)."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_http_error(client, monkeypatch):
    """Test the temperature endpoint handles missing data (HTTP error equivalent)."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_missing_sensors(client, monkeypatch):
    """Test the temperature endpoint handles missing data (no sensors equivalent)."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_no_temperature_sensor(client, monkeypatch):
    """Test the temperature endpoint handles missing data (no sensor equivalent)."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_invalid_temperature_value(client, monkeypatch):
    """Test the temperature endpoint handles missing data (invalid value equivalent)."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"


@pytest.mark.integration
def test_temperature_endpoint_stale_data(client, monkeypatch):
    """Test the temperature endpoint handles missing data (stale equivalent)."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
    assert "older than 1 hour" in payload["message"]


@pytest.mark.integration
def test_temperature_endpoint_mixed_valid_and_failed(client, monkeypatch):
    """Test temperature endpoint when latest in-memory record is available."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: _record(20.0),
    )

    response = client.get("/temperature")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["average_temperature"] == 20.0
    assert payload["status"] == "Good"


@pytest.mark.integration
def test_temperature_endpoint_mixed_all_failed(client, monkeypatch):
    """Test the temperature endpoint when no latest record exists."""
    monkeypatch.setattr(
        "src.routes.temperature.get_latest_temperature_response",
        lambda: None,
    )

    response = client.get("/temperature")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
    assert payload["error"] == "No temperature data available"
