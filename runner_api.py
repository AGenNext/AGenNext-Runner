#!/usr/bin/env python3
"""AGenNext Runner - Runtime HTTP API enforcement boundary."""

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import urllib.request
from fastapi import FastAPI, Header
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI(title="AGenNext Runner", version="1.1.0")
log = logging.getLogger("runner_api")

KERNEL_ENDPOINT = os.environ.get("KERNEL_ENDPOINT", "http://localhost:8080")
DENY_ON_POLICY_ERROR = os.environ.get("DENY_ON_POLICY_ERROR", "true").lower() == "true"


class ExecuteRequest(BaseModel):
    agent_id: str
    framework: str
    payload: Dict[str, Any]
    config: Optional[Dict[str, Any]] = {}
    tenant_id: Optional[str] = None
    protocol: Optional[str] = None


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None


class ProtocolRequest(BaseModel):
    protocol: str = Field(..., pattern="^(a2a|acp|agent_client_protocol|anp)$")
    tenant_id: str
    agent_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class IdentityResult:
    allowed: bool
    actor: Optional[Dict[str, Any]] = None
    reason: str = ""


class AgentIdentityVerifier:
    def verify(self, tenant_id: str, agent_id: str, authorization: Optional[str]) -> IdentityResult:
        if not tenant_id or not agent_id or not authorization or not authorization.startswith("Bearer "):
            return IdentityResult(False, reason="missing_identity")
        token = authorization.split(" ", 1)[1]
        if token in {"revoked", "expired", "disabled"}:
            return IdentityResult(False, reason="identity_not_active")
        parts = token.split(":")
        if len(parts) < 2 or parts[0] != tenant_id or parts[1] != agent_id:
            return IdentityResult(False, reason="cross_tenant_or_mismatch")
        return IdentityResult(True, actor={"type": "agent", "id": agent_id, "tenant_id": tenant_id, "auth_method": "bearer_token", "verified_by": "AGenNext-Runner"})


