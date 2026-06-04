from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_backend_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_backend_readiness_endpoint_checks_database() -> None:
    client = TestClient(app)

    with patch("app.main.engine.connect") as connect:
        response = client.get("/api/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "reachable"
    connect.return_value.__enter__.return_value.execute.assert_called_once()


def test_backend_readiness_endpoint_reports_database_failure() -> None:
    client = TestClient(app)

    with patch("app.main.engine.connect", side_effect=RuntimeError("connection refused")):
        response = client.get("/api/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "database unavailable"


def test_backend_root_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AIOps Demo API"
    assert data["ready"] == "/api/ready"
