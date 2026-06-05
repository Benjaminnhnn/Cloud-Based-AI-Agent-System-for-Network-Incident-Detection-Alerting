# RAG System Guide

## 1. Muc tieu

He thong RAG cung cap ngu canh van hanh cho AI Agent khi phan tich su co. No ket hop hai loai tri thuc:

- Quy trinh chuan da duoc review trong cac file runbook Markdown.
- Kinh nghiem dong tu incident da xu ly va feedback cua admin.

RAG khong tu dong sua file runbook. Feedback duoc luu vao vector database de truy xuat cho cac incident tuong tu trong tuong lai.

Retrieval loc theo `alert_name` va bo cac ket qua co ChromaDB distance vuot `RAG_MAX_DISTANCE`. Vi vay mot alert CPU khong duoc phep lay runbook Nginx hoac Redis chi vi co chung mot vai tu khoa he thong.

## 2. Thanh phan chinh

| Thanh phan | Vai tro |
| --- | --- |
| `core/rag_engine.py` | Khoi tao ChromaDB, nap runbook, luu incident, luu feedback va truy xuat tri thuc. |
| `core/tasks.py` | Goi RAG khi phan tich alert, xu ly feedback va luu ket qua verify. |
| `core/main.py` | Khoi tao RAG collections khi AI Agent startup. |
| `config/knowledge_base/*.md` | Nguon tri thuc chuan duoc track trong Git. |
| `tools/inspect_rag_db.py` | Cong cu xem collections, metadata va noi dung document trong ChromaDB. |

## 3. Kien truc du lieu

RAG su dung hai ChromaDB collections rieng biet.

### `standard_runbooks`

Chua cac runbook chuan tu:

```text
agent_src/config/knowledge_base/*.md
```

Moi file Markdown duoc chia thanh cac chunk theo heading va kich thuoc gioi han. Metadata cua moi chunk gom:

```text
source
source_file
document_type=standard_runbook
chunk_index
heading
```

Runbook la source of truth co the review, sua doi va commit vao Git.

### `incident_memory`

Chua du lieu runtime:

- Incident history sau khi task verify ket thuc.
- Feedback cua admin co ket qua `accepted` hoac `revised`.

Metadata thuong gap:

```text
source=incident_history
document_type=incident_history
alert_name
timestamp
outcome
```

Hoac:

```text
source=admin_feedback
document_type=admin_feedback
alert_name
incident_id
timestamp
review_status
```

Feedback `rejected` khong duoc luu vao RAG.

## 4. Vi sao can hai nguon du lieu

Runbook va ChromaDB khong trung vai tro:

- Runbook Markdown cung cap quy trinh chuan, de review va version control.
- ChromaDB cung cap kha nang semantic retrieval va luu kinh nghiem dong.

Neu chi co runbook, Agent khong hoc duoc tu cac tinh huong da xu ly. Neu chi co ChromaDB, he thong mat source of truth de review va co nguy co tai su dung feedback kem chat luong.

## 5. Luong nap va truy xuat

```text
AI Agent startup
    |
    +-- Tao standard_runbooks va incident_memory
    |
    +-- Doc config/knowledge_base/*.md
    |
    +-- Chunk runbook theo heading
    |
    +-- Upsert chunks vao standard_runbooks

Alert firing
    |
    +-- Build incident details
    |
    +-- Query standard_runbooks
    |
    +-- Query incident_memory
    |
    +-- Dua ngu canh RAG vao deterministic diagnosis hoac Gemini workflow
    |
    +-- Gui huong dan xu ly qua Telegram
```

## 6. Luong feedback cua admin

```text
Admin gui /feedback <incident_id> <giai phap>
    |
    +-- AI Agent lay incident context tu Redis
    |
    +-- Danh gia feedback
    |
    +-- accepted/revised: luu ban da review vao incident_memory
    |
    +-- rejected: khong luu vao RAG
```

Redis va ChromaDB co muc dich khac nhau:

- Redis giu context ngan han cua incident dang xu ly.
- ChromaDB giu tri thuc dai han de truy xuat cho incident sau.

## 7. Luu tru trong Docker

Trong release deployment, `ai-agent` va `celery-worker` phai dung chung mot persistent volume tai:

```text
/app/vector_db
```

Bien moi truong:

```env
VECTOR_DB_PATH=/app/vector_db
RAG_MAX_DISTANCE=1.2
```

Volume staging:

```text
vector-db-staging
```

Volume production:

```text
vector-db-prod
```

Khong commit cac file ChromaDB runtime vao Git.

## 8. Xem du lieu runbook trong repo

Tu root cua repo:

