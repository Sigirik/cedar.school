# users/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    message = "Недостаточно прав (требуется роль ADMIN)."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "ADMIN")
