#!/usr/bin/env bash
set -euo pipefail

cd /app

# Ждём Postgres ТОЛЬКО если указан DB_HOST
if [[ -n "${DB_HOST:-}" ]]; then
  echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT:-5432}..."
  for i in {1..60}; do
    if pg_isready -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" >/dev/null 2>&1; then
      echo "Postgres is up"; break
    fi
    sleep 1
  done
fi

echo "Apply migrations..."
python manage.py migrate --noinput

echo "Ensure superuser exists..."
python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ.get("DJANGO_SUPERUSER_USERNAME","admin")
e = os.environ.get("DJANGO_SUPERUSER_EMAIL","admin@example.com")
p = os.environ.get("DJANGO_SUPERUSER_PASSWORD","admin")
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(username=u, email=e, password=p)
    print(f"Created superuser {u}")
else:
    print(f"Superuser {u} already exists")
PY

echo "Run server..."
exec python manage.py runserver 0.0.0.0:8000
