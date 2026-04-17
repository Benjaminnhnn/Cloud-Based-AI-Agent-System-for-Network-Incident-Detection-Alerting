# Hướng Dẫn Kiểm Tra Log Lỗi - How to Check Error Logs

## 🚀 Cách Nhanh Nhất (Fastest Way)

### Run Test + Save Log + Show Errors

```bash
cd /home/hoang_viet/aws-hybrid/agent_src
source ../venv/bin/activate
python3 test_scenario_a_nginx_recovery.py 2>&1 | tee test_run.log

# Sau đó xem lỗi:
grep -i "error\|failed" test_run.log
```

### Run Test + Show Only Key Info

```bash
cd /home/hoang_viet/aws-hybrid/agent_src
source ../venv/bin/activate
python3 test_scenario_a_nginx_recovery.py 2>&1 | grep -E "(TEST|PASSED|FAILED|STEP|recovery_status)"
```

## 📊 5 Cách Kiểm Tra Log

### 1️⃣ Cách Đơn Giản Nhất - Run Test với Log File

```bash
cd /home/hoang_viet/aws-hybrid/agent_src
source ../venv/bin/activate

# Run test và lưu log
python3 test_scenario_a_nginx_recovery.py 2>&1 | tee my_test.log

# Xem lỗi
cat my_test.log | grep -i "error"

# Đếm lỗi
grep -i "error\|failed" my_test.log | wc -l
```

### 2️⃣ Kiểm Tra Từng Step

```bash
# Xem tất cả steps
grep "\[STEP" test_run.log

# Xem chỉ failed steps
grep "\[STEP.*failed" test_run.log

# Xem step 4 (config validation)
grep "\[STEP 4\]" test_run.log
```

### 3️⃣ REALTIME - Server + Test 2 Terminals

**Terminal 1 - Start Server:**
```bash
cd /home/hoang_viet/aws-hybrid/agent_src
source ../venv/bin/activate
python3 main.py 2>&1 | tee server.log
```

**Terminal 2 - Run Test:**
```bash
cd /home/hoang_viet/aws-hybrid/agent_src
source ../venv/bin/activate
python3 test_scenario_a_nginx_recovery.py 2>&1
```

**Xem Server Log trong Terminal 1** → Tất cả lỗi hiển thị realtime

### 4️⃣ Search Lỗi Cụ Thể

```bash
# Tất cả ERROR
grep "\- ERROR \-" test_run.log

# Tất cả WARNING
grep "\- WARNING \-" test_run.log

# Lỗi config
grep -i "config.*error\|syntax" test_run.log

# Lỗi restart
grep -i "restart.*failed\|could not restart" test_run.log

# Lỗi connection
grep -i "connection\|refused\|timeout" test_run.log
```

### 5️⃣ Debug Mode - Xem Tất Cả Chi Tiết

```bash
cd /home/hoang_viet/aws-hybrid/agent_src
source ../venv/bin/activate

PYTHONUNBUFFERED=1 python3 << 'PYEOF'
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

import test_scenario_a_nginx_recovery as test
tester = test.TestScenarioA()
tester.run_all_tests()
PYEOF
```

## 🎯 Phân Tích Log Nhanh

### Xem Kết Quả Tóm Tắt

```bash
# Đếm lỗi
echo "Tổng lỗi: $(grep -i 'error\|failed' test_run.log | wc -l)"

# Đếm success
echo "Success: $(grep '- Status: success' test_run.log | wc -l)"

# Đếm failed
echo "Failed: $(grep '- Status: failed' test_run.log | wc -l)"

# Đếm skipped
echo "Skipped: $(grep '- Status: skipped' test_run.log | wc -l)"

# Đếm partial
echo "Partial: $(grep '- Status: partial' test_run.log | wc -l)"
```

### Xem Thứ Tự Các Step

```bash
# Show tất cả steps
cat test_run.log | grep "\[STEP" | cut -d']' -f1 | uniq

# Pretty print
grep "\[STEP" test_run.log | awk -F'] ' '{print $1 "] " $2}' | head -30
```

### Xem Recovery Log Chi Tiết

```bash
# Tất cả steps (7 steps/test)
grep "\[STEP" test_run.log

# Chi tiết từng test
# TEST 1 - Chỉ lấy 7 steps đầu
grep "\[STEP" test_run.log | head -7

# TEST 2 - Chỉ lấy 7 steps tiếp theo  
grep "\[STEP" test_run.log | head -14 | tail -7

# TEST 3 - Và tiếp tục...
grep "\[STEP" test_run.log | head -21 | tail -7
```

## 📝 Lọc Log Theo Nhu Cầu

### Chỉ Xem ERROR
```bash
grep "\- ERROR \-" test_run.log | less
```

### Chỉ Xem WARNING  
```bash
grep "\- WARNING \-" test_run.log | less
```

### Chỉ Xem INFO + SUCCESS
```bash
grep "\- INFO \-" test_run.log | grep "success"
```

