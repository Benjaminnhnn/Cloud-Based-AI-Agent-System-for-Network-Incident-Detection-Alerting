import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
from telegram_notify import send_telegram_message

# 1. Load các biến môi trường
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 2. Khởi tạo FastAPI & Gemini Client
app = FastAPI(title="AI Ops Webhook Server")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# 3. Model dữ liệu (Pydantic) để parse dữ liệu từ Prometheus Alertmanager
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

# 4. Logic phân tích sự cố với Gemini
def analyze_incident_with_ai(incident_details):
    """Sử dụng Gemini để phân tích sự cố và đề xuất giải pháp."""
    if not client:
        return "❌ Lỗi: Chưa cấu hình GEMINI_API_KEY"

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
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi gọi AI: {str(e)}"

# 5. Hàm xử lý cảnh báo chạy ngầm (Background Task)
def process_alerts_task(payload: AlertmanagerPayload):
    for alert in payload.alerts:
        # Bỏ qua nếu cảnh báo đã kết thúc (resolved) - tùy chọn
        if alert.status == "resolved":
            # notify_msg = f"✅ *SỰ CỐ ĐÃ ĐƯỢC XỬ LÝ*: {alert.labels.get('alertname')}\nInstance: {alert.labels.get('instance')}"
            # send_telegram_message(notify_msg)
            continue

        # Gom thông tin sự cố
        alert_name = alert.labels.get("alertname", "Unknown Alert")
        instance = alert.labels.get("instance", "Unknown Instance")
        severity = alert.labels.get("severity", "unknown")
        summary = alert.annotations.get("summary", "No summary")
        description = alert.annotations.get("description", "No description")

        incident_details = f"""
        - Cảnh báo: {alert_name}
        - Server: {instance}
        - Mức độ: {severity}
        - Tóm tắt: {summary}
        - Chi tiết: {description}
        - Thời gian bắt đầu: {alert.startsAt}
        """

        print(f"🔍 Đang phân tích sự cố: {alert_name} trên {instance}...")
        
        # Gọi AI phân tích
        ai_analysis = analyze_incident_with_ai(incident_details)
        
        # Gửi báo cáo qua Telegram
        report_header = f"🚨 *CẢNH BÁO HỆ THỐNG (AI ANALYZED)*\n"
        report_header += f"🔥 *Sự cố*: {alert_name}\n"
        report_header += f"🖥️ *Instance*: `{instance}`\n"
        report_header += f"📅 *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_header += f"\n---\n\n"
        
        final_report = report_header + ai_analysis
        send_telegram_message(final_report)

# 6. Các API Endpoints
@app.post("/webhook")
async def prometheus_webhook(payload: AlertmanagerPayload, background_tasks: BackgroundTasks):
    """
    Endpoint nhận cảnh báo từ Prometheus Alertmanager.
    Sử dụng BackgroundTasks để phản hồi Prometheus ngay lập tức (200 OK) 
    trong khi AI vẫn đang phân tích dưới nền.
    """
    print(f"📥 Đã nhận {len(payload.alerts)} cảnh báo từ Alertmanager.")
    background_tasks.add_task(process_alerts_task, payload)
    return {"status": "success", "message": "Alerts are being processed by AI Agent"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "ai_enabled": client is not None,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    # Chạy server tại port 8080 (hoặc port tùy chọn)
    print("🚀 Khởi động AI Ops Webhook Server trên port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
