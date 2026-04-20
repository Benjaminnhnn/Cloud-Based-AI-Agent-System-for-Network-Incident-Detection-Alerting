# main.py
import os
import json
import logging
import redis
from contextlib import asynccontextmanager          # FIX #4
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional, cast 
from dotenv import load_dotenv

from core.tasks import process_alerts_task
from utils.telegram_bot import send_telegram_message, set_telegram_webhook
from core.rag_engine import get_rag_instance
from core.metrics import get_metrics_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

AI_AGENT_PORT       = int(os.getenv("AI_AGENT_PORT", "8000"))
AI_AGENT_PUBLIC_URL = os.getenv("AI_AGENT_PUBLIC_URL", f"http://localhost:{AI_AGENT_PORT}")

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

class AlertmanagerPayload(BaseModel):
    alerts: List[Alert]
    status: str

# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/webhook")
async def prometheus_webhook(payload: AlertmanagerPayload):
    """Tiếp nhận Alert và đẩy ngay vào Celery để xử lý bất đồng bộ."""
    process_alerts_task.delay(payload.model_dump())  # model_dump() đúng chuẩn Pydantic v2
    return {"status": "enqueued", "alert_count": len(payload.alerts)}


@app.post("/telegram/webhook")
async def telegram_callback(request: Request):
    """Xử lý phản hồi từ Telegram (Approved/Rejected)."""
    try:
        data = await request.json()
        if "callback_query" not in data:
            return {"status": "ok"}

        cb      = data["callback_query"]
        cb_data = cb.get("data", "")
        parts   = cb_data.split("|")

        if len(parts) < 2:
            return {"status": "ok"}

        action_type, incident_id = parts[0], parts[1]

        # FIX #8: Wrap Redis read trong try-except
        try:
            ctx_raw = redis_client.get(f"incident:{incident_id}")
        except redis.RedisError as e:
            logger.error(f"Redis read error: {e}")
            send_telegram_message("⚠️ Lỗi kết nối Redis, không thể xử lý callback.")
            return {"status": "error"}

        if not ctx_raw:
            send_telegram_message(f"⚠️ Hết hạn context cho sự cố `{incident_id}`.")
            return {"status": "ok"}

        ctx = json.loads(cast(str, ctx_raw))
        rag = get_rag_instance()

        if action_type == "ok":
            action = ctx.get("proposal", {}).get("action", "fix")
            send_telegram_message(f"⚙️ *Thực thi:* `{action}` trên `{ctx['instance']}`...")
            if rag:
                rag.save_incident(
                    alert_name=ctx["alert_name"],
                    description=ctx["incident_details"],
                    ai_analysis=ctx["ai_analysis"],
                    resolution=action,
                    outcome="executed_by_human"
                )
            send_telegram_message(f"🚀 *Hoàn tất:* `{action}` thành công!")

        elif action_type == "ignore":
            send_telegram_message(f"🚫 *Bỏ qua:* `{ctx['alert_name']}`.")

        # FIX #8: Wrap Redis delete trong try-except
        try:
            redis_client.delete(f"incident:{incident_id}")
        except redis.RedisError as e:
            logger.error(f"Redis delete error: {e}")

    except Exception as e:
        logger.error(f"Callback error: {e}")

    return {"status": "ok"}


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