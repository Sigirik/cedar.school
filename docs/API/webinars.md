
# Cedar.school — Вебинары (Jitsi). Документация по бэкенду

_Версия: сентябрь 2025_

## 1) Контекст и цели

Мы внедрили вебинарные комнаты на базе **Jitsi**. Требования:

- Автоматическое создание комнаты за **15 минут** до начала урока и автоматическое закрытие через **10 минут** после окончания.
- Гарантия, что у каждого урока — **ровно одна** привязанная комната.
- Роли и права: **учитель** — модератор, **ученик** — участник, **родитель** — наблюдатель. Отдельные роли **директор/завуч/методист/аудитор** — наблюдатели на всех уроках.
- Режим **«открытого урока»**: любой желающий может подключиться по публичной ссылке как наблюдатель; есть специальный фид «открытых».
- Общие собрания - публичные вебинары, на которые может подключиться любой желающий, у которого есть ссылка-приглашение. Пользователь может не быть зарегистрирован на платформе.
- **Запись** каждого урока: стартует в начале, заканчивается в конце вебинара; запись появляется на странице урока после готовности.

Работа велась **только на бэкенде**. Ниже — архитектура, API, конфиги, запуск фоновой логики и чек-листы.

---

## 2) Архитектура и модели

### 2.1 Модель `Room` (связана `OneToOne` с `RealLesson`)

Ключевые поля:

- `type`: `"LESSON"` или `"MEETING"` (общие собрания без привязки к уроку).
- `status`: `"SCHEDULED" | "OPEN" | "CLOSED"`.
- `lesson`: `OneToOne(RealLesson, null=True)` — может быть `null` для `MEETING`.
- `jitsi_domain` (default: `jitsi.school.edu`), `jitsi_room` (уникальное имя комнаты), `jitsi_env="SELF_HOSTED"`.
- `is_open` (bool) — публичная ли комната/урок, `public_slug` — публичный слаг для анонимного входа.
- `scheduled_start`, `scheduled_end`, `started_at`, `ended_at`, `join_url`.
- `auto_manage` (bool) — участвует ли комната в авто-логике (создание/закрытие).
- Поля записи: `recording_status` (`PENDING|IN_PROGRESS|READY|FAILED`), `recording_file_url`, `recording_started_at`, `recording_ended_at`, `recording_duration_secs`, `recording_storage`, `recording_meta` (JSON).

> **Время** храним в UTC; сериализуем в нужные зоны на чтение.

### 2.2 Модель `RealLesson` (добавлено поле)

- `is_open` (bool, default `False`) — флаг «открытого урока», влияет на публичный фид и доступ анонимов.

### 2.3 Таймзоны

- Проектный `TIME_ZONE`: `Europe/Amsterdam` (обсуждалось также `Europe/Moscow`).  
- В коде **не используем** `django.utils.timezone.utc` — вместо этого: `from zoneinfo import ZoneInfo; UTC = ZoneInfo("UTC")`.
- В админ-формах: собственный `DateTimeField` с виджетом `<input type="datetime-local">`, поддержка форматов `YYYY-MM-DDTHH:MM`, `YYYY-MM-DD HH:MM`, `DD.MM.YYYY HH:MM` и нормализация в UTC.

---

## 3) API

### 3.1 Комнаты

#### `GET /api/rooms/by-lesson/{lesson_id}/?force=1`
- **Доступ:** admin, учитель урока; учащиеся/родители могут читать метаданные.
- **Поведение:** создаёт комнату, если сейчас в окне `[start-15m, end+10m]`, иначе возвращает метаданные. `force=1` (admin/teacher) — создаёт вне окна.

#### `POST /api/rooms/meeting/`
- **Доступ:** admin/staff.
- **Вход:** JSON `{ "title": "…", "scheduled_start": "ISO8601", "scheduled_end": "ISO8601", "is_open": true }`.
- **Выход:** объект `Room`.

#### `GET /api/rooms/{id}/`
- Метаданные комнаты (см. сериализатор в `real_schedule/serializers.py`).

#### `POST /api/rooms/{id}/close/`
- Принудительное закрытие: `status="CLOSED"`, `ended_at=now`; по возможности останавливает запись.

### 3.2 Join (подключение)

#### `POST /api/rooms/{id}/join/` (требует auth)
- **Роли:**
  - Учитель урока/со-преподаватель → **moderator**.
  - Ученик, подписанный на предмет (`StudentSubject`) → **participant**.
  - Родитель ученика этого предмета (`ParentChild`) → **observer**.
  - Директор/завуч/методист/аудитор, staff/superuser → **observer** на любых уроках.
  - Иные: в закрытый урок — **403**; в открытый — **observer**.
