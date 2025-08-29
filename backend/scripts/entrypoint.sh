#!/usr/bin/env bash
set -Eeuo pipefail
cd /app
export PYTHONPATH="/app:${PYTHONPATH:-}"
# Подождать БД, если задан DB_HOST (как у вас было)
if [[ -n "${DB_HOST:-}" ]]; then
  echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT:-5432}..."
  for i in {1..60}; do
    if pg_isready -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" >/dev/null 2>&1; then
      echo "Postgres is up"; break
    fi
    sleep 1
  done
  if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" >/dev/null 2>&1; then
    echo "Postgres not reachable after 60s"; exit 1
  fi
fi

echo "Apply migrations..."
python manage.py migrate --noinput

if [[ "${SKIP_SUPERUSER:-0}" != "1" ]]; then
  echo "Ensure superuser exists..."
  python scripts/init_superuser.py
fi

if [[ "${DJANGO_COLLECTSTATIC:-0}" == "1" ]]; then
  echo "Collect static..."
  python manage.py collectstatic --noinput || true
fi

echo "Run: $*"
exec "$@"




