# Langflow Agent — Autonomyx LLM Gateway

## Role

A Langflow flow template that uses the gateway as its LLM backend.
Implements intelligent model routing — calls `/recommend` before every LLM call,
routes to the recommended model, captures user feedback, logs traces to Langfuse.

Customers import this flow as a starting point for their AI workflows.

---

## Flow architecture

```
User message
  │
  ▼
[Language Detection]         ← HTTP → /translate (detect_only=true)
  │
  ├─ Non-English → [Translate Input] ← HTTP → /translate
  │
  ▼
[Task Classifier]            ← HTTP → /classify
  │
  ▼
[Model Recommender]          ← HTTP → /recommend
  │ returns: best_model_alias
  ▼
[LLM Call]                   ← OpenAI-compatible → gateway /v1/chat/completions
  │ using recommended model alias
  ├─ trace_id captured from response.id
  │
  ├─ Non-English → [Translate Output] ← HTTP → /translate
  │
  ▼
[Response to user]
  │
  ▼
[Feedback Widget]            ← async → /feedback (thumbs up/down)
```

---

## Flow JSON (importable into Langflow)

```json
{
  "name": "Autonomyx Gateway Agent",
  "description": "Intelligent LLM routing via Autonomyx Gateway. Auto-selects best model per task, captures feedback, handles multilingual input/output.",
  "nodes": [

    {
      "id": "input-1",
      "type": "ChatInput",
      "data": {
        "display_name": "User Message",
        "output_key": "message"
      },
      "position": {"x": 100, "y": 300}
    },

    {
      "id": "http-detect-lang",
      "type": "HTTPRequest",
      "data": {
        "display_name": "Detect Language",
        "url": "{GATEWAY_URL}/translate",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body_template": "{\"text\": \"{input.message[:200]}\", \"detect_only\": true}",
        "output_key": "lang_detection"
      },
      "position": {"x": 350, "y": 200}
    },

    {
      "id": "http-translate-in",
      "type": "HTTPRequest",
      "data": {
        "display_name": "Translate Input → EN",
        "url": "{GATEWAY_URL}/translate",
        "method": "POST",
        "condition": "{lang_detection.src_lang} != 'en' and not {lang_detection.native_model_sufficient}",
        "body_template": "{\"text\": \"{input.message}\", \"tgt_lang\": \"en\"}",
        "output_key": "translated_input"
      },
      "position": {"x": 350, "y": 350}
    },

    {
      "id": "http-recommend",
      "type": "HTTPRequest",
      "data": {
        "display_name": "Recommend Model",
        "url": "{GATEWAY_URL}/recommend",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer {VIRTUAL_KEY}"
        },
        "body_template": "{\"prompt\": \"{translated_input.translated or input.message}\", \"virtual_key\": \"{VIRTUAL_KEY}\", \"top_n\": 1}",
        "output_key": "recommendation"
      },
      "position": {"x": 600, "y": 300}
    },

    {
      "id": "llm-call",
      "type": "OpenAIModel",
      "data": {
        "display_name": "LLM (via Gateway)",
        "openai_api_base": "{GATEWAY_URL}/v1",
        "openai_api_key": "{VIRTUAL_KEY}",
        "model_name": "{recommendation.recommendations[0].alias}",
        "temperature": 0.7,
        "output_key": "llm_response"
      },
      "position": {"x": 850, "y": 300}
    },

    {
      "id": "http-translate-out",
      "type": "HTTPRequest",
      "data": {
        "display_name": "Translate Output → Original Lang",
        "url": "{GATEWAY_URL}/translate",
        "method": "POST",
        "condition": "{lang_detection.src_lang} != 'en' and not {lang_detection.native_model_sufficient}",
        "body_template": "{\"text\": \"{llm_response.content}\", \"src_lang\": \"en\", \"tgt_lang\": \"{lang_detection.src_lang}\"}",
        "output_key": "translated_output"
      },
      "position": {"x": 1100, "y": 300}
    },

    {
      "id": "output-1",
      "type": "ChatOutput",
      "data": {
        "display_name": "Response",
        "input_key": "translated_output.translated or llm_response.content"
      },
      "position": {"x": 1350, "y": 300}
    },

    {
      "id": "http-feedback",
      "type": "HTTPRequest",
      "data": {
        "display_name": "Capture Feedback (async)",
        "url": "{GATEWAY_URL}/feedback",
        "method": "POST",
        "async": true,
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer {VIRTUAL_KEY}"
        },
        "body_template": "{\"trace_id\": \"{llm_response.id}\", \"score\": {user_feedback_score}, \"virtual_key\": \"{VIRTUAL_KEY}\", \"source\": \"langflow\"}",
        "output_key": "feedback_result"
      },
      "position": {"x": 1350, "y": 450}
    }

  ],

  "edges": [
    {"source": "input-1",          "target": "http-detect-lang"},
    {"source": "http-detect-lang", "target": "http-translate-in"},
    {"source": "http-detect-lang", "target": "http-recommend"},
    {"source": "http-translate-in","target": "http-recommend"},
    {"source": "http-recommend",   "target": "llm-call"},
    {"source": "llm-call",         "target": "http-translate-out"},
    {"source": "llm-call",         "target": "http-feedback"},
    {"source": "http-translate-out","target": "output-1"}
  ],

  "variables": {
    "GATEWAY_URL": "http://litellm:4000",
    "VIRTUAL_KEY": "sk-autonomyx-YOUR-KEY-HERE"
  }
}
```

