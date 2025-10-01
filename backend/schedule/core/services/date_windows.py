# backend/schedule/core/services/date_windows.py
from __future__ import annotations

import datetime as dt
from typing import Tuple, Optional

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from schedule.core.models import AcademicYear  # is_current, start_date, end_date

_MAX_DAYS = 31


def _monday_of(date_: dt.date) -> dt.date:
    return date_ - dt.timedelta(days=date_.weekday())  # 0=Monday


def _sunday_of(date_: dt.date) -> dt.date:
    return _monday_of(date_) + dt.timedelta(days=6)


def get_default_school_week(today: Optional[dt.date] = None) -> Tuple[dt.date, dt.date]:
    """
    Возвращает (date_from, date_to) для ближайшей учебной недели.
    Логика:
      1) Если есть текущий учебный год (is_current=True) и today ∈ [start..end] — берём Пн–Вс текущей недели.
      2) Если current-year есть, но today вне его — берём ближайшую неделю внутри этого года:
         - если today < start → неделя, начинающаяся на start (или его понедельник внутри года)
         - если today > end   → неделя, заканчивающаяся на end (или его воскресенье внутри года)
      3) Если учебный год не найден — Пн–Вс недели, в которой находится today.
    """
    ld = today or timezone.localdate()

    year = (
        AcademicYear.objects
        .filter(is_current=True)
        .order_by("-start_date")
        .first()
    )

    if year and year.start_date <= ld <= year.end_date:
        start, end = _monday_of(ld), _sunday_of(ld)
    elif year:
        if ld < year.start_date:
            start = _monday_of(year.start_date)
            if start < year.start_date:
                start = year.start_date
            end = min(start + dt.timedelta(days=6), year.end_date)
        else:
            end = _sunday_of(year.end_date)
            if end > year.end_date:
                end = year.end_date
            start = max(end - dt.timedelta(days=6), year.start_date)
    else:
        start, end = _monday_of(ld), _sunday_of(ld)

    return start, end


def parse_from_to_dates(raw_from: Optional[str], raw_to: Optional[str]) -> Tuple[Optional[dt.date], Optional[dt.date]]:
    """
    Принимаем YYYY-MM-DD или ISO-datetime, возвращаем (date, date).
    """
    def _parse_one(v: Optional[str]) -> Optional[dt.date]:
        if not v:
            return None
        v = v.strip()
        d = parse_date(v)
        if d:
            return d
        dtm = parse_datetime(v)
        if dtm:
            if timezone.is_naive(dtm):
                # В Django 5 используем стандартный datetime.timezone.utc
                dtm = timezone.make_aware(dtm, dt.timezone.utc)
            return dtm.date()
        return None

    d_from = _parse_one(raw_from)
    d_to   = _parse_one(raw_to)
    return d_from, d_to


def validate_and_materialize_range(d_from: Optional[dt.date], d_to: Optional[dt.date]) -> Tuple[dt.datetime, dt.datetime]:
    """
    Валидация диапазона и материализация в [from_dt, to_dt_exclusive)
    """
    if not d_from or not d_to or d_from > d_to:
        raise ValueError("INVALID_RANGE")

    days = (d_to - d_from).days + 1
    if days > _MAX_DAYS:
        raise ValueError("RANGE_TOO_WIDE")

    # материализуем в UTC-aware (используем datetime.timezone.utc)
    from_dt = timezone.make_aware(dt.datetime.combine(d_from, dt.time.min), dt.timezone.utc)
    # верхняя граница эксклюзивная: следующий день 00:00
    to_dt_exclusive = timezone.make_aware(dt.datetime.combine(d_to + dt.timedelta(days=1), dt.time.min), dt.timezone.utc)
    return from_dt, to_dt_exclusive
