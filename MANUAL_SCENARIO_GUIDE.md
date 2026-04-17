# 🚀 Hướng Dẫn Thực Hiện Kịch Bản Thủ Công

## Tổng Quan

Thay vì sử dụng `workflow_orchestrator.py`, bạn có thể thực hiện toàn bộ kịch bản **thủ công từng bước**:

1. **Trigger lỗi** - Tự thực hiện lệnh để gây ra lỗi
2. **Monitor** - Chạy `manual_test.py` để giám sát và detect lỗi
3. **Telegram alert** - Hệ thống tự động gửi alert + Gemini analysis
4. **Click approve** - Bạn click nút xanh ✅ trong Telegram
5. **Recovery** - Hệ thống tự động khắc phục khi bạn approve
6. **Kết quả** - Nhận kết quả hoặc giải pháp thủ công nếu fail

---

## 📋 Các Kịch Bản Có Sẵn

### 1️⃣ Nginx Down (Nginx Sập)

**Mô tả:** Nginx process bị kill/sập, port 80 không lắng nghe

#### Cách Trigger:

**Option A: Kill port 80 process**
```bash
# Tìm và kill tất cả process trên port 80
sudo lsof -ti:80 | xargs kill -9

# Hoặc dùng pkill
sudo pkill -9 nginx

# Hoặc stop service
sudo systemctl stop nginx
```

**Option B: Disable nginx config**
```bash
# Rename config để nginx không thể restart
sudo mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
```

#### Verify nginx is down:
```bash
# Test 1: Connection refused
curl -I http://localhost:80
# Expected: curl: (7) Failed to connect to localhost port 80: Connection refused

# Test 2: Port not listening
sudo netstat -tulnp | grep :80
# Expected: NO output (port 80 không có trong list)

# Test 3: Service status
sudo systemctl status nginx
# Expected: inactive (dead) or failed

# Test 4: Website inaccessible
curl -I http://localhost
# Expected: Connection refused
```

---

### 2️⃣ Port Conflict (Port 80 Bị Chiếm)

**Mô tả:** Một process khác chiếm port 80, nginx không thể start

#### Cách Trigger:
```bash
# Tạo một dummy service chiếm port 80
python3 -c "import socket; s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('0.0.0.0', 80)); s.listen(1); print('Listening on port 80'); s.accept()" &
DUMMY_PID=$!

# Cố gắng restart nginx (sẽ fail vì port đã chiếm)
sudo systemctl restart nginx

# Kill dummy process khi xong
kill $DUMMY_PID
```

#### Verify port conflict:
```bash
# Xem process chiếm port 80
sudo lsof -i :80

# Nginx log sẽ có error
sudo tail -f /var/log/nginx/error.log
# Expected: bind() to 0.0.0.0:80 failed (98: Address already in use)
```

---

### 3️⃣ Config Error (Lỗi Cấu Hình)

**Mô tả:** File nginx.conf có lỗi syntax

#### Cách Trigger:
```bash
# Backup config gốc
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.good

# Thêm syntax error vào config
echo "invalid nginx directive here;" | sudo tee -a /etc/nginx/nginx.conf

# Test syntax
sudo nginx -t
# Expected: nginx: [emerg] unexpected ";" in /etc/nginx/nginx.conf:500

# Cố gắng restart
sudo systemctl restart nginx
# Expected: Job for nginx.service failed because the control process exited with error code
```

#### Restore:
```bash
sudo cp /etc/nginx/nginx.conf.good /etc/nginx/nginx.conf
sudo systemctl restart nginx
```

---

### 4️⃣ Database Connection Error (Lỗi Kết Nối DB)

**Mô tả:** PostgreSQL không kết nối được

#### Cách Trigger:
```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Verify it's down
psql -U postgres -c "SELECT 1"
# Expected: psql: error: could not connect to server: Connection refused
```

#### Restore:
```bash
sudo systemctl start postgresql
```

---

### 5️⃣ Disk Space Full (Hết Dung Lượng)

**Mô tả:** Ổ cứng sắp hết hoặc hết dung lượng

#### Cách Trigger (Test only - NOT recommended for prod):
```bash
# Check current disk usage
df -h

# Create large dummy file (500MB)
dd if=/dev/zero of=/tmp/dummy_large_file bs=1M count=500

# Verify
df -h
```

#### Restore:
```bash
rm /tmp/dummy_large_file
```

---

## 🔄 Luồng Thực Hiện: Step by Step

### Step 1: Mở 2 Terminal

**Terminal 1 (Monitoring):**
```bash
cd /home/hoang_viet/aws-hybrid/agent_src
python3 manual_test.py
```

Output sẽ hiển thị:
```
════════════════════════════════════════════════════════════════════════════════
🚀 NGINX MANUAL CRASH MONITORING
════════════════════════════════════════════════════════════════════════════════

⏳ Monitoring for nginx crash (timeout: 120s)...
   Đợi bạn crash nginx...

✅ Initial status: RUNNING
  [3s] Nginx: UP ✅
  [6s] Nginx: UP ✅
  [9s] Nginx: UP ✅
```

