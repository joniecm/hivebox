import pytest

from src.app import app


@pytest.fixture()
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def test_metrics_endpoint_exists(client):
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_endpoint_returns_prometheus_text(client):
    response = client.get("/metrics")
    assert response.content_type.startswith("text/plain")


def test_metrics_endpoint_includes_http_metrics(client):
    client.get("/version")
    response = client.get("/metrics")
    body = response.data.decode("utf-8")
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