- **Ответ:** `{ "join_url": "https://<domain>/<room>?jwt=...", "you_are": "moderator|participant|observer" }`.
- При `JITSI_JWT_ENABLED=1` генерируем Jitsi-JWT (HS256) с `nbf/exp` и флагом `moderator` в payload.

#### `POST /api/rooms/public/{slug}/join/` (аноним)
- Только если `Room.is_open=True`.
- **Вход:** `{ "display_name": "…" }` (опц.).
- **Ответ:** `{ "join_url": "...", "you_are": "observer" }`.

### 3.3 Открытые уроки (фид для всей школы)

#### `GET /api/rooms/open-lessons/?hours=48&since_hours=0.1667&all=0`
- Возвращает список элементов вида:
  ```json
  {
    "room_id": 123,
    "public_slug": "cedar-lesson-123",
    "status": "SCHEDULED|OPEN|CLOSED",
    "scheduled_start": "…",
    "scheduled_end": "…",
    "lesson": { ...RealLessonSerializer... }
  }
  ```
- Параметры:
  - `hours` — сколько часов **вперёд**;
  - `since_hours` — сколько часов **назад** (по умолчанию ~10 минут);
  - `all=1` — игнорировать окно, отдать всё.
- Если у открытого урока комнаты нет — создаётся `Room(type="LESSON", is_open=True)` с `public_slug`.

### 3.4 Записи

#### `GET /api/rooms/{id}/recording/`
- Метаданные записи: `{ status, file_url, started_at, ended_at, duration_secs }`.

#### `POST /api/webhooks/jaas/recording/`
- Вебхук для JaaS. Header: `X-Recording-Secret`.
- Тело (адаптировано под dev):  
  `{ "room_id": 7, "preAuthenticatedLink": "https://…/video-0.mp4", "fileExt": "mp4" }`.
- Бэкенд скачивает файл (в DEV можно отключить валидацию TLS; в PROD — включена).

#### `POST /api/rooms/{id}/recording/uploaded/` (internal, self-hosted Jibri)
- Header: `X-Recording-Secret`.
- Тело: `{ "file_path": "/app/recordings/lessons/{id}/<file>.mp4", "file_ext": "mp4" }`.
- Переводит `recording_status` → `READY` и формирует `file_url` (для DEV — через Django static).

### 3.5 Dev-ручки (только при `DEBUG=True`)

- `POST /api/dev/recordings/make-dummy/` — генерирует файл в контейнере.
- `POST /api/dev/recordings/upload/` (multipart) — загружает произвольный файл в `/app/recordings`.

---

## 4) Роли и доступ

| Категория | Урок `is_open=False` | Урок `is_open=True` |
|---|---|---|
| Учитель урока / со-преподаватель | **moderator** | **moderator** |
| Подписанный ученик | **participant** | **participant** |
| Родитель подписанного ученика | **observer** | **observer** |
| Директор / Завуч / Методист / Аудитор / staff / superuser | **observer** | **observer** |
| Прочие авторизованные | **403** | **observer** |
| Аноним | **403** | **observer (по public_slug)** |

Внутри `join_url` при `observer` дополнительно урезаем UI параметрами (mute, no deep-linking, сокращённый toolbar).

---

## 5) Авто-логика (планировщик)

### 5.1 Management-команда

`webinar_maintain` выполняет три действия:

1. **Создание** комнат за 15 минут до начала урока (если ещё нет).
2. **Перевод в OPEN** около старта (опционально).
3. **Закрытие** комнат через 10 минут после `scheduled_end`.

Плюс: предсоздание комнат для открытых уроков на горизонт `N` часов (по умолчанию 48).

### 5.2 Docker Compose — сервис `scheduler` (DEV)

```yaml
scheduler:
  image: cedar-backend:dev
  working_dir: /app
  entrypoint: /bin/sh
  command:
    - -lc
    - |
      set -e
      until python manage.py migrate --noinput; do
        echo "waiting for migrations to apply...";
        sleep 3;
      done
      while :; do
        python manage.py webinar_maintain --once || echo "maintain failed";
        sleep 30;
      done
  env_file:
    - .env
  volumes:
    - ./backend:/app
  depends_on:
    db:
      condition: service_healthy
  restart: unless-stopped
```

**Команды (PowerShell):**
```powershell
docker compose build backend
docker compose up -d backend scheduler
docker compose logs -f scheduler   # выход — Ctrl+C
```

---

## 6) Настройки окружения (`.env` / `settings.py`)

