# Tutorial: Policy Enforcement (Allow/Deny)

## 1) Submit intent from Runner

```bash
curl -X POST "$KERNEL_URL/v1/decisions" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme","action":"tool.call","context":{"method":"POST"}}'
```

## 2) Kernel evaluates policy

- Rego policy checks tenant plan and action context.

## 3) Interpret result

- `allow`: Runner may execute.
- `deny`: Runner must block.

## 4) Audit

Kernel records the decision with `decision_id`, actor, tenant, policy_id, and reason.
