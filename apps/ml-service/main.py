from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from starlette.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

from port_probing import (
    DETECTION_FEATURES,
    predict_port_probing,
    train_port_probing_model,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = None
    app.state.model_metrics = None
    app.state.startup_error = None
    try:
        app.state.model, app.state.model_metrics = train_port_probing_model()
        logger.info("ML model loaded successfully with metrics: %s", app.state.model_metrics)
    except FileNotFoundError as exc:
        app.state.startup_error = str(exc)
        logger.error("Model file not found: %s", exc)
    except Exception as exc:
        app.state.startup_error = f"Failed to load model: {exc}"
        logger.error("Model load failed: %s", exc)
    yield

app = FastAPI(
    title="ML Port Probing Service", version="0.1.0", lifespan=lifespan
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [ml-service] %(message)s",
)
logger = logging.getLogger("ml-service")

REQUEST_COUNT = Counter(
    "ml_service_requests_total", "Total ML service requests", ["path", "method", "status"]
)
REQUEST_LATENCY = Histogram(
    "ml_service_request_duration_seconds", "ML service request latency", ["path", "method"]
)

@app.middleware("http")
async def strip_ml_prefix(request, call_next):
    path = request.scope.get("path") or request.url.path
    if path == "/ml":
        request.scope["path"] = "/"
    elif path.startswith("/ml/"):
        request.scope["path"] = path[3:] or "/"
    return await call_next(request)

class TrafficSample(BaseModel):
    dst_port: int = Field(..., ge=0, le=65535, description="Destination port")
    src_port: int = Field(..., ge=0, le=65535, description="Source port")
    inter_arrival_time: float = Field(..., ge=0, description="Seconds between packets")
    stream_1_count: int = Field(..., ge=0, description="Recent packet count")
    l4_tcp: bool = Field(..., description="Is the packet TCP?")
    l4_udp: bool = Field(..., description="Is the packet UDP?")

class PredictionResponse(BaseModel):
    is_port_probe: bool
    confidence: Optional[float] = None
    model_metrics: Optional[dict] = None

@app.get("/")
@app.get("/ml")
@app.get("/ml/")
def index() -> Dict[str, str]:
    return {
        "message": "ML service is running",
        "predict_endpoint": "/ml/predict",
        "health_endpoint": "/ml/health",
        "metrics_endpoint": "/ml/metrics",
    }

@app.get("/health")
@app.get("/ml/health")
def health() -> Dict[str, object]:
    REQUEST_COUNT.labels(path="/health", method="GET", status=200).inc()
    REQUEST_LATENCY.labels(path="/health", method="GET").observe(0.0)
    return {
        "status": "ok",
        "model_ready": app.state.model is not None,
        "startup_error": app.state.startup_error,
        "features": DETECTION_FEATURES,
    }

@app.get("/metrics")
@app.get("/ml/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/predict", response_model=PredictionResponse)
@app.post("/ml/predict", response_model=PredictionResponse)
def predict(sample: TrafficSample) -> PredictionResponse:
    start = time.perf_counter()
    path = "/predict"
    method = "POST"
    if app.state.model is None:
        raise HTTPException(
            status_code=503,
            detail=app.state.startup_error
            or "Model not yet available for inference",
        )

    normalized_sample = _normalize_sample(sample)

    try:
        label, confidence = predict_port_probing(
            app.state.model, normalized_sample
        )
    except Exception as exc:
        REQUEST_COUNT.labels(path=path, method=method, status=500).inc()
        raise HTTPException(status_code=500, detail=f"Failed to run inference: {exc}")

    duration = time.perf_counter() - start
    REQUEST_COUNT.labels(path=path, method=method, status=200).inc()
    REQUEST_LATENCY.labels(path=path, method=method).observe(duration)
    logger.info(
        "predict completed status=200 duration_ms=%.2f confidence=%s",
        duration * 1000,
        confidence,
    )

    return PredictionResponse(
        is_port_probe=bool(label),
        confidence=confidence,
        model_metrics=app.state.model_metrics,
    )

def _normalize_sample(sample: TrafficSample) -> Dict[str, float]:
    payload = sample.model_dump()
    payload["l4_tcp"] = int(payload["l4_tcp"])
    payload["l4_udp"] = int(payload["l4_udp"])
    return payload

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
