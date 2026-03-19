# Báo Cáo Lỗi và Giải Pháp Khắc Phục
## Monitoring Stack Deployment Issues

---

## 1. ❌ LỖI: Prometheus Targets Down (Context Deadline Exceeded)

### Triệu chứng:
- Prometheus dashboard hiển thị tất cả Node Exporter targets là **DOWN**
- Error message: `context deadline exceeded`
- Grafana dashboard hiển thị "No data" cho tất cả metrics

### Nguyên nhân:
- Prometheus config sử dụng **Elastic IPs (external public IPs)** để scrape Node Exporter:
  - `54.169.109.245:9100` (bank-web-01)
  - `3.0.123.174:9100` (bank-core-01)
  - `47.131.157.132:9100` (monitor-ai-01)
- Tuy nhiên, EC2 instances trong **VPC kết nối thông qua internal/private IPs**, không phải external IPs
- External IPs chỉ dùng để access từ bên ngoài (SSH, Web UI)
- Internal communication trong VPC không thể route qua external IPs

### Giải pháp:
**File**: `ansible/playbooks/monitoring.yml`

```yaml
- name: Create Prometheus configuration
  copy:
    content: |
      global:
        scrape_interval: 15s
        evaluation_interval: 15s
      
      scrape_configs:
        - job_name: 'prometheus'
          static_configs:
            - targets: ['localhost:9090']
        
        - job_name: 'node'
          static_configs:
            - targets: 
              - 'localhost:9100'
              - '10.10.1.169:9100'    # Monitor internal IP
              - '10.10.1.56:9100'     # Web internal IP
              - '10.10.1.232:9100'    # Core internal IP
```

**Thực hiện:**
1. Lấy internal IPs từ Terraform output:
   ```bash
   terraform output -json | python3 -c "..."
   ```
2. Update monitoring.yml với internal IPs
3. Re-run monitoring playbook
4. Restart Prometheus service

**Kết quả:**
✅ Tất cả 5 targets hiển thị **UP** (localhost:9100, 4x internal IPs)

---

## 2. ❌ LỖI: Grafana Plugin Not Registered (404 Error)

### Triệu chứng:
```
logger=context userId=1 orgId=1 uname=admin
level=error msg="plugin not registered" error="plugin not registered"
status=404 path=/api/ds/query
```

### Nguyên nhân:
- Dashboard panels có **invalid/missing datasourceUid**
- Grafana dashboard JSON không có đúng format datasource reference
- Datasource UID `efge7wazxnjlsb` tồn tại nhưng panel targets không kết nối đúng

### Giải pháp (Attempt 1 - Không thành công):
```json
{
  "targets": [
    {
      "datasourceUid": "efge7wazxnjlsb",
      "expr": "...",
      "refId": "A"
    }
  ]
}
```
❌ Vẫn lỗi plugin not registered

### Giải pháp (Attempt 2 - Không thành công):
```json
{
  "targets": [
    {
      "datasource": {"type": "prometheus", "uid": "efge7wazxnjlsb", "name": "Prometheus"},
      "expr": "...",
      "refId": "A"
    }
  ]
}
```
❌ Vẫn lỗi

### Giải pháp (Final - Thành công ✅):
Sử dụng **datasource name thay vì UID**:
```json
{
  "panels": [
    {
      "id": 1,
      "title": "CPU Usage",
      "type": "timeseries",
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
      "datasource": "Prometheus",
      "targets": [
        {
          "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
          "refId": "A"
        }
      ]
    }
  ]
}
```

**Thực hiện:**
1. Xóa dashboard cũ (with UID reference)
2. Tạo dashboard JSON file mới với datasource name
3. Upload dashboard qua API

**Kết quả:**
✅ Dashboard created successfully với UID: `1b866500-a462-4df7-8702-15276e5ca2ce`

---

## 3. ❌ LỖI: Grafana Datasource Proxy Failure

### Triệu chứng:
- Dashboard panels vẫn hiển thị **"No data"**
- Prometheus datasource test thất bại
- Grafana logs: `error while proxying request to datasource`

### Nguyên nhân:
- Grafana datasource URL: `http://localhost:9090`
- **Docker container không thể access host's localhost**
- Container có network stack riêng, `localhost` chỉ refer tới chính container đó
- Grafana container không có Prometheus chạy bên trong nó
- Cần phải sử dụng **host's internal IP address** để Grafana container access Prometheus

### Giải pháp:
**Bước 1: Lấy internal IP của monitor server**
```bash
terraform output -json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['monitor_private_ip']['value'])"
# Output: 10.10.1.169
```

**Bước 2: Update datasource URL**
```bash
curl -X PUT "http://localhost:3000/api/datasources/1" \
  -u admin:Lehoangviet@123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://10.10.1.169:9090",
    "access": "proxy",
    "isDefault": true,
    "jsonData": {"timeInterval": "15s"}
  }'
```

