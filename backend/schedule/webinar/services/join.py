# backend/schedule/webinar/services/join.py
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo
import json, uuid

import jwt  # PyJWT
from django.conf import settings
from django.utils import timezone

from schedule.real_schedule.models import Room, RealLesson
from schedule.core.models import StudentSubject
from users.models import ParentChild  # важен для родителей

def _now_utc() -> datetime:
    return timezone.now().astimezone(ZoneInfo("UTC"))

def _lesson_has_student(lesson: RealLesson, user_id: int) -> bool:
    return StudentSubject.objects.filter(
        grade_id=lesson.grade_id,
        subject_id=lesson.subject_id,
        student_id=user_id,
    ).exists()

def _lesson_has_parent(lesson: RealLesson, user_id: int) -> bool:
    # родитель, у которого есть хотя бы один ребёнок-ученик на этом уроке
    child_ids = set(ParentChild.objects.filter(parent_id=user_id, is_active=True)
                    .values_list("child_id", flat=True))
    if not child_ids:
        return False
    return StudentSubject.objects.filter(
        grade_id=lesson.grade_id,
        subject_id=lesson.subject_id,
        student_id__in=list(child_ids),
    ).exists()

def _is_co_teacher(lesson: RealLesson, user_id: int) -> bool:
    # если у модели есть m2m co_teachers — учитываем
    co = getattr(lesson, "co_teachers", None)
    if not co:
        return False
    try:
        return co.filter(id=user_id).exists()
    except Exception:
        try:
            return any(getattr(t, "id", None) == user_id for t in co.all())
        except Exception:
            return False

STAFF_OBSERVER_ROLES = {"DIRECTOR", "HEAD_TEACHER", "METHODIST", "AUDITOR"}

def _role_for_user(room: Room, user) -> Tuple[str, str, bool]:
    """
    Вернёт (base_role, label, allowed_for_closed):
      base_role: moderator | participant | observer  (роль, если пользователь "свой")
      allowed_for_closed: можно ли его пускать в закрытый урок
    """
    # анонимы — для закрытого урока не допускаются; для открытого — observer через public slug
    if not user or not getattr(user, "is_authenticated", False):
        return "observer", "observer", False

    user_role = (getattr(user, "role", None) or "").upper()

    # ===== УРОКИ =====
    if room.type == "LESSON" and room.lesson_id:
        lesson: RealLesson = room.lesson

        # 1) Учитель или со-преподаватель → moderator (допуск в закрытый)
        if getattr(lesson, "teacher_id", None) == user.id or _is_co_teacher(lesson, user.id):
            return "moderator", "moderator", True

        # 2) Ученик этого предмета/класса → participant (допуск в закрытый)
        if _lesson_has_student(lesson, user.id):
            return "participant", "participant", True

        # 3) Родитель такого ученика → observer (допуск в закрытый)
        if _lesson_has_parent(lesson, user.id):
            return "observer", "observer", True

        # 4) Директор/Завуч/Методист/Аудитор → observer (допуск в закрытый)
        if user_role in STAFF_OBSERVER_ROLES or getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return "observer", "observer", True

        # 5) Прочие пользователи школы — НЕ свой (в закрытый нельзя; в открытый станут observer)
        return "observer", "observer", False

    # ===== ОБЩИЕ СОБРАНИЯ (MEETING) =====
    if room.type == "MEETING":
        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False) or user_role in STAFF_OBSERVER_ROLES:
            return "moderator", "moderator", True
        return "participant", "participant", True

    return "observer", "observer", False

def _make_jwt(room: Room, user, display_name: str, internal_role: str) -> Optional[str]:
    if not getattr(settings, "JITSI_JWT_ENABLED", False):
        return None
    secret = getattr(settings, "JITSI_JWT_SECRET", "")
    if not secret:
        return None

    now = _now_utc()
    exp = now + timedelta(minutes=getattr(settings, "JITSI_JWT_TTL_MIN", 120))
    is_moderator = (internal_role == "moderator")

    payload = {
        "aud": getattr(settings, "JITSI_JWT_AUD", "jitsi"),
        "iss": getattr(settings, "JITSI_JWT_APP_ID", "cedar"),
        "sub": getattr(settings, "JITSI_JWT_SUB", room.jitsi_domain),
        "room": room.jitsi_room,  # конкретная комната
        "nbf": int(now.timestamp()) - 5,
        "exp": int(exp.timestamp()),
        "context": {
            "user": {
                "name": display_name or (getattr(user, "username", None) or "Guest"),
                "id": str(getattr(user, "id", "")) or str(uuid.uuid4()),
                "moderator": is_moderator,
            },
            "features": {
                "recording": is_moderator,
                "livestreaming": False,
            }
        }
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def build_join_payload(room: Room, user=None, display_name: Optional[str]=None, enforce_closed_access: bool=True) -> dict:
    """
    Правило:
      • закрытый урок: пускаем только тех, у кого allowed_for_closed=True; иначе 403
      • открытый урок: пускаем всех; "своим" даём их base_role, "прочим" — observer
      • анонимы к урокам — только через public join (этот приватный эндпоинт требует auth)
    """
    base_role, label, allowed_for_closed = _role_for_user(room, user)

    if room.type == "LESSON":
        if not room.is_open:
            if enforce_closed_access and not allowed_for_closed:
                return {"error": "forbidden", "reason": "not allowed for this lesson"}
            internal_role = base_role
        else:
            # открытый: своим — как обычно; прочим — observer
            internal_role = base_role if allowed_for_closed else "observer"
    else:
        # MEETING и пр. — как рассчиталось
        internal_role = base_role

    if not display_name:
        if user and getattr(user, "is_authenticated", False):
            display_name = getattr(user, "username", None) or f"User-{user.id}"
        else:
            display_name = "Гость"

    token = _make_jwt(room, user, display_name, internal_role)

    base = f"https://{room.jitsi_domain}/{room.jitsi_room}"
    ui_tail = ""
    if internal_role == "observer":
        ui_tail = "#config.startWithAudioMuted=true&config.startWithVideoMuted=true&config.disableDeepLinking=true&interfaceConfig.toolbarButtons=[\"tileview\",\"hangup\",\"raisehand\",\"shortcuts\"]"

    join_url = base
    if token:
        sep = "?" if "?" not in join_url else "&"
        join_url = f"{join_url}{sep}jwt={token}"
    if ui_tail:
        join_url = f"{join_url}{ui_tail}"

    return {"join_url": join_url, "you_are": internal_role}
