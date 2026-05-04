def resolve_identity(cfg: dict, tenant_id: str = "local_dev") -> dict:
    aid = cfg.get("agent", {}).get("id")
    if not tenant_id:
        return {"ok": False, "reason": "missing_tenant"}
    if not aid:
        return {"ok": False, "reason": "missing_actor"}
    return {
        "ok": True,
        "tenant_id": tenant_id,
        "actor": {"type": "agent", "id": aid, "tenant_id": tenant_id, "verified_by": "AGenNext-Runner"},
    }
