import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
from telegram_notify import send_telegram_message, TELEGRAM_TOKEN

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. Load các biến môi trường
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
AI_AGENT_PORT = int(os.getenv("AI_AGENT_PORT", "8000"))
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def format_vn_timestamp() -> str:
    """Format current time in Vietnam timezone for alert notifications."""
    return datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S ICT")

# Initialize FastAPI & Gemini Client
app = FastAPI(title="AI Ops Webhook Server")
alert_history = []

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# Pydantic models for data parsing
class Alert(BaseModel):
    status: str
    labels: dict
    annotations: dict
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    fingerprint: str

class AlertmanagerPayload(BaseModel):
    receiver: str
    status: str
    alerts: List[Alert]
    groupLabels: dict
    commonLabels: dict
    commonAnnotations: dict
    externalURL: str
    version: str
    groupKey: str


# Pydantic models for API endpoints
class DiagnosticRequest(BaseModel):
    """Request for running diagnostics"""
    type: str  # "disk", "service", "all"
    auto_remediate: bool = False

class ServiceRecoveryRequest(BaseModel):
    """Request for service recovery"""
    service_name: str
    action: str  # "diagnose", "restart", "validate_config"


# AI Analysis function
def analyze_incident_with_ai(incident_details, incident_type: str = "general"):
    """
    Sử dụng Gemini để phân tích sự cố và đề xuất giải pháp.
    
    Args:
        incident_details: Chi tiết sự cố
        incident_type: Loại sự cố (disk_space, service_down, general)
    """
    if not client:
        return "Lỗi: Chưa cấu hình GEMINI_API_KEY"

    # Customize prompt based on incident type
    if incident_type == "disk_space":
        prompt = f"""
    Bạn là một chuyên gia AI Ops cao cấp chuyên xử lý sự cố cạn kiệt không gian ổ đĩa.
    
    Phân tích tình huống sau đây:
    {incident_details}
    
    Yêu cầu:
    1. **Nguyên nhân gốc rễ**: Xác định thư mục/dịch vụ nào chiếm dung lượng lớn nhất.
    2. **Mức độ nghiêm trọng**: Đánh giá xem hệ thống có nguy hiểm không (>95% full).
    3. **Các hành động khuyến nghị** (theo ưu tiên):
       - Dọn dẹp log cũ (.gz files) hoặc file temp
       - Xóa cache không cần thiết
       - Tăng kích thước EBS volume (nếu trên AWS)
    4. **Kế hoạch theo dõi**: Đề xuất cách giám sát để tránh tái phát.
    
    Trả lời bằng tiếng Việt, định dạng Markdown chuyên nghiệp. Ưu tiên các giải pháp tự động hóa được.
        """
    
    elif incident_type == "service_down":
        prompt = f"""
    Bạn là một chuyên gia AI Ops cao cấp chuyên xử lý sự cố dịch vụ bị sập.
    
    Phân tích tình huống sau đây:
    {incident_details}
    
    Yêu cầu:
    1. **Xác định dịch vụ lỗi**: Dịch vụ nào không chạy? (Nginx, Database, API, etc.)
    2. **Nguyên nhân tiềm năng**:
       - Process crash hoặc bị kill
       - Out of memory (OOM)
       - Port conflict
       - Config error
       - Dependency failure
    3. **Các bước phục hồi** (theo ưu tiên):
       - Kiểm tra config trước restart
       - Restart service an toàn
       - Kiểm tra dependency (database, network)
       - Validate service health sau restart
    4. **Cảnh báo**: Nếu không thể tự phục hồi, cần alert quản trị viên.
    
    Trả lời bằng tiếng Việt, định dạng Markdown chuyên nghiệp. Tập trung vào các hành động có thể tự động hóa.
        """
    
    else:
        prompt = f"""
    Bạn là một chuyên gia AI Ops cao cấp. Hãy phân tích sự cố hệ thống sau:
    {incident_details}
    Yêu cầu:
    1. Xác định nguyên nhân gốc rễ (Root Cause) dựa trên các metric được cung cấp.
    2. Đánh giá mức độ ảnh hưởng (Impact) tới dịch vụ.
    3. Đề xuất 3-5 bước xử lý kỹ thuật (Remediation) chi tiết.
    
    Trả lời bằng tiếng Việt, định dạng Markdown chuyên nghiệp (Bold, Code block, List).
        """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi gọi AI: {str(e)}"


