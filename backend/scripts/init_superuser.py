import os, django
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

