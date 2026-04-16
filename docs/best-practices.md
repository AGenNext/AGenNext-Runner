# Autonomyx Model Gateway — Engineering Best Practices & Guardrails

**Last updated:** April 16, 2026
**Scope:** All contributors to `openautonomyx/autonomyx-model-gateway`

---

## 1. The Golden Rule

> **Never push code you haven't run locally.**

Every broken CI run, every failed deploy, every production outage in this repo's history was caused by pushing untested code. The fix is always the same: run it locally first.

---

## 2. Before Every Push

Run the pre-push check script. No exceptions.

```bash
bash scripts/build-test.sh
```

This runs in 3-5 minutes and catches:
- Dockerfile syntax errors (hadolint)
- Docker image build failures
- Unit test regressions
- docker-compose.yml syntax errors
- Config validation failures

**If the script fails → fix it locally → re-run → only push when it passes.**

---

## 3. CI/CD Pipeline

### Pipeline order — each job gates the next

```
Push to main
  │
  ▼
Job 1: test (~2 min)
  ├── pytest — all unit tests
  ├── docker compose config --quiet
  └── hadolint — lint all Dockerfiles
  │   ← broken code STOPS HERE, server untouched
  ▼
Job 2: build (~10-15 min first run, ~3 min cached)
  ├── Build playwright image
  ├── Build classifier image
  ├── Build translator image
  └── Push all to Docker Hub with SHA tag + :latest
  │   ← broken Dockerfiles STOP HERE
  ▼
Job 3: deploy (~2 min)
  ├── SSH to server
  ├── git fetch + git reset --hard origin/main
  ├── docker compose pull (pre-built images)
  ├── docker compose up -d --remove-orphans
  └── Health check: poll /health every 5s for 60s
      ← failed deploy is visible immediately, logs printed
```

### Non-negotiable pipeline rules

- **deploy never runs if test or build fails** — `needs:` dependency enforced
- **deploy uses pre-built images** — never builds on the production server
- **health check is mandatory** — deploy job fails if gateway doesn't respond within 60s
- **git reset --hard** — server always matches repo, local changes on server are forbidden
- **SHA-tagged images** — every build is traceable and rollback-able

---

## 4. Docker & Dockerfile Rules

### Always use the official base image for complex dependencies

```dockerfile
# WRONG — installs browser dependencies manually, fails in CI
FROM python:3.12-slim
RUN playwright install chromium --with-deps  # ← exit code 1 in GitHub Actions

# RIGHT — official image has everything pre-installed
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble
```

**Rule:** If a tool has an official Docker image, use it as the base. Never reinstall what the official image already provides.

### Never use heredocs for Python in Dockerfiles

```dockerfile
# WRONG — Docker parses Python keywords as Dockerfile instructions
RUN python3 -c "
import urllib.request   # ← Docker sees 'import' as an unknown instruction
os.makedirs('/models')
"

# RIGHT — single line, no ambiguity
RUN python3 -c "import urllib.request, os; os.makedirs('/models', exist_ok=True)"
```

**Rule:** If a Python snippet is longer than one line, write it to a `.py` file and `COPY` + `RUN` it instead of using `-c`.

### Always pin image versions

```yaml
# WRONG
image: langflowai/langflow:latest   # breaks silently when upstream releases

# RIGHT
image: langflowai/langflow:1.0.19   # reproducible, auditable
```

**Pinned versions in this repo:**

| Image | Pinned version |
|---|---|
| `ghcr.io/berriai/litellm` | `main-stable` |
| `postgres` | `15.7-alpine` |
| `ollama/ollama` | `0.3.14` |
| `prom/prometheus` | `v2.53.0` |
| `grafana/grafana` | `11.1.0` |
| `langflowai/langflow` | `1.0.19` |
| `glitchtip/glitchtip` | `v6.0.10` |
| `redis` | `7.2-alpine` |

**Review schedule:** October 2026 for all images.

### Every service must have

- `container_name` — predictable naming, no random suffixes
- `restart: always` — auto-recovery on crash
- `networks: - coolify` — Coolify's Traefik can route to it
- `labels` — Traefik routing labels if publicly exposed, `traefik.enable=false` if internal
- `healthcheck` — for all databases and caches that other services depend on

