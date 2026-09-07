"""Vercel FastAPI entrypoint: Groww homepage + chat API."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from chat_engine import reply

WEB_INDEX = ROOT / "web" / "index.html"

app = FastAPI(
    title="Groww RAG Bot",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str


@app.get("/api/health")
def health() -> dict[str, str]:
    latest = ROOT / "data" / "latest_fund_data.json"
    as_of = ""
    if latest.exists():
        try:
            payload = json.loads(latest.read_text(encoding="utf-8"))
            as_of = str(payload.get("collection_metadata", {}).get("date") or "")
        except (OSError, json.JSONDecodeError, TypeError):
            as_of = ""
    return {"status": "ok", "fund_data_as_of": as_of}


@app.post("/api/chat")
def chat(payload: ChatRequest) -> ChatResponse:
    return ChatResponse(answer=reply(payload.message))


@app.get("/")
def homepage() -> FileResponse:
    return FileResponse(WEB_INDEX, media_type="text/html")
