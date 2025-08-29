import os, sys, django
from pathlib import Path

# гарантируем, что корень проекта в sys.path
BASE_DIR = Path(__file__).resolve().parent.parent  # /app
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

u = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
e = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
p = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")

obj, created = User.objects.get_or_create(username=u, defaults={"email": e})
if created:
    obj.is_superuser = True
    obj.is_staff = True
    obj.set_password(p)
    obj.save()
    print(f"[init_superuser] Created superuser {u}")
else:
    print(f"[init_superuser] Superuser {u} already exists")