### 6.1 Jitsi / JWT
- `JITSI_JWT_ENABLED=0|1` — включить/выключить выдачу JWT.
- `JITSI_JWT_SECRET=...` — секрет для HS256.
- `JITSI_JWT_APP_ID=cedar` (iss), `JITSI_JWT_AUD=jitsi` (aud), `JITSI_JWT_SUB=jitsi.school.edu` (sub), `JITSI_JWT_TTL_MIN=120`.
- Поля комнаты: `jitsi_domain`, `jitsi_room`. `join_url` собирается как `https://{domain}/{room}` + `?jwt=...`.

### 6.2 Записи
- `RECORDING_STORAGE=LOCAL|SFTP`
- `RECORDING_LOCAL_DIR=/app/recordings` (DEV).
- `SERVE_RECORDINGS_VIA_DJANGO=1` (DEV) / `0` (PROD, раздача nginx/S3).
- `RECORDING_WEBHOOK_SECRET=dev-webhook-secret` — заголовок `X-Recording-Secret` для обоих POST финализации.

SFTP (для PROD, если нужно):
- `SFTP_HOST, SFTP_PORT, SFTP_USERNAME, SFTP_PASSWORD`
- `SFTP_BASE_DIR=/home/user/cedar_recordings`
- `SFTP_PUBLIC_BASE=https://files.example.com/cedar_recordings`

### 6.3 База/таймзоны/медиа
- `TIME_ZONE="Europe/Amsterdam"`
- `USE_TZ=True`
- Маршрут `/media/recordings/…` настроен в urls (DEV), отдаётся Django при `SERVE_RECORDINGS_VIA_DJANGO=1`.

---

## 7) Локальная разработка

- `docker compose up -d db backend`
- Миграции: `docker compose exec backend python manage.py migrate`
- Доступ к админке: `http://localhost:8000/admin/…`
- Медиа-записи в DEV: хранятся в `./dev_data/recordings` (примонтировано в `/app/recordings`).
- Проверка публичной раздачи записи: `GET /api/rooms/{id}/recording/` → поле `file_url` ведёт на `/media/recordings/...` и открывается в браузере.

---

## 8) Примеры запросов (PowerShell)

### 8.1 Создать «общее собрание» (admin)
```powershell
Invoke-WebRequest -Method POST `
  -Uri "$env:BASE/api/rooms/meeting/" `
  -Headers @{ Authorization = "Bearer $env:TOKEN"; "Content-Type"="application/json" } `
  -Body '{ "title":"Общее собрание", "scheduled_start":"2025-09-12T10:00:00+03:00", "scheduled_end":"2025-09-12T11:00:00+03:00", "is_open":true }'
```

### 8.2 Создать/получить комнату по уроку
```powershell
Invoke-WebRequest -Method GET `
  -Uri "$env:BASE/api/rooms/by-lesson/123/?force=1" `
  -Headers @{ Authorization = "Bearer $env:TOKEN" }
```

### 8.3 Приватный join
```powershell
Invoke-WebRequest -Method POST `
  -Uri "$env:BASE/api/rooms/7/join/" `
  -Headers @{ Authorization = "Bearer $env:TOKEN"; "Content-Type"="application/json" } `
  -Body "{}"
```

### 8.4 Публичный join (аноним)
```powershell
Invoke-WebRequest -Method POST `
  -Uri "$env:BASE/api/rooms/public/cedar-lesson-7/join/" `
  -ContentType "application/json" `
  -Body '{ "display_name": "Гость" }'
```

### 8.5 Завершить запись (self-hosted, DEV)
```powershell
Invoke-WebRequest -Method POST `
  -Uri "$env:BASE/api/rooms/7/recording/uploaded/" `
  -Headers @{ "X-Recording-Secret" = "dev-webhook-secret"; "Content-Type"="application/json" } `
  -Body '{ "file_path": "/app/recordings/lessons/7/demo.mp4", "file_ext": "mp4" }'
```

### 8.6 Статус записи
```powershell
Invoke-WebRequest -Method GET `
  -Uri "$env:BASE/api/rooms/7/recording/" `
  -Headers @{ Authorization = "Bearer $env:TOKEN" }
```

### 8.7 Фид открытых уроков
```powershell
Invoke-WebRequest -Method GET -Uri "$env:BASE/api/rooms/open-lessons/?hours=48"
```

---

## 9) Postman (коллекция)

Вставьте в Postman как **Raw JSON** и задайте переменные: `baseUrl`, `access_token`, `room_id`, `lesson_id`, `public_slug`, `recording_secret`.

