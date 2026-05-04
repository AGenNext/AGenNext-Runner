# API

## POST /v1/decisions

Evaluate one action intent.

### Request

```json
{
  "tenant_id": "acme",
  "actor": {"type": "agent", "id": "agent-support-1"},
  "action": "tool.call",
  "resource": {"type": "http", "id": "readonly-crm"},
  "context": {"method": "GET", "path": "/customers"}
}
```

### Response

```json
{
  "decision": "allow",
  "policy_id": "http-readonly",
  "reason": "resource allowed for role",
  "decision_id": "dec_01J..."
}
```
