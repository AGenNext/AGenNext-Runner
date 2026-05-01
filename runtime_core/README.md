# AGenNext Runtime Core (MVP)

A first-party runtime service that standardizes lifecycle semantics across external runtimes with kernel-native observability and idempotent invokes.

## Features

- **Standardized Lifecycle**: `init` → `invoke` → `stream` → `close`
- **Idempotent Invokes**: Cache results with `X-Idempotency-Key` header
- **Payload Limits**: Configurable via `RUNTIME_MAX_PAYLOAD_KEYS` env var
- **Event Streaming**: Real-time session event history
- **API Key Auth**: Optional via `RUNTIME_API_KEY` and `X-Api-Key` header

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Session/event counts |
| POST | `/runtime/init` | Create new session |
| POST | `/runtime/{session_id}/invoke` | Invoke action |
| GET | `/runtime/{session_id}/stream` | Stream events |
| POST | `/runtime/{session_id}/close` | Close session |

## Run

```bash
cd runtime_core
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

## Environment Variables

| Variable | Default | Description |
|----------|--------|-------------|
| `RUNTIME_MAX_PAYLOAD_KEYS` | 256 | Max payload keys per request |
| `RUNTIME_API_KEY` | - | Optional API key for auth |

## Example Usage

```bash
# Initialize session
curl -X POST http://localhost:8081/runtime/init \
  -H "Content-Type: application/json" \
  -d '{"runtime": "python", "config": {"version": "3.11"}}'

# Invoke action (with idempotency)
curl -X POST http://localhost:8081/runtime/{session_id}/invoke \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: unique-key-123" \
  -d '{"action": "execute", "payload": {"code": "print(1+1)"}}'

# Stream events
curl http://localhost:8081/runtime/{session_id}/stream

# Close session
curl -X POST http://localhost:8081/runtime/{session_id}/close
```

## Goals

- Consistent cross-runtime lifecycle semantics
- Kernel-native observability events with correlation IDs
- Compliance-oriented event traces for auditability
