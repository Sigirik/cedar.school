# Schedule Pipeline — Developer Guide

> Этот документ описывает, как устроены валидация черновиков и пайплайн генерации реальных уроков из шаблонной недели и КТП, а также дает практические рецепты запуска и отладки. Док отражает итоговое состояние после фиксов, на которых базируются зелёные тесты `schedule/validators/tests` и `schedule/real_schedule/tests`.

---

## TL;DR

- **Валидация черновиков**: `POST /api/draft/template-drafts/validate/` принимает список «уроков в черновике» и возвращает `{errors: [], warnings: []}`.
  - Ошибки/предупреждения кодируются как: `TEACHER_OVERLAP`, `GRADE_OVERLAP`, `ROOM_OVERLAP`, `ZERO_DURATION`, `MISSING_FIELDS` и др.
  - Пересечения считаются на полуинтервале `[start, end)`: касание границ **не** конфликт.
- **Генерация расписания**: `generate(start_date, end_date, debug=False)` удаляет все `RealLesson` в окне и заново создает из источников:
  - Шаблонные уроки `TemplateLesson` (TL).
  - Записи КТП `KTPEntry` (если в модели есть дата/датавремя) — «короткий путь».
- **Маппинг КТП**:
  - Если `RealLesson` создан из КТП — ссылка `ktp_entry` выставляется и `topic_title` берется из КТП.
  - Если урок без КТП — `topic_title` заполняется дефолтом: **«Тему задаст учитель на уроке»**.
- **Время**: `RealLesson.start` хранится как aware‑время, при конвертации в `Europe/Moscow` совпадает со «стеночным» временем TL/КТП.
- **Идемпотентность окна**: повторный вызов `generate()` для того же интервала переписывает окно (delete+create) и не плодит дублей.
- **Производительность**: одна транзакция, bulk‑операции, минимум запросов.

---

## 1) Модели и сущности (в терминах тестов)

- **TemplateWeek** — шаблонная неделя (часто обязательна привязка к `AcademicYear`).
- **TemplateLesson (TL)** — элемент шаблонной недели: `day_of_week`, `start_time`, `duration_minutes`, `grade`, `subject`, `teacher`, `type`.
- **KTPTemplate / KTPSection / KTPEntry** — план (КТП). У `KTPEntry` возможны разные поля даты в разных схемах: `date`, `lesson_date`, `scheduled_for`, `datetime` и т.п. Тесты учитывают обе ситуации.
- **RealLesson** — реальный урок. Имеет `start` (aware), опционально `end` (либо вычисляется как `start + duration`). Может иметь `ktp_entry` и `type`.

> Тесты допускают разные схемы полей (например `Grade.name|title`, наличие/отсутствие полей у КТП). Пайплайн и тесты написаны устойчиво к этим вариациям.

---

## 2) Валидация черновиков

### Эндпоинт
```
POST /api/draft/template-drafts/validate/
Content-Type: application/json
```

### Пейлоад (пример)
```json
{
  "lessons": [
    {
      "id": 1,
      "teacher_id": 77,
      "grade_id": 10,
      "subject_id": 3,
      "room_id": 101,
      "day_of_week": 1,
      "start_time": "09:00",
      "duration_minutes": 45
    },
    {
      "id": 2,
      "teacher_id": 77,
      "grade_id": 10,
      "subject_id": 3,
      "room_id": 101,
      "day_of_week": 1,
      "start_time": "09:30",
      "duration_minutes": 45
    }
  ]
}
```

### Ответ (пример)
```json
{
  "errors": [
    {
      "code": "TEACHER_OVERLAP",
      "resource": "teacher",
      "resource_id": 77,
      "day": 1,
      "range": {"start": "09:00", "end": "10:15"},
      "lesson_ids": [1, 2],
      "message": "Пересечение по teacher (id=77) в день 1",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "code": "ROOM_OVERLAP",
      "resource": "room",
      "resource_id": 101,
      "day": 1,
      "range": {"start": "09:00", "end": "10:15"},
      "lesson_ids": [1, 2],
      "message": "Пересечение по room (id=101) в день 1",
      "severity": "warning"
    }
  ]
}
```

