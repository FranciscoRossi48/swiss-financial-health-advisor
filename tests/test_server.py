from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_server_mounts_the_api_under_api_prefix():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_server_does_not_expose_api_routes_at_the_root():
    response = client.get("/users")
    assert response.status_code == 404
