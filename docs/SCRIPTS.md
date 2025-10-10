# Cedar.school — Скрипты заполнения данных (backend/scripts)

Документ описывает **как запускать** сидеры на окружениях **local** и **dev**, а также **что именно делает** каждый скрипт. Скрипты идемпотентны: их можно запускать повторно — они не создают дубликаты, а мягко актуализируют данные.

> Путь ко всем файлам: `backend/scripts/`

---

## Как запускать

### Локальное окружение (Docker Compose)

Из каталога `deploy/compose`:

```powershell
# общий вид
docker compose -f docker-compose.local.yml exec api-local bash -lc "python scripts/<имя_скрипта>.py"

# примеры
docker compose -f docker-compose.local.yml exec api-local bash -lc "python scripts/seed_school_basics.py"
docker compose -f docker-compose.local.yml exec api-local bash -lc "python scripts/seed_users_basic.py"
docker compose -f docker-compose.local.yml exec api-local bash -lc "python scripts/seed_template_week.py"
docker compose -f docker-compose.local.yml exec api-local bash -lc 'python scripts/seed_ktp_basic.py'
```

> Все скрипты сами бутстрапят Django через `DJANGO_SETTINGS_MODULE=backend.settings` и **не требуют** `manage.py`.

### Dev-окружение (Docker Compose на сервере)

На dev‑сервере команды аналогичны, но с вашим dev‑compose-файлом и сервисом API. Наиболее частый вариант:
docker compose -f docker-compose.yml exec api-dev bash -lc "python scripts/seed_school_basics.py"
docker compose -f docker-compose.yml exec api-dev bash -lc "python scripts/seed_users_basic.py"
docker compose -f docker-compose.yml exec api-dev bash -lc "python scripts/seed_template_week.py"
docker compose -f docker-compose.yml exec api-dev bash -lc 'python scripts/seed_ktp_basic.py'

```bash
# из каталога с docker-compose.dev.yml
docker compose -f docker-compose.dev.yml exec api-dev bash -lc "python backend/scripts/<имя_скрипта>.py"
```

Если названия файла и/или сервиса отличаются — подставьте ваши (`-f ...dev.yml`, `api-dev` и т.п.).

---

## Порядок запуска (рекомендуемый)

1. **Базовые справочники и учебный год** → `seed_school_basics.py`  
2. **Пользователи, роли, связи и доступности** → `seed_users_basic.py`  
3. **Шаблонная неделя без пересечений** → `seed_template_week.py`  
4. **КТП по 4 предметам** → `seed_ktp_basic.py`  

> Такой порядок гарантирует, что предметы/классы/нормы и учителя уже существуют к моменту генерации расписания и КТП.

---

## Скрипты

### 1) `seed_school_basics.py`
Создаёт все базовые сущности для школы.

- **Ступени** 1..11.  
- **Параллели** «А», «Б».  
- **Классы** 1А..11Б с корректной привязкой к ступени и параллели.  
- **Предметы**: Математика, Русский язык, Английский язык, Чтение, Окружающий мир.  
- **Связи класс–предмет**: все 5 предметов для 1–4 классов; дополнительно математика для 5–6; русский и английский — до 11.  
- **Недельные нормы**: Математика 5/нед, Русский 5/нед, Английский 3/нед (для всех классов).  
- **Типы уроков**: Обычный, Практика, Контрольная, Экзамен, Собрание.  
- **Учебный год** 2025–2026 — помечается текущим (`is_current=True`), остальные годы снимаются с «текущего».

Ссылка на исходник: `backend/scripts/seed_school_basics.py`. fileciteturn9file1

**Запуск:**
```powershell
docker compose -f docker-compose.local.yml exec api-local bash -lc "python backend/scripts/seed_school_basics.py"
```

---

### 2) `seed_users_basic.py`
Создаёт пользователей, роли и связи, а также доступности учителей. Идempotentно.

- **Суперпользователь**: `Admin / Ced@rAdm1n` (`admin@example.com`) — создаётся, если отсутствует; гарантируются флаги `is_staff`, `is_superuser`, `is_active`.  
- **Пользователи**:  
  - Завуч `Head_teacher / Ced@rH3T3` — роль *HEAD_TEACHER*;  
  - Учитель‑гуманитарий `Gumanitarii / Ced@r6um` — роль *TEACHER*;  
  - Учитель‑технарь `Tehnar / Ced@rTehnar1` — роль *TEACHER*;  
  - Ученик `Student / Ced@rStu6` — роль *STUDENT*;  
  - Родитель `Parent / Ced@r5ar3nt` — роль *PARENT*.  
  Все аккаунты **активируются** (`is_active=True`).  
