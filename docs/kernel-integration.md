# Kernel Integration

Runner depends on Kernel for policy decisions.

## Decision endpoint

Runner calls Kernel:

- `POST /v1/decisions`

## Request example

```json
{
  "tenant_id": "acme",
  "actor": {"type": "agent", "id": "agent-support-1"},
  "action": "tool.call",
  "resource": {"type": "http", "id": "crm-api"},
  "context": {"method": "POST", "path": "/customers"}
}
```

## Response examples

Allow:

```json
{"decision":"allow","policy_id":"tool-http-write","reason":"approved scope"}
```

Deny:

```json
{"decision":"deny","policy_id":"tool-http-write","reason":"write not permitted for tenant plan"}
```

## Enforcement behavior

- `allow` → execute action
- `deny` → block action, surface reason, write audit event
