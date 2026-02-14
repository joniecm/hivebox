import pytest


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