### Xem Context (5 dòng trước/sau lỗi)
```bash
grep -B5 -A5 "ERROR\|FAILED" test_run.log
```

### Xem Dòng Số Lỗi
```bash
grep -n "ERROR\|FAILED" test_run.log
```

### Xem Lần Lỗi Đầu Tiên
```bash
grep "\- ERROR \-" test_run.log | head -1
```

### Xem Lần Lỗi Cuối Cùng
```bash
grep -i "error\|failed" test_run.log | tail -1
```

## 💾 Lưu Log Toàn Bộ Session

```bash
# Lưu tất cả output (including timestamps, colors, etc)
script -c "
  cd /home/hoang_viet/aws-hybrid/agent_src
  source ../venv/bin/activate
  python3 test_scenario_a_nginx_recovery.py 2>&1
" full_session.log

# Xem session lại
cat full_session.log

# Tìm lỗi
grep -i "error\|failed" full_session.log
```

## 🔍 Kiểm Tra Telegram Notifications

```bash
# Xem có gửi Telegram không
grep "Telegram" test_run.log

# Xem tất cả thông báo
grep "Message sent\|Failed to send" test_run.log

# Đếm thông báo gửi thành công
grep "Message sent to Telegram successfully" test_run.log | wc -l

# Đếm thông báo thất bại
grep "Failed to send" test_run.log | wc -l
```

## 📋 Ví Dụ Thực Tế

### Test 1 Chạy Lỗi - Kiểm Tra Như Thế Nào?

```bash
# 1. Run test và lưu log
python3 test_scenario_a_nginx_recovery.py 2>&1 | tee test.log

# 2. Xem tất cả lỗi
grep -i "error\|failed" test.log

# 3. Xem context quanh lỗi
grep -B3 -A3 "ERROR\|FAILED" test.log

# 4. Xem step nào thất bại
grep "\[STEP.*failed" test.log

# 5. Xem chi tiết step đó
grep -n "Config.*Config.*error\|Validate Config.*failed" test.log

# 6. Xem thông báo
grep "Telegram\|notification" test.log
```

### Tìm Lỗi Config Validation (Step 4)

```bash
# Step 4 xảy ra ở dòng số bao nhiêu?
grep -n "\[STEP 4\]" test.log

# Lỗi gì?
grep "\[STEP 4\].*failed" test.log

# Error message là gì?
grep -A2 "\[STEP 4\].*failed" test.log | grep "Error:"
```

### Kiểm Tra Tất Cả Tests Pass Hay Fail?

```bash
# Summary
grep "FINAL TEST REPORT\|Success Rate\|Passed\|Failed" test.log

# Hoặc xem cuối file
tail -30 test.log
```

## 🛠️ Useful Commands

| Lệnh | Mục Đích |
|------|---------|
| `grep -i "error" file.log` | Tìm tất cả ERROR (case-insensitive) |
| `grep -n "ERROR" file.log` | Tìm lỗi + line number |
| `grep -c "ERROR" file.log` | Đếm lỗi |
| `grep -v "DEBUG" file.log` | Tất cả trừ DEBUG |
| `tail -50 file.log` | 50 dòng cuối |
| `head -50 file.log` | 50 dòng đầu |
| `less file.log` | Xem từng trang (press q to exit) |
| `wc -l file.log` | Đếm tổng dòng |
| `cat file.log \| sort` | Sắp xếp |
| `cat file.log \| uniq` | Bỏ duplicate |

## 📚 Thông Tin Chi Tiết Hơn

- **Doc Chi Tiết:** [MANUAL_SCENARIO_GUIDE.md](MANUAL_SCENARIO_GUIDE.md)
- **Quick Start:** [SERVICE_STARTUP_GUIDE.md](SERVICE_STARTUP_GUIDE.md#quick-start)
- **Webhook Server Code:** [agent_src/main.py](agent_src/main.py)
- **Monitoring Worker Code:** [agent_src/service_monitor.py](agent_src/service_monitor.py)

## 💡 Tips

1. **Luôn activate virtual environment**
```bash
source /home/hoang_viet/aws-hybrid/venv/bin/activate
```

2. **Luôn capture both stdout và stderr**
```bash
python3 your_script.py 2>&1
```

3. **Luôn lưu log vào file**
```bash
command 2>&1 | tee filename.log
```

4. **Xem log realtime trong 1 terminal**
```bash
tail -f test_run.log
```

5. **Tìm lỗi nhanh**
```bash
grep -i "error\|failed\|exception" test_run.log
```

---

**Ready to check logs?** Start with:
```bash
cd /home/hoang_viet/aws-hybrid/agent_src && \
source ../venv/bin/activate && \
python3 test_scenario_a_nginx_recovery.py 2>&1 | tee test.log && \
echo "Errors found:" && \
grep -i "error\|failed" test.log | wc -l
```
