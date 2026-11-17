#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_backup_archive.tar.gz>"
    exit 1
fi

BACKUP_ARCHIVE="$1"

if [ ! -f "${BACKUP_ARCHIVE}" ]; then
    echo "❌ Error: Backup file not found at ${BACKUP_ARCHIVE}"
    exit 1
fi

echo "⚠️  Restoring LOANORBIT from archive: ${BACKUP_ARCHIVE}"

TEMP_RESTORE_DIR=$(mktemp -d)
tar -xzf "${BACKUP_ARCHIVE}" -C "${TEMP_RESTORE_DIR}"

# 1. Restore PostgreSQL Database
SQL_DUMP=$(find "${TEMP_RESTORE_DIR}" -name "db_*.sql" | head -n 1)
if [ -f "${SQL_DUMP}" ]; then
    echo "🔄 Restoring PostgreSQL relational state..."
    docker compose exec -T postgres psql -U "${POSTGRES_USER:-loanorbit_user}" -d "${POSTGRES_DB:-loanorbit_db}" < "${SQL_DUMP}"
fi

# 2. Restore Private Documents
if [ -d "${TEMP_RESTORE_DIR}/private" ]; then
    echo "🔄 Restoring private documents..."
    cp -r "${TEMP_RESTORE_DIR}/private/"* /opt/loanorbit/storage/private/
fi

rm -rf "${TEMP_RESTORE_DIR}"
echo "🎉 Restoration completed successfully!"