---

## 5. Python Code Rules

### Never let a callback crash the host process

```python
# WRONG — an exception here crashes LiteLLM
def log_success_event(self, kwargs, response_obj, start_time, end_time):
    client.post(LAGO_URL, json=event)  # network error → LiteLLM dies

# RIGHT — always wrap in try/except, log and continue
def log_success_event(self, kwargs, response_obj, start_time, end_time):
    try:
        client.post(LAGO_URL, json=event)
    except Exception as e:
        print(f"[LagoCallback] Error: {e}")  # log and move on
```

**Rule:** Any code that runs as a side effect of a primary operation (billing callbacks, tracing, feedback) must never propagate exceptions.

### Write tests before pushing new Python files

Every `.py` file in the repo root must have a corresponding `tests/test_*.py`. Tests must pass locally before pushing.

**Current coverage:**

| File | Test file | Tests |
|---|---|---|
| `lago_callback.py` | `tests/test_lago_callback.py` | 6 |
| `recommender.py` | `tests/test_recommender.py` | 10 |
| `feedback.py` | `tests/test_feedback.py` | 6 |
| `config.yaml` | `tests/test_config.py` | 20+ |
| `docker-compose.yml` | `tests/test_config.py` | 20+ |

### Validate config files in tests

`config.yaml` and `docker-compose.yml` are code. Treat them as such:

- All models must have `model_name` and `litellm_params`
- API keys must use `os.environ/VAR` — never hardcoded
- NLLB-200 and SeamlessM4T are CC-BY-NC — must never appear
- `version:` attribute must not appear in docker-compose.yml (obsolete)

---

## 6. Secrets Management

### Never commit secrets

The following must never appear in any committed file:

- API keys (`sk-`, `gsk_`, `ghp_`, `dckr_pat_`)
- Passwords
- Private keys
- Service account JSON with real credentials

**`.gitignore` enforces:**
```
.env
vertex_key.json
*.pem
*.key
```

### `.env.example` rules

- Must contain every variable the stack needs
- Values must be placeholders (`YOUR_GROQ_API_KEY`) or generation commands
- Must never contain real values
- Tested in CI: `test_config.py::TestEnvExample::test_no_real_secrets_in_example`

### Rotate immediately if exposed

If a secret appears in a commit, in a chat, or in a log:
1. Rotate it immediately at the provider
2. Update `.env` on the server
3. Consider the old secret permanently compromised

**Keys exposed during this project that need rotation:**
- GitHub PAT `ghp_VFd6ng...` — rotate at github.com/settings/tokens
- GitHub PAT `ghp_iZCN7B...` — rotate at github.com/settings/tokens
- Docker Hub token `dckr_pat_gEyx...` — rotate at hub.docker.com/settings/security
- Groq key `gsk_lpaope...` — rotate at console.groq.com

---

## 7. Infrastructure Rules

### Never manually edit files on the production server

The server is managed by Git. The only source of truth is the repo.

```bash
# WRONG — editing docker-compose.yml on the server
nano /home/ubuntu/autonomyx-model-gateway/docker-compose.yml

# RIGHT — edit locally, push, let CI deploy
# Local edit → git push → CI runs → deploys automatically
```

If you manually edit a file on the server, the next deploy will overwrite it with `git reset --hard`. You will lose your changes.

### Never run `docker compose up --build` on the production server

Building on the server:
- Uses production RAM during build
- Is not reproducible
- Can fail mid-way leaving containers in inconsistent state
- Bypasses CI validation

Always build in CI, push to Docker Hub, pull on the server.

### The server `.env` file is the only thing you maintain manually on the server

```bash
# The ONLY thing you should ever do manually on the server:
nano /home/ubuntu/autonomyx-model-gateway/.env

# Everything else is managed by CI
```

Back up `.env` immediately after any change. Store it in a password manager. It is not in Git.

### Port allocation

