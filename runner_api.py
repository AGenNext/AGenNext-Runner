#!/usr/bin/env python3
"""
AGenNext Runner - Runtime HTTP API
All adapters for policy, guardrails, framework, memory, tools, traces
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="AGenNext Runner", version="1.0.0")

# --- Configuration ---
KERNEL_ENDPOINT = os.environ.get("KERNEL_ENDPOINT", "http://localhost:8080")
PLATFORM_CONFIG_PATH = os.environ.get("PLATFORM_CONFIG_PATH", "/data/config")

# --- Models ---
class ExecuteRequest(BaseModel):
    agent_id: str
    framework: str  # langgraph, crewai, autogen, etc.
    payload: Dict[str, Any]
    config: Optional[Dict[str, Any]] = {}
    tenant_id: Optional[str] = None

class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None

# --- Adapters ---
class PolicyAdapter:
    """OPA policy loading and enforcement."""
    
    def __init__(self):
        self.policies = {}
        self._load_policies()
    
    def _load_policies(self):
        """Load policies from config."""
        # Load from rego files
        rego_path = os.path.join(os.path.dirname(__file__), "opa", "policy.rego")
        if os.path.exists(rego_path):
            with open(rego_path) as f:
                self.policies["default"] = f.read()
    
    def enforce(self, tenant_id: str, action: Dict) -> Dict:
        """Enforce OPA policies before execution."""
        # Simplified: check against loaded policies
        # Real impl would use opa-python library
        return {"allowed": True, "reason": "allowed"}
    
    async def enforce_async(self, tenant_id: str, action: Dict) -> Dict:
        """Async policy enforcement."""
        return self.enforce(tenant_id, action)

class GuardrailAdapter:
    """Input/output filtering."""
    
    def filter_input(self, content: str) -> str:
        """Filter sensitive content from input."""
        # Simple placeholder - real impl would use regex/categories
        return content
    
    def filter_output(self, content: str) -> str:
        """Filter sensitive content from output."""
        return content

class FrameworkAdapter:
    """Framework translation to Kernel payload."""
    
    def translate(self, framework: str, payload: Dict, config: Dict) -> Dict:
        """Translate framework input to Kernel execution."""
        if framework == "langgraph":
            return self._translate_langgraph(payload, config)
        elif framework == "crewai":
            return self._translate_crewai(payload, config)
        elif framework == "autogen":
            return self._translate_autogen(payload, config)
        else:
            return payload
    
    def _translate_langgraph(self, payload: Dict, config: Dict) -> Dict:
        return {"agent_id": payload.get("agent_id"), "framework": "langgraph", "graph": payload}
    
    def _translate_crewai(self, payload: Dict, config: Dict) -> Dict:
        return {"agent_id": payload.get("agent_id"), "framework": "crewai", "crew": payload}
    
    def _translate_autogen(self, payload: Dict, config: Dict) -> Dict:
        return {"agent_id": payload.get("agent_id"), "framework": "autogen", "agents": payload}

class MemoryAdapter:
    """Memory persistence configuration."""
    
    def get_config(self, tenant_id: str) -> Dict:
        """Get memory config for tenant."""
        return {"provider": "surrealdb", "tenant_id": tenant_id}

class TraceAdapter:
    """Observability tracing."""
    
    def trace(self, event: Dict):
        """Record trace event."""
        # Would send to Langfuse/Jaeger
        pass

# Initialize adapters
policy_adapter = PolicyAdapter()
guardrail_adapter = GuardrailAdapter()
framework_adapter = FrameworkAdapter()
memory_adapter = MemoryAdapter()
trace_adapter = TraceAdapter()

# --- Helpers ---
async def invoke_kernel(endpoint: str, payload: Dict, tenant_id: str) -> Dict:
    """Invoke Kernel with pre-validated payload."""
    import urllib.request
    import urllib.parse
    
    url = f"{KERNEL_ENDPOINT}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenant_id
    }
    
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read())
    except Exception as e:
        return {"error": str(e)}

# --- Routes ---
@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "adapters": "loaded"}

@app.post("/api/v1/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest, x_tenant_id: str = Header(None)):
    """
    Execute agent with all adapters enforcing first.
    
    Flow:
    1. Platform defines config
    2. Runner enforces (policy, guardrails)
    3. Runner translates framework
    4. Runner invokes Kernel
    """
    tenant_id = request.tenant_id or x_tenant_id or "default"
    execution_id = str(uuid.uuid4())
    
    # 1. Policy enforcement
    policy_result = await policy_adapter.enforce_async(tenant_id, request.payload)
    if not policy_result.get("allowed"):
        return ExecuteResponse(
            execution_id=execution_id,
            status="blocked",
            result={"reason": policy_result.get("reason")}
        )
    
    # 2. Guardrails
    filtered_payload = {
        **request.payload,
        "input": guardrail_adapter.filter_input(request.payload.get("input", ""))
    }
    
    # 3. Framework translation
    kernel_payload = framework_adapter.translate(
        request.framework,
        filtered_payload,
        request.config or {}
    )
    kernel_payload["execution_id"] = execution_id
    kernel_payload["tenant_id"] = tenant_id
    
    # 4. Invoke Kernel
    result = await invoke_kernel("/api/v1/execute", kernel_payload, tenant_id)
    
    # 5. Guard output
    if result.get("result"):
        result["result"] = guardrail_adapter.filter_output(str(result["result"]))
    
    # 6. Trace
    trace_adapter.trace({
        "execution_id": execution_id,
        "tenant_id": tenant_id,
        "framework": request.framework,
        "status": "completed" if result.get("status") != "error" else "failed"
    })
    
    return ExecuteResponse(
        execution_id=execution_id,
        status=result.get("status", "completed"),
        result=result
    )

@app.get("/api/v1/config/{tenant_id}")
async def get_config(tenant_id: str):
    """Get Runner config for tenant."""
    return {
        "tenant_id": tenant_id,
        "memory": memory_adapter.get_config(tenant_id),
        "kernel_endpoint": KERNEL_ENDPOINT
    }

if __name__ == "__main__":
    port = int(os.environ.get("RUNNER_PORT", "8081"))
    uvicorn.run(app, host="0.0.0.0", port=port)