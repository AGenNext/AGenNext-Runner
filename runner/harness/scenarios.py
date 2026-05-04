from runner.harness.config_loader import load_agentnext_config, validate_config_shape
from runner.harness.identity import resolve_identity
from runner.harness.managed_authorization import evaluate_managed_authorization
from runner.harness.kernel_stub import invoke_kernel_stub
from runner.frameworks.langgraph.deepagents_adapter import DeepAgentsLangGraphAdapter
import uuid


def invoke_local(message: str, project_dir: str = ".") -> dict:
    cfg = load_agentnext_config(project_dir)
    validate_config_shape(cfg)
    ident = resolve_identity(cfg, tenant_id="local_dev")
    if not ident["ok"]:
        return {"status": "blocked", "reason": ident["reason"]}
    authz = evaluate_managed_authorization(cfg, ident["tenant_id"], ident["actor"])
    if not authz["allowed"]:
        return {"status": "blocked", "reason": authz["reason"]}

    adapter = DeepAgentsLangGraphAdapter(project_dir)
    result = adapter.invoke(message, cfg)
    envelope = {
        "tenant_id": ident["tenant_id"],
        "execution_id": str(uuid.uuid4()),
        "actor": ident["actor"],
        "payload": {"message": message},
        "framework_metadata": result.get("metadata", {}),
        "prevalidation": authz["decision"],
    }
    k = invoke_kernel_stub(envelope, project_dir=project_dir)
    return {"status": k["status"], "result": result.get("result"), "trace_id": k.get("trace_id"), "execution_id": envelope["execution_id"], "envelope": envelope} if k["status"] == "success" else {"status": "error", "reason": k.get("error")}
