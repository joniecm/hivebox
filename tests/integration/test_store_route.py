import pytest

from src.app import app


@pytest.fixture()
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.mark.integration
def test_store_endpoint_success(client, monkeypatch):
    """Test /store returns flushed count."""
    monkeypatch.setattr(
        "src.routes.store.flush_temperature_records",
        lambda: (2, True),
    )

    response = client.post("/store")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["flushed"] == 2


@pytest.mark.integration
def test_store_endpoint_minio_not_configured(client, monkeypatch):
    """Test /store returns 503 when MinIO is not configured."""
    monkeypatch.setattr(
        "src.routes.store.flush_temperature_records",
        lambda: (0, False),
    )

    response = client.post("/store")
    assert response.status_code == 503
    payload = response.get_json()
    assert "error" in payload
