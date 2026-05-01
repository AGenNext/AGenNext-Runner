from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from contextlib import asynccontextmanager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("runtime-core")

# ── Configuration ───────────────────────────────────────────────────────────────────
MAX_PAYLOAD_KEYS = int(os.getenv("RUNTIME_MAX_PAYLOAD_KEYS", "256"))
RUNTIME_API_KEY = os.getenv("RUNTIME_API_KEY")
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "3600"))
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"

# ── Prometheus Metrics ───────────────────────────────────────────────────────────────────────────
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)
sessions_created_total = Counter(
    "sessions_created_total",
    "Total sessions created",
)
invokes_total = Counter(
    "invokes_total",
    "Total invoke calls",
)
idempotency_cache_hits_total = Counter(
    "idempotency_cache_hits_total",
    "Total idempotency cache hits",
)


# ── Pydantic Models ────────────────────────────────────────────────────────────────────
class RuntimeSession(BaseModel):
    session_id: str
    runtime: str
    created_at: str
    config: Dict[str, Any] = Field(default_factory=dict)
    last_accessed: Optional[str] = None


class InitRequest(BaseModel):
    runtime: str
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("runtime")
    @classmethod
    def validate_runtime(cls, v):
        if not v or len(v) < 1:
            raise ValueError("runtime must be non-empty")
        if len(v) > 64:
            raise ValueError("runtime name too long (max 64 chars)")
        return v


class InvokeRequest(BaseModel):
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if not v or len(v) < 1:
            raise ValueError("action must be non-empty")
        if len(v) > 128:
            raise ValueError("action too long (max 128 chars)")
        return v


class Event(BaseModel):
    type: str
    timestamp: str
    session_id: str
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


# ── In-Memory State ───────────────────────────────────────────────────────────
_sessions: Dict[str, RuntimeSession] = {}
_events: Dict[str, List[Event]] = {}
_idempotency_results: Dict[str, Dict[str, Any]] = {}
_idempotency_timestamps: Dict[str, float] = {}


# ── Lifecycle Management ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Graceful startup and shutdown."""
    logger.info("Starting runtime-core service...")
    yield
    logger.info("Shutting down runtime-core, cleaning up...")
    # Clean up on shutdown
    _sessions.clear()
    _events.clear()
    _idempotency_results.clear()
    logger.info("Shutdown complete")


app = FastAPI(
    title="AGenNext Runtime Core",
    version="0.2.0",
    lifespan=lifespan,
)

# ── CORS Middleware ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware for Metrics ────────────────────────────────────────────────────────────
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    
    if ENABLE_METRICS:
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)
    
    return response


# ── Helper Functions ────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_api_key(x_api_key: Optional[str]) -> None:
    if RUNTIME_API_KEY and x_api_key != RUNTIME_API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


def _cleanup_stale() -> None:
    """Remove expired idempotency cache entries."""
    current_time = time.time()
    expired_keys = [
        k for k, ts in _idempotency_timestamps.items()
        if current_time - ts > IDEMPOTENCY_TTL_SECONDS
    ]
    for k in expired_keys:
        _idempotency_results.pop(k, None)
        _idempotency_timestamps.pop(k, None)
    
    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired idempotency entries")


# ── Health & Metrics ────────────────────────────────────────────────────────────
@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "runtime-core",
        "version": app.version,
    }


@app.get("/health/ready")
def readiness() -> Dict[str, Any]:
    """Readiness check - can serve requests."""
    return {
        "status": "ready",
        "sessions": len(_sessions),
    }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    if not ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="metrics disabled")
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ── Runtime Endpoints ──────────────────────────────────────────────────
@app.post("/runtime/init", response_model=RuntimeSession)
def init_runtime(
    req: InitRequest,
    x_api_key: Optional[str] = Header(default=None),
) -> RuntimeSession:
    _validate_api_key(x_api_key)
    _cleanup_stale()
    
    sid = str(uuid4())
    now = _now()
    session = RuntimeSession(
        session_id=sid,
        runtime=req.runtime,
        created_at=now,
        config=req.config,
        last_accessed=now,
    )
    _sessions[sid] = session
    _events[sid] = [Event(
        type="runtime.init",
        timestamp=now,
        session_id=sid,
        payload={"runtime": req.runtime},
    )]
    
    sessions_created_total.inc()
    logger.info(f"Created session {sid} for runtime {req.runtime}")
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
    
    _cleanup_stale()
    
    # Idempotency check
    if x_idempotency_key and x_idempotency_key in _idempotency_results:
        idempotency_cache_hits_total.inc()
        return _idempotency_results[x_idempotency_key]
    
    result = {
        "status": "accepted",
        "session_id": session_id,
        "action": req.action,
        "correlation_id": req.correlation_id,
        "result": {"echo": req.payload},
    }
    
    now = _now()
    _events[session_id].append(Event(
        type="runtime.invoke",
        timestamp=now,
        session_id=session_id,
        correlation_id=req.correlation_id,
        payload={"action": req.action},
    ))
    
    # Update session last accessed
    _sessions[session_id].last_accessed = now
    
    if x_idempotency_key:
        _idempotency_results[x_idempotency_key] = result
        _idempotency_timestamps[x_idempotency_key] = time.time()
    
    invokes_total.inc()
    return result


@app.get("/runtime/{session_id}/stream", response_model=List[Event])
def stream(
    session_id: str,
    x_api_key: Optional[str] = Header(default=None),
) -> List[Event]:
    _validate_api_key(x_api_key)
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="session not found")
    return _events.get(session_id, [])


@app.post("/runtime/{session_id}/close")
def close(
    session_id: str,
    x_api_key: Optional[str] = Header(default=None),
) -> Dict[str, str]:
    _validate_api_key(x_api_key)
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="session not found")
    
    _events[session_id].append(Event(
        type="runtime.close",
        timestamp=_now(),
        session_id=session_id,
    ))
    
    # Clean up session data
    _sessions.pop(session_id, None)
    _events.pop(session_id, None)
    
    logger.info(f"Closed session {session_id}")
    return {"status": "closed", "session_id": session_id}
