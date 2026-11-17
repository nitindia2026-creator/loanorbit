#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/opt/loanorbit/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/loanorbit_backup_${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

echo "📦 Creating LOANORBIT Database & Private Document Archive..."

# 1. Dump PostgreSQL database inside container
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-loanorbit_user}" "${POSTGRES_DB:-loanorbit_db}" > "/tmp/db_${TIMESTAMP}.sql"

# 2. Package database dump and private documents together
tar -czf "${BACKUP_FILE}" \
    -C /tmp "db_${TIMESTAMP}.sql" \
    -C /opt/loanorbit/storage private

# Cleanup temporary dump
rm -f "/tmp/db_${TIMESTAMP}.sql"

echo "✅ Backup successfully created at: ${BACKUP_FILE}"

# 3. Maintain rolling 7-day retention (prune older backups)
find "${BACKUP_DIR}" -name "loanorbit_backup_*.tar.gz" -mtime +7 -delete
echo "🧹 Pruned backups older than 7 days."
