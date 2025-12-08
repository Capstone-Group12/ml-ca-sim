from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import List, Optional, Sequence

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from models import Attack, AttackType, MLModel, ScanCSV, ScanRow

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://capstone-ml:8001/predict")
ML_SERVICE_DOS_URL = os.getenv("ML_SERVICE_DOS_URL", "http://capstone-ml:8001/dos/predict")
DOS_TARGET_URL = "https://mlcasim-api.edwardnafornita.com/output-json"
FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://mlcasim.edwardnafornita.com",
    "https://mlcasim-api.edwardnafornita.com"
]
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent.parent
SIMULATIONS_DIR = ROOT_DIR / "simulations"
if not SIMULATIONS_DIR.exists():
    SIMULATIONS_DIR = PROJECT_ROOT / "simulations"
GENERATED_DIR = SIMULATIONS_DIR / "generated_payloads"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [api] %(message)s",
)
logger = logging.getLogger("api")

REQUEST_COUNT = Counter(
    "api_requests_total", "Total API requests", ["path", "method", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds", "API request latency", ["path", "method"]
)

DOS_STORE: List[dict] = []

app = FastAPI(title="Attack API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def strip_api_prefix(request, call_next):
    path = request.scope.get("path") or request.url.path
    if path == "/api":
        request.scope["path"] = "/"
    elif path.startswith("/api/"):
        request.scope["path"] = path[4:] or "/"
    return await call_next(request)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.perf_counter() - start
        path = request.url.path
        method = request.method
        status = getattr(response, "status_code", 500)
        REQUEST_COUNT.labels(path=path, method=method, status=status).inc()
        REQUEST_LATENCY.labels(path=path, method=method).observe(duration)
        logger.info(
            "request path=%s method=%s status=%s duration_ms=%.2f",
            path,
            method,
            status,
            duration * 1000,
        )

try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        _attacks_raw = json.load(f)
    attacks: List[Attack] = [Attack.model_validate(a) for a in _attacks_raw]
except FileNotFoundError:
    attacks = []

@app.get("/")
@app.get("/api")
@app.get("/api/")
async def backend():
    return {"message": "Welcome to the backend API!"}

@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/metrics")
@app.get("/api/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/attacks", response_model=List[Attack])
@app.get("/api/attacks", response_model=List[Attack])
async def get_attacks():
    return attacks

@app.get("/metadata")
@app.get("/api/metadata")
async def get_metadata():
    return {
        "attackTypes": [t.value for t in AttackType],
        "mlModels": [m.value for m in MLModel],
    }

@app.post("/predict")
@app.post("/api/predict")
async def predict(attack: Attack):
    payload = attack.model_dump()
    result = await _post_to_ml(payload)
    return {"attack": payload, "mlResult": result}

class RunAttackRequest(BaseModel):
    attack: str = Field(..., description="Attack name, supports 'Port Probing' and 'DOS'")
    requestCount: Optional[int] = Field(
        default=100,
        description="The number of packets sent to the ML Service",
    )
    max_age_seconds: Optional[int] = Field(
        default=None,
        description="If provided, reuse the latest generated payload when it is fresher than this age.",
    )

def _rows_from_json(raw: List[dict]) -> List[ScanRow]:
    return [ScanRow.model_validate(r) for r in raw]

def _rows_from_csv(text: str) -> List[ScanRow]:
    reader = csv.DictReader(StringIO(text))
    return [ScanRow.model_validate(row) for row in reader]

def _row_to_ml_payload(row: ScanRow, prev_ts: Optional[datetime]) -> dict:
    delta = (row.timestamp - prev_ts).total_seconds() if prev_ts else 0.0
    return {
        "dst_port": row.port,
        "src_port": 0,
        "inter_arrival_time": max(delta, 0.0),
        "stream_1_count": 1,
        "l4_tcp": True,
        "l4_udp": False,
    }

async def _post_to_ml(payload: dict, ml_url: str = ML_SERVICE_URL) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(ml_url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ML service error {exc.response.status_code}: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc

async def _predict_batch(payloads: Sequence[dict], ml_url: str = ML_SERVICE_URL) -> List[dict]:
    results: List[dict] = []
    for payload in payloads:
        try:
            ml = await _post_to_ml(payload, ml_url=ml_url)
            if "model_metrics" in ml:
                # log-only: drop metrics from response, keep on server side
                print("model_metrics:", ml.get("model_metrics"))
                ml = {k: v for k, v in ml.items() if k != "model_metrics"}
            results.append({"input": payload, "ml": ml})
        except HTTPException as exc:
            results.append({"input": payload, "error": exc.detail})
    return results

async def _execute_port_probing(timeout_s: float = 200.0, param: int = 100) -> Path:
    """
    Run the port probing simulation script and return once the process finishes.
    Raises TimeoutError on timeout and RuntimeError on non-zero exit.
    """
    script = SIMULATIONS_DIR / "port_probing.py"
    if not script.exists():
        raise RuntimeError(f"Simulation script not found at {script}")

    prefix = GENERATED_DIR / "port_probe"
    cmd = [
        sys.executable,
        str(script),
        str(param),
        "--use-default-common",
        "--out-prefix",
        str(prefix),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(SIMULATIONS_DIR.parent),
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise TimeoutError("Simulation timed out") from exc

    if proc.returncode != 0:
        err = stderr.decode().strip() or stdout.decode().strip() or "unknown error"
        raise RuntimeError(f"Simulation failed: {err}")

    return GENERATED_DIR

def _load_latest_payload() -> tuple[List[dict], Path]:
    files = sorted(
        GENERATED_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        raise FileNotFoundError("No generated payloads available")
    path = files[0]
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data, path

def _latest_payload_path() -> Optional[Path]:
    files = sorted(
        GENERATED_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None

async def _execute_dos_simulation(target_url: str, count: int, timeout_s: float = 200.0) -> tuple[str, str]:
    script = SIMULATIONS_DIR / "dos.py"
    if not script.exists():
        raise RuntimeError(f"DoS simulation script not found at {script}")

    cmd = [
        sys.executable,
        str(script),
        target_url,
        str(count),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(SIMULATIONS_DIR.parent),
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise TimeoutError("DoS simulation timed out") from exc

    if proc.returncode != 0:
        err = stderr.decode().strip() or stdout.decode().strip() or "unknown error"
        raise RuntimeError(f"DoS simulation failed: {err}")

    return stdout.decode(), stderr.decode()

@app.post("/predict-from-scan-json")
@app.post("/api/predict-from-scan-json")
async def predict_from_scan_json(raw: List[dict]):
    rows = sorted(_rows_from_json(raw), key=lambda r: r.timestamp)
    payloads = []
    prev_ts = None
    for r in rows:
        payloads.append(_row_to_ml_payload(r, prev_ts))
        prev_ts = r.timestamp
    results = await _predict_batch(payloads)
    return {"count": len(results), "results": results}

@app.post("/predict-from-scan-csv")
@app.post("/api/predict-from-scan-csv")
async def predict_from_scan_csv(body: ScanCSV):
    rows = sorted(_rows_from_csv(body.csv_text), key=lambda r: r.timestamp)
    payloads = []
    prev_ts = None
    for r in rows:
        payloads.append(_row_to_ml_payload(r, prev_ts))
        prev_ts = r.timestamp
    results = await _predict_batch(payloads)
    return {"count": len(results), "results": results}

@app.post("/run-attack")
@app.post("/api/run-attack")
async def run_attack(body: RunAttackRequest):
    attack = body.attack.lower()
    request_count = int(body.requestCount or 0)
    if attack in ("port probing", "port_probing", "port-probing", "portprobing"):
        return await _run_port_probing(request_count, body.max_age_seconds)
    if attack in ("dos", "ddos", "dos attack", "denial of service"):
        return await _run_dos_attack(request_count)
    raise HTTPException(status_code=400, detail="Attack not implemented; supported: Port Probing, DOS.")

async def _run_port_probing(requestCount: int, max_age: Optional[int]) -> dict:
    requestCount = max(requestCount, 1)
    source = "generated"
    exec_error = None

    latest = _latest_payload_path()
    if max_age is not None and latest:
        age = time.time() - latest.stat().st_mtime
        if age <= max_age:
            source = "cached"
            logger.info("using cached payload (age %.1fs <= max_age %ss)", age, max_age)
        else:
            latest = None

    if source != "cached":
        try:
            await _execute_port_probing(param=requestCount)
            logger.info("port probing simulation executed successfully")
        except TimeoutError:
            source = "cached"
            exec_error = "Simulation timed out; using latest cached payload."
            logger.warning("port probing simulation timed out; using cached payload")
        except Exception as exc:
            source = "cached"
            exec_error = f"Simulation failed ({exc}); using latest cached payload."
            logger.error("port probing simulation failed: %s", exc)

    try:
        payload_data, payload_path = _load_latest_payload()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="No generated payloads available; run the simulation script to produce payloads.",
        ) from exc

    rows = sorted(_rows_from_json(payload_data), key=lambda r: r.timestamp)
    payloads = []
    prev_ts: Optional[datetime] = None
    for r in rows:
        payloads.append(_row_to_ml_payload(r, prev_ts))
        prev_ts = r.timestamp

    payloads = payloads[: max(requestCount, 1)]
    payload_data = payload_data[: len(payloads)]
    results = await _predict_batch(payloads)
    response = {
        "source": source,
        "payload_path": str(payload_path),
        "count": len(results),
        "payload": payload_data,
        "results": results,
    }
    if exec_error:
        response["note"] = exec_error
    logger.info(
        "run_attack completed source=%s payload_path=%s count=%d note=%s",
        source,
        payload_path,
        len(results),
        exec_error or "",
    )
    return response

async def _run_dos_attack(request_count: int) -> dict:
    target = DOS_TARGET_URL
    request_count = max(request_count, 1)
    payloads = [{"msg": "malicious traffic"} for _ in range(request_count)]
    DOS_STORE.clear()
    DOS_STORE.extend(payloads)

    note = ""
    try:
        stdout, stderr = await _execute_dos_simulation(target, request_count)
        logger.info("dos simulation executed successfully target=%s count=%d", target, request_count)
        if stdout.strip() or stderr.strip():
            note = (stdout.strip() + " " + stderr.strip()).strip()
    except Exception as exc:
        note = f"DoS simulation had errors: {exc}"
        logger.warning(note)

    ml_payloads = []
    for idx, _ in enumerate(DOS_STORE):
        burst_factor = 1 + (idx % 10)
        ml_payloads.append(
            {
                "Dst Port": 80,
                "Flow Packets/s": 800 + (burst_factor * 50),
                "Flow Bytes/s": 6000000 + (burst_factor * 250000),
                "Total Fwd Packet": 700 + (burst_factor * 25),
                "Flow Duration": 750000 + (burst_factor * 500),
                "Total Length of Fwd Packet": 5000000 + (burst_factor * 50000),
                "Src IP": f"10.0.0.{(idx % 240) + 1}",
                "Dst IP": "192.168.50.253",
            }
        )

    results = await _predict_batch(ml_payloads, ml_url=ML_SERVICE_DOS_URL)
    confidences = []
    for r in results:
        ml = r.get("ml") or {}
        conf = ml.get("confidence")
        if isinstance(conf, (int, float)):
            confidences.append(float(conf))
    avg_conf = sum(confidences) / len(confidences) if confidences else None

    DOS_STORE.clear()
    return {
        "source": "simulation",
        "target": target,
        "count": request_count,
        "payload": payloads,
        "results": results,
        "average_confidence": avg_conf,
        "note": note or "DoS simulation completed.",
    }

@app.post("/output-json", status_code=status.HTTP_403_FORBIDDEN)
@app.post("/api/output-json", status_code=status.HTTP_403_FORBIDDEN)
async def output_json(data: dict):
    return {
        "message": "Forbidden",
        "received": data
    }