def detect_incident_type(alert_name: str) -> str:
    """
    Detect incident type based on alert name for context-specific AI analysis.
    Returns: "service_down", "disk_space", "resource_high", or "general"
    """
    alert_lower = alert_name.lower()
    
    # Service down patterns
    if any(pattern in alert_lower for pattern in [
        "down", "unreachable", "not responding", "unavailable",
        "connection refused", "timeout", "dead", "failed"
    ]):
        return "service_down"
    
    # Disk space patterns
    elif any(pattern in alert_lower for pattern in [
        "disk", "storage", "space", "inode", "filesystem"
    ]):
        return "disk_space"
    
    # Resource patterns
    elif any(pattern in alert_lower for pattern in [
        "cpu", "memory", "load", "ram", "swap", "network"
    ]):
        return "resource_high"
    
    # Default
    return "general"

def process_alerts_task(payload: AlertmanagerPayload):
    """Xử lý cảnh báo: phân tích AI, gửi Telegram, lưu lịch sử"""
    for alert in payload.alerts:
        try:
            # Gom thông tin sự cố
            alert_name = alert.labels.get("alertname", "Unknown Alert")
            instance = alert.labels.get("instance", "Unknown Instance")
            severity = alert.labels.get("severity", "unknown")
            summary = alert.annotations.get("summary", "No summary")
            description = alert.annotations.get("description", "No description")

            # Send explicit recovery notification when alert is resolved.
            if alert.status == "resolved":
                recovered_report = "✅ *ĐÃ KHÔI PHỤC: {}*\n".format(alert_name)
                recovered_report += f"⏰ {format_vn_timestamp()}\n"
                recovered_report += f"📊 Instance: `{instance}`\n"
                recovered_report += f"📝 Tóm tắt: {summary}\n"
                recovered_report += f"🔍 Chi tiết: {description}\n"
                recovered_report += f"🕒 Bắt đầu: {alert.startsAt}\n"
                recovered_report += f"✅ Kết thúc: {alert.endsAt}\n"

                telegram_sent = False
                try:
                    telegram_sent = bool(send_telegram_message(recovered_report))
                    if not telegram_sent:
                        logger.error(f"Telegram resolved notification failed for alert: {alert_name}")
                except Exception as tg_error:
                    logger.error(f"Telegram resolved notification error: {str(tg_error)}")

                alert_history.insert(0, {
                    "name": alert_name,
                    "severity": severity,
                    "instance": instance,
                    "summary": summary,
                    "received_at": datetime.now().isoformat(),
                    "telegram_sent": telegram_sent,
                    "ai_analysis": False,
                    "status": "resolved"
                })
                logger.info(f"Resolved alert saved: {alert_name} (Telegram: {telegram_sent})")

                if len(alert_history) > 100:
                    removed = alert_history.pop()
                    logger.info(f"Alert history pruned, removed: {removed.get('name')}")
                continue

            # Prepare detailed incident report for AI
            incident_details = f"""
            - Alert: {alert_name}
            - Instance: {instance}
            - Severity: {severity}
            - Summary: {summary}
            - Description: {description}
            - Started at: {alert.startsAt}
            """

            logger.info(f"🔍 Processing alert: {alert_name} on {instance}...")
            
            # Detect incident type (FIX #1: Dynamic detection instead of hardcoded)
            incident_type = detect_incident_type(alert_name)
            logger.info(f"   Incident type detected: {incident_type}")
            
            # AI analysis with context-specific prompt
            ai_analysis = None
            try:
                ai_analysis = analyze_incident_with_ai(incident_details, incident_type=incident_type)
                if not ai_analysis or "Error" in ai_analysis:
                    logger.warning(f"AI analysis warning: {ai_analysis}")
            except Exception as ai_error:
                logger.error(f"AI analysis error: {str(ai_error)}")
                ai_analysis = f"❌ AI phân tích thất bại: {str(ai_error)}"
            
            # Xác định biểu tượng mức độ nghiêm trọng (FIX #3: Phản hồi trực quan tốt hơn)
            severity_emoji = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🟢"
            }.get(severity, "⚠️")
            
            # Gửi báo cáo qua Telegram (FIX #2: Header được cấu trúc rõ ràng)
            severity_vi = {
                "critical": "NGHIÊM TRỌNG",
                "warning": "CẢNH BÁO",
                "info": "THÔNG TIN"
            }.get(severity, severity.upper())
            report_header = f"{severity_emoji} *{severity_vi}: {alert_name}*\n"
            report_header += f"⏰ {format_vn_timestamp()}\n"
            report_header += f"📊 Instance: `{instance}`\n"
            report_header += f"🎯 Loại: {incident_type}\n"
            report_header += f"\n---\n\n"
            
            final_report = report_header + (ai_analysis or "Không có phân tích AI")
            
            # Send Telegram message
            telegram_sent = False
            try:
                result = send_telegram_message(final_report)
                telegram_sent = bool(result)
                if not telegram_sent:
                    logger.error(f"Telegram notification failed for alert: {alert_name}")
            except Exception as tg_error:
                logger.error(f"Telegram error: {str(tg_error)}")
                telegram_sent = False
            
            # Save alert to history
            alert_entry = {
                "name": alert_name,
                "severity": severity,
                "instance": instance,
                "summary": summary,
                "received_at": datetime.now().isoformat(),
                "telegram_sent": telegram_sent,
                "ai_analysis": ai_analysis is not None and "Error" not in ai_analysis,
                "status": "processed"
            }
            
            alert_history.insert(0, alert_entry)
            logger.info(f"Alert saved: {alert_name} (Telegram: {telegram_sent})")
            
            # Keep max 100 alerts
            if len(alert_history) > 100:
                removed = alert_history.pop()
                logger.info(f"Alert history pruned, removed: {removed.get('name')}")
                
        except Exception as e:
            print(f"❌ Error processing alert: {str(e)}")
            print(f"   Alert data: {alert.labels.get('alertname', 'Unknown')}")

