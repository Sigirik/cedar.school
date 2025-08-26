# users/management/commands/ensure_admin.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create or fix an admin user with role=ADMIN (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="Admin")
        parser.add_argument("--password", default="Admin123!")
        parser.add_argument("--email", default="admin@example.com")

    def handle(self, *args, **opts):
        User = get_user_model()
        u, created = User.objects.get_or_create(
            username=opts["username"],
            defaults={"email": opts["email"]},
        )
        u.is_active = True
        u.is_staff = True
        u.is_superuser = True
        # если у вас перечисление — строковое значение допустимо, мы просто кладём "ADMIN"
        u.role = "ADMIN"
        u.set_password(opts["password"])
        u.save()
        self.stdout.write(self.style.SUCCESS(
            f"OK: id={u.id}, username={u.username}, role={u.role}, superuser={u.is_superuser}"
        ))
