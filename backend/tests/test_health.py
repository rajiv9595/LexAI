"""Health and root endpoint tests."""

from fastapi.testclient import TestClient


def test_read_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "LexAssist API",
        "version": "0.1.0",
        "status": "prototype",
    }


def test_read_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "lexassist-api"}