```json
{
  "info": { "name": "Cedar Webinar API", "_postman_id": "cedar-webinar-collection", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" },
  "item": [
    { "name": "Open lessons feed", "request": { "method": "GET", "header": [], "url": { "raw": "{{baseUrl}}/api/rooms/open-lessons/?hours=48", "host": ["{{baseUrl}}"], "path": ["api","rooms","open-lessons",""], "query":[{"key":"hours","value":"48"}] } } },
    { "name": "Create meeting (admin)", "request": { "method": "POST", "header": [ { "key": "Authorization", "value": "Bearer {{access_token}}" }, { "key": "Content-Type", "value": "application/json" } ], "url": { "raw": "{{baseUrl}}/api/rooms/meeting/", "host": ["{{baseUrl}}"], "path": ["api","rooms","meeting",""] }, "body": { "mode": "raw", "raw": "{\"title\":\"Общее собрание\",\"scheduled_start\":\"2025-09-12T10:00:00+03:00\",\"scheduled_end\":\"2025-09-12T11:00:00+03:00\",\"is_open\":true}" } } },
    { "name": "Get or create by lesson", "request": { "method": "GET", "header": [ { "key": "Authorization", "value": "Bearer {{access_token}}" } ], "url": { "raw": "{{baseUrl}}/api/rooms/by-lesson/{{lesson_id}}/?force=1", "host": ["{{baseUrl}}"], "path": ["api","rooms","by-lesson","{{lesson_id}}",""], "query":[{"key":"force","value":"1"}] } } },
    { "name": "Join (private, auth)", "request": { "method": "POST", "header": [ { "key": "Authorization", "value": "Bearer {{access_token}}" }, { "key": "Content-Type", "value": "application/json" } ], "url": { "raw": "{{baseUrl}}/api/rooms/{{room_id}}/join/", "host": ["{{baseUrl}}"], "path": ["api","rooms","{{room_id}}","join",""] }, "body": { "mode": "raw", "raw": "{}" } } },
    { "name": "Join (public, anonymous)", "request": { "method": "POST", "header": [ { "key": "Content-Type", "value": "application/json" } ], "url": { "raw": "{{baseUrl}}/api/rooms/public/{{public_slug}}/join/", "host": ["{{baseUrl}}"], "path": ["api","rooms","public","{{public_slug}}","join",""] }, "body": { "mode": "raw", "raw": "{\"display_name\":\"Гость\"}" } } },
    { "name": "Recording: finalize (self-hosted)", "request": { "method": "POST", "header": [ { "key": "X-Recording-Secret", "value": "{{recording_secret}}" }, { "key": "Content-Type", "value": "application/json" } ], "url": { "raw": "{{baseUrl}}/api/rooms/{{room_id}}/recording/uploaded/", "host": ["{{baseUrl}}"], "path": ["api","rooms","{{room_id}}","recording","uploaded",""] }, "body": { "mode": "raw", "raw": "{\"file_path\":\"/app/recordings/lessons/{{room_id}}/demo.mp4\",\"file_ext\":\"mp4\"}" } } },
    { "name": "Recording: get status", "request": { "method": "GET", "header": [ { "key": "Authorization", "value": "Bearer {{access_token}}" } ], "url": { "raw": "{{baseUrl}}/api/rooms/{{room_id}}/recording/", "host": ["{{baseUrl}}"], "path": ["api","rooms","{{room_id}}","recording",""] } } }
  ],
  "variable": [
    { "key": "baseUrl", "value": "http://localhost:8000" },
    { "key": "access_token", "value": "" },
    { "key": "room_id", "value": "" },
    { "key": "lesson_id", "value": "" },
    { "key": "public_slug", "value": "" },
    { "key": "recording_secret", "value": "dev-webhook-secret" }
  ]
}
```

---

## 10) Траблшутинг

- **`timezone.utc` не существует (Django 5)** — используем `ZoneInfo("UTC")`.
- **Админка ожидала список «дата+время»** — переписали форму: `DateTimeField` с `input_formats` и парой вспомогательных полей `date/start_time`.
- **`Unknown command: webinar_maintain`** — проверь `INSTALLED_APPS += ['schedule.webinar']`, структуру `management/commands`, наличие `Command(BaseCommand)`.
- **`relation ... does not exist`** — гонка миграций. В `scheduler` сначала `migrate`, затем цикл. Дополнительно в коде сервисов есть `_tables_ready()`.
- **PowerShell заголовки с `curl`** — лучше `Invoke-WebRequest` с `-Headers @{ ... }`.
- **SSL при загрузке записи с внешнего URL** — в DEV используем локальную финализацию `/recording/uploaded/` с заранее положенным файлом.
