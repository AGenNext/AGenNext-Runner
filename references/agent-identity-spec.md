# Autonomyx Agent Identity Specification

**Version:** 1.0
**Date:** April 16, 2026
**Reference:** [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/what-are-agent-identities), [OCI Image Spec](https://github.com/opencontainers/image-spec)

---

## 1. What is an Agent Identity

An agent identity is a unique, scoped, auditable credential assigned to each AI agent operating within the Autonomyx Model Gateway. It is distinct from:

- **Tenant identities** — human users or organisations accessing the gateway
- **Operator identities** — platform administrators
- **Service identities** — internal sidecars (classifier, translator, playwright)

Every agent that calls the gateway must present its own Virtual Key — never a tenant key or master key. This ensures every LLM call, billing event, and error is traceable to a specific named agent.

---

## 2. Agent Identity Properties

Each agent identity carries the following attributes:

| Property | Type | Description |
|---|---|---|
| `agent_id` | `string` | Stable unique ID — `agent:<uuid>` |
| `agent_name` | `string` | Human-readable name — e.g. `fraud-sentinel` |
| `agent_type` | `enum` | `workflow` / `skill` / `mcp_tool` / `ephemeral` |
| `sponsor_id` | `string` | REQUIRED — Business owner accountable for lifecycle decisions |
| `owner_ids` | `list[string]` | Technical admins — manage config, credentials, can re-enable |
| `manager_id` | `string` or `null` | Org hierarchy manager — can request access packages |
| `blueprint_id` | `string` or `null` | Blueprint this agent was instantiated from |
| `tenant_id` | `string` | Keycloak group (tenant) this agent belongs to |
| `allowed_models` | `list[string]` | Allowlist of model aliases this agent may call |
| `budget_limit` | `float` | Maximum spend per billing period (USD) |
| `tpm_limit` | `int` | Token per minute rate limit |
| `litellm_key` | `string` | Scoped Virtual Key for LiteLLM API calls |
| `litellm_key_alias` | `string` | Alias — `agent:<agent_name>:<tenant_id>` |
| `status` | `enum` | `active` / `suspended` / `revoked` |
| `created_at` | `datetime` | ISO 8601 |
| `last_active_at` | `datetime` | Updated on every successful LLM call |
| `expires_at` | `datetime` or `null` | For ephemeral agents — null = permanent |
| `metadata` | `dict` | Arbitrary key-value pairs for context |

---

## 3. Agent Types

### 3.1 Workflow Agent
A persistent agent backing a Langflow workflow. Created once, lives indefinitely.
- Example: `fraud-sentinel`, `policy-creator`, `code-reviewer`
- Budget: per-workflow monthly limit
- Allowed models: only models needed for that workflow

### 3.2 Skill Agent
An agent exposing an Autonomyx skill via the MCP server.
- Example: `skill-feature-gap-analyzer`, `skill-saas-evaluator`
- Budget: inherited from the calling tenant's plan
- Allowed models: defined per skill in `metadata.yaml`

### 3.3 MCP Tool Agent
A short-lived agent created for a single MCP tool invocation.
- Created on demand, revoked after the tool call completes
- Budget: micro-budget (e.g. ₹10 per invocation)
- Expires: 1 hour from creation

### 3.4 Ephemeral Agent
A temporary agent created for a specific task, automatically revoked on expiry.
- Example: a customer-facing demo agent with 24h lifetime
- `expires_at` is always set
- Automatically revoked by the `agent_gc` background task

---

## 4. Agent Lifecycle

```
CREATE
  → Keycloak service account created (agent type)
  → LiteLLM Virtual Key created (scoped to allowed_models + budget)
  → SurrealDB record created (status: active)
  → Credentials returned to sponsor (one-time)
        │
        ▼
ACTIVE (agent makes LLM calls)
  → Virtual Key authenticates each call
  → agent_id tagged in Langfuse trace metadata
  → GlitchTip captures errors with agent_id context
  → Lago bills per agent_id
  → last_active_at updated per call
        │
        ├─► SUSPEND (temporary — key revoked, identity preserved)
        │     → LiteLLM key deleted
        │     → SurrealDB status: suspended
        │     → Can be reactivated (new key issued, same agent_id)
        │
        ├─► ROTATE (key rotation — zero downtime)
        │     → New LiteLLM key created
        │     → Old key deleted
        │     → New key returned to sponsor
        │
        └─► REVOKE (permanent — full deprovisioning)
              → LiteLLM key deleted
              → Keycloak service account deleted
              → SurrealDB status: revoked (record retained for audit)
              → No reactivation possible
```

---

## 5. Access Model (Right-Sized Access)

Each agent may only call models in its `allowed_models` list. This is enforced at the LiteLLM Virtual Key level — LiteLLM rejects calls to models not in the key's allowlist.

### Default model allowlists per agent type:

| Agent | Allowed models |
|---|---|
| `fraud-sentinel` | `ollama/qwen3:30b-a3b`, `groq/llama3-70b` |
| `policy-creator` | `ollama/qwen3:30b-a3b`, `vertex/gemini-2.5-pro` |
| `code-reviewer` | `ollama/qwen2.5-coder:32b`, `groq/llama3-70b` |
| `web-scraper` | `ollama/qwen2.5:14b`, `ollama/nomic-embed-text` |
| `feature-gap-analyzer` | `ollama/qwen3:30b-a3b` |
| `ephemeral/*` | `ollama/qwen3:30b-a3b` (local only, no cloud) |

No agent has access to all models. The master key is never used by agents.

---

## 6. Traceability Requirements

Every LLM call made by an agent must carry:

```json
{
  "metadata": {
    "agent_id": "agent:550e8400-e29b-41d4-a716-446655440000",
    "agent_name": "fraud-sentinel",
    "agent_type": "workflow",
    "tenant_id": "tenant-acme",
    "sponsor_id": "user:chinmay@openautonomyx.com",
    "call_id": "call:uuid"
  }
}
```

This metadata is:
- Stored in Langfuse as trace tags (queryable)
- Forwarded to Lago as event properties (billable per agent)
- Forwarded to GlitchTip as error context (debuggable per agent)

---

## 7. API Endpoints

All endpoints mounted on LiteLLM at `/agents/*`. Require `Authorization: Bearer <LITELLM_MASTER_KEY>`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/agents/create` | Provision a new agent identity |
| `GET` | `/agents` | List all agents (filterable by tenant, status, type) |
| `GET` | `/agents/{agent_id}` | Get agent details |
| `POST` | `/agents/{agent_id}/suspend` | Suspend agent (revoke key, preserve identity) |
| `POST` | `/agents/{agent_id}/reactivate` | Reactivate suspended agent (new key) |
| `POST` | `/agents/{agent_id}/rotate` | Rotate agent key (zero downtime) |
| `DELETE` | `/agents/{agent_id}` | Permanently revoke agent |
| `GET` | `/agents/{agent_id}/activity` | Agent call history from Langfuse |

---

## 8. Separation from Tenant Identities

| Property | Tenant identity | Agent identity |
|---|---|---|
| Created by | Self-signup or Keycloak group | Sponsor (human user) via API |
| Lifetime | Account lifetime | Task lifetime (ephemeral) or indefinite |
| Authentication | Virtual Key (tenant scoped) | Virtual Key (agent scoped) |
| Model access | Plan-based | Explicit allowlist |
| Budget | Plan-based monthly | Per-agent, per-period |
| In Langfuse | `user_id` = tenant | `metadata.agent_id` = agent |
| In Lago | `external_customer_id` = tenant | `external_subscription_id` = agent |
| In GlitchTip | Project = tenant | Tag `agent_id` = agent |

---

## 9. Security Rules

- An agent key must never be used as a tenant key or vice versa
- Agent keys never have access to `/key/create`, `/key/delete`, or `/user/*` endpoints
- Ephemeral agents are automatically revoked by `agent_gc` — never manually managed
- Agent credentials are returned once at creation — never stored in plaintext after that
- Sponsor must authenticate before creating or managing agent identities
- Agent `allowed_models` must be an explicit allowlist — never `*`
- Master key is never used by any agent — only for provisioning

---

## 10. SurrealDB Schema

```sql
DEFINE TABLE agents SCHEMAFULL;

DEFINE FIELD agent_id        ON agents TYPE string ASSERT $value != NONE;
DEFINE FIELD agent_name      ON agents TYPE string ASSERT $value != NONE;
DEFINE FIELD agent_type      ON agents TYPE string ASSERT $value IN ['workflow','skill','mcp_tool','ephemeral'];
DEFINE FIELD sponsor_id      ON agents TYPE string ASSERT $value != NONE;  -- REQUIRED
DEFINE FIELD owner_ids       ON agents TYPE array   DEFAULT [$sponsor_id];
DEFINE FIELD manager_id      ON agents TYPE option<string>;
DEFINE FIELD blueprint_id    ON agents TYPE option<string>;
DEFINE FIELD tenant_id       ON agents TYPE string;
DEFINE FIELD allowed_models  ON agents TYPE array;
DEFINE FIELD budget_limit    ON agents TYPE float  DEFAULT 5.0;
DEFINE FIELD tpm_limit       ON agents TYPE int    DEFAULT 10000;
DEFINE FIELD litellm_key     ON agents TYPE string; -- stored encrypted
DEFINE FIELD litellm_key_alias ON agents TYPE string;
DEFINE FIELD status          ON agents TYPE string ASSERT $value IN ['active','suspended','revoked'] DEFAULT 'active';
DEFINE FIELD created_at      ON agents TYPE datetime DEFAULT time::now();
DEFINE FIELD last_active_at  ON agents TYPE datetime DEFAULT time::now();
DEFINE FIELD expires_at      ON agents TYPE option<datetime>;
DEFINE FIELD metadata        ON agents TYPE object  DEFAULT {};

DEFINE INDEX agents_name_tenant ON agents FIELDS agent_name, tenant_id UNIQUE;
DEFINE INDEX agents_status      ON agents FIELDS status;
DEFINE INDEX agents_expires     ON agents FIELDS expires_at;
```

---

## 11. Pre-provisioned Agents (Bootstrap)

These agents are created on first deploy via `docker exec autonomyx-litellm python agent_bootstrap.py`:

| Agent name | Type | Allowed models | Monthly budget |
|---|---|---|---|
| `fraud-sentinel` | workflow | qwen3:30b-a3b, groq/llama3-70b | $2.00 |
| `policy-creator` | workflow | qwen3:30b-a3b, vertex/gemini-2.5-pro | $5.00 |
| `policy-reviewer` | workflow | qwen3:30b-a3b | $2.00 |
| `code-reviewer` | workflow | qwen2.5-coder:32b, groq/llama3-70b | $3.00 |
| `feature-gap-analyzer` | workflow | qwen3:30b-a3b | $3.00 |
| `saas-evaluator` | workflow | qwen3:30b-a3b | $3.00 |
| `app-alternatives-finder` | workflow | qwen3:30b-a3b | $2.00 |
| `saas-standardizer` | workflow | qwen3:30b-a3b | $2.00 |
| `oss-to-saas-analyzer` | workflow | qwen3:30b-a3b | $2.00 |
| `structured-data-parser` | workflow | qwen2.5:14b | $1.00 |
| `web-scraper` | workflow | qwen2.5:14b, nomic-embed-text | $2.00 |
| `gateway-agent` | workflow | qwen3:30b-a3b | $5.00 |

---

## 12. Administrative Roles (Three-Role Model)

Per Microsoft Entra Agent ID, three distinct administrative roles govern each agent identity. These roles separate technical administration from business accountability.

### Owner
- **Who:** Developers, IT professionals, technical application owners
- **Permissions:** Full technical control — edit settings, manage credentials, add/remove other owners and sponsors, re-enable disabled agents, restore soft-deleted agents
- **Cannot do:** Make business lifecycle decisions (that's sponsor's role)
- **In Autonomyx:** Stored in `owner_ids[]`. Defaults to `[sponsor_id]` if not specified.
- **Required:** No — optional at creation

### Sponsor
- **Who:** Business owners, product managers, team leads, stakeholders
- **Permissions:** Lifecycle decisions — enable/disable agents, access reviews, incident response authorization
- **Cannot do:** Modify application settings or credentials
- **In Autonomyx:** Stored in `sponsor_id`. **Required at creation.** The calling user is auto-assigned if none specified.
- **Required:** YES — mandatory at creation

### Manager
- **Who:** Individual user responsible for the agent in org hierarchy
- **Permissions:** Request access packages for agent users; agent appears as a direct report in directory
- **Cannot do:** Modify or delete agents
- **In Autonomyx:** Stored in `manager_id`. Optional.
- **Required:** No — optional

### Role comparison table

| Capability | Owner | Sponsor | Manager |
|---|---|---|---|
| Edit agent config/settings | ✅ | ❌ | ❌ |
| Manage credentials | ✅ | ❌ | ❌ |
| Add/remove owners & sponsors | ✅ | ❌ | ❌ |
| Enable/disable agent | ✅ | ✅ | ❌ |
| Revoke agent (delete) | ✅ | ✅ | ❌ |
| Re-enable disabled agent | ✅ | ❌ | ❌ |
| Request access packages | ❌ | ✅ | ✅ |
| Lifecycle decisions | ❌ | ✅ | ❌ |
| Required at creation | No | **YES** | No |

---

## 13. Blueprint Pattern

An agent identity blueprint is a template from which agent identities are created. It provides:

- **Template:** Common configuration shared across all agent identities of this type
- **Factory:** Creates agent identities (holds `AgentIdentity.CreateAsManager` permission)
- **Credential holder:** Credentials are on the blueprint, not individual agents
- **Policy container:** Policies applied to blueprint apply to all its agents

### Autonomyx Blueprint Implementation

In Autonomyx, blueprints are represented as named templates in SurrealDB:

```sql
DEFINE TABLE agent_blueprints SCHEMAFULL;

DEFINE FIELD blueprint_id    ON agent_blueprints TYPE string;
DEFINE FIELD blueprint_name  ON agent_blueprints TYPE string;
DEFINE FIELD description     ON agent_blueprints TYPE string;
DEFINE FIELD agent_type      ON agent_blueprints TYPE string;
DEFINE FIELD default_models  ON agent_blueprints TYPE array;
DEFINE FIELD default_budget  ON agent_blueprints TYPE float;
DEFINE FIELD default_tpm     ON agent_blueprints TYPE int;
DEFINE FIELD owner_ids       ON agent_blueprints TYPE array;
DEFINE FIELD sponsor_id      ON agent_blueprints TYPE string;
DEFINE FIELD created_at      ON agent_blueprints TYPE datetime DEFAULT time::now();
DEFINE FIELD metadata        ON agent_blueprints TYPE object DEFAULT {};
```

Pre-defined blueprints (created at bootstrap):
- `blueprint:workflow` — for all 12 workflow agents
- `blueprint:skill` — for MCP skill agents
- `blueprint:ephemeral` — for short-lived task agents

Agent identities reference their blueprint via `blueprint_id`. Disabling a blueprint suspends all agents created from it.

---

*Reference: [Microsoft Entra Agent ID documentation](https://learn.microsoft.com/en-us/entra/agent-id/)*
*Last updated: April 16, 2026*
