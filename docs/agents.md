# Agents

Agents in AGenNext-Runner are executable units that perform tasks through tools, APIs, and workflows.

## Agent contract

Each agent should declare:

- `id`: unique stable identifier
- `capabilities`: allowed task types
- `tools`: integration endpoints the agent may request
- `kernel_subject`: identity presented during policy checks

## Example agent manifest

```json
{
  "id": "agent-finops-1",
  "capabilities": ["analysis", "reporting"],
  "tools": ["erp_api", "billing_export"],
  "kernel_subject": "agent:agent-finops-1"
}
```

## Runtime rule

Runner must request a Kernel decision before each sensitive tool call.
