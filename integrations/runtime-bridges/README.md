# Runtime Integration Bridges

AGenNext Kernels now includes runtime integration bridge templates for popular agent runtimes and language ecosystems.

## Included bridges

- **Python** (`python/bridge.py`) — for LangChain, LlamaIndex, CrewAI, and AutoGen-style workflows.
- **Node.js / TypeScript** (`node/bridge.ts`) — for Vercel AI SDK, LangChain JS, and custom orchestration pipelines.
- **Go** (`go/bridge.go`) — for backend services and low-latency control planes.
- **Java** (`java/Bridge.java`) — for enterprise JVM orchestration services.
- **.NET** (`dotnet/Bridge.cs`) — for Semantic Kernel and ASP.NET based agent services.
- **Rust** (`rust/bridge.rs`) — for high-performance and edge-native agent runtimes.

Each bridge implements the same minimal lifecycle:

1. `init` — initialize bridge and authenticate.
2. `invoke` — dispatch an action to Kernel API.
3. `stream` — consume telemetry/events.
4. `close` — graceful shutdown.

All templates are intentionally minimal and ready to wire to `kernel_api` endpoints.

## Runtime compatibility

These bridges are **language templates** and will work anywhere the runtime can make outbound HTTP calls to `kernel_api` (or any compatible gateway).

- **Python 3.9+**
- **Node.js 18+ / TypeScript 5+**
- **Go 1.21+**
- **Java 17+**
- **.NET 8+ (C#)**
- **Rust stable (1.75+)**

> Note: the current bridge files are starter implementations (not production SDKs). You still need to wire authentication, retries, serialization, and endpoint mappings for your deployment.


## LangGraph runtime compatibility

Yes — this works with **LangGraph runtime** through the Python and Node.js bridge templates.

Recommended mapping:
- Use `python/bridge.py` for LangGraph Python deployments.
- Use `node/bridge.ts` for LangGraph JS/TS deployments.

To run in production with LangGraph, wire the bridge methods to your graph entrypoints and add:
1. API authentication headers/tokens
2. retry + timeout policy
3. structured request/response serialization
4. telemetry event forwarding from graph node execution


## Extensions / plugins

Bridge templates are also published in-repo as plugin descriptors under `integrations/runtime-bridges/plugins/` so each runtime can be consumed as an extension package.


## Agentfield.ai runtime compatibility

Yes — it can work with the **agentfield.ai runtime** as long as the runtime can call external HTTP APIs/webhooks.

Recommended approach:
- Use the runtime bridge matching your Agentfield execution language (Python or Node.js first).
- Map bridge `invoke` to Agentfield task/tool execution hooks.
- Map bridge `stream` to Agentfield event stream callbacks.

Production checklist for Agentfield integration:
1. kernel API authentication + key rotation
2. request signing / webhook validation (if applicable)
3. retry, timeout, and idempotency keys
4. telemetry correlation IDs between Agentfield runs and kernel events

If you share your Agentfield runtime version and deployment mode (cloud/self-hosted), we can provide a concrete adapter mapping.


## Design goals for native runtime

To justify a first-party runtime, the integration layer should optimize for:

- **Consistent cross-runtime behavior**: identical lifecycle semantics (`init`, `invoke`, `stream`, `close`), error codes, retries, and timeout handling regardless of language runtime.
- **Kernel-native observability and compliance**: built-in telemetry correlation, audit events, policy decision traces, and enforcement hooks as first-class runtime behavior.

These goals keep bridge implementations predictable while preserving governance guarantees across Python, Node.js, Go, Java, .NET, and Rust ecosystems.
