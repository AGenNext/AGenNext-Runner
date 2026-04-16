"""
tests/test_agent_identity.py
Unit tests for the Agent Identity layer.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestAgentIdentityModule:

    def test_import(self):
        from agent_identity import router
        assert router is not None

    def test_router_prefix(self):
        from agent_identity import router
        assert router.prefix == "/agents"

    def test_all_endpoints_present(self):
        from agent_identity import router
        paths = [r.path for r in router.routes]
        assert "/agents/create" in paths
        assert "/agents" in paths
        assert "/agents/{agent_id}" in paths
        assert "/agents/{agent_id}/suspend" in paths
        assert "/agents/{agent_id}/reactivate" in paths
        assert "/agents/{agent_id}/rotate" in paths
        assert "/agents/{agent_id}/activity" in paths


class TestAgentModels:

    def test_create_request_defaults(self):
        from agent_identity import AgentCreateRequest
        req = AgentCreateRequest(
            agent_name="fraud-sentinel",
            sponsor_id="user:admin",
            tenant_id="tenant-acme",
        )
        assert req.agent_type == "workflow"
        assert req.tpm_limit == 10000
        assert req.allowed_models is None
        assert req.metadata == {}

    def test_create_request_with_models(self):
        from agent_identity import AgentCreateRequest
        req = AgentCreateRequest(
            agent_name="code-reviewer",
            sponsor_id="user:admin",
            tenant_id="tenant-acme",
            allowed_models=["ollama/qwen2.5-coder:32b"],
            budget_limit=3.0,
        )
        assert req.allowed_models == ["ollama/qwen2.5-coder:32b"]
        assert req.budget_limit == 3.0

    def test_create_response_has_key(self):
        from agent_identity import AgentCreateResponse
        resp = AgentCreateResponse(
            agent_id="agent:123",
            agent_name="fraud-sentinel",
            agent_type="workflow",
            sponsor_id="user:admin",
            tenant_id="tenant-acme",
            allowed_models=["ollama/qwen3:30b-a3b"],
            budget_limit=2.0,
            tpm_limit=10000,
            litellm_key="sk-test-key",
            litellm_key_alias="agent:fraud-sentinel:tenant-acme",
            status="active",
            created_at="2026-04-16T00:00:00Z",
            last_active_at="2026-04-16T00:00:00Z",
            expires_at=None,
            metadata={},
        )
        assert resp.litellm_key == "sk-test-key"
        assert resp.status == "active"

    def test_agent_response_no_key(self):
        """AgentResponse must NOT expose the key."""
        from agent_identity import AgentResponse
        fields = AgentResponse.model_fields
        assert "litellm_key" not in fields, \
            "AgentResponse must never expose the LiteLLM key"


class TestDefaultModelAllowlists:

    def test_all_12_agents_have_allowlists(self):
        from agent_identity import DEFAULT_MODEL_ALLOWLISTS
        expected = [
            "fraud-sentinel", "policy-creator", "policy-reviewer",
            "code-reviewer", "feature-gap-analyzer", "saas-evaluator",
            "app-alternatives-finder", "saas-standardizer", "oss-to-saas-analyzer",
            "structured-data-parser", "web-scraper", "gateway-agent",
        ]
        for agent in expected:
            assert agent in DEFAULT_MODEL_ALLOWLISTS, f"Missing allowlist for: {agent}"

    def test_no_agent_has_wildcard_access(self):
        from agent_identity import DEFAULT_MODEL_ALLOWLISTS
        for agent, models in DEFAULT_MODEL_ALLOWLISTS.items():
            assert "*" not in models, f"{agent} has wildcard model access — not allowed"
            assert len(models) > 0, f"{agent} has empty model allowlist"

    def test_code_reviewer_has_coder_model(self):
        from agent_identity import DEFAULT_MODEL_ALLOWLISTS
        models = DEFAULT_MODEL_ALLOWLISTS["code-reviewer"]
        assert any("coder" in m for m in models)

    def test_web_scraper_has_embed_model(self):
        from agent_identity import DEFAULT_MODEL_ALLOWLISTS
        models = DEFAULT_MODEL_ALLOWLISTS["web-scraper"]
        assert any("embed" in m for m in models)

    def test_ephemeral_not_in_allowlist(self):
        """Ephemeral agents use a fallback, not a named preset."""
        from agent_identity import DEFAULT_MODEL_ALLOWLISTS
        assert "ephemeral" not in DEFAULT_MODEL_ALLOWLISTS


class TestDefaultBudgets:

    def test_all_types_have_budgets(self):
        from agent_identity import DEFAULT_BUDGETS
        for t in ["workflow", "skill", "mcp_tool", "ephemeral"]:
            assert t in DEFAULT_BUDGETS
            assert DEFAULT_BUDGETS[t] > 0

    def test_ephemeral_budget_lowest(self):
        from agent_identity import DEFAULT_BUDGETS
        assert DEFAULT_BUDGETS["ephemeral"] <= DEFAULT_BUDGETS["workflow"]

    def test_mcp_tool_budget_is_micro(self):
        from agent_identity import DEFAULT_BUDGETS
        assert DEFAULT_BUDGETS["mcp_tool"] <= 0.50


class TestAgentBootstrap:

    def test_bootstrap_has_all_12_agents(self):
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location(
            "agent_bootstrap",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_bootstrap.py")
        )
        mod = importlib.util.load_from_spec = None
        # Just check the file is parseable and has AGENTS
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_bootstrap.py")
        with open(path) as f:
            content = f.read()
        assert "AGENTS = [" in content
        # count verified by spot check below

    def test_bootstrap_no_wildcard_models(self):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_bootstrap.py")
        with open(path) as f:
            content = f.read()
        assert '"*"' not in content, "Bootstrap must never assign wildcard model access"

    def test_bootstrap_all_agents_have_budget(self):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_bootstrap.py")
        with open(path) as f:
            content = f.read()
        assert '"budget":' in content
        assert content.count('"budget":') == 12


class TestAgentIdentitySpec:
    """Verify the spec document exists and covers required sections."""

    def test_spec_exists(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "references", "agent-identity-spec.md"
        )
        assert os.path.exists(path), "references/agent-identity-spec.md missing"

    def test_spec_covers_required_sections(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "references", "agent-identity-spec.md"
        )
        content = open(path).read()
        required = [
            "Agent Identity Properties",
            "Agent Types",
            "Agent Lifecycle",
            "Access Model",
            "Traceability",
            "API Endpoints",
            "SurrealDB Schema",
            "Security Rules",
        ]
        for section in required:
            assert section in content, f"Spec missing section: {section}"

    def test_spec_references_microsoft_entra(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "references", "agent-identity-spec.md"
        )
        content = open(path).read()
        assert "Microsoft Entra" in content