### Правила
- **Полуинтервал**: коллизии проверяются на `[start, end)`. Касание границ, например 10:00–10:45 и 10:45–11:30 — **валидно**.
- **Типы конфликтов**:
  - `TEACHER_OVERLAP` — **ошибка**.
  - `GRADE_OVERLAP` — **ошибка**.
  - `ROOM_OVERLAP` — **предупреждение**.
  - `ZERO_DURATION` — **ошибка** (нулевая длительность).
  - `MISSING_FIELDS` — **предупреждение** (например, пустой `teacher`).
- Сообщения содержат `lesson_ids`, `resource(_id)`, `day`, `range.start|end`.

### Быстрый self‑check URL’а
```bash
# если нужен reverse() — используйте manage.py и DJANGO_SETTINGS_MODULE
docker compose exec backend bash -lc \
"DJANGO_SETTINGS_MODULE=cedar.settings python manage.py shell -c \
'from django.urls import reverse; print(reverse(\"draft:template-draft-validate\"))'"
# или проверить resolve():
docker compose exec backend bash -lc \
\"DJANGO_SETTINGS_MODULE=cedar.settings python manage.py shell -c '\
from django.urls import resolve; print(resolve(\"/api/draft/template-drafts/validate/\"))'\"
```

---

## 3) Генерация реального расписания

### Входная точка
```python
from schedule.real_schedule.pipeline import generate
res = generate(date_from, date_to, debug=False)
# res: GenerateResult(version, generation_batch_id, deleted, created, warnings)
```

### Поведение
- **Переписывание окна**: все `RealLesson` в интервале `[date_from, date_to]` удаляются и создаются заново. Значение `res.created` равно числу созданных объектов после переписывания.
- **Источники**:
  1) **TemplateLesson** (TL): создаются уроки по `day_of_week`, времени и длительности.
  2) **KTPEntry** с датой/датавременем (если поле существует) — «короткий путь»:
     - может создавать `RealLesson` даже если TL на эту дату нет;
     - при одновременном наличии TL и КТП на одну дату возможны разные стратегии (совмещение/раздельно) — тесты допускают обе.
- **Маппинг и темы**:
  - если урок создан из КТП — заполняется `ktp_entry` и `topic_title` берется из КТП;
  - если урок без КТП — `topic_title = "Тему задаст учитель на уроке"`.
- **Тип урока**: `RealLesson.type` (если поле есть) переносится из `TemplateLesson.type`.
- **Время/таймзоны**:
  - `RealLesson.start` — aware‑время; при `astimezone(ZoneInfo("Europe/Moscow"))` соответствует стеночному времени TL/КТП;
  - если у модели есть поле `end`, оно тоже aware; иначе длительность считается как `start + duration_minutes`.

### Производительность
- Одна транзакция на окно.
- Массовые операции (`bulk_create`, пакетные выборки).
- Минимум обращений к БД и отсутствуют N+1.

---

## 4) Известные вариации схем и «гибкость»

Док и тесты учитывают, что у инсталляций могут отличаться имена и обязательность полей:

- `Grade.name` vs `Grade.title` — тесты проверяют и то, и другое.
- `TemplateWeek.academic_year` может быть **обязателен** — в тестах добавлен `AcademicYear`.
- `KTPEntry` может иметь дату как `date`/`lesson_date`/`scheduled_for`/`datetime` — генератор ищет подходящее поле.
- `KTPSection.order` может быть `NOT NULL` — в тестах передаётся, если поле есть.
- Совмещение TL + КТП на одну дату:
  - Схема А: КТП‑запись «приклеивается» к существующему TL.
  - Схема B: создаются отдельные уроки. Тесты допускают обе (с проверками количества уроков и числа уроков, связанных с КТП).

