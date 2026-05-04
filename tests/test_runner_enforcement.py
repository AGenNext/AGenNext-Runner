from fastapi.testclient import TestClient
import runner_api


client = TestClient(runner_api.app)


async def _ok_kernel(endpoint, payload, tenant_id):
    return {"status": "completed", "echo": payload, "tenant": tenant_id}


def test_allow_path_calls_kernel_with_prevalidation(monkeypatch):
    monkeypatch.setattr(runner_api, "invoke_kernel", _ok_kernel)
    resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {"input": "hi"}, "tenant_id": "t1", "config": {}},
        headers={"Authorization": "Bearer t1:agent1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    env = body["result"]["echo"]
    assert env["prevalidation"]["identity_verified"] is True
    assert env["tenant_id"] == "t1"


def test_deny_path_does_not_call_kernel(monkeypatch):
    called = {"v": False}

    async def _never(*args, **kwargs):
        called["v"] = True
        return {}

    monkeypatch.setattr(runner_api, "invoke_kernel", _never)
    resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "tenant_id": "t1", "config": {"deny_authzen": True}},
        headers={"Authorization": "Bearer t1:agent1"},
    )
    assert resp.json()["status"] == "blocked"
    assert called["v"] is False


def test_missing_tenant_denied():
    resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "config": {}},
        headers={"Authorization": "Bearer t1:agent1"},
    )
    assert resp.json()["status"] == "blocked"


def test_invalid_identity_denied():
    resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "tenant_id": "t1", "config": {}},
        headers={"Authorization": "Bearer t2:agent1"},
    )
    assert resp.json()["status"] == "blocked"


def test_authzen_openfga_opa_allow_deny():
    assert runner_api.authzen_adapter.evaluate("t1", {"id": "a"}, {"id": "r"}, "execute", {}).get("allow") is True
    assert runner_api.authzen_adapter.evaluate("t1", {"id": "a"}, {"id": "r"}, "execute", {"deny_authzen": True}).get("allow") is False


def test_protocol_request_maps_into_envelope(monkeypatch):
    monkeypatch.setattr(runner_api, "invoke_kernel", _ok_kernel)
    resp = client.post(
        "/api/v1/protocol/execute",
        json={"protocol": "a2a", "tenant_id": "t1", "agent_id": "agent1", "action": "sync", "payload": {"task": "x"}},
        headers={"Authorization": "Bearer t1:agent1"},
    )
    env = resp.json()["result"]["echo"]
    assert env["protocol"]["protocol"] == "a2a"
    assert env["payload"]["task"] == "x"
