import asyncio
import json
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from core import main, tasks


def test_extract_feedback_payload_from_command() -> None:
    incident_id, feedback = main._extract_feedback_payload({
        "text": "/feedback abc12345 restart container rồi kiểm tra lại /health"
    })

    assert incident_id == "abc12345"
    assert feedback == "restart container rồi kiểm tra lại /health"


def test_extract_feedback_payload_from_reply_context() -> None:
    incident_id, feedback = main._extract_feedback_payload({
        "text": "kiểm tra docker logs trước khi restart service",
        "reply_to_message": {"text": "🚨 SỰ CỐ: WebEndpointDown\nID: deadbee1\n"},
    })

    assert incident_id == "deadbee1"
    assert feedback == "kiểm tra docker logs trước khi restart service"


def test_telegram_webhook_enqueues_admin_feedback() -> None:
    client = TestClient(main.app)

    with (
        patch.object(main, "TELEGRAM_CHAT_ID", "123"),
        patch.object(main.process_admin_feedback_task, "delay") as delay,
    ):
        response = client.post("/telegram/webhook", json={
            "message": {
                "chat": {"id": 123},
                "text": "/feedback abc12345 docker restart frontend-web-prod",
            }
        })

    assert response.status_code == 200
    assert response.json() == {"status": "enqueued", "incident_id": "abc12345"}
    delay.assert_called_once_with("abc12345", "docker restart frontend-web-prod", "123")


def test_process_admin_feedback_saves_reviewed_solution_to_rag() -> None:
    context = {
        "alert_name": "WebEndpointDown",
        "incident_details": "Alert: WebEndpointDown\nInstance: bank-web-01",
        "ai_analysis": "check frontend-web-prod",
    }
    fake_redis = Mock()
    fake_redis.get.return_value = json.dumps(context)
    fake_rag = Mock()

    with (
        patch.object(tasks, "redis_client", fake_redis),
        patch.object(tasks, "GEMINI_API_KEY", None),
        patch.object(tasks, "get_rag_instance", return_value=fake_rag),
        patch.object(tasks, "send_telegram_message") as send_message,
    ):
        result = asyncio.run(tasks.process_admin_feedback(
            "abc12345",
            "docker restart frontend-web-prod rồi curl /health",
            chat_id="123",
        ))

    assert result["status"] == "accepted"
    assert result["saved"] is True
    fake_rag.save_admin_solution.assert_called_once()
    send_message.assert_called_once()


def test_destructive_feedback_is_rejected_and_not_saved() -> None:
    context = {
        "alert_name": "WebEndpointDown",
        "incident_details": "Alert: WebEndpointDown\nInstance: bank-web-01",
        "ai_analysis": "check frontend-web-staging",
    }
    fake_redis = Mock()
    fake_redis.get.return_value = json.dumps(context)
    fake_rag = Mock()

    with (
        patch.object(tasks, "redis_client", fake_redis),
        patch.object(tasks, "GEMINI_API_KEY", "configured"),
        patch.object(tasks, "get_rag_instance", return_value=fake_rag),
        patch.object(tasks, "send_telegram_message") as send_message,
    ):
        result = asyncio.run(tasks.process_admin_feedback(
            "abc12345",
            "xóa Docker volume rồi deploy lại",
            chat_id="123",
        ))

    assert result["status"] == "rejected"
    assert result["saved"] is False
    fake_rag.save_admin_solution.assert_not_called()
    assert "Lưu vào RAG: no" in send_message.call_args.args[0]


def test_vague_upstream_feedback_is_revised_with_expected_value() -> None:
    context = {
        "alert_name": "FrontendAPIProxyDown",
        "labels": {
            "expected_upstream": "http://10.10.1.119:18080",
        },
        "incident_details": "Alert: FrontendAPIProxyDown\nInstance: bank-web-01",
        "ai_analysis": "check PAYMENT_API_UPSTREAM",
    }

    review = asyncio.run(tasks.review_admin_feedback(
        context,
        "Kiểm tra PAYMENT_API_UPSTREAM, nếu sai thì chỉnh sửa rồi redeploy web.",
    ))

    assert review["status"] == "revised"
    assert "PAYMENT_API_UPSTREAM=http://10.10.1.119:18080" in review["reviewed_solution"]
    assert "api/ready" in review["reviewed_solution"]
