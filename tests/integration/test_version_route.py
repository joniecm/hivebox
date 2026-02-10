import pytest

from src.app import app, VERSION


@pytest.fixture()
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def test_version_endpoint_exists(client):
    response = client.get("/version")
    assert response.status_code == 200


def test_version_endpoint_returns_json(client):
    response = client.get("/version")
    assert response.content_type == "application/json"


def test_version_endpoint_returns_correct_version(client):
    response = client.get("/version")
    data = response.get_json()
    assert "version" in data
    assert data["version"] == VERSION


def test_version_endpoint_no_parameters(client):
    response = client.get("/version")
    assert response.status_code == 200
    data = response.get_json()
    assert "version" in data
