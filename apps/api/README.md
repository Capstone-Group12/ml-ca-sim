# API (FastAPI)

FastAPI backend that sanitizes raw attack outputs and forwards them to the ML service.

## Startup (local)

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t api-backend apps/api
docker run -p 8000:8000 api-backend
```