- **Учителя ↔ предметы**: привязка **только к уже существующим предметам** из базового сидера. Отсутствующие — пропускаются с логом.  
  - Гуманитарий: История, Русский, Английский, География (пропуск, если каких‑то нет).  
  - Технарь: Математика, Физика, Информатика (пропуск, если каких‑то нет).  
- **Учителя ↔ классы**:  
  - Гуманитарий → 5 и 6 классы;  
  - Технарь → 6 и 7 классы.  
- **Родитель ↔ ребёнок**: `Parent → Student`.  
- **Доступности** (`TeacherAvailability`), Пн–Пт:  
  - Технарь: **08:00–11:00**;  
  - Гуманитарий: **09:00–13:00**.  

Ссылка на исходник: `backend/scripts/seed_users_basic.py`. fileciteturn9file3

**Запуск:**
```powershell
docker compose -f docker-compose.local.yml exec api-local bash -lc "python backend/scripts/seed_users_basic.py"
```

---

### 3) `seed_template_week.py`
Генерирует **шаблонную неделю** без пересечений — ровно **30 уроков** (по 10 на каждый из 5,6,7 классов; по 2 урока в день на класс).

- Предметы: **Математика, Русский язык, История, Информатика**.  
- **Нормы**: История = норма **+1**; Русский = норма **−1**; остальные **по норме** (если норм нет — применяются мягкие дефолты с последующей нормализацией до 10/класс).  
- **Учителя строго закреплены**: Технарь → Математика/Информатика; Гуманитарий → Русский/История.  
- Учитываются **TeacherSubject/TeacherGrade** и **TeacherAvailability**.  
- **Длительность** урока — 45 мин, **перерыв** — 15 мин. Сетка начинается ровно в `:00`.  
- Слоты без пересечений: Технарь — 8/9/10; Гуманитарий — 11/12 (приоритет), затем 9/10/13.  
- Создаётся новый активный `TemplateWeek` и набор `TemplateLesson` с проверкой занятости учителя/класса.

Ссылка на исходник: `backend/scripts/seed_template_week.py`. fileciteturn9file2

**Запуск:**
```powershell
docker compose -f docker-compose.local.yml exec api-local bash -lc "python backend/scripts/seed_template_week.py"
```

---

### 4) `seed_ktp_basic.py`
Создаёт **КТП** для 4 предметов (математика, русский, история, информатика) для **5–7 классов** — только если у пары *класс–предмет* есть подходящий учитель (по связям **TeacherSubject** и **TeacherGrade**).

- Для каждой пары *(класс, предмет)* создаётся `KTPTemplate` на **текущий учебный год** (либо последний по датам; при отсутствии — создаётся 2025–2026).  
- Привязка к последней `TemplateWeek` этого учебного года — в поле `last_template_week_used` (если неделя есть).  
- В каждом КТП — **2 раздела** (`KTPSection`, `order=1,2`, по 10 часов) и в каждом разделе **10 тем** (`KTPEntry`, `order=1..10`, `lesson_number=1..10`, `type='lesson'`).  
- Учителя **жёстко закреплены по предметам**:  
  - `Tehnar` → Математика, Информатика;  
  - `Gumanitarii` → Русский язык, История.  
- Пропуски (нет предмета/учителя/связи) выводятся в лог, сидер продолжает работу.

Ссылка на исходник: `backend/scripts/seed_ktp_basic.py`. fileciteturn9file0

**Запуск:**
```powershell
docker compose -f docker-compose.local.yml exec api-local bash -lc "python backend/scripts/seed_ktp_basic.py"
```

---

## Частые вопросы

- **Можно ли запускать выборочно?** — Да, скрипты независимы, но лучше соблюдать порядок из раздела «Порядок запуска».  
- **Что если предметов История/Информатика нет?** — `seed_template_week.py` при необходимости создаёт их; `seed_users_basic.py` *не* создаёт предметы и просто пропускает привязки, которых нет (с логом).  
- **Как проверить результат?** — через админку `http://127.0.0.1:5401/admin/` (локально) и API (например, `/api/ktp/templates/`, `/api/template/weeks/`, `/api/template/lessons/` — реальные пути зависят от вашего роутинга).

---

## Технические детали

- Каждый скрипт самостоятельно загружает Django‑контекст (`backend.settings`) и использует `apps.get_models()` для доступа к моделям, что упрощает переносимость между окружениями.  
- Изменения выполняются в рамках транзакций там, где это важно (`@transaction.atomic`).  
- Повторные запуски безопасны: используются `get_or_create`, «мягкие» обновления полей и логирование пропущенных элементов.
