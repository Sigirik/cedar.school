from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserSubject, UserGrade

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Переопределяем fieldsets с включением middle_name
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("last_name", "first_name", "middle_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Роль", {"fields": ("role",)}),
    )

    list_display = ("username", "email", "last_name", "first_name", "middle_name", "role")
    list_filter = ("role",)


admin.site.register(UserSubject)
admin.site.register(UserGrade)