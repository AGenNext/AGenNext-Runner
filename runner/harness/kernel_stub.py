from pathlib import Path
import json, uuid


def invoke_kernel_stub(envelope: dict, project_dir: str = ".") -> dict:
    if not envelope.get("tenant_id"):
        return {"status": "error", "error": "missing_tenant"}
    pv = envelope.get("prevalidation", {})
    if pv.get("validated_by") != "AGenNext-Runner":
        return {"status": "error", "error": "invalid_prevalidation"}
    if pv.get("authorization_result") != "allowed" and pv.get("policy_result") != "allowed":
        return {"status": "error", "error": "authorization_not_allowed"}
    if not envelope.get("actor"):
        return {"status": "error", "error": "missing_actor"}

    trace_id = f"trace_local_{uuid.uuid4()}"
    trace_dir = Path(project_dir) / ".agentnext" / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / f"{trace_id}.json").write_text(json.dumps(envelope, indent=2))
    return {"status": "success", "execution_id": envelope.get("execution_id"), "tenant_id": envelope.get("tenant_id"), "trace_id": trace_id}
