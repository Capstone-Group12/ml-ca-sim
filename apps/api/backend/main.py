# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import os
import httpx
from models import Attack, AttackType, MLModel

app = FastAPI(title="Attack API")

# Allow your frontend origin(s) here:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # adjust for your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load static attack data from data.json (exported from TypeScript)
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        _attacks_raw = json.load(f)
    # Validate with Pydantic to ensure server enforces same constraints
    attacks: List[Attack] = [Attack.parse_obj(a) for a in _attacks_raw]
except FileNotFoundError:
    attacks = []  # fallback; you can seed programmatically if you prefer

# just a lil test
@app.get("/")
async def print_hello():
    return {"message" : "Hello World!"}

@app.get("/attacks", response_model=List[Attack])
async def get_attacks():
    """Return the list of attack definitions (validated)."""
    return attacks


@app.get("/metadata")
async def get_metadata():
    """Return attack types and ML models for frontend dropdowns."""
    return {
        "attackTypes": [t.value for t in AttackType],
        "mlModels": [m.value for m in MLModel],
    }

@app.post("/predict")
async def predict(attack: Attack):
    """
    Forward the attack data to an external ML service and return prediction.
    Example payload will be validated automatically by Pydantic (same shape as your TS schema).
    """
    # Example: ML service URL (replace with your actual ML service)
    ML_SERVICE_URL = "http://localhost:8001/predict"  # assume another service running
    payload = attack.dict()

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(ML_SERVICE_URL, json=payload)
            resp.raise_for_status()
        except httpx.RequestError as exc:
            # network error or timeout
            raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            # ML service returned 4xx/5xx
            raise HTTPException(
                status_code=502,
                detail=f"ML service returned error {exc.response.status_code}: {exc.response.text}"
            ) from exc

    # Assuming the ML service returns JSON like {"prediction": "...", "confidence": 0.98}
    try:
        result = resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="ML service returned non-JSON response")

    return {"attack": payload, "mlResult": result}
