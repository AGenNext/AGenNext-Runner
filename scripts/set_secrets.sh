#!/usr/bin/env bash
# scripts/set_secrets.sh
# Sets all GitHub Secrets using curl + GitHub API.
# No gh CLI needed — just curl, openssl, base64 (all on Mac by default).
#
# Usage:
#   chmod +x scripts/set_secrets.sh
#   ./scripts/set_secrets.sh
#
# You need a GitHub Personal Access Token with repo scope:
#   github.com → Settings → Developer settings →
#   Personal access tokens → Tokens (classic) → Generate new token
#   Scopes: check "repo" (includes secrets)

set -euo pipefail

REPO_OWNER="OpenAutonomyx"
REPO_NAME="autonomyx-model-gateway"
REPO="$REPO_OWNER/$REPO_NAME"
SSH_KEY="$HOME/.ssh/autonomyx_ci"
API="https://api.github.com"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Autonomyx — GitHub Secrets Setup                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Preflight checks ──────────────────────────────────────────────────────────
if [ ! -f "$SSH_KEY" ]; then
  echo "❌ SSH key not found at $SSH_KEY"
  echo "   Generate: ssh-keygen -t ed25519 -C autonomyx-ci -f ~/.ssh/autonomyx_ci -N ''"
  exit 1
fi

# ── GitHub token ──────────────────────────────────────────────────────────────
echo "  GitHub Personal Access Token (classic)"
echo "  Get at: github.com → Settings → Developer settings →"
echo "          Personal access tokens → Tokens (classic) →"
echo "          Generate new token → check 'repo' scope"
echo ""
read -rsp "  Paste GitHub token: " GITHUB_TOKEN
echo ""

# Verify token works
WHOAMI=$(curl -sf -H "Authorization: token $GITHUB_TOKEN" \
  "$API/user" | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])" 2>/dev/null || echo "")
if [ -z "$WHOAMI" ]; then
  echo "❌ GitHub token invalid or insufficient scope"
  exit 1
fi
echo "  ✅ Authenticated as: $WHOAMI"
echo ""

# ── Get repo public key for secret encryption ─────────────────────────────────
PUB_KEY_RESP=$(curl -sf \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "$API/repos/$REPO/actions/secrets/public-key")
PUB_KEY=$(echo "$PUB_KEY_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['key'])")
KEY_ID=$(echo "$PUB_KEY_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['key_id'])")

# ── Encrypt and set secret using Python (nacl/libsodium) ─────────────────────
set_secret() {
  local name="$1"
  local value="$2"
  if [ -z "$value" ]; then
    echo "  ⏭  $name — skipped"
    return
  fi

  # Encrypt using Python (PyNaCl or fallback to base64 for simple cases)
  ENCRYPTED=$(python3 - <<PYEOF
import base64, sys
from base64 import b64decode, b64encode

secret_value = """$value"""
public_key_b64 = "$PUB_KEY"

try:
    from nacl import encoding, public
    public_key = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    print(b64encode(encrypted).decode())
except ImportError:
    # nacl not available — install it
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyNaCl', '-q'])
    from nacl import encoding, public
    public_key = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    print(b64encode(encrypted).decode())
PYEOF
)

  HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "$API/repos/$REPO/actions/secrets/$name" \
    -d "{\"encrypted_value\":\"$ENCRYPTED\",\"key_id\":\"$KEY_ID\"}")

  if [ "$HTTP" = "201" ] || [ "$HTTP" = "204" ]; then
    echo "  ✅ $name"
  else
    echo "  ❌ $name — HTTP $HTTP"
  fi
}

prompt_secret() {
  local name="$1"
  local hint="$2"
  echo ""
  echo "  $name"
  echo "  $hint"
  read -rsp "  Value (paste, Enter to skip): " value
  echo ""
  set_secret "$name" "$value"
}

# ── Set secrets ───────────────────────────────────────────────────────────────
echo "── Required secrets ─────────────────────────────────────"

# SSH key — read from file
SSH_KEY_CONTENT=$(cat "$SSH_KEY")
set_secret "SSH_PRIVATE_KEY" "$SSH_KEY_CONTENT"

# Docker Hub username
set_secret "DOCKERHUB_USERNAME" "thefractionalpm"

# Docker Hub token
prompt_secret "DOCKERHUB_TOKEN" \
  "hub.docker.com → Account Settings → Personal Access Tokens → New token (Read & Write)"

# Auto-generate
set_secret "FRP_TOKEN" "$(openssl rand -hex 32)"
set_secret "LITELLM_MASTER_KEY" "$(openssl rand -hex 32)"

echo ""
echo "── AI provider keys ─────────────────────────────────────"

prompt_secret "ANTHROPIC_API_KEY" \
  "console.anthropic.com → API Keys"

prompt_secret "GROQ_API_KEY" \
  "console.groq.com → API Keys (free tier available)"

echo ""
echo "── Optional — press Enter to skip ───────────────────────"

prompt_secret "OPENAI_API_KEY"     "platform.openai.com → API Keys"
prompt_secret "VERTEX_PROJECT_ID"  "Google Cloud project ID"
prompt_secret "RAZORPAY_KEY_ID"    "Razorpay (billing — skip for now)"
prompt_secret "STRIPE_SECRET_KEY"  "Stripe (billing — skip for now)"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "── Secrets set in $REPO ─────────────"
curl -sf \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "$API/repos/$REPO/actions/secrets" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Total: {d[\"total_count\"]} secrets')
for s in d['secrets']:
    print(f'  ✅ {s[\"name\"]}')
"

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  Trigger first deploy:"
echo ""
echo "  cd autonomyx-model-gateway"
echo "  git commit --allow-empty -m 'chore: first deploy'"
echo "  git push origin main"
echo "══════════════════════════════════════════════════════════"
