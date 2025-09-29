#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="/opt/backups/postgres"
DATE=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$BACKUP_ROOT/beta" "$BACKUP_ROOT/prod"

# Beta
docker exec cedar-pg-beta sh -lc "pg_dump -U \"${POSTGRES_USER}\" \"${POSTGRES_DB}\"" \
  > "${BACKUP_ROOT}/beta/cedar_beta_${DATE}.sql"

# Prod
docker exec cedar-pg-prod sh -lc "pg_dump -U \"${POSTGRES_USER}\" \"${POSTGRES_DB}\"" \
  > "${BACKUP_ROOT}/prod/cedar_prod_${DATE}.sql"

# очистка старше 14 дней
find "${BACKUP_ROOT}/beta" -type f -mtime +14 -delete || true
find "${BACKUP_ROOT}/prod" -type f -mtime +14 -delete || true
