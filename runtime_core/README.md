# AGenNext Runtime Core (MVP)

This is a first-party runtime MVP that standardizes lifecycle behavior across external runtimes.

## Endpoints

- `POST /runtime/init`
- `POST /runtime/{session_id}/invoke`
- `GET /runtime/{session_id}/stream`
- `POST /runtime/{session_id}/close`
- `GET /health`

## Run

```bash
uvicorn runtime_core.main:app --host 0.0.0.0 --port 8081 --reload
```

## Goals

- consistent cross-runtime lifecycle semantics
- kernel-native observability events with correlation IDs
- compliance-oriented event traces for auditability
