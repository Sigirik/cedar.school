# users/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from djoser.serializers import UserCreateSerializer

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import User, RoleRequest
from .serializers import UserSerializer, RoleRequestSerializer, SetRoleSerializer
from .permissions import IsAdminRole


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
    """
    Список и чтение пользователей.
    Добавлен экшен POST /api/users/{id}/set-role/ для ADMIN — назначение роли.
    """
    queryset = User.objects.all()  # без availabilities
    serializer_class = UserSerializer

    @action(
        detail=True,
        methods=['post'],
        url_path='set-role',
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def set_role(self, request, pk=None):
        """
        ADMIN назначает роль любому пользователю.
        Тело: {"role": "ADMIN" | "DIRECTOR" | "HEAD_TEACHER" | "TEACHER" | "STUDENT" | "PARENT" | "AUDITOR"}
        """
        target_user = self.get_object()
        serializer = SetRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user.role = serializer.validated_data["role"]
        target_user.save(update_fields=["role"])
        return Response({"id": target_user.id, "role": target_user.role}, status=status.HTTP_200_OK)


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(role=User.Role.TEACHER).prefetch_related('availabilities')
    serializer_class = UserSerializer


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(role=User.Role.STUDENT)
    serializer_class = UserSerializer


class RoleRequestViewSet(viewsets.ModelViewSet):
    """
    Заявки на назначение роли.

    Правила:
    - Обычный пользователь (без роли) и пользователи с ролью STUDENT/PARENT могут подать заявку
      только на STUDENT или PARENT.
    - TEACHER/HEAD_TEACHER/DIRECTOR/ADMIN (и прочие служебные роли) заявки не подают — им роли назначают напрямую.
    - Утверждать/отклонять:
        * DIRECTOR — любые заявки
        * HEAD_TEACHER — только STUDENT и PARENT
    - Остальные пользователи видят только свои заявки.
    """
    queryset = RoleRequest.objects.all().select_related('user')
    serializer_class = RoleRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _allowed_request_roles_for_user(self, user: User) -> list[str]:
        service_roles = {
            getattr(User.Role, 'ADMIN', None),
            getattr(User.Role, 'DIRECTOR', None),
            getattr(User.Role, 'HEAD_TEACHER', None),
            getattr(User.Role, 'METHODIST', None),
            getattr(User.Role, 'AUDITOR', None),
            getattr(User.Role, 'TEACHER', None),
        }
        if user.role in service_roles:
            return []
        # Базовый сценарий само-заявки:
        return [getattr(User.Role, 'STUDENT', 'STUDENT'), getattr(User.Role, 'PARENT', 'PARENT')]

    def get_queryset(self):
        user = self.request.user
        if user.role == getattr(User.Role, 'DIRECTOR', 'DIRECTOR'):
            return self.queryset
        elif user.role == getattr(User.Role, 'HEAD_TEACHER', 'HEAD_TEACHER'):
            return self.queryset.filter(requested_role__in=[
                getattr(User.Role, 'STUDENT', 'STUDENT'),
                getattr(User.Role, 'PARENT', 'PARENT'),
            ])
        # остальные видят только свои заявки
        return self.queryset.filter(user=user)

    def create(self, request, *args, **kwargs):
        user: User = request.user
        requested_role = request.data.get('requested_role')

        allowed = self._allowed_request_roles_for_user(user)
        if not allowed:
            return Response({"detail": "Для вашей роли заявка не требуется. Обратитесь к администратору."}, status=400)

        if requested_role not in allowed:
            return Response({"detail": "Эта роль недоступна для самостоятельного запроса."}, status=400)

        # не даём создать дубликат PENDING на ту же роль
        if RoleRequest.objects.filter(user=user, requested_role=requested_role, status=RoleRequest.Status.PENDING).exists():
            return Response({"detail": "Заявка уже отправлена и ожидает рассмотрения."}, status=400)

        # сериализатор сам проверит requested_role и заполнит user в perform_create
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='allowed-roles')
    def allowed_roles(self, request):
        """Для фронта: какие роли текущий пользователь может запросить."""
        return Response({"allowed": self._allowed_request_roles_for_user(request.user)})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        role_request = self.get_object()
        if role_request.status != RoleRequest.Status.PENDING:
            return Response({"detail": "Уже обработано."}, status=400)

        if not self._can_manage(request.user, role_request.requested_role):
            return Response({"detail": "Недостаточно прав."}, status=403)

        role_request.status = RoleRequest.Status.APPROVED
        role_request.save(update_fields=["status"])
        role_request.user.role = role_request.requested_role
        role_request.user.save(update_fields=["role"])
        return Response({"detail": "Роль назначена."})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        role_request = self.get_object()
        if role_request.status != RoleRequest.Status.PENDING:
            return Response({"detail": "Уже обработано."}, status=400)

        if not self._can_manage(request.user, role_request.requested_role):
            return Response({"detail": "Недостаточно прав."}, status=403)

        role_request.status = RoleRequest.Status.REJECTED
        role_request.save(update_fields=["status"])
        return Response({"detail": "Заявка отклонена."})

    def _can_manage(self, user: User, requested_role: str) -> bool:
        if user.role == getattr(User.Role, 'DIRECTOR', 'DIRECTOR'):
            return True
        if user.role == getattr(User.Role, 'HEAD_TEACHER', 'HEAD_TEACHER'):
            return requested_role in [
                getattr(User.Role, 'STUDENT', 'STUDENT'),
                getattr(User.Role, 'PARENT', 'PARENT'),
            ]
        return False

@method_decorator(csrf_exempt, name='dispatch')
class CsrfExemptRegisterView(APIView):
    """
    Упрощённая регистрация под Djoser (CSRF-exempt), если нужна.
    """
    def post(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Текущий пользователь (удобно фронту). Обрати внимание:
    каноничный Djoser-эндпоинт — /api/auth/users/me/.
    Этот — просто короткий алиас, если фронт ждёт именно /api/users/me/.
    """
    return Response(UserSerializer(request.user).data)
