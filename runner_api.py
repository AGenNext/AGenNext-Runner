#!/usr/bin/env python3
"""AGenNext Runner - Runtime HTTP API enforcement boundary."""

import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

import httpx
from fastapi import FastAPI, Header
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI(title="AGenNext Runner", version="1.2.0")
log = logging.getLogger("runner_api")

KERNEL_ENDPOINT = os.environ.get("KERNEL_ENDPOINT", "http://localhost:8080")
AUTHZEN_ENDPOINT = os.environ.get("AUTHZEN_ENDPOINT", "")
OPA_ENDPOINT = os.environ.get("OPA_ENDPOINT", "")
OPENFGA_ENDPOINT = os.environ.get("OPENFGA_ENDPOINT", "")
DENY_ON_POLICY_ERROR = os.environ.get("DENY_ON_POLICY_ERROR", "true").lower() == "true"
IDENTITY_SHARED_SECRET = os.environ.get("IDENTITY_SHARED_SECRET", "")
ALLOWED_PROTOCOLS = {"a2a", "acp", "agent_client_protocol", "anp", "direct"}


class ExecuteRequest(BaseModel):
    agent_id: str
    framework: str
    payload: Dict[str, Any]
    config: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None
    protocol: Optional[str] = None


class ExecuteResponse(BaseModel):
    execution_id: str
    status: Literal["completed", "blocked", "error"]
    result: Dict[str, Any] = Field(default_factory=dict)


