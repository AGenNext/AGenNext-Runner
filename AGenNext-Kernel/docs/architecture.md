# Architecture

Kernel is the policy control plane for Runner.

## System flow

1. Runner submits action intent.
2. Kernel validates schema and tenant context.
3. Kernel evaluates OPA/Rego bundles.
4. Kernel returns `allow` or `deny` with reason.
5. Kernel writes decision to audit log.

## Design goals

- Deterministic decisions
- Explainable denial reasons
- Centralized governance across all runners
