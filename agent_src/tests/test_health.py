import asyncio
from unittest.mock import patch

from fastapi.testclient import TestClient

from core import main
from core.main import app


def test_agent_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "queue" in data
    assert "redis" in data


def test_lifespan_initializes_rag_collections() -> None:
    with (
        patch.object(main, "AI_AGENT_PUBLIC_URL", None),
        patch.object(main, "get_rag_instance") as get_rag_instance,
    ):
        async def run_lifespan() -> None:
            async with main.lifespan(main.app):
                pass

        asyncio.run(run_lifespan())

    get_rag_instance.assert_called_once()
