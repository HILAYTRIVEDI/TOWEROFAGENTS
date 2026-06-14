from fastapi.testclient import TestClient

from main import app


def test_health_works_without_external_credentials() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

