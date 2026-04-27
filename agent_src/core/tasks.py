# tasks.py
# FIX #5: Sắp xếp lại imports — stdlib trước, third-party sau, local cuối cùng
import asyncio
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import redis
from dotenv import load_dotenv
from google import genai
from google.genai import types

from core.celery_app import celery_app
from core.metrics import ACTIVE_TASKS, AI_WORKFLOW_LATENCY_SECONDS, ALERTS_PROCESSED_TOTAL
from core.rag_engine import get_rag_instance
from tools.diag_tools import AGENT_TOOLS
from utils.telegram_bot import send_telegram_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def valid_env_value(value):
    if not value:
        return None

    value = value.strip()
    placeholders = ("your_", "change_me", "_here")
    if not value or any(marker in value for marker in placeholders):
        return None

    return value


GEMINI_API_KEY = valid_env_value(os.getenv("GEMINI_API_KEY"))
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# Redis Configuration (để lưu incident context)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB   = int(os.getenv("REDIS_DB", "0"))

# FIX #8: Thêm socket_timeout và xử lý lỗi khởi tạo Redis
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )
    redis_client.ping()
    logger.info("✅ Redis connected successfully.")
except redis.RedisError as e:
    logger.error(f"❌ Redis connection failed: {e}")
    redis_client = None  # type: ignore


def save_incident_to_redis(incident_id: str, context: dict, ttl: int = 86400):
    if redis_client is None:
        logger.error("Redis client unavailable, skipping incident save.")
        return
    try:
        redis_client.setex(f"incident:{incident_id}", ttl, json.dumps(context))
    except redis.RedisError as e:
        logger.error(f"Error writing to Redis: {e}")


async def run_agent_workflow(incident_details: str):
    if not GEMINI_API_KEY:
        return "❌ Error: GEMINI_API_KEY not configured", None

    client = genai.Client(api_key=GEMINI_API_KEY)
    rag = get_rag_instance()

    runbook_context = "⚠️ RAG Engine không khả dụng."
    if rag:
        runbook_context = rag.query_runbook(incident_details)

    system_instruction = f"""
        Bạn là AI Ops Agent chuyên nghiệp, chuyên xử lý sự cố hạ tầng.
        QUY TRÌNH CHUẨN VÀ LỊCH SỬ INCIDENT từ kho tri thức:
        ---
        {runbook_context}
        ---
        BẮT BUỘC: Dòng cuối cùng của response PHẢI là:
        PROPOSAL_JSON: {{"action": "tên_hành_động", "host": "tên_máy_chủ"}}
    """

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Phân tích sự cố: {incident_details}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=AGENT_TOOLS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=5
                )
            )
        )
        full_text = response.text or ""
        proposal  = None
        match = re.search(r"PROPOSAL_JSON:\s*(\{.*\})", full_text)
        if match:
            try:
                proposal = json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse PROPOSAL_JSON from AI response.")
        return full_text if full_text else "AI không phản hồi.", proposal
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return f"❌ Lỗi AI: {e}", None


async def process_single_alert(alert: dict) -> None:
    """Xử lý logic cho một alert đơn lẻ (async)."""
    ACTIVE_TASKS.inc()
    start_time = time.time()
    try:
        alert_name  = alert["labels"].get("alertname", "Unknown")
        instance    = alert["labels"].get("instance", "Unknown")
        summary     = alert["annotations"].get("summary", "")
        description = alert["annotations"].get("description", "")

        if alert.get("status") == "resolved":
            send_telegram_message(f"✅ *ĐÃ KHÔI PHỤC:* {alert_name} trên `{instance}`")
            ALERTS_PROCESSED_TOTAL.labels(status='resolved').inc()
            return

        incident_details = f"Alert: {alert_name} | Host: {instance} | Summary: {summary}"

        ai_analysis, proposal = await run_agent_workflow(incident_details)

        duration = time.time() - start_time
        AI_WORKFLOW_LATENCY_SECONDS.observe(duration)
        ALERTS_PROCESSED_TOTAL.labels(status='success').inc()

        incident_id = uuid.uuid4().hex[:8]
        incident_context = {
            "alert_name": alert_name,
            "instance": instance,
            "incident_details": incident_details,
            "ai_analysis": ai_analysis,
            "proposal": proposal,
            "timestamp": datetime.now(VN_TZ).isoformat()
        }
        save_incident_to_redis(incident_id, incident_context)

        reply_markup = None
        if proposal:
            action_name = proposal.get("action") or "fix"
            reply_markup = {"inline_keyboard": [[
                {"text": f"✅ Thực thi: {action_name[:20]}", "callback_data": f"ok|{incident_id}"},
                {"text": "❌ Bỏ qua", "callback_data": f"ignore|{incident_id}"}
            ]]}

        report = (
            f"*SỰ CỐ:* {alert_name}\n"
            f" Server: `{instance}`\n"
            f" ID: `{incident_id}`\n\n"
            f" *Phân tích :*\n{ai_analysis}"
        )
        send_telegram_message(report, reply_markup=reply_markup)

    except Exception as e:
        ALERTS_PROCESSED_TOTAL.labels(status='failure').inc()
        logger.error(f"Error processing alert: {e}")
        raise  # re-raise để Celery task biết alert này thất bại
    finally:
        ACTIVE_TASKS.dec()


# FIX #2 + #1 (Critical):
# - FIX #2: Chạy TẤT CẢ alerts trong một lần asyncio.run() duy nhất với gather()
#   thay vì gọi asyncio.run() lặp lại trong vòng for → tốn tài nguyên tạo/hủy event loop
# - FIX #1: Tách xử lý lỗi per-alert ra khỏi retry của toàn bộ task.
#   Logic cũ: 1 alert lỗi → retry TOÀN BỘ task → các alert đã thành công bị xử lý lại.
#   Logic mới: gather(return_exceptions=True) thu thập lỗi từng alert riêng biệt;
#   chỉ retry task nếu có lỗi hệ thống thực sự (ví dụ Redis/network down).
@celery_app.task(name="process_alerts_task", bind=True, max_retries=3)
def process_alerts_task(self, payload_dict: dict):
    """Celery task xử lý alert payload từ Prometheus."""
    alerts = payload_dict.get("alerts", [])
    if not alerts:
        logger.info("No alerts in payload, skipping.")
        return

    async def _run_all():
        # gather với return_exceptions=True để không dừng lại khi 1 alert lỗi
        results = await asyncio.gather(
            *[process_single_alert(alert) for alert in alerts],
            return_exceptions=True
        )
        # Ghi log các alert bị lỗi mà không làm ảnh hưởng đến alert khác
        failed = [
            (i, str(exc)) for i, exc in enumerate(results)
            if isinstance(exc, Exception)
        ]
        if failed:
            for idx, err in failed:
                alert_name = alerts[idx].get("labels", {}).get("alertname", "unknown")
                logger.error(f"Alert[{idx}] '{alert_name}' failed: {err}")
            # Chỉ raise nếu TẤT CẢ alerts đều thất bại (lỗi hệ thống)
            if len(failed) == len(alerts):
                raise RuntimeError(f"All {len(alerts)} alerts failed. Last error: {failed[-1][1]}")

    try:
        asyncio.run(_run_all())
    except RuntimeError as e:
        # Retry khi toàn bộ batch thất bại (thường do lỗi kết nối hệ thống)
        raise self.retry(exc=e, countdown=10)
