from fastapi.testclient import TestClient
import runner_api

client = TestClient(runner_api.app)


def _cfg(monkeypatch):
    monkeypatch.setattr(runner_api.platform_client, "get_tenant_config", lambda t: {"id": t})
    monkeypatch.setattr(runner_api.platform_client, "get_agent_config", lambda t, a: {"id": a, "tool_allowlist": ["github.create_issue"], "rate_limits": {"max_requests_per_minute": 999}, "approval": {"required": False}})
    monkeypatch.setattr(runner_api.platform_client, "get_framework_config", lambda f: {"enabled": True})
    monkeypatch.setattr(runner_api.platform_client, "get_guardrail_bundle", lambda t: {"version": "g7"})
    monkeypatch.setattr(runner_api.platform_client, "get_memory_config", lambda t: {"provider": "surreal"})


async def _ok(path, envelope):
    return {"status": "ok", "echo": envelope}


def test_langchain_normalizes_into_kernel_envelope(monkeypatch):
    _cfg(monkeypatch)
    monkeypatch.setattr(runner_api, "kernel_post", _ok)
    r = client.post("/api/v1/run", json={"tenant_id": "t1", "agent_id": "a1", "framework": "langchain", "payload": {"tool": "github.create_issue", "x": 1}})
    assert r.status_code == 200
    env = r.json()["result"]["output"]["result"]["echo"]
    assert env["task"]["type"] == "tool_call"
    assert "signature" in env


def test_langgraph_crewai_autogen_normalize(monkeypatch):
    _cfg(monkeypatch)
    monkeypatch.setattr(runner_api, "kernel_post", _ok)
    for fw in ["langgraph", "crewai", "autogen"]:
        r = client.post("/api/v1/run", json={"tenant_id": "t1", "agent_id": "a1", "framework": fw, "payload": {"tool": "github.create_issue"}})
        assert r.json()["status"] == "completed"


def test_unsupported_framework_returns_error():
    r = client.post("/api/v1/run", json={"tenant_id": "t1", "agent_id": "a1", "framework": "unknown", "payload": {}})
    assert r.json()["status"] == "blocked"


def test_missing_platform_config_rejected(monkeypatch):
    monkeypatch.setattr(runner_api.platform_client, "get_tenant_config", lambda t: {})
    monkeypatch.setattr(runner_api.platform_client, "get_agent_config", lambda t, a: {})
    r = client.post("/api/v1/run", json={"tenant_id": "t1", "agent_id": "a1", "framework": "langchain", "payload": {}})
    assert r.json()["status"] == "blocked"


def test_policy_and_guardrail_denied_never_calls_kernel(monkeypatch):
    _cfg(monkeypatch)
    called = {"v": 0}

    async def _k(path, envelope):
        called["v"] += 1
        return {"status": "ok"}

    monkeypatch.setattr(runner_api, "kernel_post", _k)
    p = client.post("/api/v1/run", json={"tenant_id": "t1", "agent_id": "a1", "framework": "langchain", "payload": {}, "config": {"deny_policy": True}})
    g = client.post("/api/v1/run", json={"tenant_id": "t1", "agent_id": "a1", "framework": "langchain", "payload": {"tool": "not.allowed"}})
    assert p.json()["status"] == "blocked"
    assert g.json()["status"] == "blocked"
    assert called["v"] == 0


def test_kernel_error_surfaced_and_no_framework_fields_to_kernel(monkeypatch):
    _cfg(monkeypatch)

    async def _err(path, envelope):
        assert "framework" not in envelope["task"]["input"]
        return {"status": "error", "error": "boom"}

    monkeypatch.setattr(runner_api, "kernel_post", _err)
    r = client.post("/api/v1/run", json={"tenant_id": "t1", "agent_id": "a1", "framework": "langchain", "payload": {"tool": "github.create_issue", "framework": "leak"}})
    assert r.json()["status"] == "error"
