import os
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from core import main


client = TestClient(main.app)


def test_register_tool_api_queues_review_without_publishing() -> None:
    with TemporaryDirectory() as tmp:
        workflow_dir = os.path.join(tmp, "workflow")
        kb_dir = os.path.join(tmp, "knowledge_base")
        os.makedirs(kb_dir)

        with (
            patch.dict(os.environ, {"RUNBOOK_WORKFLOW_DIR": workflow_dir, "KNOWLEDGE_BASE_DIR": kb_dir}),
            patch.object(main.review_tool_change_task, "delay") as delay,
        ):
            response = client.post(
                "/api/tools",
                json={
                    "name": "check_redis_queue_depth",
                    "version": "1.0.0",
                    "description": "Read Celery queue depth",
                    "risk_level": "read_only",
                    "related_services": ["redis", "celery"],
                    "runbook_tags": ["queue-backlog"],
                },
            )

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "registered"
        assert body["review_status"] == "queued"
        assert body["tool_name"] == "check_redis_queue_depth"
        delay.assert_called_once()
        assert not os.path.exists(os.path.join(kb_dir, "published"))