**Terminal 2 (Commands):**
Dùng để chạy các lệnh trigger lỗi

### Step 2: Trigger lỗi trong Terminal 2

Ví dụ - Trigger nginx down:
```bash
# Terminal 2
sudo lsof -ti:80 | xargs kill -9
```

### Step 3: Monitor sẽ detect trong Terminal 1

```
[12s] Nginx: UP ✅
🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴
🔴 NGINX CRASH DETECTED!
🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴

🔍 PHASE 1: Analyze Error
────────────────────────────────────────────────────────────────────────────────
✅ Detected: Kết Nối Bị Từ Chối (Severity: CRITICAL)

📱 PHASE 2: Create Alert Message
────────────────────────────────────────────────────────────────────────────────
✅ Title: 🚨 CRITICAL: Kết Nối Bị Từ Chối 🤖

📋 PHASE 3: Create Approval Request
────────────────────────────────────────────────────────────────────────────────
✅ Request ID: 4298d37a

📤 PHASE 4: Send Alert to Telegram
────────────────────────────────────────────────────────────────────────────────
✅ Alert sent with buttons
   [✅ DUYỆT & THỰC HIỆN KHẮC PHỤC]
   [❌ HỦY] [📋 CHI TIẾT]

⏳ PHASE 5: Wait for Your Approval
────────────────────────────────────────────────────────────────────────────────
👉 Go to Telegram and click the green button!
   Timeout: 300 seconds
```

### Step 4: Bạn mở Telegram và click nút xanh

✅ **DUYỆT & THỰC HIỆN KHẮC PHỤC**

### Step 5: Monitor sẽ tự động execute recovery

```
✅ APPROVED! Executing recovery...

⚙️  PHASE 6: Execute Recovery
────────────────────────────────────────────────────────────────────────────────
📌 Kill processes on port 80...
📌 Restore nginx.conf if needed...
📌 Restart nginx...
📌 Verifying recovery...
   Port 80: LISTENING ✅

📊 PHASE 7: Report Results
────────────────────────────────────────────────────────────────────────────────
✅ Success message sent to Telegram!
```

Hoặc nếu fail:

```
⚙️  PHASE 6: Execute Recovery
────────────────────────────────────────────────────────────────────────────────
📌 Kill processes on port 80...
📌 Restore nginx.conf if needed...
📌 Restart nginx...
📌 Verifying recovery...
   Port 80: NOT LISTENING ❌

📊 PHASE 7: Report Results
────────────────────────────────────────────────────────────────────────────────
❌ Failure message sent to Telegram!
   + Manual intervention with Gemini solutions
```

---

## 📱 Telegram Messages

### Alert Message (Khi lỗi được detect)

```
🚨 CRITICAL: Kết Nối Bị Từ Chối 🤖

Port 80 Connection Refused

━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dịch Vụ: Nginx
Mức Độ Nghiêm Trọng: CRITICAL
Lỗi: Connection refused to 127.0.0.1:80
Người Dùng Bị Ảnh Hưởng: Tất cả người dùng

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 PHÂN TÍCH (AI-POWERED):

**Xác Định Nguyên Nhân Gốc:**
Nginx process không chạy hoặc không lắng nghe trên port 80...

**Mức Độ Ảnh Hưởng:**
Toàn bộ hệ thống web không hoạt động...

**Các Bước Khắc Phục:**
1. Kill các process chiếm port 80
2. Khởi động lại nginx service
3. Kiểm tra service status
4. Verify port 80 listening

━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bạn muốn làm gì?

[✅ DUYỆT & THỰC HIỆN KHẮC PHỤC]
[❌ HỦY] [📋 CHI TIẾT]
```

### Success Message (Khi khắc phục thành công)

```
✅ RECOVERY SUCCESSFUL!

Nginx has been restored:
• Service: ACTIVE ✅
• Port 80: LISTENING ✅
• Website: ONLINE ✅

🌐 Website trở lại bình thường!
```

### Manual Intervention Message (Khi auto khắc phục fail)

```
👨‍💼 CẦN CAN THIỆP THỦ CÔNG - GIẢI PHÁP CHI TIẾT

Lỗi: Kết Nối Bị Từ Chối
Mức Độ: CRITICAL 🔴

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PHÂN TÍCH VÀ GIẢI PHÁP (AI-POWERED):

**Xác Định Nguyên Nhân Gốc:**
Nginx process crashed hoặc bị kill...

**Các Bước Khắc Phục Chi Tiết:**
1. SSH vào server: ssh user@server
2. Kiểm tra trạng thái: sudo systemctl status nginx
3. Khởi động lại: sudo systemctl restart nginx
4. Verify: curl -I http://localhost

**Các Lệnh SSH:**
sudo lsof -ti:80 | xargs kill -9
sudo systemctl restart nginx
sudo systemctl status nginx

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hãy thực hiện các lệnh trên SSH server để fix lỗi.
Không cần click button - System sẽ tự động kiểm tra.
```

---

## 🛠️ Các Lệnh Tiện Ích

