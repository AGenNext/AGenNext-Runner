import hashlib
import hmac
import time

from fastapi.testclient import TestClient
import runner_api


client = TestClient(runner_api.app)


def _mk_token(tenant: str, agent: str, ttl_seconds: int = 300, secret: str = "") -> str:
    exp = int(time.time()) + ttl_seconds
    msg = f"{tenant}:{agent}:{exp}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest() if secret else "nosig"
    return f"Bearer {tenant}:{agent}:{exp}:{sig}"


async def _ok_kernel(endpoint, payload, tenant_id):
    return {"status": "completed", "echo": payload, "tenant": tenant_id}


def test_allow_path_calls_kernel_with_prevalidation(monkeypatch):
    monkeypatch.setattr(runner_api, "invoke_kernel", _ok_kernel)
    resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {"input": "hi"}, "tenant_id": "t1"},
        headers={"Authorization": _mk_token("t1", "agent1")},
    )
    assert resp.status_code == 200
    env = resp.json()["result"]["echo"]
    assert env["prevalidation"]["identity_verified"] is True
    assert env["prevalidation"]["authorization_engines"] == ["OPA", "AuthZEN", "OpenFGA"]


def test_deny_path_does_not_call_kernel(monkeypatch):
    called = {"v": False}

    async def _never(*args, **kwargs):
        called["v"] = True
        return {}

    monkeypatch.setattr(runner_api, "invoke_kernel", _never)
    resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "tenant_id": "t1", "config": {"deny_authzen": True}},
        headers={"Authorization": _mk_token("t1", "agent1")},
    )
    assert resp.json()["status"] == "blocked"
    assert called["v"] is False


def test_missing_tenant_denied():
    resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {}},
        headers={"Authorization": _mk_token("t1", "agent1")},
    )
    assert resp.json()["status"] == "blocked"


def test_invalid_revoked_or_cross_tenant_identity_denied():
    bad_format = client.post("/api/v1/execute", json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "tenant_id": "t1"}, headers={"Authorization": "Bearer t1:agent1"})
    cross_tenant = client.post("/api/v1/execute", json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "tenant_id": "t1"}, headers={"Authorization": _mk_token("t2", "agent1")})
    expired = client.post("/api/v1/execute", json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "tenant_id": "t1"}, headers={"Authorization": _mk_token("t1", "agent1", ttl_seconds=-1)})
    assert bad_format.json()["status"] == "blocked"
    assert cross_tenant.json()["status"] == "blocked"
    assert expired.json()["status"] == "blocked"


def test_authzen_endpoint_and_opa_openfga_denies():
    eval_resp = client.post("/api/v1/authzen/evaluate", json={"tenant_id": "t1", "subject": {"id": "a"}, "resource": {"id": "r"}, "action": "execute", "context": {}})
    assert eval_resp.status_code == 200
    deny_resp = client.post(
        "/api/v1/execute",
        json={"agent_id": "agent1", "framework": "langgraph", "payload": {}, "tenant_id": "t1", "config": {"deny_openfga": True}},
        headers={"Authorization": _mk_token("t1", "agent1")},
    )
    assert deny_resp.json()["status"] == "blocked"


def test_protocol_request_maps_into_kernel_envelope(monkeypatch):
    monkeypatch.setattr(runner_api, "invoke_kernel", _ok_kernel)
    resp = client.post(
        "/api/v1/protocol/execute",
        json={"protocol": "a2a", "tenant_id": "t1", "agent_id": "agent1", "action": "sync", "payload": {"task": "x"}},
        headers={"Authorization": _mk_token("t1", "agent1")},
    )
    env = resp.json()["result"]["echo"]
    assert env["protocol"]["protocol"] == "a2a"
    assert env["payload"]["task"] == "x"
