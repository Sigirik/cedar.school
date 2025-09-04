# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ParentChild
from schedule.core.models import TeacherAvailability

class TeacherAvailabilityInline(admin.TabularInline):
    model = TeacherAvailability
    extra = 0

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # fieldsets и прочее как у тебя
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("last_name", "first_name", "middle_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Роль", {"fields": ("role",)}),
    )

    list_display = ("username", "email", "last_name", "first_name", "middle_name", "role")
    list_filter = ("role",)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.role == User.Role.STUDENT:
            for i, (name, opts) in enumerate(fieldsets):
                if name == "Personal info":
                    opts['fields'] = opts['fields'] + ("individual_subjects_enabled",)
                    break
        return fieldsets

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        if obj and obj.role == User.Role.TEACHER:
            inlines.append(TeacherAvailabilityInline(self.model, self.admin_site))
        return inlines

@admin.register(ParentChild)
class ParentChildAdmin(admin.ModelAdmin):
    list_display = ("id", "parent", "child", "is_active", "relation", "created_at")
    list_filter = ("is_active",)
    search_fields = (
        "parent__username",
        "parent__email",
        "parent__last_name",
        "parent__first_name",
        "child__username",
        "child__email",
        "child__last_name",
        "child__first_name",
    )
    raw_id_fields = ("parent", "child")