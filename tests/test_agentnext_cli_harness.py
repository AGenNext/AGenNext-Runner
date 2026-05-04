from pathlib import Path
import tarfile
import yaml

from agentnext_cli import cmd_init, cmd_package
from runner.harness.config_loader import load_agentnext_config
from runner.harness.scenarios import invoke_local
from runner.harness.kernel_stub import invoke_kernel_stub
from runner.frameworks.langgraph.deepagents_adapter import DeepAgentsLangGraphAdapter


class A: pass


def test_init_creates_expected_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args=A(); args.name="support-agent"; args.template="langgraph-deepagent"
    cmd_init(args)
    base = tmp_path/"support-agent"
    for f in ["agent.py","tools.py","agentnext.yaml","requirements.txt","README.md","tests/test_agent.py"]:
        assert (base/f).exists()


def test_generated_yaml_validates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args=A(); args.name="support-agent"; args.template="langgraph-deepagent"; cmd_init(args)
    cfg = yaml.safe_load((tmp_path/"support-agent"/"agentnext.yaml").read_text())
    assert cfg["agent"]["framework"] == "langgraph"


def test_invoke_builds_prevalidation_and_low_risk_allowed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args=A(); args.name="support-agent"; args.template="langgraph-deepagent"; cmd_init(args)
    proj = tmp_path/"support-agent"
    monkeypatch.chdir(proj)
    # fake agent module
    (proj/"agent.py").write_text("""\nclass G:\n    def invoke(self, payload):\n        return {'ok': True, 'payload': payload}\nagent = G()\n""")
    result = invoke_local("hello", project_dir=".")
    assert result["status"] == "success"
    assert result["envelope"]["prevalidation"]["validated_by"] == "AGenNext-Runner"


def test_requires_approval_denied_when_env_set(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args=A(); args.name="support-agent"; args.template="langgraph-deepagent"; cmd_init(args)
    proj = tmp_path/"support-agent"
    monkeypatch.chdir(proj)
    (proj/"agent.py").write_text("""\nclass G:\n    def invoke(self, payload):\n        return {'ok': True}\nagent = G()\n""")
    monkeypatch.setenv("AGENTNEXT_APPROVAL", "deny")
    result = invoke_local("hello", project_dir=".")
    assert result["status"] == "blocked"


def test_package_creates_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args=A(); args.name="support-agent"; args.template="langgraph-deepagent"; cmd_init(args)
    proj = tmp_path/"support-agent"
    monkeypatch.chdir(proj)
    cmd_package(A())
    artifact = proj/".agentnext"/"dist"/"support_agent.tar.gz"
    assert artifact.exists()
    with tarfile.open(artifact) as t:
        assert any(m.name.endswith("agentnext.yaml") for m in t.getmembers())


def test_kernel_stub_rejects_missing_prevalidation():
    out = invoke_kernel_stub({"tenant_id":"x","actor":{"id":"a"}}, project_dir=".")
    assert out["status"] == "error"


def test_adapter_invokes_fake_graph(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path/"agent.py").write_text("""\nclass G:\n    def invoke(self, payload):\n        return {'messages':[{'content':'ok'}]}\nagent = G()\n""")
    (tmp_path/"agentnext.yaml").write_text("""agent:\n  id: a1\n  framework: langgraph\n  sdk: deepagents\n  entrypoint: agent:agent\nruntime: {streaming: true}\nauthorization: {mode: managed}\nidentity: {subject_type: agent, subject_id: a1}\ntools: []\n""")
    cfg = load_agentnext_config(".")
    adapter = DeepAgentsLangGraphAdapter(".")
    out = adapter.invoke("hello", cfg)
    assert out["metadata"]["framework"] == "langgraph"