### Kiểm tra Nginx Status
```bash
# Trạng thái service
sudo systemctl status nginx

# Kiểm tra port 80 listening
sudo netstat -tulnp | grep :80
# Hoặc
sudo ss -tulnp | grep :80

# Kiểm tra nginx syntax
sudo nginx -t

# Xem nginx config
sudo cat /etc/nginx/nginx.conf
```

### View Nginx Logs
```bash
# Error log (real-time)
sudo tail -f /var/log/nginx/error.log

# Access log
sudo tail -f /var/log/nginx/access.log

# System log
sudo tail -f /var/log/syslog | grep nginx
```

### Restart Nginx
```bash
# Restart
sudo systemctl restart nginx

# Reload config (graceful)
sudo systemctl reload nginx

# Stop
sudo systemctl stop nginx

# Start
sudo systemctl start nginx
```

### Test Website
```bash
# Test port 80
curl -I http://localhost:80

# Test localhost
curl -I http://localhost

# Test with verbose
curl -v http://localhost

# Check HTTP response
curl http://localhost | head -20
```

---

## 📊 Complete Manual Workflow Example

### Scenario: Nginx Down

```bash
# ════════════════════════════════════════════════════════════════
# Terminal 1: Start Monitoring
# ════════════════════════════════════════════════════════════════
cd /home/hoang_viet/aws-hybrid/agent_src
python3 manual_test.py

# Output:
# ⏳ Monitoring for nginx crash (timeout: 120s)...
# ✅ Initial status: RUNNING
# [3s] Nginx: UP ✅
# [6s] Nginx: UP ✅


# ════════════════════════════════════════════════════════════════
# Terminal 2: Trigger nginx crash (after a few seconds)
# ════════════════════════════════════════════════════════════════
sudo lsof -ti:80 | xargs kill -9

# Verify it's down:
curl -I http://localhost:80
# curl: (7) Failed to connect to localhost port 80: Connection refused


# ════════════════════════════════════════════════════════════════
# Terminal 1: Shows CRASH DETECTED + sends Alert to Telegram
# ════════════════════════════════════════════════════════════════
# 🔴 NGINX CRASH DETECTED!
# 
# 🔍 PHASE 1: Analyze Error
# ✅ Detected: Kết Nối Bị Từ Chối
# 
# 📤 PHASE 4: Send Alert to Telegram
# ✅ Alert sent with buttons
# 
# ⏳ PHASE 5: Wait for Your Approval
# 👉 Go to Telegram and click the green button!


# ════════════════════════════════════════════════════════════════
# YOU: Open Telegram and Click Green Button
# ════════════════════════════════════════════════════════════════
# Message received: 🚨 CRITICAL: Kết Nối Bị Từ Chối 🤖
# Click: [✅ DUYỆT & THỰC HIỆN KHẮC PHỤC]


# ════════════════════════════════════════════════════════════════
# Terminal 1: Auto-executes recovery after approval
# ════════════════════════════════════════════════════════════════
# ✅ APPROVED! Executing recovery...
# 
# ⚙️  PHASE 6: Execute Recovery
# 📌 Kill processes on port 80...
# 📌 Restore nginx.conf if needed...
# 📌 Restart nginx...
# 📌 Verifying recovery...
#    Port 80: LISTENING ✅
# 
# 📊 PHASE 7: Report Results
# ✅ Success message sent to Telegram!


# ════════════════════════════════════════════════════════════════
# YOU: Receive Success Message in Telegram
# ════════════════════════════════════════════════════════════════
# ✅ RECOVERY SUCCESSFUL!
# Service: ACTIVE ✅
# Port 80: LISTENING ✅
# Website: ONLINE ✅
```

---

## ⚠️ Important Notes

1. **Admin Privileges:** Một số lệnh cần `sudo`. Đảm bảo user của bạn có quyền sudo
   ```bash
   sudo visudo
   # Thêm: username ALL=(ALL) NOPASSWD: ALL
   ```

2. **Backup Config:** Luôn backup nginx.conf trước khi modify
   ```bash
   sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
   ```

3. **Telegram Bot Running:** Đảm bảo bot telegramđã được setup và chạy
   ```bash
   # Check if bot is running
   ps aux | grep telegram
   ```

4. **Services Running:** Đảm bảo tất cả services đã start
   ```bash
   docker ps  # Check Docker containers
   sudo systemctl status nginx
   sudo systemctl status postgresql  # if using DB
   ```

5. **Gemini API:** Model `gemini-2.5-flash` cần API key valid
   ```bash
   cat /home/hoang_viet/aws-hybrid/agent_src/.env | grep GEMINI
   ```

---

## 🎯 Quick Commands Reference

```bash
# Start monitoring
cd /home/hoang_viet/aws-hybrid/agent_src && python3 manual_test.py

# Kill nginx
sudo lsof -ti:80 | xargs kill -9

# Restart nginx
sudo systemctl restart nginx

# Check port 80
sudo netstat -tulnp | grep :80

# Test website
curl -I http://localhost

# View error logs
sudo tail -f /var/log/nginx/error.log

# Nginx syntax check
sudo nginx -t
```

---

**✅ You're ready to go! Hãy bắt đầu với scenario thứ nhất: Nginx Down**