```bash
find agent_src/config/knowledge_base -maxdepth 1 -type f -name '*.md'
sed -n '1,200p' agent_src/config/knowledge_base/<runbook-file>.md
```

Tren PowerShell:

```powershell
Get-ChildItem agent_src/config/knowledge_base -Filter *.md
Get-Content agent_src/config/knowledge_base/<runbook-file>.md
```

## 9. Xem du lieu ChromaDB tren staging

Chay cac lenh sau tren Monitor EC2, khong chay trong WSL local:

```bash
ssh -i "$KEY" ec2-user@13.213.161.83
cd /home/ec2-user/aws-hybrid
```

Liet ke collections:

```bash
docker exec celery-worker-staging python tools/inspect_rag_db.py
```

Xem runbook chunks:

```bash
docker exec celery-worker-staging python tools/inspect_rag_db.py \
  --collection standard_runbooks
```

Xem incident memory:

```bash
docker exec celery-worker-staging python tools/inspect_rag_db.py \
  --collection incident_memory
```

Chi xem feedback cua admin:

```bash
docker exec celery-worker-staging python tools/inspect_rag_db.py \
  --collection incident_memory \
  --source admin_feedback
```

Chi xem incident history:

```bash
docker exec celery-worker-staging python tools/inspect_rag_db.py \
  --collection incident_memory \
  --source incident_history
```

## 10. Xac nhan shared volume

Hai container phai hien cung ten volume tai `/app/vector_db`:

```bash
docker inspect ai-agent-staging \
  --format '{{range .Mounts}}{{println .Name .Destination}}{{end}}'

docker inspect celery-worker-staging \
  --format '{{range .Mounts}}{{println .Name .Destination}}{{end}}'
```

Xem chi tiet volume:

```bash
docker volume inspect aws-hybrid-staging-monitor_vector-db-staging
```

Ten volume thuc te co the thay doi theo Docker Compose project name.

## 11. Kiem tra sau deploy

```bash
docker restart ai-agent-staging
docker logs --tail=100 ai-agent-staging

docker exec celery-worker-staging python tools/inspect_rag_db.py
```

Ket qua mong doi:

```text
standard_runbooks: <so document lon hon 0>
incident_memory: <so document co the bang 0>
```

`incident_memory: 0 documents` la binh thuong neu chua co incident hoac feedback moi.

## 12. Kiem thu feedback

1. Tao mot alert staging va lay Incident ID tu Telegram.
2. Gui feedback:

```text
/feedback <incident_id> Kiem tra logs va health endpoint truoc khi restart service.
```

3. Cho Agent tra ve `accepted` hoac `revised`.
4. Kiem tra du lieu:

```bash
docker exec celery-worker-staging python tools/inspect_rag_db.py \
  --collection incident_memory \
  --source admin_feedback
```

## 13. Migration tu collection cu

Phien ban cu su dung collection:

```text
ops_runbooks
```

Khi RAG Engine startup, du lieu dong co `source=incident_history` hoac `source=admin_feedback` se duoc migrate sang `incident_memory`.

Runbook cu khong duoc migrate nguyen file sang `standard_runbooks`, vi runbook hien tai se duoc chunk va nap lai tu cac file Markdown trong repo.

## 14. Backup truoc khi doi volume

Truoc lan recreate dau tien co shared volume, backup ChromaDB cu:

```bash
docker cp celery-worker-staging:/app/vector_db /home/ec2-user/rag-vector-db-backup
```

Khong xoa volume ChromaDB trong demo hoac production neu chua co backup.

## 15. Troubleshooting

### Chi thay `ops_runbooks`

Image moi chua duoc deploy hoac AI Agent chua startup.

```bash
docker restart ai-agent-staging
docker logs --tail=100 ai-agent-staging
```

### `incident_memory` khong ton tai

Kiem tra image tag cua `ai-agent-staging` va deploy lai monitor role. Cong cu inspect moi se bao collection hien co thay vi traceback.

### Feedback khong xuat hien

Kiem tra:

```bash
docker logs --tail=200 celery-worker-staging
docker exec redis-staging redis-cli GET "incident:<incident_id>"
docker exec celery-worker-staging python tools/inspect_rag_db.py \
  --collection incident_memory \
  --source admin_feedback
```

Feedback chi duoc luu neu incident context con trong Redis va review status la `accepted` hoac `revised`.

### Hai container thay du lieu khac nhau

Kiem tra ca hai container co mount cung volume `/app/vector_db`. Neu khong, deploy lai monitor role bang release compose moi.

## 16. Test trong repo

Tu thu muc `agent_src`:

```bash
python -m pytest tests/test_rag_engine.py
python -m pytest tests/test_inspect_rag_db.py
python -m pytest tests
```
