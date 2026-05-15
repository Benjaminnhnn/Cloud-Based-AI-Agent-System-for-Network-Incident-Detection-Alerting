# tasks.py
# FIX #5: Sắp xếp lại imports — stdlib trước, third-party sau, local cuối cùng
import asyncio
import hashlib
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
from tools.prometheus_check import get_prometheus_checker
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
GEMINI_MODEL = valid_env_value(os.getenv("GEMINI_MODEL")) or "gemini-2.5-flash"
GEMINI_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv("GEMINI_FALLBACK_MODELS", "").split(",")
    if model.strip()
]
GEMINI_MAX_ATTEMPTS = int(os.getenv("GEMINI_MAX_ATTEMPTS", "1"))
GEMINI_MAX_REMOTE_CALLS = int(os.getenv("GEMINI_MAX_REMOTE_CALLS", "1"))
GEMINI_RETRY_BASE_SECONDS = float(os.getenv("GEMINI_RETRY_BASE_SECONDS", "2"))
ALERT_AI_COOLDOWN_SECONDS = int(os.getenv("ALERT_AI_COOLDOWN_SECONDS", "900"))
ALERT_DEDUP_ENABLED = os.getenv("ALERT_DEDUP_ENABLED", "true").lower() not in {"0", "false", "no"}
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

_local_alert_cooldowns: dict[str, float] = {}


def _truncate_text(value: str, max_chars: int = 1500) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + "\n...[truncated]"


def _alert_identity(alert: dict) -> str:
    fingerprint = alert.get("fingerprint")
    if fingerprint:
        return str(fingerprint)

    labels = alert.get("labels", {})
    identity = {
        "alertname": labels.get("alertname", "Unknown"),
        "instance": labels.get("instance", "Unknown"),
        "job": labels.get("job", ""),
        "service": labels.get("service", ""),
        "target": labels.get("target", ""),
    }
    identity_json = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(identity_json.encode("utf-8")).hexdigest()[:16]


def _alert_cooldown_key(alert: dict) -> str:
    return f"alert-ai-cooldown:{_alert_identity(alert)}"


def _reserve_alert_processing(alert: dict) -> bool:
    if not ALERT_DEDUP_ENABLED or ALERT_AI_COOLDOWN_SECONDS <= 0:
        return True

    key = _alert_cooldown_key(alert)
    if redis_client is not None:
        try:
            return bool(redis_client.set(key, "processing", ex=ALERT_AI_COOLDOWN_SECONDS, nx=True))
        except redis.RedisError as e:
            logger.warning("Redis cooldown check failed, using in-memory fallback: %s", e)

    now = time.time()
    expires_at = _local_alert_cooldowns.get(key, 0)
    if expires_at > now:
        return False
    _local_alert_cooldowns[key] = now + ALERT_AI_COOLDOWN_SECONDS
    return True


def _clear_alert_cooldown(alert: dict) -> None:
    key = _alert_cooldown_key(alert)
    _local_alert_cooldowns.pop(key, None)
    if redis_client is None:
        return
    try:
        redis_client.delete(key)
    except redis.RedisError as e:
        logger.warning("Redis cooldown cleanup failed: %s", e)


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

    def parse_proposal(full_text: str):
        match = re.search(r"PROPOSAL_JSON:\s*(\{.*\})", full_text)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.warning("Failed to parse PROPOSAL_JSON from AI response.")
            return None

    def is_retryable_gemini_error(exc: Exception) -> bool:
        error_text = str(exc).lower()
        retryable_markers = (
            "429",
            "500",
            "502",
            "503",
            "504",
            "deadline",
            "rate limit",
            "resource_exhausted",
            "temporarily",
            "timeout",
            "unavailable",
            "high demand",
        )
        return any(marker in error_text for marker in retryable_markers)

    def fallback_analysis(last_error: Exception | None):
        host_match = re.search(r"Host:\s*([^|]+)", incident_details)
        host = host_match.group(1).strip() if host_match else "unknown"
        error_text = _truncate_text(str(last_error), 500) if last_error else "Gemini không phản hồi."
        analysis = (
            "⚠️ *Gemini tạm thời không khả dụng, dùng phân tích dự phòng từ RAG/runbook.*\n\n"
            f"*Sự cố:* {incident_details}\n\n"
            f"*Lỗi Gemini gần nhất:* `{error_text}`\n\n"
            "*Ngữ cảnh runbook/RAG liên quan:*\n"
            f"{_truncate_text(runbook_context, 1200)}\n\n"
            "*Biện pháp khắc phục đề xuất:*\n"
            "1. Xác nhận alert còn firing trong Prometheus/Alertmanager.\n"
            "2. Kiểm tra service/endpoint bị báo lỗi trên host liên quan.\n"
            "3. Khôi phục service hoặc rollback release gần nhất nếu lỗi xuất hiện sau deploy.\n"
            "4. Kiểm tra lại `/health` và chờ Prometheus resolve alert.\n"
            "PROPOSAL_JSON: "
            + json.dumps({"action": "fallback_runbook_recovery", "host": host}, ensure_ascii=False)
        )
        return analysis, {"action": "fallback_runbook_recovery", "host": host}

    models = [GEMINI_MODEL]
    models.extend(model for model in GEMINI_FALLBACK_MODELS if model not in models)
    last_error = None

    for model in models:
        for attempt in range(1, max(GEMINI_MAX_ATTEMPTS, 1) + 1):
            try:
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=f"Phân tích sự cố: {incident_details}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=AGENT_TOOLS,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            maximum_remote_calls=max(GEMINI_MAX_REMOTE_CALLS, 0)
                        )
                    )
                )
                full_text = response.text or ""
                return full_text if full_text else "AI không phản hồi.", parse_proposal(full_text)
            except Exception as e:
                last_error = e
                retryable = is_retryable_gemini_error(e)
                logger.warning(
                    "Gemini call failed: model=%s attempt=%s/%s retryable=%s error=%s",
                    model,
                    attempt,
                    GEMINI_MAX_ATTEMPTS,
                    retryable,
                    e,
                )
                if not retryable or attempt >= GEMINI_MAX_ATTEMPTS:
                    break
                await asyncio.sleep(GEMINI_RETRY_BASE_SECONDS * (2 ** (attempt - 1)))

    logger.error("Gemini unavailable after retries/fallback models: %s", last_error)
    return fallback_analysis(last_error)