---

## Setting up the Langflow flow

### 1. Import the flow

```bash
# Via Langflow API
curl -X POST http://langflow:7860/api/v1/flows/ \
  -H "Content-Type: application/json" \
  -d @langflow-gateway-agent.json
```

Or via Langflow UI: **Flows → Import → Upload JSON**

### 2. Set environment variables in Langflow

```bash
# In Langflow .env or docker-compose
GATEWAY_URL=http://litellm:4000
VIRTUAL_KEY=sk-autonomyx-langflow-prod
```

### 3. Test the flow

```bash
curl -X POST http://langflow:7860/api/v1/run/{FLOW_ID} \
  -H "Content-Type: application/json" \
  -d '{"input_value": "Write a Python function to validate Indian PAN card numbers"}'
```

Expected behaviour:
1. Language detected as English
2. Task classified as `code`
3. Model recommended: `ollama/qwen2.5-coder:32b` (always-on, best code model)
4. LLM call routed to Qwen2.5-Coder-32B via gateway
5. Response returned
6. Feedback endpoint receives trace_id for later scoring

---

## Variant flows

### Variant A: Code assistant (simplified)

```python
# Langflow Python component — replaces full flow for code-only use cases

from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema.message import Message
import httpx

class GatewayCodeAssistant(Component):
    display_name = "Autonomyx Code Assistant"
    description  = "Routes code tasks to Qwen2.5-Coder-32B via gateway"

    inputs = [MessageTextInput(name="user_message", display_name="Code Request")]
    outputs = [Output(name="response", display_name="Code Response", method="generate")]

    GATEWAY_URL  = "http://litellm:4000"
    VIRTUAL_KEY  = "sk-autonomyx-langflow-prod"

    def generate(self) -> Message:
        prompt = self.user_message.text

        # Always use code model — skip recommender for code-specific flows
        response = httpx.post(
            f"{self.GATEWAY_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.VIRTUAL_KEY}"},
            json={
                "model": "ollama/qwen2.5-coder:32b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,   # low temp for code
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return Message(text=content)
```

### Variant B: RAG-enhanced agent

Adds SurrealDB vector retrieval before LLM call:

```
User message
  → Language detect
  → Embed query (nomic-embed-text via Ollama)
  → SurrealDB vector search (tenant-scoped collection)
  → Prepend retrieved chunks to prompt
  → Recommend model
  → LLM call with enriched context
  → Feedback capture
```

### Variant C: Multi-turn memory agent

```python
# Langflow Memory component — maintains conversation history

class GatewayMemoryAgent(Component):
    def __init__(self):
        self.history = []

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        # Recommend model based on full conversation context
        context = " ".join(m["content"] for m in self.history[-3:])
        rec = httpx.post(f"{GATEWAY_URL}/recommend",
            headers={"Authorization": f"Bearer {VIRTUAL_KEY}"},
            json={"prompt": context, "virtual_key": VIRTUAL_KEY, "top_n": 1})
        model = rec.json()["recommendations"][0]["alias"]

        # Call with full history
        resp = httpx.post(f"{GATEWAY_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {VIRTUAL_KEY}"},
            json={"model": model, "messages": self.history})
        reply = resp.json()["choices"][0]["message"]["content"]
        self.history.append({"role": "assistant", "content": reply})
        return reply
```

---

## Deploying as a customer-facing template

### Package for customer distribution

```bash
# Export flow with variables blanked out
curl -X GET http://langflow:7860/api/v1/flows/{FLOW_ID}/export \
  -H "Authorization: Bearer $LANGFLOW_TOKEN" \
  > autonomyx-gateway-agent-template.json

# Customer imports and fills in their VIRTUAL_KEY
```

### Customer onboarding step

Add to `kc_lago_sync.py` GROUP_CREATE handler:

```python
async def provision_langflow_flow(group_id: str, virtual_key: str):
    """
    Clone the gateway agent template for a new tenant.
    Set their virtual key in the flow variables.
    """
    # Get template flow
    template = httpx.get(f"{LANGFLOW_URL}/api/v1/flows/template-id")
    flow = template.json()

    # Inject tenant's virtual key
    flow["variables"]["VIRTUAL_KEY"] = virtual_key
    flow["name"] = f"Gateway Agent — {group_id}"

    # Create tenant's flow
    httpx.post(
        f"{LANGFLOW_URL}/api/v1/flows/",
        json=flow,
        headers={"x-tenant-id": group_id},
    )
```

---

## Env vars

```
# Langflow Agent
LANGFLOW_GATEWAY_URL=http://litellm:4000
LANGFLOW_VIRTUAL_KEY=sk-autonomyx-langflow-prod
LANGFLOW_TEMPLATE_FLOW_ID=YOUR_TEMPLATE_FLOW_ID
```
