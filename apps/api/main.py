from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI()

class MessageRequest(BaseModel):
    message: str

class ResponseModel(BaseModel):
    status: str
    message: str

@app.post("/message", response_model=ResponseModel)
async def post_message(payload: MessageRequest):
    # handle frontend -> backend request; return whatever processing you need
    return ResponseModel(status="ok", message=payload.message)

@app.get("/message", response_model=ResponseModel)
async def get_message(message: str):
    # optional: simple GET retrieval via query param
    return ResponseModel(status="ok", message=message)

@app.post("/predict")
async def predict(payload: MessageRequest):
    # forward to ML service asynchronously and return its JSON
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://ml-service:8001/predict", json={"input": payload.message})
        resp.raise_for_status()
        return {"ml_result": resp.json()}

@app.get("/health")
async def health():
    return {"status": "ok"}