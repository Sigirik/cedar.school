# backend/schedule/real_schedule/serializers.py
from __future__ import annotations

import datetime as dt
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import localtime, is_aware
from rest_framework import serializers
from zoneinfo import ZoneInfo
from datetime import timedelta

from schedule.real_schedule.models import RealLesson, Room
from schedule.core.models import StudentSubject
from users.models import ParentChild

User = get_user_model()
# ——— Вспомогательные мини-сериализаторы ———

class _RefSerializer(serializers.Serializer):
    """Унифицированный вид для справочников: {id, name}"""
    id = serializers.IntegerField()
    name = serializers.CharField()


class _TeacherRefSerializer(serializers.Serializer):
    """Учитель: {id, fio} (короткое ФИО или username)"""
    id = serializers.IntegerField()
    fio = serializers.CharField()


class _LessonTypeRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.CharField()
    label = serializers.CharField()

def _local_dt(dt):
    if dt is None:
        return None
    try:
        return localtime(dt) if is_aware(dt) else dt
    except Exception:
        # на всякий случай не падаем из-за неправильных tz
        return dt
# ——— Основные сериализаторы, используемые за пределами /my/ ———

class RealLessonSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор RealLesson для уже существующих эндпойнтов (generate, conduct, и т.п.)
    Сохранил состав полей максимально консервативным.
    """
    end = serializers.SerializerMethodField()
    # ВАЖНО: не указываем source='subject'|'grade'|'lesson_type' — это ломает DRF 3.16+
    subject = _RefSerializer(read_only=True)
    grade = _RefSerializer(read_only=True)
    teacher = serializers.SerializerMethodField()
    lesson_type = _LessonTypeRefSerializer(read_only=True)

    class Meta:
        model = RealLesson
        fields = (
            "id",
            "subject",
            "grade",
            "teacher",
            "start",
            "duration_minutes",
            "end",
            "lesson_type",
            "topic_order",
            "topic_title",
            # Ниже поля оставлены только те, что точно существуют в модели.
            # Если в твоей модели есть дополнительные (ktp_entry и пр.) — можно добавить здесь.
        )

    def get_end(self, obj: RealLesson) -> str:
        end_dt = obj.start + dt.timedelta(minutes=obj.duration_minutes or 0)
        # единый ISO8601 с Z для UTC
        return end_dt.isoformat().replace("+00:00", "Z")

    def get_teacher(self, obj: RealLesson) -> dict:
        t = obj.teacher
        # поддержка короткого ФИО, если есть
        fio = getattr(t, "short_fio", None) or getattr(t, "username", None) or str(t)
        return {"id": getattr(t, "id", None), "fio": fio}


class RoomSerializer(serializers.ModelSerializer):
    available_from = serializers.SerializerMethodField()
    available_until = serializers.SerializerMethodField()
    is_join_allowed_now = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = (
            "id", "type", "lesson",
            "jitsi_domain", "jitsi_room", "jitsi_env",
            "join_url",
            "is_open", "public_slug",
            "status",
            "scheduled_start", "scheduled_end",
            "started_at", "ended_at",
            "available_from", "available_until", "is_join_allowed_now",
            "recording_status", "recording_file_url",
            "created_at",
        )
        read_only_fields = fields

    def get_available_from(self, obj: Room):
        if not obj.scheduled_start:
            return None
        # было: .astimezone(timezone.utc)
        return (obj.scheduled_start - timedelta(minutes=15)).astimezone(ZoneInfo("UTC"))

    def get_available_until(self, obj: Room):
        if not obj.scheduled_end:
            return None
        # было: .astimezone(timezone.utc)
        return (obj.scheduled_end + timedelta(minutes=10)).astimezone(ZoneInfo("UTC"))

    def get_is_join_allowed_now(self, obj: Room):
        now = timezone.now()
        af = self.get_available_from(obj)
        au = self.get_available_until(obj)
        return bool(af and au and (af <= now <= au))


# ——— Компактный сериализатор для /api/real_schedule/my/ ———

class MyRealLessonSerializer(serializers.ModelSerializer):
    subject = serializers.IntegerField(source="subject_id")
    grade = serializers.IntegerField(source="grade_id")
    teacher = serializers.IntegerField(source="teacher_id")

    # было: type = _LessonTypeRefSerializer(read_only=True)
    # стало: ключ типа (str), берём из lesson_type.key
    type = serializers.SerializerMethodField()

    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()

    class Meta:
        model = RealLesson
        fields = (
            "id",
            "subject",
            "grade",
            "teacher",
            "date",
            "start_time",
            "duration_minutes",
            "type",
            "room",
        )

    def _get_target_tz(self) -> ZoneInfo:
        # Можно будет расширить: взять user.profile.timezone или заголовок X-TZ
        tz_name = (self.context or {}).get("tz") or "Europe/Amsterdam"
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return ZoneInfo("Europe/Amsterdam")

    def get_date(self, obj):
        dt = obj.start
        if dt is None:
            return None
        if is_aware(dt):
            dt = dt.astimezone(self._get_target_tz())
        return dt.date().isoformat()

    def get_start_time(self, obj):
        dt = obj.start
        if dt is None:
            return None
        if is_aware(dt):
            dt = dt.astimezone(self._get_target_tz())
        return dt.time().isoformat()

    def get_type(self, obj):
        lt = getattr(obj, "lesson_type", None)
        return getattr(lt, "key", None) if lt else None

<<<<<<< HEAD
    def get_room(self, obj):
        r = getattr(obj, "room", None)
        if not r:
            return None
        return {"provider": getattr(r, "provider", None), "join_url": getattr(r, "join_url", None)}
=======

>>>>>>> origin/staging

# Страница урока

def _attendance_display(status, late_minutes):
    """
    Нейтральный текст посещаемости:
      "+" → "+"
      "-" → "-"
      "late" + N → "опоздание N мин"
    """
    if status == "late":
        return f"опоздание {late_minutes} мин" if late_minutes is not None else "опоздание"
    return status or None  # "+", "-" или None


class LessonDetailSerializer(serializers.ModelSerializer):
    # Плоские ID вместо вложенных объектов
    subject = serializers.IntegerField(source="subject_id", read_only=True)
    grade   = serializers.IntegerField(source="grade_id", read_only=True)
    teacher = serializers.IntegerField(source="teacher_id", read_only=True)

    # Вычисляемые поля-вида
    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    room_name = serializers.SerializerMethodField()
    webinar_url = serializers.SerializerMethodField()
    materials = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    topic = serializers.SerializerMethodField()
    homework_summary = serializers.SerializerMethodField()

    # Новый блок — полный список учеников урока
    students = serializers.SerializerMethodField()

    class Meta:
        model = RealLesson
        fields = (
            "id",
            "subject", "grade", "teacher",
            "date", "start_time", "duration_minutes",
            "room_name", "webinar_url",
            "topic", "materials", "participants",
            "homework_summary",
            "students",
        )

    # ---------------------------
    # Дата/время/длительность
    # ---------------------------
    def _local_start(self, obj):
        try:
            return timezone.localtime(obj.start)
        except Exception:
            return obj.start

    def get_date(self, obj):
        dt = self._local_start(obj)
        return dt.date().isoformat() if dt else None

    def get_start_time(self, obj):
        dt = self._local_start(obj)
        return dt.strftime("%H:%M:%S") if dt else None

    def get_duration_minutes(self, obj):
        # Берём из поля модели (у вас нет end)
        return getattr(obj, "duration_minutes", None)

    # ---------------------------
    # Комнаты / материалы / тема
    # ---------------------------
    def get_room_name(self, obj):
        # Пока нет модели "аудитория школы" — возвращаем None
        return None

    def get_webinar_url(self, obj):
        room = getattr(obj, "room", None)  # OneToOne(Room) опционально
        return getattr(room, "join_url", None) if room else None

    def get_materials(self, obj):
        # Заглушка на MVP
        return []

    def get_topic(self, obj):
        title = getattr(obj, "topic_title", None)
        if title:
            return title
        # Дружелюбный фолбэк для STUDENT/PARENT
        request = self.context.get("request")
        role = getattr(getattr(request, "user", None), "role", None) if request else None
        return "Тема будет объявлена учителем в начале урока." if role in ("STUDENT", "PARENT") else ""

    # ---------------------------
    # Участники (учителя + счётчик учеников)
    # ---------------------------
    def get_participants(self, obj):
        # Учителя: основной + со-преподаватели (если поле есть)
        teacher_ids = []
        if getattr(obj, "teacher_id", None):
            teacher_ids.append(obj.teacher_id)

        co = getattr(obj, "co_teachers", None)
        if co is not None:
            try:
                teacher_ids += list(co.values_list("id", flat=True))
            except Exception:
                try:
                    teacher_ids += [t.id for t in co.all()]
                except Exception:
                    pass

        # Уникализируем
        teacher_ids = list(dict.fromkeys([tid for tid in teacher_ids if tid]))

        # Кол-во учеников по подписке на предмет (grade + subject)
        students_count = StudentSubject.objects.filter(
            grade_id=obj.grade_id,
            subject_id=obj.subject_id
        ).count()

        return {"teachers": teacher_ids, "students_count": students_count}

    def get_homework_summary(self, obj):
        # Заглушка на MVP
        return ""

    # ---------------------------
    # Полный список учеников урока
    # ---------------------------
    def get_students(self, obj):
        """
        Возвращает список учеников урока:
          - базово: все подписанные на предмет (StudentSubject по паре grade+subject)
          - плюс: индивидуально отмеченные в LessonStudent (если модель есть)
        Видимость:
          - ADMIN/HEAD_TEACHER/DIRECTOR/TEACHER — видят всех
          - STUDENT — только себя
          - PARENT — только своих детей
        На каждого ученика отдаём:
          id, first_name, last_name, fio, attendance:{status,late_minutes,display}, mark
        """
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        role = getattr(user, "role", None) if user else None

        # 1) Все, кто подписан на предмет этого урока
        sub_ids = set(
            StudentSubject.objects.filter(
                grade_id=obj.grade_id,
                subject_id=obj.subject_id
            ).values_list("student_id", flat=True)
        )

        # 2) Индивидуальные записи посещаемости/оценок (если модель есть)
        ls_model = None
        try:
            ls_model = apps.get_model("real_schedule", "LessonStudent")
        except LookupError:
            ls_model = None

        ls_map = {}  # student_id -> {status, late_minutes, mark}
        if ls_model:
            for row in ls_model.objects.filter(lesson_id=obj.id):
                ls_map[row.student_id] = {
                    "status": row.status,
                    "late_minutes": row.late_minutes,
                    "mark": row.mark,
                }

        # Полный набор ID, которые «имеют отношение к уроку»
        related_ids = set(sub_ids)
        related_ids.update(ls_map.keys())

        if not related_ids:
            return []

        # 3) Политика видимости
        allowed_ids = set()
        if role in ("ADMIN", "HEAD_TEACHER", "DIRECTOR", "TEACHER"):
            allowed_ids = related_ids
        elif role == "STUDENT" and user:
            if user.id in related_ids:
                allowed_ids = {user.id}
        elif role == "PARENT" and user:
            child_ids = set(
                ParentChild.objects.filter(parent=user, is_active=True)
                .values_list("child_id", flat=True)
            )
            pp = getattr(user, "parent_profile", None)
            # parent_profile.children (StudentProfile → user_id)
            if pp and hasattr(pp, "children"):
                try:
                    for sp in pp.children.all():
                        uid = getattr(sp, "user_id", None)
                        if uid:
                            child_ids.add(uid)
                except Exception:
                    pass
            # parent_profile.child_users (User)
            if pp and hasattr(pp, "child_users"):
                try:
                    for cu in pp.child_users.all():
                        child_ids.add(cu.id)
                except Exception:
                    pass
            allowed_ids = related_ids.intersection(child_ids)
        else:
            return []

        if not allowed_ids:
            return []

        # 4) Подтянем пользователей (минимум полей)
        users = User.objects.filter(id__in=allowed_ids)
        # Соберём карту id -> пользователь
        user_map = {u.id: u for u in users}

        # 5) Сбор финального списка
        def fio_of(u):
            first = getattr(u, "first_name", "") or ""
            last  = getattr(u, "last_name", "") or ""
<<<<<<< HEAD
            middle = getattr(u, "middle_name", None) or getattr(u, "patronymic", None)
            middle_initial = (middle[:1] + ".") if middle else ""
            first_initial = (first[:1] + ".") if first else ""
            return f"{last} {first_initial}{middle_initial}".strip()
=======
            # middle = getattr(u, "middle_name", None) or getattr(u, "patronymic", None)
            # middle_initial = (middle[:1] + ".") if middle else ""
            # first_initial = (first[:1] + ".") if first else ""
            return f"{last} {first}".strip()
>>>>>>> origin/staging

        result = []
        # Для стабильности сортируем по ФИО
        for sid in sorted(allowed_ids, key=lambda _id: fio_of(user_map.get(_id, User(id=_id)))):
            u = user_map.get(sid)
            if not u:
                continue
            st = ls_map.get(sid, {}).get("status")
            lm = ls_map.get(sid, {}).get("late_minutes")
            mk = ls_map.get(sid, {}).get("mark")

            result.append({
                "id": sid,
                "first_name": getattr(u, "first_name", "") or "",
                "last_name": getattr(u, "last_name", "") or "",
                "fio": fio_of(u),
                "attendance": {
                    "status": st,               # "+", "-", "late" или None
                    "late_minutes": lm,         # None или число минут
                    "display": _attendance_display(st, lm),
                },
                "mark": mk,                    # оценка (Decimal/float) или None
            })

        return result