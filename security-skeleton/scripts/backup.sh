#!/usr/bin/env bash
# scripts/backup.sh
# PostgreSQL backup → timestamped gzip dump.
# Designed to run as persistent cron process in Docker.
#
# Usage (standalone):
#   chmod +x scripts/backup.sh
#   ./scripts/backup.sh
#
# As persistent cron (see docker-compose addition below):
#   docker-compose up backup-cron
#
# Backups saved to: ./backups/logoracle_YYYYMMDD_HHMMSS.sql.gz
# Retention: keeps last 7 days, deletes older

set -euo pipefail

# Load env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

DB_USER="${DB_USER:-logoracle}"
DB_PASS="${DB_PASS:?DB_PASS not set}"
DB_NAME="${DB_NAME:-logoracle}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETAIN_DAYS="${RETAIN_DAYS:-7}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTFILE="$BACKUP_DIR/logoracle_${TIMESTAMP}.sql.gz"

echo "$(date -u +%FT%TZ) [backup] Starting backup → $OUTFILE"

PGPASSWORD="$DB_PASS" pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --no-password \
  | gzip > "$OUTFILE"

SIZE=$(du -sh "$OUTFILE" | cut -f1)
echo "$(date -u +%FT%TZ) [backup] ✓ Done — $SIZE"

# Prune backups older than RETAIN_DAYS
find "$BACKUP_DIR" -name "logoracle_*.sql.gz" -mtime "+${RETAIN_DAYS}" -delete
REMAINING=$(ls "$BACKUP_DIR" | wc -l)
echo "$(date -u +%FT%TZ) [backup] Retained $REMAINING backup(s) (>${RETAIN_DAYS}d pruned)"