async def process_single_alert(alert: dict) -> None:
    """
    Xử lý logic cho một alert đơn lẻ (async).
    
    NEW WORKFLOW (Phase 7):
    - AI phân tích sự cố
    - Gửi hướng dẫn xử lí chi tiết cho Admin (không có buttons)
    - Lưu context vào Redis để verify sau
    - Kích hoạt task verification sau 5-10 phút
    """
    ACTIVE_TASKS.inc()
    start_time = time.time()
    try:
        alert_name  = alert["labels"].get("alertname", "Unknown")
        instance    = alert["labels"].get("instance", "Unknown")
        summary     = alert["annotations"].get("summary", "")
        description = alert["annotations"].get("description", "")

        if alert.get("status") == "resolved":
            _clear_alert_cooldown(alert)
            send_telegram_message(f"✅ *ĐÃ KHÔI PHỤC:* {alert_name} trên `{instance}`")
            ALERTS_PROCESSED_TOTAL.labels(status='resolved').inc()
            return

        if not _reserve_alert_processing(alert):
            logger.info(
                "Skipping duplicate alert within cooldown: alert=%s instance=%s cooldown=%ss",
                alert_name,
                instance,
                ALERT_AI_COOLDOWN_SECONDS,
            )
            ALERTS_PROCESSED_TOTAL.labels(status='deduped').inc()
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

        # PHASE 7: Format resolution guide (NO approval buttons)
        action_name = proposal.get("action", "fix") if proposal else "xử lí"
        
        report = (
            f"*🚨 SỰ CỐ:* {alert_name}\n"
            f"📊 *Server:* `{instance}`\n"
            f"🆔 *ID:* `{incident_id}`\n\n"
            f"🔍 *NGUYÊN NHÂN & PHÂN TÍCH:*\n"
            f"{ai_analysis}\n\n"
            f"🛠️ *HƯỚNG DẪN XỬ LÍ:*\n"
            f"Thực hiện hành động: *{action_name}*\n\n"
            f"⏱️ Agent sẽ tự động kiểm lại trong 5-10 phút."
        )
        
        # Gửi hướng dẫn cho admin (NO buttons)
        send_telegram_message(report)
        
        # PHASE 9: Schedule verification task sau 5-10 phút (300-600 seconds)
        verification_countdown = 300  # 5 minutes (có thể điều chỉnh)
        verify_resolution_task.apply_async(
            args=[incident_id, alert_name, instance],
            countdown=verification_countdown
        )
        logger.info(f"📋 Scheduled verification for incident {incident_id} in {verification_countdown}s")

    except Exception as e:
        ALERTS_PROCESSED_TOTAL.labels(status='failure').inc()
        logger.error(f"Error processing alert: {e}")
        raise  # re-raise để Celery task biết alert này thất bại
    finally:
        ACTIVE_TASKS.dec()


