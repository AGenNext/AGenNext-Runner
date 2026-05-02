# AGenNext Runner

Runtime bridge layer between **AGenNext Platform** and **AGenNext Kernel**.

AGenNext is structured as:

```text
AGenNext Platform
  └─ user selects framework / SDK / runtime style
      ↓
AGenNext Runner
  └─ loads the matching runtime bridge
      ↓
AGenNext Kernel
  └─ executes through the core kernel runtime
```

The Platform is the user-facing layer. The user selects the framework, SDK, or integration style there. Runner is the runtime bridge layer. It loads the corresponding bridge adapter and connects that selected runtime to AGenNext Kernel. Kernel is the core execution engine.

This repository should stay focused on Runner responsibilities: runtime bridges, compose references, model access, routing, observability, usage metering, billing, policy checks, and integration with Kernel. Framework-specific apps should live outside this repo unless they become official bridge adapters.

---

## Responsibilities

AGenNext Runner is for:

- Loading the correct runtime bridge selected by AGenNext Platform
- Connecting selected frameworks and SDKs to AGenNext Kernel
- Providing model access through LiteLLM and Ollama
- Running workflow/runtime support services such as Langflow
- Collecting traces, metrics, feedback, and billing events
- Enforcing runtime policy and authorization through OPA and OpenFGA
- Running the Docker Compose stack that connects Kernel, bridges, gateway, observability, and metering

AGenNext Runner is not for:

- Bundling one-off deep-agent applications
- Keeping framework-specific experiments as first-class runtime code
- Hardcoding one framework as the product
- Mixing old brand-specific app modules into the runner layer

---

## AGenNext Kernel

**AGenNext Kernel is the kernel.**

Runner does not replace Kernel. Runner connects selected runtime bridges to Kernel.

The runner includes an `agennext-kernel` Docker Compose service reference. It is intentionally a reference to a Kernel image/repository, not a copy of Kernel source code.

Expected compose pattern:

```yaml
agennext-kernel:
  image: ${AGENNEXT_KERNEL_IMAGE:-ghcr.io/agennext/kernel:latest}
  environment:
    - KERNEL_REPO=${AGENNEXT_KERNEL_REPO:-https://github.com/AGenNext/Kernel}
```

Use this repo to configure, run, and connect Kernel. Keep Kernel implementation in the Kernel repository.

---

## Runtime bridge model

Platform chooses the framework or SDK. Runner loads the matching bridge. The bridge communicates with Kernel and shared runtime services.

Primary bridge points:

| Bridge point | Purpose |
|---|---|
| AGenNext Kernel service | Core kernel execution target |
| LiteLLM OpenAI-compatible API | Model access for Kernel, frameworks, SDKs, and agents |
| Langflow API | Workflow execution and hosted flow templates |
| Model recommender route | Runtime model selection once enabled |
| Feedback route | Human/application feedback capture once enabled |
| Agent discovery route | Runtime capability discovery once enabled |
| Agent identity route | Runtime identity lifecycle once enabled |
| OpenFGA / OPA | Authorization and policy checks |
| Langfuse | Tracing, evaluation, and observability |
| Lago | Usage metering and billing |

Bridge adapters can be added as docs, compose snippets, or lightweight adapter services, for example:

```text
bridges/langgraph/
bridges/crewai/
bridges/autogen/
bridges/langchain/
bridges/llamaindex/
bridges/semantic-kernel/
bridges/mastra/
bridges/custom-sdk/
```

Each bridge should document environment variables, base URLs, auth keys, example calls, and health checks. Framework application code should remain in its own repo.

---

## Current status

Implemented in this repository:

- Docker Compose runtime stack
- AGenNext Kernel compose reference service
- LiteLLM model gateway configuration with local-first routing and cloud fallbacks
- Ollama local model stack and pull script
- Langflow service with flow files mounted from `flows/`
- Lago billing services and LiteLLM callback integration files
- Langfuse tracing configuration
- Prometheus and Grafana monitoring
- Uptime Kuma, GlitchTip, OpenTelemetry, Jaeger, VictoriaLogs, backup, pgAdmin, Infisical, SurrealDB
- OpenFGA and OPA policy/authz services
- Classifier, translator, and Playwright sidecar service definitions

Known limitations:

