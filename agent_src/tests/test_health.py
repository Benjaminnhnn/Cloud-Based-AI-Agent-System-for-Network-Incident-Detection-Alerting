from unittest.mock import patch

from fastapi.testclient import TestClient
import redis

from core import main


client = TestClient(main.app)


def test_agent_health_endpoint() -> None:
    with (
        patch.object(main.redis_client, "ping"),
        patch.object(main.redis_client, "llen", return_value=3),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["queue"] == "celery-redis"
    assert data["queue_depth"] == 3
    assert data["redis"] == "connected"


def test_agent_health_endpoint_is_degraded_when_redis_is_down() -> None:
    with patch.object(main.redis_client, "ping", side_effect=redis.RedisError("down")):
        response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["queue_depth"] is None
    assert data["redis"] == "disconnected"
