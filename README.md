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

# **DOCKER**

## Весь стек
# запустить (создаст, если ещё нет)
docker compose up -d
# остановить (не удаляя)
docker compose stop
# перезапустить
docker compose restart
# посмотреть состояние
docker compose ps
# логи (в реальном времени)
docker compose logs -f

## Только backend
# запустить только backend (и db подтянется, если нужно)
docker compose up -d backend
# остановить только backend
docker compose stop backend
# перезапустить только backend
docker compose restart backend
# логи backend (последние 200 строк)
docker compose logs backend --tail 200
docker compose logs -f backend     # “follow”

## Полная пересборка / пересоздание
# пересоздать контейнеры без удаления томов (быстро)
docker compose up -d --force-recreate
# пересобрать образы (если менялся Dockerfile/requirements)
docker compose build
docker compose up -d
# жёсткая пересборка без кэша
docker compose build --no-cache
docker compose up -d

**Алгоритм работы с Git (для двоих)**
Общие правила

Базовые ветки:
main (прод) ← staging (сборка) ← be/test и fe/test (интеграция своих PR).

Рабочие ветки всегда из соответствующей test-ветки:
BE → feature/be/<task> от be/test
FE → feature/fe/<task> от fe/test

Маленькие PR (≤300 SLOC), один логический смысл.

PowerShell-команды без &&.

# **Для бэкенда**
0) Сначала приведи рабочее дерево в чистое состояние

Вариант A — сохранить текущие правки:

git add -A
git commit -m "wip: local changes before switching branches"


Вариант B — отложить (stash), если коммитить не хочешь:

git stash push -u -m "temp before switching to staging"

1) Убедись, что be/test свежая
git checkout be/test
git pull origin be/test

2) От ветки staging создай промоут-ветку
git checkout staging
git pull origin staging
git checkout -b promote/backend-to-staging-YYYYMMDD

3) Притяни только нужные пути из be/test

(backend целиком + файлы в корне; список можно скорректировать под твой репозиторий)

# из be/test «принеси» каталоги/файлы в текущую ветку
git checkout be/test -- backend/
git checkout be/test -- docker-compose.yml
git checkout be/test -- docker-compose.override.yml
git checkout be/test -- .gitattributes
git checkout be/test -- .gitignore
git checkout be/test -- README.md
# добавь другие корневые файлы, если нужны: e.g. .env.example, Makefile и т.п.


Посмотри, что изменилось:

git status
git diff --name-only

4) Закоммить и запушить
git add -A
git commit -m "promote: backend + root from be/test (exclude frontend)"
git push -u origin promote/backend-to-staging-YYYYMMDD

### Старая инструкция
1. Обновиться:
git fetch origin
git checkout be/test
git pull
2. Создать рабочую ветку:
git checkout -b feature/be/<task-key>-short
3. Работать → коммиты:
git add -A
git commit -m "be: <кратко что сделали>"
git push -u origin feature/be/<task-key>-short
4. PR → be/test
Создай PR (GitHub UI или gh pr create --base be/test --head feature/be/<...>).
В PR — чек-лист (см. ниже шаблон).
5. После аппрува/CI зелёный → Merge в be/test.
6. Промоут в staging:
git checkout staging
git pull
git merge be/test
git push origin staging
(или PR be/test → staging — если нужно review)
7. Релиз (когда FE тоже влит в staging и e2e ок):
PR staging → main, после мержа поставить тег v0.1.0.

# **Для фронтенда**
1. Обновиться:
git fetch origin
git checkout fe/test
git pull
2. Создать рабочую ветку:
git checkout -b feature/fe/<task-key>-short
3. Работать → коммиты:
git add -A
git commit -m "fe: <кратко что сделали>"
git push -u origin feature/fe/<task-key>-short
4. PR → fe/test (чек-лист ниже).
5. После аппрува/CI зелёный → Merge в fe/test.
6. Промоут в staging (когда нужно собрать вместе с BE):
git checkout staging
git pull
git merge fe/test
git push origin staging
(или PR fe/test → staging)
7. Релиз: PR staging → main (совместно с BE).