- LiteLLM `additional_routers` are currently disabled in `config.yaml` because some modules crash on startup when dependent services are unavailable.
- `/recommend`, `/feedback`, `/translate`, and related router endpoints should be treated as present in code but not enabled by default.
- Some Langflow flows call disabled endpoints, so they may need router re-enablement or URL changes before they run end to end.
- Tenant onboarding is not fully automatic yet.
- Per-tenant Langfuse isolation is partly implemented.
- Logto references still exist in `.env.example` and docs even though the intended direction is Keycloak-based SSO.

---

## Model gateway layer

AGenNext Runner includes a model gateway layer powered by LiteLLM and Ollama. This gives Kernel, bridges, workflows, SDKs, and external runtimes a single OpenAI-compatible endpoint while routing requests to local models first and cloud providers only as fallbacks.

The gateway is configured in `config.yaml`, deployed through `docker-compose.yml`, and backed by the local model pull/warmup script in `ollama-pull.sh`.

---

## What external runtimes call

For direct model access, bridges and frameworks can call the LiteLLM OpenAI-compatible endpoint:

```bash
curl -X POST https://llm.<your-domain>/v1/chat/completions \
  -H "Authorization: Bearer sk-your-litellm-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama/qwen3:30b-a3b",
    "messages": [{"role": "user", "content": "Summarise this policy"}]
  }'
```

When Langflow flows are imported and the relevant services are configured, callers can run Langflow flow endpoints:

```bash
curl -X POST https://flows.<your-domain>/api/v1/run/{flow_id} \
  -H "Authorization: Bearer lf-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"input_value": "Review this contract for risk clauses"}'
```

---

## Operator endpoint pattern

```text
flows.<your-domain>    → Langflow workflows
llm.<your-domain>      → LiteLLM gateway API
traces.<your-domain>   → Langfuse tracing
billing.<your-domain>  → Lago billing API/UI path
metrics.<your-domain>  → Grafana dashboards
uptime.<your-domain>   → Uptime Kuma
errors.<your-domain>   → GlitchTip
trust.<your-domain>    → Trust centre site
```

Internal-only services include SurrealDB, OPA, OpenFGA, classifier, translator, Playwright, Kernel internals, and backup.

---

## Local models

| Model | Intended tasks | Loading mode | Approx RAM |
|---|---|---:|---:|
| `ollama/qwen3:30b-a3b` | reasoning, agent, chat, analysis, policy | always-on | 19GB |
| `ollama/qwen2.5-coder:32b` | code review, generation, debugging | always-on | 22GB |
| `ollama/qwen2.5:14b` | extraction, structured output, summarisation | always-on | 9GB |
| `ollama/llama3.2-vision:11b` | vision tasks | warm slot | 9GB |
| `ollama/llama3.1:8b` | fast chat, simple tasks | warm slot | 6GB |
| `ollama/gemma3:9b` | long-context documents | warm slot | 6GB |
| `nomic-embed-text` | embeddings for RAG/scraping | always-on | ~274MB |

---

## Langflow workflows

Flow files live in `flows/` and are mounted into the Langflow container.

| Flow | Purpose | Notes |
|---|---|---|
| `gateway-agent.json` | Detect language, recommend model, call LLM, capture feedback | Depends on disabled routes unless re-enabled. |
| `code-review.json` | Structured code review through `ollama/qwen2.5-coder:32b` | Requires Langflow import and LiteLLM key setup. |

Treat flow JSON files as importable templates. Validate each flow before offering it as a production endpoint.

---

## Deployment

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

## Production readiness checklist

- Re-enable and test `additional_routers` one by one.
- Confirm `/recommend`, `/feedback`, and `/translate` are reachable from Langflow before flows depend on them.
- Finish tenant-specific Langfuse key lookup.
- Validate Lago usage events from LiteLLM completions.
- Reconcile Keycloak vs Logto references in `.env.example`, docs, and compose.
- Add bridge docs/compose snippets for Platform-selectable frameworks and SDKs.
- Run end-to-end tests for each public flow and bridge.
- Load test Ollama memory behaviour on the target VPS.
- Keep framework-specific apps outside this repo unless they become official runtime bridges.

---

## Backup note

The removed old deep-agent module is preserved on branch:

```text
backup/autonomyx-deep-agent-before-removal
```

Use that branch if the old experimental module needs to be restored or migrated into a separate framework repo.
