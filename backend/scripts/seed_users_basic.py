import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from django.apps import apps

User = get_user_model()

def find_model(name: str):
    for m in apps.get_models():
        if m.__name__ == name:
            return m
    raise LookupError(f"Model {name} not found")

# core models
Subject        = find_model("Subject")
Grade          = find_model("Grade")
GradeLevel     = find_model("GradeLevel")
Parallel       = find_model("Parallel")
TeacherGrade   = find_model("TeacherGrade")
TeacherSubject = find_model("TeacherSubject")
ParentChild    = find_model("ParentChild")

def upsert_user(u, password=None, **fields):
    """Обновить поля и пароль при необходимости; всегда активировать."""
    changed = False
    for k, v in fields.items():
        if getattr(u, k) != v:
            setattr(u, k, v)
            changed = True
    if password and (not u.has_usable_password()):
        u.set_password(password)
        changed = True
    if changed:
        u.save()
    return u

def get_or_create_user(username, password, email, last_name, first_name, middle_name, role):
    u, created = User.objects.get_or_create(
        username=username,
        defaults=dict(
            email=email,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            role=role,
            is_active=True,
        ),
    )
    # гарантируем значения и пароль (идемпотентно)
    u = upsert_user(
        u,
        password=password if created else None,
        email=email,
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        role=role,
        is_active=True,
    )
    return u

def get_or_create_superuser(username, password, email, last_name, first_name, middle_name):
    """Создать суперпользователя, если его нет. Если есть — гарантировать флаги и активность."""
    try:
        u = User.objects.get(username=username)
        # гарантируем флаги и актуальные данные
        u = upsert_user(
            u,
            email=email,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        # пароль меняем только если не установлен
        if not u.has_usable_password():
            u.set_password(password)
            u.save()
        return u, False
    except User.DoesNotExist:
        # создаём корректно как суперпользователя
        u = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            is_active=True,
        )
        u.is_staff = True
        u.is_superuser = True
        u.save(update_fields=["is_staff", "is_superuser"])
        return u, True

def get_existing_subjects(names):
    """Вернёт dict {имя: Subject} только для уже существующих предметов. Ничего не создаёт."""
    wanted = {n.strip(): None for n in names}
    qs = Subject.objects.filter(name__in=list(wanted.keys()))
    found = {s.name: s for s in qs}
    skipped = sorted(set(wanted.keys()) - set(found.keys()))
    return found, skipped

def grades_by_levels(level_numbers, prefer_parallel="А"):
    res = []
    levels = {gl.number: gl for gl in GradeLevel.objects.all()}
    for lvl in level_numbers:
        qs = Grade.objects.filter(level=levels.get(lvl)).order_by("name")
        g = None
        if prefer_parallel and Parallel.objects.filter(code=prefer_parallel).exists():
            g = qs.filter(parallel__code=prefer_parallel).first()
        g = g or qs.first()
        if g:
            res.append(g)
    return res

TeacherAvailability = None
try:
    TeacherAvailability = find_model("TeacherAvailability")
except LookupError:
    pass

from datetime import time

def upsert_availability(teacher, start: time, end: time, weekdays=(0,1,2,3,4)):
    """
    Создаёт/обновляет доступность учителя на указанные дни недели (0=Пн .. 6=Вс).
    Идемпотентно: если запись на день уже есть — обновит окно времени.
    """
    if not TeacherAvailability:
        print("[WARN] TeacherAvailability model not found — skipping availability seeding")
        return 0

    created_or_updated = 0
    for wd in weekdays:
        obj, created = TeacherAvailability.objects.get_or_create(
            teacher=teacher,
            day_of_week=wd,                               # <-- исправлено
            defaults={"start_time": start, "end_time": end},
        )
        changed = False
        if obj.start_time != start:
            obj.start_time = start; changed = True
        if obj.end_time != end:
            obj.end_time = end; changed = True
        if changed and not created:
            obj.save(update_fields=["start_time", "end_time"])
        created_or_updated += 1
    return created_or_updated

@transaction.atomic
def main():
    # --- суперпользователь (создать, если нет)
    # Параметры: логин, пароль, email, ФИО (фамилия, имя, отчество)
    admin_user, created_admin = get_or_create_superuser(
        username="Admin",                 # логин; можно сменить на "Админ", если нужно кириллицей
        password="Ced@rAdm1n",
        email="admin@example.com",
        last_name="Админов",
        first_name="Админ",
        middle_name="Админович",
    )
    print(f"Superuser: {'created' if created_admin else 'exists/updated'}: {admin_user.username}")

    # --- обычные пользователи
    zavuch  = get_or_create_user("Head_teacher", "Ced@rH3T3", "zav@example.com",
                                 "Старшов", "Завуч", "Учителевич", User.Role.HEAD_TEACHER)
    guman   = get_or_create_user("Gumanitarii", "Ced@r6um", "gum@example.com",
                                 "Историкович", "Географ", "Языкович", User.Role.TEACHER)
    tehnar  = get_or_create_user("Tehnar", "Ced@rTehnar1", "teh@example.com",
                                 "Физикович", "Техрарь", "Геометриевич", User.Role.TEACHER)
    student = get_or_create_user("Student", "Ced@rStu6", "student@example.com",
                                 "Студентович", "Ученик", "Родителевич", User.Role.STUDENT)
    parent  = get_or_create_user("Parent", "Ced@r5ar3nt", "parent@example.com",
                                 "Мудров", "Родитель", "Прорадителевич", User.Role.PARENT)

    # --- учитель ↔ предмет (только существующие предметы, ничего не создаём)
    guman_wants  = ["История", "Русский язык", "Английский язык", "География"]
    tehnar_wants = ["Математика", "Физика", "Информатика"]

    guman_subj,  guman_skipped  = get_existing_subjects(guman_wants)
    tehnar_subj, tehnar_skipped = get_existing_subjects(tehnar_wants)

    ops1 = upsert_availability(
        teacher=tehnar,
        start=time(8, 0),
        end=time(11, 0),
        weekdays=(0,1,2,3,4),  # Пн–Пт
    )
    ops2 = upsert_availability(
        teacher=guman,
        start=time(9, 0),
        end=time(13, 0),
        weekdays=(0,1,2,3,4),  # Пн–Пт
    )

    created_ts = 0
    for s in guman_subj.values():
        _, was = TeacherSubject.objects.get_or_create(teacher=guman, subject=s)
        created_ts += int(was)
    for s in tehnar_subj.values():
        _, was = TeacherSubject.objects.get_or_create(teacher=tehnar, subject=s)
        created_ts += int(was)
    if guman_skipped:
        print(f"[INFO] Нет в базе (пропущены) для Gumanitarii: {', '.join(guman_skipped)}")
    if tehnar_skipped:
        print(f"[INFO] Нет в базе (пропущены) для Tehnar: {', '.join(tehnar_skipped)}")
    print(f"TeacherSubject linked (created new): {created_ts}")

    # --- учитель ↔ классы
    for g in grades_by_levels([5, 6]):
        TeacherGrade.objects.get_or_create(teacher=guman, grade=g)
    for g in grades_by_levels([6, 7]):
        TeacherGrade.objects.get_or_create(teacher=tehnar, grade=g)

    # --- родитель ↔ ученик
    ParentChild.objects.get_or_create(parent=parent, child=student, defaults={"is_active": True})

    print(f"TeacherAvailability upserted: {ops1 + ops2} records")

    print("Seed (users/roles/links + superuser + availability) finished.")

if __name__ == "__main__":
    main()
