# Autonomyx Model Gateway

Self-hosted AI platform stack for running local LLMs behind a LiteLLM gateway, with Langflow workflows, usage billing, tracing, monitoring, policy enforcement, and operational tooling.

This repository is an operator stack, not a single binary product. The core services and many integration files are present, but a few advanced API routes are intentionally disabled until their dependent services are stable.

---

## Current status

Implemented in this repository:

- LiteLLM gateway configuration with local-first routing and cloud fallbacks
- Ollama local model stack and pull script
- Langflow service with flow files mounted from `flows/`
- Lago billing services and LiteLLM callback integration files
- Langfuse tracing configuration
- Prometheus and Grafana monitoring
- Uptime Kuma, GlitchTip, OpenTelemetry, Jaeger, VictoriaLogs, backup, pgAdmin, Infisical, SurrealDB
- OpenFGA and OPA policy/authz services
- Classifier, translator, and Playwright sidecar service definitions
- Docker Compose deployment for the primary 96GB node

Known limitations in the current code:

- LiteLLM `additional_routers` are currently disabled in `config.yaml` because some modules crash on startup when connecting to dependent services.
- `/recommend`, `/feedback`, `/translate`, and related router endpoints should be treated as present in code but not enabled by default.
- Some Langflow flows call disabled endpoints, so they may need router re-enablement or URL changes before they run end to end.
- Tenant onboarding is not fully automatic yet. Keycloak, Lago, LiteLLM, and Langfuse pieces exist in docs/config, but the full create-group-to-provision-everything path should be validated before production claims.
- Per-tenant Langfuse isolation is partly implemented; `feedback.py` currently falls back to shared Langfuse project keys until tenant-specific key lookup is completed.
- Logto references still exist in `.env.example` and docs even though the intended direction is Keycloak-based SSO.

---

## What customers call

When Langflow flows are imported and the relevant services are configured, customers call Langflow flow endpoints:

```bash
curl -X POST https://flows.openautonomyx.com/api/v1/run/{flow_id} \
  -H "Authorization: Bearer lf-their-api-key" \
  -H "Content-Type: application/json" \
  -d '{"input_value": "Review this contract for risk clauses"}'
```

For direct model access, developers can call the LiteLLM OpenAI-compatible endpoint:

```bash
curl -X POST https://llm.openautonomyx.com/v1/chat/completions \
  -H "Authorization: Bearer sk-your-litellm-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama/qwen3:30b-a3b",
    "messages": [{"role": "user", "content": "Summarise this policy"}]
  }'
```

---

## Operator endpoints

Default public hostnames used by the stack:

```text
flows.openautonomyx.com    → Langflow workflows
llm.openautonomyx.com      → LiteLLM gateway API
traces.openautonomyx.com   → Langfuse tracing
billing.openautonomyx.com  → Lago billing API/UI path
metrics.openautonomyx.com  → Grafana dashboards
uptime.openautonomyx.com   → Uptime Kuma
errors.openautonomyx.com   → GlitchTip
trust.openautonomyx.com    → Trust centre site
```

Several internal-only services are intentionally not exposed publicly, including SurrealDB, OPA, OpenFGA, classifier, translator, Playwright, and backup.

---

## Local models

The local model configuration is defined in `config.yaml`, and the pull/warmup routine is in `ollama-pull.sh`.

| Model | Intended tasks | Loading mode | Approx RAM |
|---|---|---:|---:|
| `ollama/qwen3:30b-a3b` | reasoning, agent, chat, analysis, policy | always-on | 19GB |
| `ollama/qwen2.5-coder:32b` | code review, generation, debugging | always-on | 22GB |
| `ollama/qwen2.5:14b` | extraction, structured output, summarisation | always-on | 9GB |
| `ollama/llama3.2-vision:11b` | vision tasks | warm slot | 9GB |
| `ollama/llama3.1:8b` | fast chat, simple tasks | warm slot | 6GB |
| `ollama/gemma3:9b` | long-context documents | warm slot | 6GB |
| `nomic-embed-text` | embeddings for RAG/scraping | always-on | ~274MB |

The intended peak model RAM is about 84GB on a 96GB VPS. `docker-compose.yml` sets `OLLAMA_MEM_LIMIT` to 76GB by default, so tune this against actual workload and available memory.

---

## Routing and fallbacks

`config.yaml` uses LiteLLM with local models as primary routes and cloud providers as fallback routes.

Examples:

- `ollama/qwen3:30b-a3b` falls back to Groq, Vertex Claude/Gemini, Anthropic, and OpenAI models.
- `ollama/qwen2.5-coder:32b` falls back to Groq, Vertex Gemini, OpenAI, and Vertex Claude.
- `ollama/qwen2.5:14b` falls back to Groq, OpenAI mini, and Gemini Flash.

