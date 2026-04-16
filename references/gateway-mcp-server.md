# autonomyx-gateway-mcp — MCP Server

## Role

Thin FastMCP wrapper around the running gateway's FastAPI endpoints.
Exposes gateway capabilities as typed MCP tools so any Claude session,
Langflow flow, or other agent can call them without knowing the gateway internals.

This is NOT the gateway itself — it calls the gateway's endpoints.

---

## Tools exposed

| Tool | Calls | Returns |
|---|---|---|
| `recommend_model` | POST /recommend | Ranked model list + budget state |
| `submit_feedback` | POST /feedback | Confirmation + score ID |
| `check_budget` | GET via LiteLLM API | Spend, remaining, reset_in_hours |
| `translate` | POST /translate (translator sidecar) | Translated text + detected lang |
| `list_models` | GET /v1/models | All available model aliases |
| `get_spend_logs` | GET /spend/logs | Recent traces with cost |
| `create_virtual_key` | POST /key/generate | New scoped virtual key |
| `classify_task` | POST /classify (classifier sidecar) | Task type + confidence |

---

## `gateway_mcp/server.py`

```python
"""
autonomyx-gateway-mcp
FastMCP server exposing Autonomyx LLM Gateway capabilities as MCP tools.

Deploy alongside the gateway stack (same coolify network).
Env vars:
  GATEWAY_URL      — e.g. http://litellm:4000
  TRANSLATOR_URL   — e.g. http://translator:8200
  CLASSIFIER_URL   — e.g. http://classifier:8100
  LITELLM_MASTER_KEY
"""

import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="autonomyx-gateway",
    version="1.0.0",
    description="Autonomyx LLM Gateway — model routing, billing, translation, feedback",
)

GATEWAY_URL    = os.environ.get("GATEWAY_URL",    "http://litellm:4000")
TRANSLATOR_URL = os.environ.get("TRANSLATOR_URL", "http://translator:8200")
CLASSIFIER_URL = os.environ.get("CLASSIFIER_URL", "http://classifier:8100")
MASTER_KEY     = os.environ.get("LITELLM_MASTER_KEY", "")

HEADERS = {"Authorization": f"Bearer {MASTER_KEY}", "Content-Type": "application/json"}


# ── Tool: recommend_model ──────────────────────────────────────────────────

@mcp.tool()
async def recommend_model(
    prompt: str,
    virtual_key: str,
    top_n: int = 3,
    require_private: bool = False,
) -> dict:
    """
    Recommend the best model(s) for a given prompt and virtual key.

    Infers task type from prompt content (local classifier).
    Reads budget state from LiteLLM + Lago.
    Reads latency + error rate from Prometheus.
    Returns ranked list with fit scores, budget remaining, tokens remaining, reset time.

    Args:
        prompt: The user prompt or task description
        virtual_key: LiteLLM virtual key alias (e.g. 'langflow-prod')
        top_n: Number of recommendations to return (default 3)
        require_private: If True, only return local/on-VPS models

    Returns:
        task_type, task_confidence, recommendations[], budget_state
    """
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{GATEWAY_URL}/recommend",
            headers=HEADERS,
            json={
                "prompt": prompt,
                "virtual_key": virtual_key,
                "top_n": top_n,
                "require_private": require_private,
            },
        )
        r.raise_for_status()
        return r.json()


# ── Tool: submit_feedback ──────────────────────────────────────────────────

@mcp.tool()
async def submit_feedback(
    trace_id: str,
    score: int,
    virtual_key: str,
    comment: str = "",
) -> dict:
    """
    Submit human feedback for a specific LLM response.

    Routes to the correct Langfuse tenant project via virtual key.
    Feeds into the model improvement pipeline (if tenant opted in).

    Args:
        trace_id: Response ID from the LLM call (response.id field)
        score: 1 = thumbs up (good), 0 = thumbs down (bad)
        virtual_key: LiteLLM virtual key alias for tenant routing
        comment: Optional freetext feedback

    Returns:
        status, trace_id, score, langfuse_score_id
    """
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{GATEWAY_URL}/feedback",
            headers=HEADERS,
            json={
                "trace_id": trace_id,
                "score": score,
                "comment": comment,
                "virtual_key": virtual_key,
                "source": "agent",
            },
        )
        r.raise_for_status()
        return r.json()


# ── Tool: check_budget ────────────────────────────────────────────────────

@mcp.tool()
async def check_budget(virtual_key: str) -> dict:
    """
    Check current spend, remaining budget, and reset time for a virtual key.

    Args:
        virtual_key: LiteLLM virtual key alias (e.g. 'langflow-prod')

    Returns:
        spend_usd, max_budget_usd, remaining_usd, budget_duration,
        reset_in_hours, tokens_used_total
    """
    async with httpx.AsyncClient(timeout=10) as client:
        # Get key info from LiteLLM
        r = await client.get(
            f"{GATEWAY_URL}/key/info",
            headers=HEADERS,
            params={"key": virtual_key},
        )
        r.raise_for_status()
        info = r.json().get("info", {})
        spend     = float(info.get("spend", 0))
        max_budget = float(info.get("max_budget", 0))
        return {
            "spend_usd":       round(spend, 4),
            "max_budget_usd":  round(max_budget, 4),
            "remaining_usd":   round(max(0, max_budget - spend), 4),
            "budget_duration": info.get("budget_duration"),
            "reset_in_hours":  info.get("budget_reset_at"),
            "tokens_used":     info.get("total_tokens", 0),
            "key_alias":       info.get("key_alias"),
        }


# ── Tool: translate ────────────────────────────────────────────────────────

@mcp.tool()
async def translate(
    text: str,
    target_lang: str = "en",
    source_lang: str = None,
) -> dict:
    """
    Translate text between languages using the local translation sidecar.

    Uses IndicTrans2 (MIT) for Indian languages, Opus-MT (Apache 2.0) for
    Arabic and Southeast Asian. Routes natively supported languages (Hindi,
    Tamil, Arabic etc.) through Qwen3 directly — no translation overhead.

    Args:
        text: Text to translate
        target_lang: ISO 639-1 target language code (e.g. 'en', 'hi', 'ta', 'ar')
        source_lang: ISO 639-1 source language (auto-detected if not provided)

    Returns:
        translated, src_lang, tgt_lang, needs_translation, native_model_sufficient
    """
    payload = {"text": text, "tgt_lang": target_lang}
    if source_lang:
        payload["src_lang"] = source_lang

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{TRANSLATOR_URL}/translate", json=payload)
        r.raise_for_status()
        return r.json()


# ── Tool: list_models ─────────────────────────────────────────────────────

@mcp.tool()
async def list_models() -> dict:
    """
    List all available model aliases on the gateway.

    Returns model IDs that can be used in chat completion calls.

    Returns:
        List of model aliases (e.g. ollama/qwen3:30b-a3b, gpt-4o, claude-3-5-sonnet)
    """
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{GATEWAY_URL}/v1/models", headers=HEADERS)
        r.raise_for_status()
        models = [m["id"] for m in r.json().get("data", [])]
        return {"models": models, "count": len(models)}


# ── Tool: get_spend_logs ──────────────────────────────────────────────────

@mcp.tool()
async def get_spend_logs(
    virtual_key: str = None,
    limit: int = 10,
) -> dict:
    """
    Get recent spend logs from the gateway.

    Args:
        virtual_key: Filter by key alias (optional — omit for all keys)
        limit: Number of log entries to return (default 10, max 100)

    Returns:
        List of {model, spend, total_tokens, request_id, timestamp}
    """
    params = {"limit": min(limit, 100)}
    if virtual_key:
        params["key_alias"] = virtual_key

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{GATEWAY_URL}/spend/logs",
            headers=HEADERS,
            params=params,
        )
        r.raise_for_status()
        logs = r.json()
        return {
            "logs": [
                {
                    "model":        entry.get("model"),
                    "spend":        entry.get("spend"),
                    "total_tokens": entry.get("total_tokens"),
                    "request_id":   entry.get("request_id"),
                    "timestamp":    entry.get("startTime"),
                }
                for entry in (logs if isinstance(logs, list) else [])
            ],
            "count": len(logs) if isinstance(logs, list) else 0,
        }


# ── Tool: create_virtual_key ──────────────────────────────────────────────

@mcp.tool()
async def create_virtual_key(
    key_alias: str,
    max_budget_usd: float = 10.0,
    budget_duration: str = "30d",
    models: list[str] = None,
    metadata: dict = None,
) -> dict:
    """
    Create a new scoped virtual key for a tenant or application.

    Args:
        key_alias: Human-readable alias (e.g. 'acme-prod', 'langflow-dev')
        max_budget_usd: Monthly budget limit in USD (default $10)
        budget_duration: Reset period — '1d', '7d', '30d' (default '30d')
        models: List of allowed model aliases (None = all models)
        metadata: Optional metadata dict (team, env, tenant_id, etc.)

    Returns:
        key (the virtual key value), key_alias, max_budget, budget_duration
    """
    payload = {
        "key_alias":       key_alias,
        "max_budget":      max_budget_usd,
        "budget_duration": budget_duration,
        "metadata":        metadata or {"created_by": "autonomyx-gateway-mcp"},
    }
    if models:
        payload["models"] = models

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{GATEWAY_URL}/key/generate",
            headers=HEADERS,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "key":             data.get("key"),
            "key_alias":       data.get("key_alias"),
            "max_budget":      data.get("max_budget"),
            "budget_duration": data.get("budget_duration"),
        }


# ── Tool: classify_task ───────────────────────────────────────────────────

@mcp.tool()
async def classify_task(text: str, top_n: int = 3) -> dict:
    """
    Classify the task type of a prompt using the local sentence-transformers classifier.

    Task types: chat, code, reason, summarise, extract, vision, long_context, agent

    Args:
        text: The prompt or task description to classify
        top_n: Number of top predictions to return (default 3)

    Returns:
        task, confidence, below_threshold, top_n predictions, threshold
    """
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.post(
            f"{CLASSIFIER_URL}/classify",
            json={"text": text[:2000], "top_n": top_n},
        )
        r.raise_for_status()
        return r.json()


# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")   # Claude Desktop / Claude Code
    # For HTTP: mcp.run(transport="sse", host="0.0.0.0", port=8300)
```

