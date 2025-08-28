#!/usr/bin/env bash
set -e

# Ждём БД
python - <<'PY'
import os, time, psycopg2
host = os.getenv("DB_HOST","db")
port = int(os.getenv("DB_PORT","5432"))
user = os.getenv("POSTGRES_USER","cedar")
password = os.getenv("POSTGRES_PASSWORD","cedar")
dbname = os.getenv("POSTGRES_DB","cedar")
for _ in range(30):
    try:
        psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname).close()
        break
    except Exception:
        time.sleep(1)
PY

# Миграции (идемпотентно)
python manage.py migrate --noinput

# Создаём суперпользователя, если его нет (идемпотентно)
if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
  python - <<'PY'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ["DJANGO_SUPERUSER_USERNAME"]
e = os.environ.get("DJANGO_SUPERUSER_EMAIL","admin@example.com")
p = os.environ["DJANGO_SUPERUSER_PASSWORD"]
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(username=u, email=e, password=p)
    print(f"[entrypoint] Superuser '{u}' created")
else:
    print(f"[entrypoint] Superuser '{u}' already exists")
PY
fi

# Запуск dev-сервера (или gunicorn — как удобно)
python manage.py runserver 0.0.0.0:8000
