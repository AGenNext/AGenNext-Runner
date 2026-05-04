from __future__ import annotations
import base64, hashlib, hmac, json, os, time, uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol


class RunnerError(Exception): ...
class UnsupportedFramework(RunnerError): ...
class UnsupportedOperation(RunnerError): ...
class AdapterNotConfigured(RunnerError): ...


@dataclass
class ValidationResult:
    valid: bool
    reason: str = ""


class FrameworkAdapter(Protocol):
    name: str
    async def validate_request(self, request: Dict[str, Any], config: Dict[str, Any]) -> ValidationResult: ...
    async def normalize(self, request: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]: ...
    async def denormalize_result(self, kernel_result: Dict[str, Any], config: Dict[str, Any]) -> Any: ...


class PlatformClient:
    """File/env backed control-plane client (replaceable with API client)."""
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.environ.get("RUNNER_PLATFORM_CONFIG", "")
        self._cfg = {}
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._cfg = json.load(f)

    def _get(self, key: str, default: Any):
        return self._cfg.get(key, default)

    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        return self._get("tenants", {}).get(tenant_id, {})

    def get_agent_config(self, tenant_id: str, agent_id: str) -> Dict[str, Any]:
        return self._get("agents", {}).get(tenant_id, {}).get(agent_id, {})

    def get_framework_config(self, framework: str) -> Dict[str, Any]:
        return self._get("frameworks", {}).get(framework, {})

    def get_policy_bundle(self, tenant_id: str) -> Dict[str, Any]:
        return self._get("policies", {}).get(tenant_id, {"version": "dev-local"})

    def get_guardrail_bundle(self, tenant_id: str) -> Dict[str, Any]:
        return self._get("guardrails", {}).get(tenant_id, {"version": "dev-local"})

    def get_tool_allowlist(self, tenant_id: str, agent_id: str) -> List[str]:
        agent = self.get_agent_config(tenant_id, agent_id)
        return agent.get("tool_allowlist", [])

    def get_memory_config(self, tenant_id: str) -> Dict[str, Any]:
        return self._get("memory", {}).get(tenant_id, {})

    def get_rate_limits(self, tenant_id: str, agent_id: str) -> Dict[str, int]:
        agent = self.get_agent_config(tenant_id, agent_id)
        return agent.get("rate_limits", {"max_requests_per_minute": 60})

    def get_approval_requirements(self, tenant_id: str, agent_id: str) -> Dict[str, Any]:
        agent = self.get_agent_config(tenant_id, agent_id)
        return agent.get("approval", {"required": False})


class SimpleRateLimiter:
    def __init__(self):
        self.state: Dict[str, List[float]] = {}

    def allow(self, key: str, max_requests_per_minute: int) -> bool:
        now = time.time()
        bucket = [t for t in self.state.get(key, []) if now - t < 60]
        if len(bucket) >= max_requests_per_minute:
            self.state[key] = bucket
            return False
        bucket.append(now)
        self.state[key] = bucket
        return True


class GuardrailEngine:
    def check_input(self, payload: Dict[str, Any], allow_tools: List[str]) -> ValidationResult:
        text = json.dumps(payload).lower()
        if "ignore previous instructions" in text:
            return ValidationResult(False, "prompt_injection_detected")
        tool = payload.get("tool")
        if tool and allow_tools and tool not in allow_tools:
            return ValidationResult(False, "tool_not_allowed")
        return ValidationResult(True)

    def check_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "secret" in json.dumps(result).lower():
            return {"blocked": True, "reason": "sensitive_output_detected"}
        return {"blocked": False}


class PolicyEngine:
    def evaluate(self, req: Dict[str, Any], prod_mode: bool) -> Dict[str, Any]:
        if req.get("config", {}).get("deny_policy"):
            return {"allowed": False, "version": "local", "reason": "policy_denied"}
        if req.get("config", {}).get("simulate_policy_backend_failure") and prod_mode:
            return {"allowed": False, "version": "unknown", "reason": "policy_backend_unavailable"}
        return {"allowed": True, "version": "local", "reason": "allowed"}


class EnvelopeSigner:
    def __init__(self, secret: str):
        self.secret = secret.encode()

    def sign(self, envelope: Dict[str, Any]) -> str:
        body = json.dumps(envelope, sort_keys=True).encode()
        return base64.b64encode(hmac.new(self.secret, body, hashlib.sha256).digest()).decode()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_execution_id() -> str:
    return str(uuid.uuid4())
