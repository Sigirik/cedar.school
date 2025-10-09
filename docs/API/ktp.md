# Cedar.school — API модуля КТП

КТП включает три сущности: **шаблон КТП** (Template), **раздел** (Section) и **запись урока** (Entry). Базовые CRUD-эндпоинты предоставлены через `ModelViewSet` для каждой сущности.

> Примечание о префиксе: ниже используется базовый префикс `/api/ktp/`. В проектных `urls.py` он должен подключаться к `ktp.urls` под этим префиксом. Внутри модуля зарегистрированы маршруты `templates/`, `sections/`, `entries/` благодаря `DefaultRouter`.

---

## Модели данных

### KTPTemplate
Шаблон КТП объединяет **предмет**, **класс** и **учебный год**; хранит ссылку на «последнюю использованную» шаблонную неделю расписания для распределения дат.

**Поля:**
- `subject: ForeignKey(Subject)`
- `grade: ForeignKey(Grade)`
- `academic_year: ForeignKey(AcademicYear)`
- `last_template_week_used: ForeignKey(TemplateWeek, null, blank)`
- `name: CharField`
- `created_at: DateTimeField(auto_now_add=True)`

### KTPSection
Раздел внутри конкретного шаблона КТП.

**Поля:**
- `ktp_template: ForeignKey(KTPTemplate, related_name='sections')`
- `title: CharField`
- `description: TextField(blank=True, null=True)`
- `order: PositiveIntegerField` — порядок разделов
- `hours: PositiveIntegerField(default=0)` — часы в разделе
- `created_at: DateTimeField(auto_now_add=True)`
- `updated_at: DateTimeField(auto_now=True)`

Секции сортируются по `order` (возрастанию).

### KTPEntry
Единица плана — один урок/занятие.

**Поля:**
- `section: ForeignKey(KTPSection, related_name='entries')`
- `lesson_number: PositiveIntegerField(default=1)`
- `type: CharField(choices=[('lesson','Урок'),('course','Курс')], default='lesson')`
- `planned_date: DateField(null, blank)`
- `actual_date: DateField(null, blank)`
- `title: CharField`
- Текстовые поля: `objectives`, `tasks`, `homework`, `materials`, `planned_outcomes`, `motivation` (все допускают `blank/null`)
- `order: PositiveIntegerField` — позиция внутри раздела
- `template_lesson: ForeignKey(TemplateLesson, null, blank)`
- `created_at: DateTimeField(auto_now_add=True)`
- `updated_at: DateTimeField(auto_now=True)`

Записи сортируются по `order` (возрастанию).

---

## Сериалайзеры и бизнес-правила

### KTPEntrySerializer
- Многие поля помечены **необязательными** (`extra_kwargs`): `title`, текстовые поля, `planned_date/actual_date`, `template_lesson`.
- При **создании** (`create`):
  - если `lesson_number` не передан — назначается как `max(lesson_number)+1` в рамках секции;
  - если `order` не передан — назначается как `max(order)+1` в рамках секции.

### KTPSectionSerializer
- Возвращает вложенный список `entries` (read-only) данной секции.

### KTPTemplateSerializer
- Возвращает вложенный список `sections` (read-only).

---

## Эндпоинты

Базовые CRUD-операции предоставляются для каждого ресурса.

### Templates
- `GET /api/ktp/templates/` — список шаблонов
- `POST /api/ktp/templates/` — создать шаблон  
  Пример запроса:
  ```json
  {
    "name": "КТП по математике 5А 2025–2026",
    "subject": 10,
    "grade": 5,
    "academic_year": 2
  }
  ```
- `GET /api/ktp/templates/{id}/` — детально
- `PATCH /api/ktp/templates/{id}/` — частичное обновление
- `DELETE /api/ktp/templates/{id}/` — удалить

### Sections
- `GET /api/ktp/sections/` — список разделов
- `POST /api/ktp/sections/` — создать раздел  
  Пример запроса:
  ```json
  {
    "ktp_template": 1,
    "title": "Раздел 1. Натуральные числа",
    "order": 1,
    "hours": 12,
    "description": ""
  }
  ```
- `GET /api/ktp/sections/{id}/` — детально
- `PATCH /api/ktp/sections/{id}/` — частичное обновление
- `DELETE /api/ktp/sections/{id}/` — удалить

### Entries
- `GET /api/ktp/entries/` — список записей (уроков)
- `POST /api/ktp/entries/` — создать запись  
  Пример минимального запроса:
  ```json
  {
    "section": 1,
    "title": "Урок 1. Введение"
  }
  ```
  > Если не указаны `lesson_number` и/или `order`, они будут назначены автоматически по правилам сериалайзера.
- `GET /api/ktp/entries/{id}/` — детально
- `PATCH /api/ktp/entries/{id}/` — частичное обновление
- `DELETE /api/ktp/entries/{id}/` — удалить

> Историческая заметка: ранее использовались пути `/api/ktp/ktptemplate/`, `/api/ktp/ktpsection/`, `/api/ktp/ktpentry/`. Текущая реализация использует `templates/`, `sections/`, `entries/` через роутер.

---

## Утилиты планирования дат (ktp/utils.py)

Функции для синхронизации КТП с **шаблонной неделей** расписания и автогенерации дат:

- `get_template_schedule(template_week, subject, grade)` — вернуть уроки шаблонной недели по предмету и классу (отсортированы по дню/времени).
- `is_schedule_changed(old_tw, new_tw, subject, grade)` — сравнить «снимки» расписания по составу уроков, времени и учителю.
- `get_next_monday(start_date=None)` — получить ближайший понедельник от заданной даты или «сегодня».
- `is_holiday_or_vacation(date)` — заглушка проверки каникул/праздников (TODO).
- `generate_ktp_dates_from_template(ktp_template, template_week, start_date=None)` — разложить **плановые даты (`planned_date`)** по записям КТП, проходя календарём вперёд и пропуская каникулы/праздники; обновляет `last_template_week_used` у шаблона КТП. Возвращает количество обновлённых записей.

> Примечание: внутри `generate_ktp_dates_from_template` выбор записей должен идти по выражению `KTPEntry.objects.filter(section__ktp_template=ktp_template)` (если в коде используется `section__template`, это требуется исправить).

---

## Сигналы и инициализация

`apps.py` подключает `ktp.signals` при старте приложения через `ready()`. Используйте `ktp/signals.py` для автоматических действий (например, автогенерация дат после изменения шаблонной недели).

---

## Права доступа

В текущих `ViewSet` явных пермишенов/фильтров не задано — используются глобальные настройки DRF. При необходимости ограничить доступ (по ролям/школе), добавьте `permission_classes` и фильтрацию queryset в соответствующие ViewSet’ы.

---

## Примеры (cURL)

Создать шаблон КТП:
```bash
curl -X POST http://127.0.0.1:5401/api/ktp/templates/  -H "Authorization: Bearer <token>" -H "Content-Type: application/json"  -d '{"name":"КТП Математика 5А 2025–2026","subject":10,"grade":5,"academic_year":2}'
```

Добавить раздел:
```bash
curl -X POST http://127.0.0.1:5401/api/ktp/sections/  -H "Authorization: Bearer <token)" -H "Content-Type: application/json"  -d '{"ktp_template":1,"title":"Раздел 1. Натуральные числа","order":1,"hours":12}'
```

Добавить запись урока (минимум полей):
```bash
curl -X POST http://127.0.0.1:5401/api/ktp/entries/  -H "Authorization: Bearer <token>" -H "Content-Type: application/json"  -d '{"section":1,"title":"Урок 1. Введение"}'
```
