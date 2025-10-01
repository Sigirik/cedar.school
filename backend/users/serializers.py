from rest_framework import serializers
from users.models import User, RoleRequest
from schedule.core.models import TeacherSubject, TeacherGrade, StudentSubject, GradeSubject
from schedule.core.serializers import (
    TeacherSubjectSerializer, TeacherGradeSerializer,
    StudentSubjectSerializer, GradeSubjectSerializer
)
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    middle_name = serializers.CharField(read_only=True)
    subjects = serializers.SerializerMethodField()
    grades = serializers.SerializerMethodField()
    individual_subjects_enabled = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'last_name', 'first_name', 'middle_name', 'role',
            'subjects', 'grades', 'individual_subjects_enabled'
        ]

    def get_subjects(self, obj):
        if obj.role == User.Role.STUDENT and getattr(obj, 'individual_subjects_enabled', False):
            # Индивидуальные предметы через StudentSubject
            qs = StudentSubject.objects.filter(student=obj)
            return StudentSubjectSerializer(qs, many=True).data
        elif obj.role == User.Role.STUDENT:
            # Предметы класса через GradeSubject (требуется связь user → grade!)
            # !!! Требуется реализовать obj.grade !!!
            if hasattr(obj, 'grade'):
                qs = GradeSubject.objects.filter(grade=obj.grade)
                return GradeSubjectSerializer(qs, many=True).data
            return []
        else:
            qs = TeacherSubject.objects.filter(teacher=obj)
            return TeacherSubjectSerializer(qs, many=True).data

    def get_grades(self, obj):
        if obj.role == User.Role.TEACHER:
            qs = TeacherGrade.objects.filter(teacher=obj)
            return TeacherGradeSerializer(qs, many=True).data
        return []

class RoleRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    current_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = RoleRequest
        fields = [
            'id', 'user', 'username', 'current_role',
            'requested_role', 'full_name', 'additional_info',
            'status', 'submitted_at'
        ]
        read_only_fields = ['id', 'status', 'submitted_at', 'user', 'username', 'current_role']

    def validate_requested_role(self, value):
        """
        Ограничиваем роли, которые пользователь может запросить сам:
        - обычный пользователь (без роли) и пользователи с ролью STUDENT/PARENT
          могут запросить только STUDENT или PARENT;
        - TEACHER/HEAD_TEACHER/DIRECTOR/ADMIN (+прочие служебные роли) заявки не подают.
        """
        request = self.context.get("request")
        if not request:  # на всякий случай
            return value

        user: User = request.user

        # служебные роли не подают заявки
        disallowed_submitters = {
            getattr(User.Role, 'ADMIN', None),
            getattr(User.Role, 'DIRECTOR', None),
            getattr(User.Role, 'HEAD_TEACHER', None),
            getattr(User.Role, 'METHODIST', None),
            getattr(User.Role, 'AUDITOR', None),
            getattr(User.Role, 'TEACHER', None),
        }
        if user.role in disallowed_submitters:
            raise serializers.ValidationError("Для вашей роли заявка не требуется. Обратитесь к администратору.")

        # разрешённые цели для само-заявки
        allowed_targets = {getattr(User.Role, 'STUDENT', 'STUDENT'), getattr(User.Role, 'PARENT', 'PARENT')}
        if value not in allowed_targets:
            raise serializers.ValidationError("Эта роль недоступна для самостоятельного запроса.")

        return value

class CustomUserSerializer(DjoserUserSerializer):
    middle_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    individual_subjects_enabled = serializers.BooleanField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + (
            'middle_name',
            'role',
            'individual_subjects_enabled',
        )


# --- Сериализатор для "Забыли пароль?" без зависимости от djoser.serializers ---
class PasswordResetUsernameEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        email = attrs.get("email")
        username = (attrs.get("username") or "").strip()
        User = get_user_model()
        qs = User.objects.filter(email__iexact=email)

        # кеш: кого вернём из get_user()
        self._matched_user = None

        # Если email не найден — не раскрываем факт отсутствия аккаунта
        if not qs.exists():
            return attrs

        # Единственный пользователь на email — можем слать письмо
        if qs.count() == 1:
            self._matched_user = qs.first()
            return attrs

        # Несколько пользователей на один email — просим указать логин
        if not username:
            raise serializers.ValidationError({
                "username": "На этот e-mail зарегистрировано несколько аккаунтов. Укажите логин."
            })
        user = qs.filter(username__iexact=username).first()
        if not user:
            raise serializers.ValidationError({
                "username": "Указанный логин не привязан к этому e-mail."
            })
        self._matched_user = user
        return attrs

    def get_user(self):
        """
        Djoser вызывает этот метод во view reset_password.
        Должен вернуть пользователя или None.
        """
        # если уже вычисляли на этапе validate — вернём кеш
        if hasattr(self, "_matched_user"):
            return self._matched_user

        # форс-поиск на всякий случай (обычно не понадобится)
        email = self.validated_data.get("email")
        username = (self.initial_data.get("username") or "").strip()
        User = get_user_model()
        qs = User.objects.filter(email__iexact=email)
        if not qs.exists():
            return None
        if qs.count() == 1:
            return qs.first()
        if username:
            return qs.filter(username__iexact=username).first()
        return None

class SetRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["ADMIN","DIRECTOR","HEAD_TEACHER", "METHODIST", "TEACHER","STUDENT","PARENT","AUDITOR"])