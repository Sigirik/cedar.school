from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer

@login_required
def dashboard(request):
    user = request.user
    role = user.role

    if role == User.Role.STUDENT:
        template = "users/dashboard_student.html"
    elif role == User.Role.TEACHER:
        template = "users/dashboard_teacher.html"
    elif role in [User.Role.DIRECTOR, User.Role.HEAD_TEACHER, User.Role.AUDITOR]:
        template = "users/dashboard_admin.html"
    elif role == User.Role.PARENT:
        template = "users/dashboard_parent.html"
    else:
        template = "users/dashboard_default.html"

    return render(request, template, {"user": user})

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().prefetch_related('availabilities')
    serializer_class = UserSerializer