# PHASE 9: Automatic Verification Task
# ─────────────────────────────────────────────────────────────────────
async def verify_resolution(incident_id: str, alert_name: str, instance: str):
    """
    PHASE 9: Automatic Verification - kiểm lại sau 5-10 phút
    
    1. Query Prometheus để lấy metrics hiện tại
    2. So sánh với alert threshold
    3. Gửi báo cáo về kết quả (resolved/failed)
    4. Lưu vào ChromaDB với outcome
    """
    logger.info(f"🔍 Starting verification for incident {incident_id} ({alert_name} on {instance})")
    
    try:
        # Retrieve incident context từ Redis
        try:
            ctx_raw = redis_client.get(f"incident:{incident_id}")
        except redis.RedisError as e:
            logger.error(f"Redis read error during verification: {e}")
            send_telegram_message(f"⚠️ Không thể xác nhận kết quả vì Redis unavailable")
            return
        
        if not ctx_raw:
            logger.warning(f"Incident context expired for {incident_id}")
            send_telegram_message(f"⚠️ Context hết hạn cho sự cố `{incident_id}`")
            return
        
        ctx = json.loads(ctx_raw)
        
        # Query Prometheus metrics để kiểm lại
        # Cách 1: Gọi các diagnostic tools tương tự như AI analysis
        # Cách 2: Query trực tiếp Prometheus API (nếu cấu hình public)
        logger.info(f"📊 Checking current metrics for {instance}...")
        
        # Simulate health check (thực tế sẽ call Prometheus API hoặc diagnostic tools)
        is_resolved = await check_alert_resolved(alert_name, instance)
        
        if is_resolved:
            # Issue RESOLVED ✅
            outcome = "resolved_by_human"
            message = (
                f"✅ *SỰ CỐ ĐÃ ĐƯỢC KHÔI PHỤC*\n"
                f"Alert: {alert_name}\n"
                f"Server: {instance}\n"
                f"ID: {incident_id}\n\n"
                f"Metrics hiện tại đã trở lại bình thường."
            )
        else:
            # Issue STILL FAILING ❌
            outcome = "failed_to_resolve"
            message = (
                f"❌ *SỰ CỐ VẪN TỒN TẠI*\n"
                f"Alert: {alert_name}\n"
                f"Server: {instance}\n"
                f"ID: {incident_id}\n\n"
                f"⚠️ Các metrics vẫn còn cao.\n"
                f"💡 Gợi ý: Hãy thử giải pháp thay thế hoặc escalate."
            )
        
        # Send verification report
        send_telegram_message(message)
        
        # Save to ChromaDB with outcome
        rag = get_rag_instance()
        if rag:
            rag.save_incident(
                alert_name=ctx["alert_name"],
                description=ctx["incident_details"],
                ai_analysis=ctx["ai_analysis"],
                resolution=ctx.get("proposal", {}).get("action", "manual_fix"),
                outcome=outcome
            )
            logger.info(f"✅ Saved incident to ChromaDB with outcome: {outcome}")
        
        # Cleanup Redis
        try:
            redis_client.delete(f"incident:{incident_id}")
        except redis.RedisError as e:
            logger.warning(f"Error deleting incident from Redis: {e}")
    
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        send_telegram_message(f"⚠️ Lỗi kiểm tra kết quả: {str(e)}")


async def check_alert_resolved(alert_name: str, instance: str) -> bool:
    """
    Check nếu alert đã được resolve bằng cách query Prometheus.
    
    Thực hiện:
    1. Query Prometheus API để lấy current metrics
    2. Compare với alert threshold
    3. Return True nếu metrics < threshold
    
    Example:
    - alert_name: "node_cpu_high"
    - instance: "10.10.1.68:9100"
    - Return: True nếu CPU < 80%
    """
    try:
        logger.info(f"Checking if {alert_name} is resolved on {instance}...")
        
        checker = get_prometheus_checker()
        is_resolved = checker.is_alert_resolved(alert_name, instance)
        
        if is_resolved:
            logger.info(f"✅ Alert {alert_name} is RESOLVED")
        else:
            logger.warning(f"❌ Alert {alert_name} is STILL FAILING")
        
        # Log metrics for debugging
        metrics = checker.get_alert_metrics(instance)
        logger.info(f"📊 Current metrics: {metrics}")
        
        return is_resolved
    
    except Exception as e:
        logger.error(f"Error checking alert resolution: {e}")
        # Default to failed if can't determine
        return False


@celery_app.task(name="verify_resolution_task", bind=True, max_retries=2)
def verify_resolution_task(self, incident_id: str, alert_name: str, instance: str):
    """
    Celery task để verify resolution (chạy sau 5-10 phút)
    
    Parameters:
    - incident_id: ID của incident
    - alert_name: Tên alert (e.g., node_cpu_high)
    - instance: Instance bị ảnh hưởng (e.g., 10.10.1.68)
    """
    try:
        logger.info(f"🔄 Running verification for {incident_id}")
        asyncio.run(verify_resolution(incident_id, alert_name, instance))
    except Exception as e:
        logger.error(f"Verification task failed: {e}")
        # Retry 1 lần sau 1 phút
        raise self.retry(exc=e, countdown=60)
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
