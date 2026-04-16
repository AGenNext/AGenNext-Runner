# Deploy Runbook
# Exact commands for every step. Run in order.

# ══════════════════════════════════════════════════════════
# STEP 1 — SSH KEY
# ══════════════════════════════════════════════════════════

# Generate (if you don't have one):
ssh-keygen -t ed25519 -C "autonomyx-ci" -f ~/.ssh/autonomyx_ci -N ""

# Add public key to VPS (run from your local machine):
ssh-copy-id -i ~/.ssh/autonomyx_ci.pub root@51.75.251.56
# OR if only root password access:
cat ~/.ssh/autonomyx_ci.pub | ssh root@51.75.251.56 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Test SSH works:
ssh -i ~/.ssh/autonomyx_ci root@51.75.251.56 "echo OK"

# ══════════════════════════════════════════════════════════
# STEP 2 — GITHUB SECRETS (gh CLI — install at cli.github.com)
# ══════════════════════════════════════════════════════════

REPO="OpenAutonomyx/autonomyx-model-gateway"

# SSH private key (required — CI needs this to reach VPS)
gh secret set SSH_PRIVATE_KEY \
  --repo $REPO \
  < ~/.ssh/autonomyx_ci

# Docker Hub (required — CI pushes images here)
gh secret set DOCKERHUB_USERNAME --repo $REPO --body "thefractionalpm"
# Get token at: hub.docker.com → Account Settings → Personal Access Tokens
gh secret set DOCKERHUB_TOKEN --repo $REPO

# Auto-generated if absent — but set now so it persists across rebuilds
gh secret set FRP_TOKEN --repo $REPO --body "$(openssl rand -hex 32)"
gh secret set LITELLM_MASTER_KEY --repo $REPO --body "$(openssl rand -hex 32)"

# AI providers (optional — Ollama handles local models without these)
gh secret set GROQ_API_KEY --repo $REPO       # console.groq.com (free)
gh secret set ANTHROPIC_API_KEY --repo $REPO  # console.anthropic.com
gh secret set OPENAI_API_KEY --repo $REPO     # platform.openai.com

# Payments (skip until billing is needed)
# gh secret set RAZORPAY_KEY_ID --repo $REPO
# gh secret set STRIPE_SECRET_KEY --repo $REPO

# ══════════════════════════════════════════════════════════
# STEP 3 — DNS (at your DNS provider — Cloudflare, OVH, etc.)
# ══════════════════════════════════════════════════════════

# Wildcard (covers everything with one record):
# Type: A
# Name: *
# Value: 51.75.251.56
# TTL: 300

# OR per-subdomain if no wildcard:
# dockge.openautonomyx.com   A  51.75.251.56
# metrics.openautonomyx.com  A  51.75.251.56
# errors.openautonomyx.com   A  51.75.251.56
# flows.openautonomyx.com    A  51.75.251.56
# trust.openautonomyx.com    A  51.75.251.56
# llm.openautonomyx.com      A  51.75.251.56

# Verify DNS propagation:
dig +short dockge.openautonomyx.com
# Should return: 51.75.251.56

# ══════════════════════════════════════════════════════════
# STEP 4 — TRIGGER FIRST DEPLOY
# ══════════════════════════════════════════════════════════

cd /path/to/autonomyx-model-gateway
git commit --allow-empty -m "chore: trigger first deploy"
git push origin main

# Watch CI:
gh run watch --repo $REPO

# ══════════════════════════════════════════════════════════
# STEP 5 — POST-DEPLOY (one-time, after CI succeeds)
# ══════════════════════════════════════════════════════════

# 5a. Verify all services running
ssh root@51.75.251.56 "cd /home/ubuntu/autonomyx-model-gateway && docker compose ps"

# 5b. Get GlitchTip auth token (needed for uptime monitors)
# Visit: https://errors.openautonomyx.com → Profile → API Keys → Create
# Then:
gh secret set GLITCHTIP_AUTH_TOKEN --repo $REPO --body "YOUR_TOKEN"

# 5c. Migrate SurrealDB from cloud to self-hosted
ssh root@51.75.251.56 "cd /home/ubuntu/autonomyx-model-gateway && \
  export SURREAL_CLOUD_URL=your-cloud-url && \
  export SURREAL_CLOUD_PASS=your-cloud-pass && \
  bash scripts/migrate_surrealdb.sh"

# 5d. Rotate the Docker Hub PAT mentioned in docs/best-practices.md
# hub.docker.com → Account Settings → Security → Delete old token → New token

# 5e. frp tunnel — verify working
ssh root@51.75.251.56 "docker logs autonomyx-frpc --tail 20"
# Should see: "start proxy success" for each service

# 5f. Create Upptime status page repo
gh repo create OpenAutonomyx/status --public
# Push files from /mnt/user-data/outputs/autonomyx-status/ to it

# ══════════════════════════════════════════════════════════
# VERIFY EVERYTHING IS UP
# ══════════════════════════════════════════════════════════

# Gateway API
curl https://llm.openautonomyx.com/health

# Dockge (Docker UI)
open https://dockge.openautonomyx.com

# Grafana (metrics)
open https://metrics.openautonomyx.com

# GlitchTip (errors)
open https://errors.openautonomyx.com

# Langflow (workflows)
open https://flows.openautonomyx.com

# Trust centre
open https://trust.openautonomyx.com
