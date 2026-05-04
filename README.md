# AGenNext Runner

Framework-agnostic runtime bridge layer between the SDK/model-agnostic **AGenNext Platform** and the infra-agnostic **AGenNext Kernel**.

AGenNext is structured as:

```text
AGenNext Platform
  └─ makes the system SDK agnostic and model agnostic by supporting all SDKs and exposing the model gateway
      ↓
AGenNext Runner
  └─ makes the system framework agnostic by loading the matching runtime bridge
      ↓
AGenNext Kernel
  └─ makes the system infrastructure agnostic by executing on any deployment target
```

The Platform is the user-facing layer. It is SDK agnostic, supports all SDKs and integration styles, and is model agnostic through the model gateway. The user selects the SDK, model/provider path, framework, or runtime style there. Runner is the framework-agnostic bridge layer. It loads the corresponding runtime bridge and connects that selected framework/SDK/model path to AGenNext Kernel. Kernel is the infra-agnostic core execution engine and can be deployed anywhere.

This repository should stay focused on Runner responsibilities: runtime bridges, compose references, model access plumbing, routing, observability, usage metering, billing, policy checks, and integration with Kernel. Framework-specific apps should live outside this repo unless they become official bridge adapters.

---

## Responsibilities

AGenNext Runner is for:

- Making AGenNext framework agnostic
- Loading the correct runtime bridge selected by AGenNext Platform
- Connecting Platform-selected frameworks, SDKs, and model gateway choices to AGenNext Kernel
- Providing the runtime side of model gateway connectivity through LiteLLM and Ollama
- Running workflow/runtime support services such as Langflow
- Collecting traces, metrics, feedback, and billing events
- Enforcing runtime policy and authorization through OPA and OpenFGA
- Running the Docker Compose stack that connects Kernel, bridges, gateway, observability, and metering

AGenNext Runner is not for:

- Owning SDK selection or user-facing SDK experience; that belongs in Platform
- Owning model selection UX; Platform exposes the model gateway experience
- Bundling one-off deep-agent applications
- Keeping framework-specific experiments as first-class runtime code
- Hardcoding one framework as the product
- Mixing old brand-specific app modules into the runner layer

---

## Layer responsibilities

| Layer | Agnostic boundary | Responsibility |
|---|---|---|
| AGenNext Platform | SDK agnostic and model agnostic | Supports all SDKs, exposes the model gateway, and provides the user-facing selection/configuration experience |
| AGenNext Runner | Framework agnostic | Loads the selected framework/runtime bridge and connects it to Kernel and runtime services |
| AGenNext Kernel | Infrastructure agnostic | Executes on any deployment target selected by the operator/customer |

---

## AGenNext Kernel

**AGenNext Kernel is the kernel.**

Kernel makes AGenNext infrastructure agnostic. It can run anywhere the operator chooses, including local Docker, a VPS, Kubernetes, private cloud, public cloud, edge nodes, customer infrastructure, or a managed AGenNext environment.

Runner does not replace Kernel and does not own Kernel source code. Runner makes the system framework agnostic by connecting Platform-selected runtime bridges to whichever Kernel deployment is configured.

The runner includes an `agennext-kernel` Docker Compose service reference for local or co-located deployments. It is intentionally a reference to a Kernel image/repository, not a copy of Kernel source code.

Expected compose pattern:

```yaml
agennext-kernel:
  image: ${AGENNEXT_KERNEL_IMAGE:-ghcr.io/agennext/kernel:latest}
  environment:
    - KERNEL_REPO=${AGENNEXT_KERNEL_REPO:-https://github.com/AGenNext/Kernel}
    - KERNEL_ENDPOINT=${AGENNEXT_KERNEL_ENDPOINT:-http://agennext-kernel:8080}
```

For external Kernel deployments, Runner should point to the remote Kernel endpoint instead of starting a local Kernel container:

```env
AGENNEXT_KERNEL_ENDPOINT=https://kernel.<your-domain>
AGENNEXT_KERNEL_IMAGE=
AGENNEXT_KERNEL_REPO=https://github.com/AGenNext/Kernel
```

Use this repo to configure, run, and connect Kernel. Keep Kernel implementation in the Kernel repository.

---

## Runtime bridge model

Platform chooses the SDK, model gateway path, framework, or runtime style. Runner loads the matching bridge. The bridge communicates with Kernel and shared runtime services.

Primary bridge points:

| Bridge point | Purpose |
|---|---|
| AGenNext Kernel endpoint | Infra-agnostic core kernel execution target, local or remote |
| Runtime bridge adapters | Framework-agnostic connection layer for Platform-selected frameworks and SDKs |
| LiteLLM OpenAI-compatible API | Runtime model gateway backend for Kernel, frameworks, SDKs, and agents |
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

AGenNext Platform exposes the model gateway experience so users can remain model agnostic. AGenNext Runner provides the runtime-side gateway connectivity through LiteLLM and Ollama.

This gives Kernel, bridges, workflows, SDKs, and external runtimes a single OpenAI-compatible endpoint while routing requests to local models first and cloud providers only as fallbacks.

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
kernel.<your-domain>   → Optional external Kernel endpoint
traces.<your-domain>   → Langfuse tracing
billing.<your-domain>  → Lago billing API/UI path
metrics.<your-domain>  → Grafana dashboards
uptime.<your-domain>   → Uptime Kuma
errors.<your-domain>   → GlitchTip
trust.<your-domain>    → Trust centre site
```

Internal-only services include SurrealDB, OPA, OpenFGA, classifier, translator, Playwright, Kernel internals when co-located, and backup.

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
# Fill required secrets, provider keys, and Kernel endpoint/image settings.
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
- Validate SDK and model gateway selection in Platform against bridge loading in Runner.
- Validate local and remote Kernel deployment modes.
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


## Runner Enforcement Boundary (AgentNext)

Runner is the mandatory runtime enforcement boundary. Before any Kernel call, Runner now performs a deny-by-default pre-execution pipeline: tenant resolution, agent identity verification, AuthZEN/OpenFGA/OPA evaluation, protocol adapter normalization (A2A, Agent Communication Protocol, Agent Client Protocol, Agent Network Protocol), and guardrail-ready prevalidation envelope assembly. Kernel only executes prevalidated envelopes and does not perform primary policy enforcement.

The Kernel handoff envelope includes `tenant_id`, `execution_id`, canonical `actor`, original `payload`, `protocol` metadata, and `prevalidation` metadata (`validated_by`, identity flag, policy/authorization decisions, decision ids, subject/resource/action/context, and policy bundle version).


### Production/Security/Deployment Hardening Notes
- Runner enforcement is deny-by-default for missing tenant, malformed identity token, expired identity, signature mismatch, malformed policy input, and failed authorization checks.
- Runtime auth supports signed bearer tokens (`tenant:agent:exp:sig`) with HMAC verification via `IDENTITY_SHARED_SECRET`; cross-tenant and expired identities are rejected before Kernel invocation.
- AuthZEN/OpenFGA/OPA adapters support remote endpoints (`AUTHZEN_ENDPOINT`, `OPENFGA_ENDPOINT`, `OPA_ENDPOINT`) with fail-closed behavior by default.
- Kernel handoff includes execution and prevalidation metadata, and kernel calls carry `X-Tenant-ID` and `X-Execution-ID` headers for traceability across distributed deployments.
