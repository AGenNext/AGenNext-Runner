# Runtime

The Runner runtime schedules and executes agent actions.

## Core stages

1. Load workflow and execution context.
2. Resolve next action.
3. Call Kernel decision API.
4. Execute or block.
5. Emit logs, traces, and status.

## Execution record example

```json
{
  "run_id": "run_01JZ...",
  "agent_id": "agent-finops-1",
  "action": "tool.call",
  "policy_decision": "allow",
  "status": "completed",
  "latency_ms": 281
}
```