Cloud provider keys are read from environment variables. No provider API keys should be committed.

---

## Langflow workflows

Flow files live in `flows/` and are mounted into the Langflow container.

Examples currently present include:

| Flow | Purpose | Notes |
|---|---|---|
| `gateway-agent.json` | Detect language, recommend model, call LLM, capture feedback | Depends on `/recommend`, `/feedback`, and `/translate`; these routers are disabled by default in `config.yaml`. |
| `code-review.json` | Structured code review through `ollama/qwen2.5-coder:32b` | More self-contained; still requires Langflow import and LiteLLM key setup. |

Treat flow JSON files as importable templates. Validate each flow in your Langflow version before offering it as a production endpoint.

---

## Disabled custom routers

The following files contain FastAPI routers or gateway extensions:

- `recommender.py`
- `feedback.py`
- `openfga_authz.py`
- `opa_middleware.py`
- `agent_identity.py`
- `agent_discovery.py`

`config.yaml` currently comments out `general_settings.additional_routers` because the modules can crash on startup when dependent services are unavailable. Re-enable these only after confirming service availability and import-time behaviour.

Recommended validation before re-enabling:

```bash
docker compose config
docker compose up -d postgres classifier translator openfga opa litellm
docker logs autonomyx-litellm --tail=200
curl http://localhost:4000/health
```

Then re-enable one router at a time in `config.yaml` and restart LiteLLM.

---

## Billing and tracing

Lago services are defined in `docker-compose.yml`, including API, worker, clock, frontend, database, Redis, storage, and Gotenberg PDF support.

`lago_callback.py` is mounted into the LiteLLM container and registered in `config.yaml` callbacks. This is intended to send LiteLLM usage events to Lago.

Langfuse is configured through environment variables and LiteLLM callback settings. Current tenant isolation should be validated before claiming strict per-tenant trace separation. `feedback.py` currently contains a TODO for tenant-specific Langfuse key lookup.

---

## Auth and policy

The stack includes:

- OpenFGA for relationship-based authorization
- OPA for conditional policy checks
- Keycloak variables and intended identity-provider direction
- Legacy Logto/shared SSO variables still present in `.env.example` and docs

Current state: Keycloak is the intended direction, but Logto references have not yet been fully removed. Do not claim the auth layer is fully migrated until the env/docs and deployment services are reconciled.

---

## Deployment

Primary deployment target: a Coolify-managed Docker Compose stack on a 96GB VPS.

```bash
cp .env.example .env
# Fill required secrets and provider keys.
docker compose config
docker compose up -d
```

Pull and warm local models:

```bash
docker exec autonomyx-ollama sh /ollama-pull.sh
```

Useful checks:

```bash
docker compose ps
docker logs autonomyx-litellm --tail=200
docker exec autonomyx-ollama ollama ps
curl http://127.0.0.1:4000/health
```

---

## Repository structure

```text
.
├── README.md
├── SKILL.md
├── docker-compose.yml
├── config.yaml
├── .env.example
├── ollama-pull.sh
├── lago_callback.py
├── recommender.py
├── feedback.py
├── openfga_authz.py
├── opa_middleware.py
├── agent_identity.py
├── agent_discovery.py
├── flows/
├── docs/
├── references/
├── classifier/
├── translator/
├── playwright/
├── postgres/
├── postgres-lago/
├── opa/
├── otel/
├── grafana/
├── jaeger/
├── backup/
├── frpc/
├── trust/
└── landing/
```

---

## Production readiness checklist

Before marketing this as a complete production product, validate and/or complete:

- Re-enable and test `additional_routers` one by one.
- Confirm `/recommend`, `/feedback`, and `/translate` are reachable from Langflow.
- Update `gateway-agent.json` URLs if translation remains a sidecar-only service.
- Finish tenant-specific Langfuse key lookup.
- Validate Lago usage events from LiteLLM completions.
- Reconcile Keycloak vs Logto references in `.env.example`, docs, and compose.
- Confirm Keycloak group creation provisions Lago customer, LiteLLM key, Langfuse project, and Langflow access if that remains the onboarding claim.
- Run end-to-end tests for each public flow.
- Load test Ollama memory behaviour on the target VPS.
- Remove or clearly mark any aspirational pricing/tenant claims until automation is proven.

---

## Contact

- Platform: [openautonomyx.com](https://openautonomyx.com)
- Skills: [agentnxxt/agentskills](https://github.com/agentnxxt/agentskills)
- Email: chinmay@openautonomyx.com
- Book: [cal.com/thefractionalpm](https://cal.com/thefractionalpm)
