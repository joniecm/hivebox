import pytest


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
