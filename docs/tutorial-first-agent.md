# Tutorial: First Agent

This tutorial shows how to run one agent through Runner with mandatory Kernel validation.

## 1) Define the agent

```json
{
  "id": "agent-support-1",
  "tools": ["crm-api"]
}
```

## 2) Submit an action intent

Runner prepares intent:

```json
{
  "action": "tool.call",
  "resource": {"type":"http","id":"crm-api"}
}
```

## 3) Ask Kernel for decision

```bash
curl -X POST "$KERNEL_URL/v1/decisions" -H "Content-Type: application/json" -d @intent.json
```

## 4) Execute or block

- If allow: Runner executes tool call.
- If deny: Runner returns policy error and does not execute.

For policy authoring and governance details, see AGenNext-Kernel docs.
