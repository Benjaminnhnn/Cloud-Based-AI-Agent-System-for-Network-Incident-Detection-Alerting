# main.py
import os
import logging
import redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from core.tasks import process_alerts_task
from utils.telegram_bot import send_telegram_message, set_telegram_webhook
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