---

## 5) Рецепты

### Проверка валидации из CLI
```bash
curl -X POST http://localhost:8000/api/draft/template-drafts/validate/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lessons": [
      {"id": 1, "teacher_id": 1, "grade_id": 1, "subject_id": 1, "room_id": 101,
       "day_of_week": 1, "start_time": "09:00", "duration_minutes": 45},
      {"id": 2, "teacher_id": 1, "grade_id": 1, "subject_id": 1, "room_id": 101,
       "day_of_week": 1, "start_time": "09:30", "duration_minutes": 45}
    ]
  }'
```

### Быстрый smoke генерации
```python
from datetime import date
from schedule.real_schedule.pipeline import generate
res = generate(date(2025,9,1), date(2025,9,7), debug=True)
print(res.created, res.deleted, res.generation_batch_id)
```

### Запуск тестов
```bash
# валидатор черновиков
docker compose exec backend bash -lc "pytest schedule/validators/tests -q"

# пайплайн расписания (без долгих perf)
docker compose exec backend bash -lc "pytest schedule/real_schedule/tests -q -k 'not perf' -m 'not slow'"

# всё подряд
docker compose exec backend bash -lc "pytest -q"
```

---

## 6) Точки расширения

- Добавить новые правила валидатора — следуйте общей форме `{code, severity, lesson_ids, resource(_id), day, range}`.
- Маппинг КТП ↔ TL: если хотите строгого «слияния» по дате/парам (grade/subject/teacher), добавляйте соответствующее правило сопоставления.
- Локали и сообщения — все тексты сообщений централизованы в валидаторе; коды остаются стабильными для фронта.

---

## 7) Траблшутинг

- **404 на валидации**: проверьте подключение урла и namespace:
  - `reverse("draft:template-draft-validate")` возвращает `/api/draft/template-drafts/validate/`.
  - `resolve("/api/draft/template-drafts/validate/")` должен попадать во вью.
- **ImproperlyConfigured (DJANGO_SETTINGS_MODULE)**: запускайте через `manage.py` или установите переменную окружения перед вызовами `reverse/resolve`.
- **IntegrityError на TemplateWeek.academic_year**: создайте `AcademicYear` и передавайте в `TemplateWeek`.
- **KTPSection.order NOT NULL**: укажите `order` при создании.
- **Отсутствует дата у KTPEntry**: «короткий путь» отключится; генерация пойдет только от TL — тесты это допускают.

---

## 8) Контрольный список перед релизом

- [ ] Урлы валидатора доступны и покрыты интеграционным smoke.
- [ ] В `settings` корректные `TIME_ZONE` и `USE_TZ=True`.
- [ ] Миграции обеспечивают обязателные FK (`TemplateWeek.academic_year`, `KTPSection.order` по необходимости).
- [ ] Логи валидатора и пайплайна не содержат неожиданных исключений.
- [ ] Тесты `schedule/validators/tests` и `schedule/real_schedule/tests` зелёные.

---

## Приложение: структура ответа валидатора

Поле | Тип | Описание
---- | --- | --------
`code` | `str` | Короткий код: `TEACHER_OVERLAP`, `GRADE_OVERLAP`, `ROOM_OVERLAP`, `ZERO_DURATION`, `MISSING_FIELDS`, …
`severity` | `str` | `error` \| `warning`
`lesson_ids` | `list[int]` | Задействованные уроки из входного пейлоада
`resource` | `str` | `teacher` \| `grade` \| `room` (если применимо)
`resource_id` | `int` | Идентификатор ресурса (если применимо)
`day` | `int` | День недели (1–7)
`range.start|end` | `str` | Локальное время начала/конца в формате `HH:MM`
`message` | `str` | Человекочитаемое сообщение