---

## `gateway_mcp/Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastmcp httpx
COPY server.py .
EXPOSE 8300
CMD ["python", "server.py"]
```

---

## docker-compose addition (Coolify)

```yaml
  gateway-mcp:
    build:
      context: ./gateway_mcp
    container_name: autonomyx-gateway-mcp
    restart: always
    networks:
      - coolify
    environment:
      - GATEWAY_URL=http://litellm:4000
      - TRANSLATOR_URL=http://translator:8200
      - CLASSIFIER_URL=http://classifier:8100
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
    # SSE transport for remote MCP clients
    command: ["python", "-c",
      "from server import mcp; mcp.run(transport='sse', host='0.0.0.0', port=8300)"]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gateway-mcp.rule=Host(`mcp.openautonomyx.com`)"
      - "traefik.http.routers.gateway-mcp.entrypoints=https"
      - "traefik.http.routers.gateway-mcp.tls.certresolver=letsencrypt"
      - "traefik.http.services.gateway-mcp.loadbalancer.server.port=8300"
```

---

## Claude Desktop config (`~/.claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "autonomyx-gateway": {
      "url": "https://mcp.openautonomyx.com/sse",
      "headers": {
        "Authorization": "Bearer YOUR_LITELLM_MASTER_KEY"
      }
    }
  }
}
```

---

## autonomyx-mcp registration (`config.yaml`)

```python
# In autonomyx-mcp FastMCP server — register gateway as a sub-server
from fastmcp import FastMCP, Client

gateway_client = Client("https://mcp.openautonomyx.com/sse")
mcp.mount("gateway", gateway_client)
```

---

## Env vars

```
# Gateway MCP Server
GATEWAY_MCP_PORT=8300
```