# 6. Các API Endpoints

@app.get("/")
async def root():
    """API Status"""
    return {
        "service": "AI Ops Webhook",
        "status": "running",
        "version": "2.0",
        "endpoints": ["/webhook", "/health", "/api/status", "/api/alerts"]
    }

# Get system status
@app.get("/api/status")
async def get_status():
    """Return current system status and configuration"""
    return {
        "status": "healthy",
        "ai_enabled": client is not None,
        "webhook_count": len(alert_history),
        "telegram_configured": bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID),
        "gemini_configured": bool(GEMINI_API_KEY),
        "timestamp": datetime.now().isoformat(),
        "uptime": "Running"
    }

# Get alert history
@app.get("/api/alerts")
async def get_alerts(limit: int = 10):
    """Return recent alerts from history"""
    try:
        return {
            "alerts": alert_history[:limit],
            "total": len(alert_history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "alerts": [],
            "total": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/webhook")
async def prometheus_webhook(payload: AlertmanagerPayload, background_tasks: BackgroundTasks):
    """
    Endpoint nhận cảnh báo từ Prometheus Alertmanager.
    Sử dụng BackgroundTasks để phản hồi Prometheus ngay lập tức (200 OK) 
    trong khi AI vẫn đang phân tích dưới nền.
    """
    print(f" Đã nhận {len(payload.alerts)} cảnh báo từ Alertmanager.")
    background_tasks.add_task(process_alerts_task, payload)
    return {
        "status": "success",
        "message": "Alerts are being processed by AI Agent",
        "alerts_count": len(payload.alerts),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "ai_enabled": client is not None,
        "telegram_enabled": bool(TELEGRAM_TOKEN),
        "total_alerts": len(alert_history),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# DIAGNOSTIC ENDPOINTS
# ============================================================================

@app.post("/api/diagnose")
async def run_diagnostic(request: DiagnosticRequest, background_tasks: BackgroundTasks):
    """
    Run system diagnostics (disk, service, or all).
    """
    logger.info(f"🔧 Diagnostic request: type={request.type}, auto_remediate={request.auto_remediate}")
    
    # For now, return status - not used in active workflow
    return {
        "status": "success",
        "type": request.type,
        "message": "Diagnostic endpoint - use webhook for active monitoring"
    }

@app.post("/api/service/recover")
async def recover_service(request: ServiceRecoveryRequest):
    """
    Recover a specific service (diagnose, restart, or validate config).
    """
    service_name = request.service_name
    action = request.action
    
    logger.info(f"🔄 Service recovery request: {service_name} - {action}")
    
    # For now, return status - not used in active workflow
    return {
        "status": "success",
        "service": service_name,
        "action": action,
        "message": "Recovery endpoint - use webhook for active monitoring"
    }




# ============================================================================
# BACKGROUND TASKS FOR REMEDIATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Ops Webhook Server...")
    print(f"   📍 Port: {AI_AGENT_PORT}")
    print(f"   🤖 Gemini AI: {'✅ Enabled' if GEMINI_API_KEY else '❌ Disabled'}")
    print(f"   📱 Telegram: {'✅ Configured' if TELEGRAM_CHAT_ID else '❌ Not Configured'}")
    print(f"   📚 API Docs: http://0.0.0.0:{AI_AGENT_PORT}/docs")
    print("-" * 50)
    uvicorn.run(app, host="0.0.0.0", port=AI_AGENT_PORT)
