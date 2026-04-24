# Bao Cao Loi Trien Khai CI/CD va Cach Khac Phuc

Ngay cap nhat: 2026-04-17
Repository: Benjaminnhnn/Cloud-Based-AI-Agent-System-for-Network-Incident-Detection-Alerting
Workflow: .github/workflows/ci.yml
Job: lint-test-build

## 1) Tom tat su co

Trong qua trinh trien khai CI/CD, workflow `CI / lint-test-build` da fail nhieu lan truoc khi on dinh.

- Run #1 (commit `32330cb`): fail
- Run #2 (commit `751e815`): fail
- Run #3 (commit `cd8b966`): success

## 2) Trieu chung va loi thuc te

### Loi chinh gay fail CI

Pytest fail o buoc test API do xung dot phien ban `httpx` voi stack `FastAPI/Starlette` hien tai.

Loi xuat hien:

```text
TypeError: Client.__init__() got an unexpected keyword argument 'app'
```

Boi canh:

- Workflow cai `httpx` khong pin phien ban (`pip install pytest ruff httpx`)
- Ban `httpx` moi nhat khong con tuong thich voi cach `TestClient` duoc su dung trong bo thu vien hien tai

### Nhung dau hieu gay nham lan ban dau

1. Da tung nghi package AI SDK sai ten (`google-genai` vs `google-generativeai`)
2. Sau khi reproduce day du theo tung step CI, xac dinh day KHONG phai nguyen nhan fail pytest trong run moi

## 3) Nguyen nhan goc (Root Cause)

- Thieu pin version cho dependency test (`httpx`)
- CI moi lan chay co the keo ban moi nhat => de vo tinh vo compatibility

## 4) Cach khac phuc da ap dung

### 4.1 Sua workflow CI

File da sua: `.github/workflows/ci.yml`

Tu:

```yaml
pip install pytest ruff httpx
```

Thanh:

```yaml
pip install pytest ruff "httpx<0.28"
```

### 4.2 Xac nhan lai dependency cua AI agent

File: `agent_src/requirements.txt`

- Giu `google-genai` de khop voi import hien tai:

```python
from google import genai
```

### 4.3 Commit fix

- `cd8b966` - `fix(ci): pin httpx for FastAPI TestClient compatibility`

## 5) Ket qua sau khac phuc

Run CI moi nhat:

- Run ID: `24575277582`
- SHA: `cd8b966`
- Status: `completed`
- Conclusion: `success`

Tat ca step trong job `lint-test-build` deu pass:

1. Checkout
2. Setup Python
3. Install dependencies
4. Lint (critical rules)
5. Test AI Agent (pytest)
6. Test Backend API (pytest)
7. Build AI Agent image
8. Build Payment API image
9. Validate Docker Compose files

## 6) Cac canh bao/han che con lai (khong lam fail run)

1. Canh bao Node.js 20 deprecation cho GitHub Actions (`actions/checkout@v4`, `actions/setup-python@v5`)
2. Moi truong local co the khong co `docker compose` plugin, nhung GitHub runner co ho tro nen workflow van pass
3. Download log zip qua API public co the bi `403` neu khong xac thuc; tuy nhien Jobs API van xac nhan day du trang thai step

## 7) Huong dan phong ngua tai phat

1. Pin dependency test/tooling trong CI (khong de latest floating)
2. Duy tri matrix test tuong thich cho cac cap:
   - fastapi/starlette/httpx
3. Bo sung buoc verify lockfile hoac constraints file
4. Review warning deprecation dinh ky (Node runtime, Python package deprecation)

## 8) Mau checklist truoc khi merge

```text
[ ] Cai dependencies trong moi truong sach (venv)
[ ] Ruff check pass
[ ] Pytest pass (agent + backend)
[ ] Docker build pass (2 images)
[ ] Docker compose config validate pass
[ ] Kiem tra warning quan trong (deprecation/breaking changes)
```

## 9) Lenh reproduce nhanh (local)

```bash
python3 -m venv .venv-ci
. .venv-ci/bin/activate
python -m pip install --upgrade pip
pip install -r agent_src/requirements.txt
pip install -r demo-web/backend/requirements.txt
pip install pytest ruff "httpx<0.28"
ruff check agent_src demo-web/backend/app --select E9,F63,F7,F82
PYTHONPATH=agent_src pytest -q agent_src/tests
PYTHONPATH=demo-web/backend pytest -q demo-web/backend/tests
```
