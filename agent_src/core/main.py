# main.py
import os
import logging
import redis
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from core.tasks import process_admin_feedback_task, process_alerts_task
from utils.telegram_bot import TELEGRAM_CHAT_ID, send_telegram_message, set_telegram_webhook
from core.rag_engine import get_rag_instance
from core.metrics import get_metrics_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def valid_env_value(value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip()
    placeholders = ("your_", "change_me", "_here")
    if not value or any(marker in value for marker in placeholders):
        return None

    return value


AI_AGENT_PORT       = int(os.getenv("AI_AGENT_PORT", "8000"))
AI_AGENT_PUBLIC_URL = valid_env_value(os.getenv("AI_AGENT_PUBLIC_URL"))

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB   = int(os.getenv("REDIS_DB", "0"))

# FIX #9: Thêm socket_timeout để tránh treo khi Redis down
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
)

# ─────────────────────────────────────────────
# FIX #4: Dùng lifespan thay cho @app.on_event("startup") (deprecated từ FastAPI 0.93)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    rag = get_rag_instance()
    if rag is None:
        logger.warning("RAG Engine is unavailable; collections were not initialized.")

    if AI_AGENT_PUBLIC_URL:
        try:
            set_telegram_webhook(AI_AGENT_PUBLIC_URL)
        except Exception as e:
            logger.error(f"Failed to set Telegram webhook: {e}")
    yield
    # (shutdown logic nếu cần đặt ở đây)

app = FastAPI(title="AIOps Intelligent Agent (Celery Enabled)", lifespan=lifespan)

# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class Alert(BaseModel):
    status: str
    labels: dict
    annotations: dict
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    fingerprint: Optional[str] = None

class AlertmanagerPayload(BaseModel):
    alerts: List[Alert]
    status: str


def _extract_incident_id(text: str) -> str | None:
    patterns = (
        r"(?:^|\s)/feedback\s+([a-fA-F0-9]{6,16})\b",
        r"(?:^|\s)feedback\s+([a-fA-F0-9]{6,16})\b",
        r"(?:^|\s)ID\s*:\s*([a-fA-F0-9]{6,16})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _extract_feedback_payload(message: dict) -> tuple[str | None, str | None]:
    text = (message.get("text") or message.get("caption") or "").strip()
    reply_text = ((message.get("reply_to_message") or {}).get("text") or "").strip()

    incident_id = _extract_incident_id(text) or _extract_incident_id(reply_text)
    if not incident_id:
        return None, None

    feedback = text
    command_match = re.search(
        r"(?:^|\s)/feedback\s+[a-fA-F0-9]{6,16}\s*(.*)$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    plain_match = re.search(
        r"(?:^|\s)feedback\s+[a-fA-F0-9]{6,16}\s*(.*)$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if command_match:
        feedback = command_match.group(1).strip()
    elif plain_match:
        feedback = plain_match.group(1).strip()

    if _extract_incident_id(text) and feedback == text:
        feedback = re.sub(
            r"(?:^|\s)ID\s*:\s*[a-fA-F0-9]{6,16}\b",
            " ",
            feedback,
            flags=re.IGNORECASE,
        ).strip()

    return incident_id, feedback or None

# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/webhook")
async def prometheus_webhook(payload: AlertmanagerPayload):
    """
    PHASE 3: Tiếp nhận Alert và đẩy ngay vào Celery để xử lý bất đồng bộ.
    
    AlertManager gửi webhook POST → FastAPI nhận → enqueue to Celery
    """
    process_alerts_task.delay(payload.model_dump())  # model_dump() đúng chuẩn Pydantic v2
    return {"status": "enqueued", "alert_count": len(payload.alerts)}


@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    """
    Nhận tin nhắn Telegram của admin để góp ý thêm giải pháp cho một incident.
    Cú pháp: /feedback <incident_id> <góp ý>
    """
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if TELEGRAM_CHAT_ID and str(chat_id) != str(TELEGRAM_CHAT_ID):
        logger.warning("Ignored Telegram message from unauthorized chat_id=%s", chat_id)
        return {"status": "ignored"}

    incident_id, feedback = _extract_feedback_payload(message)
    if not incident_id or not feedback:
        send_telegram_message(
            "Gửi góp ý theo cú pháp: /feedback <incident_id> <giải pháp>",
            chat_id=str(chat_id) if chat_id is not None else None,
            parse_mode=None,
        )
        return {"status": "ignored", "reason": "missing_feedback"}

    process_admin_feedback_task.delay(
        incident_id,
        feedback,
        str(chat_id) if chat_id is not None else None,
    )
    return {"status": "enqueued", "incident_id": incident_id}


@app.get("/metrics")
async def metrics():
    return get_metrics_response()


@app.get("/health")
async def health():
    # Kiểm tra Redis health
    try:
        redis_client.ping()
        redis_status = "connected"
    except redis.RedisError:
        redis_status = "disconnected"
    return {"status": "healthy", "queue": "celery-redis", "redis": redis_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AI_AGENT_PORT)
