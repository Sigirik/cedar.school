from __future__ import annotations
from django.db.models import Q
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from users.models import User
from schedule.core.models import Grade, Subject

DEFAULT_PAGE_SIZE = getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 50)

def _qstr(request):
    q = (request.query_params.get("q") or "").strip()
    if len(q) < 2:
        raise ValueError("QUERY_TOO_SHORT")
    return q

class BaseRefList(APIView):
    permission_classes = [IsAuthenticated]
    model = None
    fields = None
    order_by = None

    def search(self, q):
        raise NotImplementedError

    def get_queryset(self, request):
        raise NotImplementedError

    def get(self, request):
        try:
            q = (request.query_params.get("q") or "").strip()
            if len(q) < 2:
                raise ValueError("QUERY_TOO_SHORT")
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        qs = self.get_queryset(request).filter(self.search(q)).order_by(*self.order_by)

        paginator = PageNumberPagination()
        try:
            paginator.page_size = int(request.query_params.get("page_size", DEFAULT_PAGE_SIZE))
        except Exception:
            paginator.page_size = DEFAULT_PAGE_SIZE

        page = paginator.paginate_queryset(qs, request, view=self)

        def pick(obj, *names):
            return {name: getattr(obj, name, None) for name in names}

        if page is not None:
            data = [pick(obj, *self.fields) for obj in page]
            return paginator.get_paginated_response(data)

        # Fallback без пагинации (на всякий случай)
        data = [pick(obj, *self.fields) for obj in qs]
        return Response({"count": len(data), "next": None, "previous": None, "results": data}, status=200)

class TeacherRefView(BaseRefList):
    model = User
    fields = ("id", "last_name", "first_name", "middle_name")
    order_by = ("last_name", "first_name", "middle_name", "id")

    def search(self, q):
        return (Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(middle_name__icontains=q) |
                Q(username__icontains=q) |
                Q(email__icontains=q))

    def get_queryset(self, request):
        return User.objects.filter(role=User.Role.TEACHER, is_active=True)

class StudentRefView(BaseRefList):
    model = User
    fields = ("id", "last_name", "first_name", "middle_name")
    order_by = ("last_name", "first_name", "middle_name", "id")

    def search(self, q):
        return (Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(middle_name__icontains=q) |
                Q(username__icontains=q) |
                Q(email__icontains=q))

    def get_queryset(self, request):
        return User.objects.filter(role=User.Role.STUDENT, is_active=True)

class ParentRefView(BaseRefList):
    model = User
    fields = ("id", "last_name", "first_name", "middle_name")
    order_by = ("last_name", "first_name", "middle_name", "id")

    def search(self, q):
        return (Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(middle_name__icontains=q) |
                Q(username__icontains=q) |
                Q(email__icontains=q))

    def get_queryset(self, request):
        return User.objects.filter(role=User.Role.PARENT, is_active=True)

class GradeRefView(BaseRefList):
    model = Grade
    fields = ("id", "name")
    order_by = ("name", "id")

    def search(self, q):
        return Q(name__icontains=q)

    def get_queryset(self, request):
        return Grade.objects.all()

class SubjectRefView(BaseRefList):
    model = Subject
    fields = ("id", "name")
    order_by = ("name", "id")

    def search(self, q):
        return Q(name__icontains=q)

    def get_queryset(self, request):
        return Subject.objects.all()