class ProtocolRequest(BaseModel):
    protocol: str = Field(..., pattern="^(a2a|acp|agent_client_protocol|anp)$")
    tenant_id: str
    agent_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class AuthZENEvalRequest(BaseModel):
    tenant_id: str
    subject: Dict[str, Any]
    resource: Dict[str, Any]
    action: str
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentIdentityVerifier:
    @staticmethod
    def _parse_token(token: str) -> Dict[str, str]:
        # Expected token format: tenant:agent:exp:sig
        parts = token.split(":")
        if len(parts) != 4:
            return {}
        return {"tenant": parts[0], "agent": parts[1], "exp": parts[2], "sig": parts[3]}

    def verify(self, tenant_id: str, agent_id: str, authorization: Optional[str]) -> Dict[str, Any]:
        if not tenant_id or not agent_id or not authorization or not authorization.startswith("Bearer "):
            return {"allowed": False, "reason": "missing_identity"}

        parsed = self._parse_token(authorization.split(" ", 1)[1])
        if not parsed:
            return {"allowed": False, "reason": "invalid_token_format"}
        if parsed["tenant"] != tenant_id or parsed["agent"] != agent_id:
            return {"allowed": False, "reason": "cross_tenant_or_mismatch"}

        try:
            exp = int(parsed["exp"])
        except ValueError:
            return {"allowed": False, "reason": "invalid_expiry"}
        if datetime.now(timezone.utc).timestamp() > exp:
            return {"allowed": False, "reason": "expired_identity"}

        if IDENTITY_SHARED_SECRET:
            msg = f"{parsed['tenant']}:{parsed['agent']}:{parsed['exp']}".encode()
            digest = hmac.new(IDENTITY_SHARED_SECRET.encode(), msg, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(digest, parsed["sig"]):
                return {"allowed": False, "reason": "signature_mismatch"}

        actor = {
            "type": "agent",
            "id": agent_id,
            "tenant_id": tenant_id,
            "auth_method": "bearer_token",
            "verified_by": "AGenNext-Runner",
        }
        return {"allowed": True, "actor": actor}


class AuthZENAdapter:
    async def evaluate(self, tenant_id: str, subject: Dict[str, Any], resource: Dict[str, Any], action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        decision_id = str(uuid.uuid4())
        if not subject.get("id") or not resource.get("id") or not action:
            return {"engine": "AuthZEN", "allow": False, "decision_id": decision_id, "tenant_id": tenant_id, "reason": "malformed_input"}

        if AUTHZEN_ENDPOINT:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.post(AUTHZEN_ENDPOINT, json={"tenant_id": tenant_id, "subject": subject, "resource": resource, "action": action, "context": context})
                    if resp.status_code == 200:
                        body = resp.json()
                        return {"engine": "AuthZEN", "allow": bool(body.get("allow", False)), "decision_id": body.get("decision_id", decision_id), "tenant_id": tenant_id, "reason": body.get("reason", "remote")}
                    return {"engine": "AuthZEN", "allow": False, "decision_id": decision_id, "tenant_id": tenant_id, "reason": "authzen_http_error"}
            except Exception:
                return {"engine": "AuthZEN", "allow": False, "decision_id": decision_id, "tenant_id": tenant_id, "reason": "authzen_unavailable"}

        return {"engine": "AuthZEN", "allow": not context.get("deny_authzen", False), "decision_id": decision_id, "tenant_id": tenant_id, "reason": "local_stub"}


class OpenFGAAdapter:
    async def check(self, tenant_id: str, user: str, relation: str, object_: str, context: Dict[str, Any]) -> Dict[str, Any]:
        decision_id = str(uuid.uuid4())
        store_id = context.get("openfga_store_id") or os.environ.get(f"OPENFGA_STORE_ID_{tenant_id.upper()}", "")

        if OPENFGA_ENDPOINT and store_id:
            payload = {"tuple_key": {"user": user, "relation": relation, "object": object_}}
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.post(f"{OPENFGA_ENDPOINT}/stores/{store_id}/check", json=payload)
                    if resp.status_code == 200:
                        allowed = bool(resp.json().get("allowed", False))
                        return {"engine": "OpenFGA", "allow": allowed, "decision_id": decision_id, "reason": "remote_check" if allowed else "relation_denied"}
                    return {"engine": "OpenFGA", "allow": False, "decision_id": decision_id, "reason": "openfga_http_error"}
            except Exception:
                return {"engine": "OpenFGA", "allow": False, "decision_id": decision_id, "reason": "openfga_unavailable"}

        return {"engine": "OpenFGA", "allow": not context.get("deny_openfga", False), "decision_id": decision_id, "reason": "local_stub"}


class OPAAdapter:
    async def evaluate(self, policy_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        decision_id = str(uuid.uuid4())
        if not isinstance(policy_input, dict) or not policy_input:
            return {"engine": "OPA", "allow": False, "decision_id": decision_id, "bundle_version": "unknown", "reason": "malformed_input"}

        if OPA_ENDPOINT:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.post(OPA_ENDPOINT, json={"input": policy_input})
                    if resp.status_code == 200:
                        result = resp.json().get("result", {})
                        return {"engine": "OPA", "allow": bool(result.get("allow", False)), "decision_id": result.get("decision_id", decision_id), "bundle_version": result.get("bundle_version", "unknown"), "reason": result.get("reason", "remote")}
                    return {"engine": "OPA", "allow": False, "decision_id": decision_id, "bundle_version": "unknown", "reason": "opa_http_error"}
            except Exception:
                return {"engine": "OPA", "allow": not DENY_ON_POLICY_ERROR, "decision_id": decision_id, "bundle_version": "unknown", "reason": "opa_unavailable"}

        if context.get("deny_opa"):
            return {"engine": "OPA", "allow": False, "decision_id": decision_id, "bundle_version": "local-v1", "reason": "local_stub_deny"}
        return {"engine": "OPA", "allow": True, "decision_id": decision_id, "bundle_version": "local-v1", "reason": "local_stub_allow"}


class ProtocolAdapter:
    def translate(self, protocol: Optional[str], body: Dict[str, Any]) -> Dict[str, Any]:
        protocol_name = protocol or "direct"
        if protocol_name not in ALLOWED_PROTOCOLS:
            raise ValueError("unsupported_protocol")
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


async def invoke_kernel(endpoint: str, payload: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json", "X-Tenant-ID": tenant_id, "X-Execution-ID": payload.get("execution_id", "")}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(f"{KERNEL_ENDPOINT}{endpoint}", json=payload, headers=headers)
            if response.status_code >= 400:
                return {"status": "error", "error": f"kernel_http_{response.status_code}"}
            return response.json()
        except Exception as exc:
            return {"status": "error", "error": str(exc)}


async def run_enforcement(req: ExecuteRequest, tenant_hdr: Optional[str], authorization: Optional[str]) -> Dict[str, Any]:
    tenant_id = req.tenant_id or tenant_hdr
    if not tenant_id:
        return {"allowed": False, "reason": "missing_tenant"}

    identity = identity_verifier.verify(tenant_id=tenant_id, agent_id=req.agent_id, authorization=authorization)
    if not identity["allowed"]:
        return {"allowed": False, "reason": identity["reason"]}

    subject = {"type": "agent", "id": req.agent_id, "tenant_id": tenant_id}
    resource = {"type": "runtime", "id": req.framework}
    action = "execute"
    context = dict(req.config or {})

    authzen = await authzen_adapter.evaluate(tenant_id, subject, resource, action, context)
    if not authzen["allow"]:
        return {"allowed": False, "reason": authzen["reason"], "engines": [authzen]}

    openfga = await openfga_adapter.check(tenant_id, f"agent:{req.agent_id}", "can_execute", f"tool:{req.framework}", context)
    if not openfga["allow"]:
        return {"allowed": False, "reason": openfga["reason"], "engines": [authzen, openfga]}

    opa = await opa_adapter.evaluate({"tenant_id": tenant_id, "subject": subject, "resource": resource, "action": action, "context": context, "payload": req.payload}, context)
    if not opa["allow"] and DENY_ON_POLICY_ERROR:
        return {"allowed": False, "reason": opa["reason"], "engines": [authzen, openfga, opa]}

    execution_id = str(uuid.uuid4())
    protocol = protocol_adapter.translate(req.protocol, req.payload)
    envelope = {
        "tenant_id": tenant_id,
        "execution_id": execution_id,
        "actor": identity["actor"],
        "payload": req.payload,
        "protocol": protocol,
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
    log.info("enforcement_audit=%s", {"tenant_id": tenant_id, "actor": identity["actor"], "subject": subject, "resource": resource, "action": action, "context": context, "engines": [authzen["engine"], openfga["engine"], opa["engine"]], "decision_ids": [authzen["decision_id"], openfga["decision_id"], opa["decision_id"]], "allow": True, "execution_id": execution_id, "protocol": protocol["protocol"]})
    return {"allowed": True, "execution_id": execution_id, "envelope": envelope}


@app.post("/api/v1/authzen/evaluate")
async def authzen_evaluate(request: AuthZENEvalRequest):
    return await authzen_adapter.evaluate(request.tenant_id, request.subject, request.resource, request.action, request.context)


@app.post("/api/v1/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest, x_tenant_id: Optional[str] = Header(None), authorization: Optional[str] = Header(None)):
    try:
        enforcement = await run_enforcement(request, x_tenant_id, authorization)
    except ValueError as exc:
        return ExecuteResponse(execution_id=str(uuid.uuid4()), status="blocked", result={"reason": str(exc)})

    if not enforcement["allowed"]:
        return ExecuteResponse(execution_id=str(uuid.uuid4()), status="blocked", result={"reason": enforcement["reason"]})

    kernel_result = await invoke_kernel("/api/v1/execute", enforcement["envelope"], enforcement["envelope"]["tenant_id"])
    status = "completed" if kernel_result.get("status") != "error" else "error"
    return ExecuteResponse(execution_id=enforcement["execution_id"], status=status, result=kernel_result)


@app.post("/api/v1/protocol/execute", response_model=ExecuteResponse)
async def protocol_execute(request: ProtocolRequest, authorization: Optional[str] = Header(None)):
    proxy = ExecuteRequest(agent_id=request.agent_id, framework="protocol", payload={"action": request.action, **request.payload}, tenant_id=request.tenant_id, protocol=request.protocol, config={})
    return await execute(proxy, x_tenant_id=request.tenant_id, authorization=authorization)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("RUNNER_PORT", "8081")))
