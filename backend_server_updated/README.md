# Backend for Chrome Extension: AI Business Dev Email (v1.1.0)

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Health check
- Open http://localhost:8000/  → should return {"status":"ok", ...}
- Open http://localhost:8000/healthz → should return {"ok": true}

### If model downloads fail (first run / offline)
- Set `LITE_MODE=1` to skip heavy models and use a lightweight template:
```bash
LITE_MODE=1 uvicorn server:app --host 0.0.0.0 --port 8000 --reload
# Windows PowerShell:
# $env:LITE_MODE=1; uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