| Port | Service | Exposed |
|---|---|---|
| 80/443 | Nginx → Coolify Traefik | Yes (public) |
| 4000 | LiteLLM | Via Traefik only |
| 7860 | Langflow | Via Traefik only |
| 8000 | GlitchTip | Via Traefik only |
| 8000 | Coolify | Via Nginx only |
| 9090 | Prometheus | Internal only |
| 3000 | Grafana | Via Traefik only |
| 11434 | Ollama | Internal only |
| 8100 | Classifier | Internal only |
| 8200 | Translator | Internal only |
| 8400 | Playwright | Internal only |
| 5432 | Postgres (multiple) | Internal only |
| 6379 | Redis (multiple) | Internal only |

**Rule:** Never expose internal ports (Ollama, Postgres, Redis, sidecars) to the public internet. Traefik handles all ingress.

---

## 8. Service Decision Log

Every new service added to the stack must be documented in `references/service-decision-log.md` with:

- Why this service was chosen over alternatives
- Licence (must be MIT, Apache 2.0, or AGPL-3.0 — CC-BY-NC is banned)
- RAM footprint
- Review date

**Banned licences:** CC-BY-NC (NLLB-200, SeamlessM4T). Detected automatically in `test_config.py`.

---

## 9. Adding a New Service Checklist

Before adding any new service to `docker-compose.yml`:

- [ ] Check licence — MIT/Apache/AGPL only
- [ ] Document in `references/service-decision-log.md`
- [ ] Pin image version — no `:latest`
- [ ] Add `container_name`, `restart: always`, `networks: - coolify`
- [ ] Add healthcheck if it's a database or cache
- [ ] Add Traefik labels if publicly exposed (`traefik.enable=false` if internal)
- [ ] Add required env vars to `.env.example` with placeholder values
- [ ] Add tests to `tests/test_config.py`
- [ ] Run `bash scripts/build-test.sh` — all tests must pass
- [ ] Add subdomain to DNS (covered by wildcard `*.openautonomyx.com`)
- [ ] Document in `references/service-decision-log.md`

---

## 10. URL Map

| Service | URL | Auth |
|---|---|---|
| Gateway API | `llm.openautonomyx.com` | Virtual Key |
| Langflow | `flows.openautonomyx.com` | Username/password |
| Langfuse | `traces.openautonomyx.com` | Username/password |
| Lago API | `billing.openautonomyx.com` | API key |
| Lago UI | `billing-ui.openautonomyx.com` | Username/password |
| Keycloak | `auth.openautonomyx.com` | Admin credentials |
| Grafana | `metrics.openautonomyx.com` | Username/password |
| GlitchTip | `errors.openautonomyx.com` | Username/password |
| MCP server | `mcp.openautonomyx.com` | Virtual Key |
| Coolify | `vps.openautonomyx.com` | Username/password |
| Website | `openautonomyx.com` | Public |

---

## 11. Lessons Learned (Incident Log)

| Date | Incident | Root cause | Fix | Prevention |
|---|---|---|---|---|
| Apr 16 2026 | Duplicate `container_name: autonomyx-playwright` | Two playwright services in compose file — old build-based + new image-based | Deleted old `playwright-scraper` block | `test_config.py` checks for duplicate container names |
| Apr 16 2026 | Translator Dockerfile heredoc error | Python code inside `RUN python3 -c "..."` multi-line block parsed as Dockerfile instructions | Collapsed to single line | hadolint in CI catches unknown instructions |
| Apr 16 2026 | Playwright `--with-deps` failure in CI | GitHub Actions runners don't have apt access needed for system browser deps | Switched to `mcr.microsoft.com/playwright/python:v1.49.0-noble` | hadolint + `scripts/build-test.sh` |
| Apr 16 2026 | Manual file edits on server conflicted with git pull | `docker-compose.yml` edited manually on server, then CI tried to pull | `git reset --hard origin/main` in deploy script | Policy: never manually edit files on server |
| Apr 16 2026 | CI ran old commit instead of latest | Workflow manually triggered on stale commit | Trigger on latest main | Always use "Run workflow" on branch `main`, not a specific commit |
| Apr 16 2026 | Deploy ran before build gate existed | Single-job pipeline, no test/build separation | Split into 3 jobs with `needs:` dependencies | Current pipeline enforces: test → build → deploy |

---

*This document is a living record. Add to the incident log every time something breaks.*
