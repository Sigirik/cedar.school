#!/usr/bin/env bash
set -euo pipefail

# 1) миграции
python manage.py migrate --noinput

# 2) проверка наличия данных:
# НЕ роняем скрипт — используем результат python в if/else.
if python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
import django; django.setup()
from schedule.template.models import TemplateWeek
import sys
# exit 0 => данные есть; exit 1 => данных нет
sys.exit(0 if TemplateWeek.objects.exists() else 1)
PY
then
  echo "[entrypoint] Data exists. Skipping seed."
else
  echo "[entrypoint] No data found. Loading seed/dev_seed.json..."
  python manage.py loaddata seed/dev_seed.json
fi

# 3) опционально: автосоздание суперпользователя через ENV
# DJ_CREATE_SUPERUSER=1 DJ_SUPERUSER_EMAIL=... DJ_SUPERUSER_PASSWORD=... [DJ_SUPERUSER_USERNAME=admin]
if [ "${DJ_CREATE_SUPERUSER:-0}" = "1" ]; then
  python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
import django; django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.getenv("DJ_SUPERUSER_EMAIL")
password = os.getenv("DJ_SUPERUSER_PASSWORD")
username = os.getenv("DJ_SUPERUSER_USERNAME","admin")
if email and password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("[entrypoint] Superuser created:", username)
else:
    print("[entrypoint] Superuser skipped")
PY
fi

# 4) запуск дев-сервера
python manage.py runserver 0.0.0.0:8000
