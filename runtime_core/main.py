from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

MAX_PAYLOAD_KEYS = int(os.getenv("RUNTIME_MAX_PAYLOAD_KEYS", "256"))
RUNTIME_API_KEY = os.getenv("RUNTIME_API_KEY")


class RuntimeSession(BaseModel):
    session_id: str
    runtime: str
    created_at: str
    config: Dict[str, Any] = Field(default_factory=dict)


class InitRequest(BaseModel):
    runtime: str
    config: Dict[str, Any] = Field(default_factory=dict)


class InvokeRequest(BaseModel):
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None


class Event(BaseModel):
    type: str
    timestamp: str
    session_id: str
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="AGenNext Runtime Core", version="0.2.0")
_sessions: Dict[str, RuntimeSession] = {}
_events: Dict[str, List[Event]] = {}
_idempotency_results: Dict[str, Dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_api_key(x_api_key: Optional[str]) -> None:
    if RUNTIME_API_KEY and x_api_key != RUNTIME_API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "runtime-core"}


@app.get("/metrics")
def metrics() -> Dict[str, int]:
    return {
        "sessions": len(_sessions),
        "events": sum(len(v) for v in _events.values()),
        "idempotency_cache": len(_idempotency_results),
    }


@app.post("/runtime/init", response_model=RuntimeSession)
def init_runtime(req: InitRequest, x_api_key: Optional[str] = Header(default=None)) -> RuntimeSession:
    _validate_api_key(x_api_key)
    sid = str(uuid4())
    session = RuntimeSession(session_id=sid, runtime=req.runtime, created_at=_now(), config=req.config)
    _sessions[sid] = session
    _events[sid] = [Event(type="runtime.init", timestamp=_now(), session_id=sid, payload={"runtime": req.runtime})]
    return session


@app.post("/runtime/{session_id}/invoke")
def invoke(
    session_id: str,
    req: InvokeRequest,
    x_api_key: Optional[str] = Header(default=None),
    x_idempotency_key: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    _validate_api_key(x_api_key)
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="session not found")
    if len(req.payload.keys()) > MAX_PAYLOAD_KEYS:
        raise HTTPException(status_code=413, detail="payload too large")

    if x_idempotency_key and x_idempotency_key in _idempotency_results:
        return _idempotency_results[x_idempotency_key]

    result = {
        "status": "accepted",
        "session_id": session_id,
        "action": req.action,
        "correlation_id": req.correlation_id,
        "result": {"echo": req.payload},
    }
    _events[session_id].append(
        Event(
            type="runtime.invoke",
            timestamp=_now(),
            session_id=session_id,
            correlation_id=req.correlation_id,
            payload={"action": req.action},
        )
    )
    if x_idempotency_key:
        _idempotency_results[x_idempotency_key] = result
    return result


@app.get("/runtime/{session_id}/stream", response_model=List[Event])
def stream(session_id: str, x_api_key: Optional[str] = Header(default=None)) -> List[Event]:
    _validate_api_key(x_api_key)
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="session not found")
    return _events.get(session_id, [])


@app.post("/runtime/{session_id}/close")
def close(session_id: str, x_api_key: Optional[str] = Header(default=None)) -> Dict[str, str]:
    _validate_api_key(x_api_key)
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="session not found")
    _events[session_id].append(Event(type="runtime.close", timestamp=_now(), session_id=session_id))
    return {"status": "closed", "session_id": session_id}