**Thực hiện:**
```bash
ansible monitor -m shell -a \
  'curl -s -X PUT "http://localhost:3000/api/datasources/1" \
  -u admin:Lehoangviet@123 \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Prometheus\",\"type\":\"prometheus\",\"url\":\"http://10.10.1.169:9090\",\"access\":\"proxy\",\"isDefault\":true,\"jsonData\":{\"timeInterval\":\"15s\"}}"'
```

**Kết quả:**
✅ Datasource updated
✅ Grafana datasource proxy test: **SUCCESS**
✅ Dashboard panels: **Data displayed** ✅

---

## Tóm tắt Root Cause Analysis

| Error | Layer | Root Cause | Solution |
|-------|-------|-----------|----------|
| Prometheus Targets Down | Infrastructure/Networking | External IPs vs Internal IPs | Use private IPs (10.10.x.x) for VPC communication |
| Plugin Not Registered | Dashboard JSON | Invalid datasourceUid format | Use datasource `name` instead of `uid` in JSON |
| Datasource Proxy Failure | Container Networking | Docker localhost isolation | Use host's internal IP (10.10.1.169) |

---

## Key Learnings

### 🔑 VPC Networking (AWS)
- **External IPs (Elastic IPs)**: Used for outside-world access (SSH, HTTP, etc.)
- **Internal IPs (Private IPs)**: Used for instance-to-instance communication within VPC
- EC2 instances resolve `localhost` to themselves, not to other instances
- Always use **internal IPs** for inter-instance communication

### 🐳 Docker Networking
- **Container localhost** ≠ **Host localhost**
- Each container has isolated network namespace
- To access services on host from container, use **host's actual network interface IP**
- Cannot use `localhost:port` from container to reach host services
- Use container DNS or host IP address instead

### 📊 Grafana Best Practices
- Datasource URL should be **reachable from Grafana container** perspective
- For Grafana containers accessing same-host services: use `http://<host-internal-ip>:port`
- Dashboard JSON: use **datasource `name`** field for better compatibility
- Always include `refId` field in query targets
- Test datasource connectivity after configuration changes

### 📈 Monitoring Stack Architecture
```
┌─────────────────────────────────────────────────────┐
│ AWS VPC (10.10.0.0/16)                              │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────────┐       ┌──────────────────┐   │
│  │ monitor-ai-01    │       │ bank-web-01      │   │
│  │ (10.10.1.169)    │       │ (10.10.1.56)     │   │
│  │                  │       │                  │   │
│  │ ┌──────────────┐ │       │ ┌──────────────┐ │   │
│  │ │ Prometheus   │ │       │ │ Node Export  │ │   │
│  │ │ :9090        │◄├─IP───►│ │ :9100 (UP)   │ │   │
│  │ └──────────────┘ │       │ └──────────────┘ │   │
│  │                  │       │                  │   │
│  │ ┌──────────────┐ │       │                  │   │
│  │ │ Grafana(🐳)  │ │       │                  │   │
│  │ │ :3000        │ │       │                  │   │
│  │ │              │ │       │                  │   │
│  │ │ API queries◄┬┘ │       │                  │   │
│  │ └──────────────┘ │       │                  │   │
│  │    ↑             │       │                  │   │
│  │ 10.10.1.169:9090 │       │                  │   │
│  │    (FIXED)       │       │                  │   │
│  │                  │       │                  │   │
│  └──────────────────┘       └──────────────────┘   │
│                                                       │
└─────────────────────────────────────────────────────┘
         ↓ External IP (Elastic IP)
┌─────────────────────────────────────────────────────┐
│ External Access (Your Machine)                       │
├─────────────────────────────────────────────────────┤
│                                                       │
│  47.131.157.132:3000 → Grafana Dashboard ✅         │
│  47.131.157.132:9090 → Prometheus UI ✅             │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## Deployment Status

✅ **COMPLETED:**
- Terraform infrastructure (VPC, 3 EC2 instances, Security Groups)
- Elastic IPs (static public IPs allocated)
- Ansible bootstrap (Python, Docker, tools installed)
- Node Exporter deployment (3 servers collecting metrics)
- Prometheus deployment (scraping 5 targets - UP ✅)
- Grafana deployment (Docker container running)
- Prometheus datasource (configured)
- System Overview dashboard (4 panels: CPU, Memory, Disk, Network)

✅ **WORKING:**
- **Prometheus** collecting metrics from all 3 servers
- **Grafana** displaying live metrics on dashboard
- **Datasource proxy** successfully routing requests to Prometheus

---

## Monitoring Stack Access

| Component | URL | Access | Credentials |
|-----------|-----|--------|-------------|
| **Grafana** | http://47.131.157.132:3000 | Browser | admin / Lehoangviet@123 |
| **Prometheus** | http://47.131.157.132:9090 | Browser | (no auth) |
| **Node Exporter** | http://47.131.157.132:9100/metrics | CLI | (no auth) |

---

**Report Generated:** 2026-03-18  
**Project:** aws-hybrid (aiops-bank)  
**Status:** ✅ All issues resolved - Monitoring stack fully operational
