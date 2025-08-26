# cedar.school

## 🚀 Описание

Cedar.school — современная система для планирования, заполнения и визуализации школьного расписания на Django.  
Включает шаблонные недели, редактор уроков, справочники предметов, классов и учителей, а также роли пользователей.

---

## 📦 Структура API

Проект разделён на логические зоны:

### 🖥 Web-интерфейс (Django views)
- **URL**: `/schedule/`
- **Файл маршрутов**: `web_urls.py`
- **Файл view**: `web_views.py`
- **Назначение**: страницы с HTML (через `render()`), формы, списки

---

### 📘 Шаблонная неделя
- **URL-префикс**: `/api/template/`
- **Файл маршрутов**: `template_api_urls.py`
- **Файл view**: `template_api_views.py`
- **Основные эндпоинты**:
  - `GET template-week/active/` — получить активную шаблонную неделю
  - `POST template-week/<id>/clone_to_draft/` — скопировать шаблон в черновик
  - `GET template-week/historical_templates/` — список прошлых версий

---

### ✏️ Черновики
- **URL-префикс**: `/api/draft/`
- **Файл маршрутов**: `draft_api_urls.py`
- **Файл view**: `draft_api_views.py`
- **Основные эндпоинты**:
  - `POST template-drafts/` — создать новый черновик
  - `POST template-drafts/create-from/<id>/` — создать черновик из шаблона
  - `POST template-drafts/create-empty/` — создать пустой черновик
  - `POST template-drafts/<id>/commit/` — утвердить черновик как активный шаблон

---

### 📚 КТП и справочники
- **URL-префикс**: `/api/ktp/`
- **Файл маршрутов**: `ktp_api_urls.py`
- **Файл view**: `ktp_api_views.py`
- **Сущности**:
  - `ktp-templates/`, `ktp-sections/`, `ktp-entries/`
  - `subjects/`, `grades/`, `teachers/`, `weekly-norms/`
  - `teacher-subjects/`, `teacher-grades/`, `grade-subjects/`, `student-subjects/`
  - `lesson-types/`, `teacher-availabilities/`, `academic-years/`

---

### 👤 Пользователи и роли

- **Файл моделей**: `users/models.py`
- **Основные роли**: `TEACHER`, `STUDENT`, `PARENT`, `DIRECTOR`, `HEAD_TEACHER`, `ADMIN`, `AUDITOR`
- **Профиль пользователя**: поддержка поля "отчество", принадлежности к классу, индивидуальных предметов, флаг индивидуального выбора предметов (`individual_subjects_enabled` для учеников)
- **Сериализация и API**: все сериализаторы пользователей и их связей в `users/serializers.py`, используемые в API

---

## ✅ Общие принципы
- Все API построены на DRF (Django REST Framework)
- ViewSet'ы регистрируются через `DefaultRouter`
- Одно namespace = один модуль (web / template / draft / ktp / users)
- Справочники, связи (учитель-предмет, ученик-предмет, класс-предмет) реализованы в core, доступны через API и в админке
- Все модели снабжены русскими именами (`verbose_name` и `verbose_name_plural`), для админки и API

---

## 🛠 Автоматическое заполнение базы (seed-скрипты)

- В проекте есть скрипты для быстрого наполнения:
  - создания типовых учителей, классов, предметов
  - генерации связей и доступности учителей
  - заполнения норм и шаблонной недели с уроками
- Скрипты можно запускать как management commands или через отдельные скрипты с `django.setup()`
- Пример запуска management-команды:
  ```sh
  python manage.py fill_template_week

# Первый старт (dev)
docker compose up --build

- Бэкенд автоматически прогонит миграции.
- Если в БД нет данных, он загрузит seed/dev_seed.json.
- Повторные запуски сид не перезаливают.

Ручные команды:
docker compose exec backend python manage.py loaddata seed/dev_seed.json
docker compose exec backend python manage.py migrate

Мини-шпаргалка по командам docker

Запуск:
docker compose up -d

Логи бэка:
docker compose logs -f web

Одноразовые Django-команды (внутри запущенного сервиса):
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

Пересобрать (если поменялся requirements.txt):
docker compose up -d --build

Остановить:
docker compose down