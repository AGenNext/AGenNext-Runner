#!/usr/bin/env python3
import os
from typing import Any, Dict, Optional
import httpx
from fastapi import FastAPI, Header
from pydantic import BaseModel, Field

from runner.adapters import get_adapter, list_frameworks
from runner.core import (
    EnvelopeSigner,
    GuardrailEngine,
    PlatformClient,
    PolicyEngine,
    RunnerError,
    SimpleRateLimiter,
    new_execution_id,
    now_iso,
)

app = FastAPI(title="AGenNext Runner", version="2.0.0")

KERNEL_ENDPOINT = os.environ.get("KERNEL_ENDPOINT", "http://localhost:8080")
RUNNER_ID = os.environ.get("RUNNER_ID", "runner_default")
RUNNER_SIGNING_SECRET = os.environ.get("RUNNER_SIGNING_SECRET", "dev-runner-secret")
PROD_MODE = os.environ.get("RUNNER_ENV", "dev") == "prod"

platform_client = PlatformClient()
policy_engine = PolicyEngine()
guardrails = GuardrailEngine()
signer = EnvelopeSigner(RUNNER_SIGNING_SECRET)
limiter = SimpleRateLimiter()


class RunRequest(BaseModel):
    tenant_id: str
    agent_id: str
    framework: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    stream: bool = False
    config: Dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    execution_id: str
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)


async def kernel_post(path: str, envelope: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(f"{KERNEL_ENDPOINT}{path}", json=envelope, headers={"X-Tenant-ID": envelope["tenant_id"], "X-Execution-ID": envelope["execution_id"]})
            if r.status_code >= 400:
                return {"status": "error", "error": f"kernel_http_{r.status_code}"}
            return r.json()
        except Exception as exc:
            return {"status": "error", "error": str(exc)}


async def run_pipeline(req: RunRequest) -> Dict[str, Any]:
    execution_id = new_execution_id()
    tenant_cfg = platform_client.get_tenant_config(req.tenant_id)
    agent_cfg = platform_client.get_agent_config(req.tenant_id, req.agent_id)
    framework_cfg = platform_client.get_framework_config(req.framework)
    if not tenant_cfg or not agent_cfg:
        return {"blocked": True, "reason": "missing_platform_config", "execution_id": execution_id}

    limits = platform_client.get_rate_limits(req.tenant_id, req.agent_id)
    if not limiter.allow(f"{req.tenant_id}:{req.agent_id}", limits.get("max_requests_per_minute", 60)):
        return {"blocked": True, "reason": "rate_limit_exceeded", "execution_id": execution_id}

    approval = platform_client.get_approval_requirements(req.tenant_id, req.agent_id)
    if approval.get("required") and req.config.get("approval_state") != "APPROVED":
        return {"blocked": True, "reason": "PENDING_APPROVAL", "execution_id": execution_id}

    policy = policy_engine.evaluate(req.model_dump(), prod_mode=PROD_MODE)
    if not policy["allowed"]:
        return {"blocked": True, "reason": policy["reason"], "execution_id": execution_id}

    tools = platform_client.get_tool_allowlist(req.tenant_id, req.agent_id)
    input_guard = guardrails.check_input(req.payload, tools)
    if not input_guard.valid:
        return {"blocked": True, "reason": input_guard.reason, "execution_id": execution_id}

    adapter = get_adapter(req.framework)
    v = await adapter.validate_request(req.model_dump(), framework_cfg)
    if not v.valid:
        return {"blocked": True, "reason": v.reason, "execution_id": execution_id}
    task = await adapter.normalize(req.model_dump(), framework_cfg)

    envelope = {
        "tenant_id": req.tenant_id,
        "execution_id": execution_id,
        "agent_id": req.agent_id,
        "runner_id": RUNNER_ID,
        "task": task,
        "policy_verdict": {
            "allowed": True,
            "policy_version": policy["version"],
            "checked_by": "runner",
            "checked_at": now_iso(),
            "evidence": {"reason": policy["reason"]},
        },
        "guardrail_verdict": {
            "input_allowed": True,
            "output_required": True,
            "guardrail_version": platform_client.get_guardrail_bundle(req.tenant_id).get("version", "dev-local"),
            "evidence": {},
        },
        "trace_context": {"framework": req.framework},
        "memory_context": platform_client.get_memory_config(req.tenant_id),
    }
    envelope["signature"] = signer.sign(envelope)
    return {"blocked": False, "envelope": envelope, "adapter": adapter, "execution_id": execution_id}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "runner"}


@app.get("/api/v1/frameworks")
async def frameworks():
    return {"frameworks": list_frameworks()}


@app.post("/api/v1/frameworks/{framework}/run", response_model=RunResponse)
async def framework_run(framework: str, request: RunRequest):
    request.framework = framework
    return await run(request)


@app.post("/api/v1/run", response_model=RunResponse)
async def run(request: RunRequest):
    try:
        p = await run_pipeline(request)
    except RunnerError as exc:
        return RunResponse(execution_id=new_execution_id(), status="blocked", result={"reason": str(exc)})
    if p["blocked"]:
        return RunResponse(execution_id=p["execution_id"], status="blocked", result={"reason": p["reason"]})

    kernel = await kernel_post("/api/v1/execute/stream" if request.stream else "/api/v1/execute", p["envelope"])
    if kernel.get("status") == "error":
        return RunResponse(execution_id=p["execution_id"], status="error", result=kernel)

    out_guard = guardrails.check_output(kernel)
    if out_guard["blocked"]:
        return RunResponse(execution_id=p["execution_id"], status="blocked", result={"reason": out_guard["reason"]})

    output = await p["adapter"].denormalize_result(kernel, platform_client.get_framework_config(request.framework))
    return RunResponse(execution_id=p["execution_id"], status="completed", result={"output": output})


@app.post("/api/v1/run/stream", response_model=RunResponse)
async def run_stream(request: RunRequest):
    request.stream = True
    return await run(request)
