import requests
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_chat_id():
    """
    Lấy Chat ID thực tế từ getUpdates.
    Dùng khi bị lỗi 403 hoặc không chắc TELEGRAM_CHAT_ID trong .env có đúng không.
    Yêu cầu: Phải nhắn ít nhất 1 tin cho bot trước khi chạy hàm này.
    """
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN không tìm thấy trong file .env")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get("ok"):
            print(f"Token không hợp lệ hoặc bot lỗi: {data.get('description')}")
            return None

        results = data.get("result", [])
        if not results:
            print("Không tìm thấy tin nhắn nào.")
            print("Hãy mở Telegram, tìm bot của bạn và nhấn /start hoặc gửi bất kỳ tin nhắn nào, rồi chạy lại.")
            return None

        # Lấy chat_id từ tin nhắn mới nhất
        latest = results[-1]
        chat = latest.get("message", {}).get("chat", {})
        chat_id = chat.get("id")
        chat_name = chat.get("username") or chat.get("first_name") or "Unknown"

        print(f"Tìm thấy Chat ID: {chat_id}  (từ user: {chat_name})")
        print(f"Hãy cập nhật TELEGRAM_CHAT_ID={chat_id} vào file .env của bạn")
        return chat_id

    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi kết nối khi gọi getUpdates: {e}")
        return None


def send_telegram_message(message=None, chat_id=None):
    """Sends a message to the configured Telegram chat with error handling."""

    # 1. Dùng chat_id truyền vào hoặc fallback về biến môi trường
    effective_chat_id = chat_id or TELEGRAM_CHAT_ID

    # 2. Đảm bảo tin nhắn luôn có nội dung mặc định
    if message is None or str(message).strip() == "":
        print(" Warning: Tin nhắn trống. Đang sử dụng nội dung mặc định...")
        message = " *Hệ thống AI Ops Thông báo*:\nĐã phát hiện một sự cố nhưng không có nội dung chi tiết kèm theo."

    if not TELEGRAM_TOKEN or not effective_chat_id:
        print("❌ Error: TELEGRAM_TOKEN hoặc TELEGRAM_CHAT_ID không tìm thấy trong file .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": effective_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        # 3. FIX 403: Tự động gợi ý lấy đúng chat_id
        if response.status_code == 403:
            print(" Error 403: Bot bị chặn hoặc chat_id không đúng.")
            print(" Đang thử tìm Chat ID thực tế từ getUpdates...\n")
            fetched_id = get_chat_id()
            if fetched_id and str(fetched_id) != str(effective_chat_id):
                print(f"\n Phát hiện Chat ID không khớp!")
                print(f"   .env hiện tại : {effective_chat_id}")
                print(f"   Chat ID đúng  : {fetched_id}")
                print(f" Cập nhật TELEGRAM_CHAT_ID={fetched_id} vào .env rồi chạy lại.")
            return False

        # 4. Bắt lỗi 400 (sai định dạng Markdown)
        elif response.status_code == 400:
            error_detail = response.json().get("description", response.text)
            print(f" Error 400: Bad Request — {error_detail}")
            print(" Thử gửi lại không dùng Markdown...")
            # Retry không có parse_mode
            payload.pop("parse_mode")
            retry = requests.post(url, json=payload, timeout=10)
            if retry.ok:
                print(" Message sent (plain text) successfully!")
                return True
            print(f" Retry cũng thất bại: {retry.text}")
            return False

        response.raise_for_status()
        print(" Message sent to Telegram successfully!")
        return True

    except requests.exceptions.RequestException as e:
        print(f" Lỗi kết nối khi gửi tin nhắn: {e}")
        return False


if __name__ == "__main__":
    # Test message
    test_msg = "*AI Ops Alert Test*\nSystem is now connected to Telegram!"
    send_telegram_message(test_msg)

    # Test empty message case
    print("\n--- Testing empty message case ---")
    send_telegram_message("")

    # Uncomment dòng dưới nếu muốn kiểm tra / lấy lại Chat ID đúng
    # print("\n--- Lấy Chat ID từ getUpdates ---")
    # get_chat_id()