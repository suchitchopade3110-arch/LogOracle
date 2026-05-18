#!/usr/bin/env bash
# scripts/vault_seed.sh
# Seeds Vault KV-v2 with LogOracle secrets.
# Run ONCE after first docker-compose up.
# After seeding: set VAULT_REQUIRED=true in .env and restart app.
#
# Usage:
#   chmod +x scripts/vault_seed.sh
#   ./scripts/vault_seed.sh

set -euo pipefail

# Load env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:?VAULT_TOKEN not set in .env}"

echo "🔐 Seeding Vault at $VAULT_ADDR ..."

# Wait for Vault to be ready
for i in {1..10}; do
  if curl -sf "$VAULT_ADDR/v1/sys/health" > /dev/null 2>&1; then
    break
  fi
  echo "  Waiting for Vault... ($i/10)"
  sleep 2
done

# Enable KV-v2 secrets engine (idempotent)
curl -sf \
  --header "X-Vault-Token: $VAULT_TOKEN" \
  --request POST \
  --data '{"type":"kv","options":{"version":"2"}}' \
  "$VAULT_ADDR/v1/sys/mounts/secret" > /dev/null 2>&1 || true

echo "  ✓ KV-v2 engine ready"

# Helper: write secret
vault_write() {
  local path="$1"
  local data="$2"
  curl -sf \
    --header "X-Vault-Token: $VAULT_TOKEN" \
    --request POST \
    --data "$data" \
    "$VAULT_ADDR/v1/secret/data/$path" > /dev/null
  echo "  ✓ Written: $path"
}

# Seed secrets
vault_write "logoracle/groq" \
  "{\"data\":{\"api_key\":\"${GROQ_API_KEY:-}\"}}"

vault_write "logoracle/db" \
  "{\"data\":{\"user\":\"${DB_USER:-logoracle}\",\"pass\":\"${DB_PASS:-}\",\"name\":\"${DB_NAME:-logoracle}\",\"host\":\"${DB_HOST:-db}\",\"port\":\"${DB_PORT:-5432}\"}}"

vault_write "logoracle/redis" \
  "{\"data\":{\"pass\":\"${REDIS_PASS:-}\",\"url\":\"${REDIS_URL:-redis://:${REDIS_PASS:-}@redis:6379}\"}}"

vault_write "logoracle/app" \
  "{\"data\":{\"api_key\":\"${API_KEY:-}\",\"jwt_secret\":\"${JWT_SECRET:-}\",\"encryption_key\":\"${ENCRYPTION_KEY:-}\",\"backup_encryption_key\":\"${BACKUP_ENCRYPTION_KEY:-}\",\"slack_security_webhook\":\"${SLACK_SECURITY_WEBHOOK:-}\"}}"

echo ""
echo "✅ Vault seeded. Next steps:"
echo "   1. Set VAULT_REQUIRED=true in .env"
echo "   2. docker-compose restart app"
echo "   3. Verify: curl -H 'X-Vault-Token: \$VAULT_TOKEN' \$VAULT_ADDR/v1/secret/data/logoracle/groq"
