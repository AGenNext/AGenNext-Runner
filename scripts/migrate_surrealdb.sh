#!/usr/bin/env bash
# migrate_surrealdb.sh — Migrate SurrealDB from cloud to self-hosted
#
# Usage:
#   chmod +x migrate_surrealdb.sh
#   ./migrate_surrealdb.sh
#
# Pre-requisites:
#   1. Self-hosted SurrealDB container is running:
#      docker compose up -d surrealdb
#   2. Cloud credentials in environment:
#      export SURREAL_CLOUD_URL=https://schemadb-06ehsj292ppah8kbsk9pmnjjbc.aws-aps1.surreal.cloud
#      export SURREAL_CLOUD_USER=root
#      export SURREAL_CLOUD_PASS=<your-cloud-pass>
#   3. Local credentials in environment:
#      export SURREAL_USER=root
#      export SURREAL_PASS=<your-local-pass>

set -euo pipefail

CLOUD_URL="${SURREAL_CLOUD_URL:-}"
CLOUD_USER="${SURREAL_CLOUD_USER:-root}"
CLOUD_PASS="${SURREAL_CLOUD_PASS:-}"
LOCAL_URL="http://localhost:8000"
LOCAL_USER="${SURREAL_USER:-root}"
LOCAL_PASS="${SURREAL_PASS:-}"
BACKUP_DIR="./backup/surrealdb_$(date +%Y%m%d_%H%M%S)"
EXPORT_FILE="${BACKUP_DIR}/export.surql"

# Namespaces and databases to migrate
# Format: "namespace:database"
NAMESPACES=(
  "autonomyx:schema"
  "autonomyx:agents"
  "autonomyx:skills"
)

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     SurrealDB Cloud → Self-Hosted Migration              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Validation ───────────────────────────────────────────────────────────────

if [[ -z "$CLOUD_URL" ]]; then
  echo "❌ SURREAL_CLOUD_URL not set. Export SURREAL_CLOUD_URL=https://..."
  exit 1
fi
if [[ -z "$CLOUD_PASS" ]]; then
  echo "❌ SURREAL_CLOUD_PASS not set."
  exit 1
fi
if [[ -z "$LOCAL_PASS" ]]; then
  echo "❌ SURREAL_PASS not set."
  exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "📁 Backup dir: $BACKUP_DIR"
echo ""

# ── Step 1: Check self-hosted is running ─────────────────────────────────────

echo "Step 1/5 — Verifying self-hosted SurrealDB..."
if ! docker exec autonomyx-surrealdb /surreal is-ready --conn http://localhost:8000 2>/dev/null; then
  echo "❌ Self-hosted SurrealDB not ready. Run: docker compose up -d surrealdb"
  exit 1
fi
echo "✅ Self-hosted SurrealDB is ready"
echo ""

# ── Step 2: Export from cloud ────────────────────────────────────────────────

echo "Step 2/5 — Exporting from cloud..."
for NS_DB in "${NAMESPACES[@]}"; do
  NS="${NS_DB%%:*}"
  DB="${NS_DB##*:}"
  OUTFILE="${BACKUP_DIR}/${NS}_${DB}.surql"

  echo "  Exporting ns=${NS} db=${DB}..."
  curl -sS \
    --user "${CLOUD_USER}:${CLOUD_PASS}" \
    -H "surreal-ns: ${NS}" \
    -H "surreal-db: ${DB}" \
    "${CLOUD_URL}/export" \
    -o "$OUTFILE"

  if [[ -s "$OUTFILE" ]]; then
    LINES=$(wc -l < "$OUTFILE")
    echo "  ✅ Exported ${LINES} lines → ${OUTFILE}"
  else
    echo "  ⚠️  Empty export for ${NS}:${DB} — may not exist on cloud yet"
    rm -f "$OUTFILE"
  fi
done
echo ""

# ── Step 3: Import to self-hosted ────────────────────────────────────────────

echo "Step 3/5 — Importing to self-hosted..."
for NS_DB in "${NAMESPACES[@]}"; do
  NS="${NS_DB%%:*}"
  DB="${NS_DB##*:}"
  INFILE="${BACKUP_DIR}/${NS}_${DB}.surql"

  if [[ ! -f "$INFILE" ]]; then
    echo "  ⏭  Skipping ${NS}:${DB} — no export file"
    continue
  fi

  echo "  Importing ns=${NS} db=${DB}..."
  HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST \
    --user "${LOCAL_USER}:${LOCAL_PASS}" \
    -H "surreal-ns: ${NS}" \
    -H "surreal-db: ${DB}" \
    -H "Accept: application/json" \
    --data-binary "@${INFILE}" \
    "${LOCAL_URL}/import")

  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "  ✅ Imported ${NS}:${DB}"
  else
    echo "  ❌ Import failed for ${NS}:${DB} — HTTP ${HTTP_CODE}"
    exit 1
  fi
done
echo ""

# ── Step 4: Verify record counts ────────────────────────────────────────────

echo "Step 4/5 — Verifying record counts..."
for NS_DB in "${NAMESPACES[@]}"; do
  NS="${NS_DB%%:*}"
  DB="${NS_DB##*:}"

  # Count tables in each DB on cloud vs local
  CLOUD_TABLES=$(curl -sS \
    --user "${CLOUD_USER}:${CLOUD_PASS}" \
    -H "surreal-ns: ${NS}" \
    -H "surreal-db: ${DB}" \
    -H "Accept: application/json" \
    -X POST \
    --data "INFO FOR DB;" \
    "${CLOUD_URL}/sql" 2>/dev/null | python3 -c "
import sys,json
try:
  r=json.load(sys.stdin)
  t=r[0].get('result',{}).get('tables',{})
  print(len(t))
except: print('?')
" 2>/dev/null || echo "?")

  LOCAL_TABLES=$(curl -sS \
    --user "${LOCAL_USER}:${LOCAL_PASS}" \
    -H "surreal-ns: ${NS}" \
    -H "surreal-db: ${DB}" \
    -H "Accept: application/json" \
    -X POST \
    --data "INFO FOR DB;" \
    "${LOCAL_URL}/sql" 2>/dev/null | python3 -c "
import sys,json
try:
  r=json.load(sys.stdin)
  t=r[0].get('result',{}).get('tables',{})
  print(len(t))
except: print('?')
" 2>/dev/null || echo "?")

  STATUS="✅"
  [[ "$CLOUD_TABLES" != "$LOCAL_TABLES" ]] && STATUS="⚠️ "
  echo "  ${STATUS} ${NS}:${DB} — cloud: ${CLOUD_TABLES} tables, local: ${LOCAL_TABLES} tables"
done
echo ""

# ── Step 5: Update SURREAL_URL ───────────────────────────────────────────────

echo "Step 5/5 — Next steps:"
echo ""
echo "  1. Update .env on server:"
echo "     SURREAL_URL=http://surrealdb:8000"
echo "     (remove or comment out SURREAL_URL_CLOUD)"
echo ""
echo "  2. Restart services that use SurrealDB:"
echo "     docker compose restart litellm langflow"
echo ""
echo "  3. Verify connectivity from LiteLLM container:"
echo "     docker exec autonomyx-litellm curl -s http://surrealdb:8000/health"
echo ""
echo "  4. Once confirmed working, revoke cloud credentials at:"
echo "     https://surrealist.app → Cloud → Settings → Access keys"
echo ""
echo "✅ Migration complete. Backup stored at: ${BACKUP_DIR}"
