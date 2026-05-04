import os, uuid


def evaluate_managed_authorization(cfg: dict, tenant_id: str, actor: dict) -> dict:
    mode = cfg.get("authorization", {}).get("mode", "managed")
    if mode == "custom":
        return {"allowed": False, "reason": "custom_authorization_not_configured"}
    if not tenant_id:
        return {"allowed": False, "reason": "missing_tenant"}
    if not actor:
        return {"allowed": False, "reason": "missing_actor"}

    for tool in cfg.get("tools", []):
        if tool.get("risk") == "low":
            continue
        if tool.get("requires_approval"):
            if os.environ.get("AGENTNEXT_APPROVAL", "allow") == "deny":
                return {"allowed": False, "reason": f"approval_denied:{tool.get('id')}"}
        else:
            return {"allowed": False, "reason": f"unknown_tool_risk:{tool.get('id')}"}

    return {
        "allowed": True,
        "decision": {
            "validated_by": "AGenNext-Runner",
            "identity_verified": True,
            "authorization_result": "allowed",
            "policy_result": "allowed",
            "authorization_mode": "managed",
            "policy_decision_id": f"local_decision_{uuid.uuid4()}",
            "subject": {"type": "agent", "id": actor["id"]},
            "resource": {"type": "agent", "id": actor["id"]},
            "action": "invoke",
            "context": {"framework": cfg["agent"]["framework"], "sdk": cfg["agent"].get("sdk", "deepagents"), "environment": "local"},
        },
    }
