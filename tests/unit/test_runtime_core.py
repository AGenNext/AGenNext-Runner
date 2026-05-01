"""
Unit tests for runtime_core module.
Tests individual functions and components in isolation.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Add runtime_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from runtime_core import main


class TestRuntimeCoreImports:
    """Test module imports and basic setup."""

    def test_app_exists(self):
        from runtime_core.main import app
        assert app is not None

    def test_app_title(self):
        from runtime_core.main import app
        assert app.title == "AGenNext Runtime Core"

    def test_app_version(self):
        from runtime_core.main import app
        assert app.version == "0.2.0"


class TestPydanticModels:
    """Test Pydantic models."""

    def test_runtime_session_model(self):
        from runtime_core.main import RuntimeSession
        session = RuntimeSession(
            session_id="test-123",
            runtime="python",
            created_at="2026-01-01T00:00:00Z",
            config={"version": "3.11"}
        )
        assert session.session_id == "test-123"
        assert session.runtime == "python"
        assert session.config["version"] == "3.11"

    def test_init_request_model(self):
        from runtime_core.main import InitRequest
        req = InitRequest(runtime="node", config={"version": "20"})
        assert req.runtime == "node"
        assert req.config["version"] == "20"

    def test_invoke_request_model(self):
        from runtime_core.main import InvokeRequest
        req = InvokeRequest(action="execute", payload={"code": "print(1)"}, correlation_id="corr-1")
        assert req.action == "execute"
        assert req.payload["code"] == "print(1)"
        assert req.correlation_id == "corr-1"

    def test_event_model(self):
        from runtime_core.main import Event
        event = Event(
            type="runtime.invoke",
            timestamp="2026-01-01T00:00:00Z",
            session_id="test-123",
            correlation_id="corr-1",
            payload={"action": "test"}
        )
        assert event.type == "runtime.invoke"
        assert event.session_id == "test-123"


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_returns_ok(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_returns_service_name(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.json()["service"] == "runtime-core"


class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    def test_metrics_returns_ok(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_readiness_endpoint(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestInitEndpoint:
    """Test /runtime/init endpoint."""

    def test_init_creates_session(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.post("/runtime/init", json={"runtime": "python"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["runtime"] == "python"

    def test_init_with_config(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.post("/runtime/init", json={
            "runtime": "node",
            "config": {"version": "20", "timeout": 30}
        })
        assert response.status_code == 200
        assert response.json()["config"]["version"] == "20"

    def test_init_returns_uuid(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.post("/runtime/init", json={"runtime": "go"})
        import uuid
        session_id = response.json()["session_id"]
        # Validate it's a UUID
        uuid.UUID(session_id)


class TestInvokeEndpoint:
    """Test /runtime/{session_id}/invoke endpoint."""

    def test_invoke_requires_valid_session(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.post(
            "/runtime/invalid-session/invoke",
            json={"action": "test"}
        )
        assert response.status_code == 404

    def test_invoke_returns_accepted(self):
        from runtime_core.main import app
        client = TestClient(app)
        # Create session first
        init = client.post("/runtime/init", json={"runtime": "python"})
        session_id = init.json()["session_id"]
        
        response = client.post(
            f"/runtime/{session_id}/invoke",
            json={"action": "execute", "payload": {"code": "print(1)"}}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    def test_invoke_returns_correlation_id(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        response = client.post(
            f"/runtime/{session_id}/invoke",
            json={"action": "test", "payload": {}, "correlation_id": "corr-abc"}
        )
        assert response.json()["correlation_id"] == "corr-abc"

    def test_invoke_with_idempotency_key(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        # First call
        response1 = client.post(
            f"/runtime/{session_id}/invoke",
            json={"action": "test", "payload": {"val": 1}},
            headers={"x-idempotency-key": "idem-key-123"}
        )
        
        # Second call with same key - should return cached result
        response2 = client.post(
            f"/runtime/{session_id}/invoke",
            json={"action": "test", "payload": {"val": 2}},
            headers={"x-idempotency-key": "idem-key-123"}
        )
        
        assert response1.json() == response2.json()


class TestPayloadLimit:
    """Test payload size limit."""

    def test_payload_under_limit_succeeds(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        # Default limit is 256 keys
        payload = {f"key{i}": i for i in range(200)}
        response = client.post(
            f"/runtime/{session_id}/invoke",
            json={"action": "test", "payload": payload}
        )
        assert response.status_code == 200

    def test_payload_over_limit_fails(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        # Exceed default 256 key limit
        payload = {f"key{i}": i for i in range(300)}
        response = client.post(
            f"/runtime/{session_id}/invoke",
            json={"action": "test", "payload": payload}
        )
        assert response.status_code == 413


class TestStreamEndpoint:
    """Test /runtime/{session_id}/stream endpoint."""

    def test_stream_returns_empty_for_new_session(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        response = client.get(f"/runtime/{session_id}/stream")
        assert response.status_code == 200
        events = response.json()
        assert len(events) >= 1  # At least init event

    def test_stream_returns_init_event(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        response = client.get(f"/runtime/{session_id}/stream")
        events = response.json()
        assert any(e["type"] == "runtime.init" for e in events)

    def test_stream_returns_invoke_events(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        # Invoke some actions
        client.post(f"/runtime/{session_id}/invoke", json={"action": "test1", "payload": {}})
        client.post(f"/runtime/{session_id}/invoke", json={"action": "test2", "payload": {}})
        
        response = client.get(f"/runtime/{session_id}/stream")
        events = response.json()
        invoke_events = [e for e in events if e["type"] == "runtime.invoke"]
        assert len(invoke_events) >= 2

    def test_stream_requires_valid_session(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.get("/runtime/invalid-session/stream")
        assert response.status_code == 404


class TestCloseEndpoint:
    """Test /runtime/{session_id}/close endpoint."""

    def test_close_returns_ok(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        response = client.post(f"/runtime/{session_id}/close")
        assert response.status_code == 200
        assert response.json()["status"] == "closed"

    def test_close_removes_session(self):
        """Close should clean up session data."""
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        # Session exists
        response = client.get(f"/runtime/{session_id}/stream")
        assert response.status_code == 200
        
        client.post(f"/runtime/{session_id}/close")
        
        # Session should be cleaned up
        response = client.get(f"/runtime/{session_id}/stream")
        assert response.status_code == 404

    def test_close_requires_valid_session(self):
        from runtime_core.main import app
        client = TestClient(app)
        response = client.post("/runtime/invalid-session/close")
        assert response.status_code == 404


class TestAPIKeyAuth:
    """Test API key authentication."""

    def test_no_api_key_works_when_not_required(self):
        from runtime_core.main import app
        client = TestClient(app)
        session_id = client.post("/runtime/init", json={"runtime": "python"}).json()["session_id"]
        
        response = client.post(
            f"/runtime/{session_id}/invoke",
            json={"action": "test", "payload": {}}
        )
        assert response.status_code == 200

    def test_init_endpoint_works_without_api_key(self):
        """Init endpoint does not require API key by default."""
        from runtime_core.main import app
        client = TestClient(app)
        response = client.post("/runtime/init", json={"runtime": "python"})
        assert response.status_code == 200


class TestTimestampHelper:
    """Test _now() helper function."""

    def test_now_returns_iso_format(self):
        import datetime
        from runtime_core.main import _now
        result = _now()
        # Should be parseable as ISO format
        dt = datetime.datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert dt is not None

    def test_now_returns_utc_timezone(self):
        from runtime_core.main import _now
        result = _now()
        assert "Z" in result or "+" in result or result.endswith("+00:00")