class AuthZENAdapter:
    def evaluate(self, tenant_id: str, subject: Dict[str, Any], resource: Dict[str, Any], action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        decision_id = str(uuid.uuid4())
        malformed = not subject.get("id") or not resource.get("id") or not action
        if malformed:
            return {"engine": "AuthZEN", "allow": False, "decision_id": decision_id, "tenant_id": tenant_id, "reason": "malformed_input"}
        denied = context.get("deny_authzen") is True
        return {"engine": "AuthZEN", "allow": not denied, "decision_id": decision_id, "tenant_id": tenant_id, "reason": "explicit_deny" if denied else "allowed"}


class OpenFGAAdapter:
    async def check(self, tenant_id: str, user: str, relation: str, object_: str, context: Dict[str, Any]) -> Dict[str, Any]:
        decision_id = str(uuid.uuid4())
        if context.get("openfga_unavailable"):
            return {"engine": "OpenFGA", "allow": False, "decision_id": decision_id, "reason": "openfga_unavailable"}
        if context.get("deny_openfga"):
            return {"engine": "OpenFGA", "allow": False, "decision_id": decision_id, "reason": "relation_denied"}
        return {"engine": "OpenFGA", "allow": True, "decision_id": decision_id, "check": {"user": user, "relation": relation, "object": object_}}


class OPAAdapter:
    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        decision_id = str(uuid.uuid4())
        malformed = "input" not in payload
        if malformed:
            return {"engine": "OPA", "allow": False, "decision_id": decision_id, "bundle_version": "unknown", "reason": "malformed_input"}
        if payload.get("input", {}).get("deny_opa"):
            return {"engine": "OPA", "allow": False, "decision_id": decision_id, "bundle_version": "v1", "reason": "policy_denied"}
        return {"engine": "OPA", "allow": True, "decision_id": decision_id, "bundle_version": "v1", "reason": "allowed"}


class ProtocolAdapter:
    def translate(self, protocol: Optional[str], body: Dict[str, Any]) -> Dict[str, Any]:
        protocol_name = protocol or "direct"
        return {
            "protocol": protocol_name,
            "sync_supported": True,
            "async_supported": True,
            "streaming_supported": protocol_name in {"a2a", "acp"},
            "cancel_supported": protocol_name in {"a2a", "anp"},
            "manifest_validated": True,
            "translated_payload": body,
        }


identity_verifier = AgentIdentityVerifier()
authzen_adapter = AuthZENAdapter()
openfga_adapter = OpenFGAAdapter()
opa_adapter = OPAAdapter()
protocol_adapter = ProtocolAdapter()


async def invoke_kernel(endpoint: str, payload: Dict, tenant_id: str) -> Dict:
    url = f"{KERNEL_ENDPOINT}{endpoint}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "X-Tenant-ID": tenant_id}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


async def run_enforcement(req: ExecuteRequest, tenant_hdr: Optional[str], authorization: Optional[str]) -> Dict[str, Any]:
    tenant_id = req.tenant_id or tenant_hdr
    if not tenant_id:
        return {"allowed": False, "reason": "missing_tenant"}

    identity = identity_verifier.verify(tenant_id=tenant_id, agent_id=req.agent_id, authorization=authorization)
    if not identity.allowed:
        return {"allowed": False, "reason": identity.reason}

    subject = {"type": "agent", "id": req.agent_id, "tenant_id": tenant_id}
    resource = {"type": "runtime", "id": req.framework}
    action = "execute"
    context = dict(req.config or {})

    authzen = authzen_adapter.evaluate(tenant_id, subject, resource, action, context)
    if not authzen["allow"]:
        return {"allowed": False, "reason": authzen["reason"], "decisions": [authzen]}

    openfga = await openfga_adapter.check(tenant_id, f"agent:{req.agent_id}", "can_execute", f"tool:{req.framework}", context)
    if not openfga["allow"]:
        return {"allowed": False, "reason": openfga["reason"], "decisions": [authzen, openfga]}

    opa = opa_adapter.evaluate({"input": {**req.payload, **context}})
    if not opa["allow"] and DENY_ON_POLICY_ERROR:
        return {"allowed": False, "reason": opa["reason"], "decisions": [authzen, openfga, opa]}

    execution_id = str(uuid.uuid4())
    proto_meta = protocol_adapter.translate(req.protocol, req.payload)
    envelope = {
        "tenant_id": tenant_id,
        "execution_id": execution_id,
        "actor": identity.actor,
        "payload": req.payload,
        "protocol": proto_meta,
        "prevalidation": {
            "validated_by": "AGenNext-Runner",
            "identity_verified": True,
            "authorization_result": "allowed",
            "policy_result": "allowed",
            "policy_decision_id": opa["decision_id"],
            "authorization_engines": ["OPA", "AuthZEN", "OpenFGA"],
            "policy_bundle_version": opa.get("bundle_version", "unknown"),
            "subject": subject,
            "resource": resource,
            "action": action,
            "context": context,
        },
    }
    audit = {"tenant_id": tenant_id, "actor": identity.actor, "engines": [authzen, openfga, opa], "result": "allowed", "execution_id": execution_id, "ts": datetime.now(timezone.utc).isoformat(), "protocol": proto_meta.get("protocol")}
    log.info("enforcement_audit=%s", audit)
    return {"allowed": True, "envelope": envelope, "execution_id": execution_id}


@app.post("/api/v1/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest, x_tenant_id: Optional[str] = Header(None), authorization: Optional[str] = Header(None)):
    check = await run_enforcement(request, x_tenant_id, authorization)
    if not check["allowed"]:
        return ExecuteResponse(execution_id=str(uuid.uuid4()), status="blocked", result={"reason": check["reason"]})
    kernel_result = await invoke_kernel("/api/v1/execute", check["envelope"], check["envelope"]["tenant_id"])
    return ExecuteResponse(execution_id=check["execution_id"], status=kernel_result.get("status", "completed"), result=kernel_result)


@app.post("/api/v1/protocol/execute", response_model=ExecuteResponse)
async def protocol_execute(request: ProtocolRequest, authorization: Optional[str] = Header(None)):
    exec_req = ExecuteRequest(agent_id=request.agent_id, framework="protocol", payload={"action": request.action, **request.payload}, config={}, tenant_id=request.tenant_id, protocol=request.protocol)
    return await execute(exec_req, x_tenant_id=request.tenant_id, authorization=authorization)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("RUNNER_PORT", "8081")))
