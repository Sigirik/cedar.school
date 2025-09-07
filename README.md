# cedar.school

## 🚀 Описание

Cedar.school — система для планирования и визуализации школьного расписания (Django + DRF backend, React frontend). Поддерживает шаблонные недели, черновики, реальное расписание, КТП, справочники и роли пользователей.

---

## 📚 Документация API (локально в репозитории)

Папка: `docs/API/`

- **Auth & Core**  
  - Док: `docs/API/core.md`
- **Draft (TemplateWeekDraft)**  
  - Док: `docs/API/draft.md`
- **Template (Active Week & Lessons)**  
  - Док: `docs/API/template.md`
- **КТП (Календарно-тематический план)**  
  - Док: `docs/API/ktp.md`
- **Real Schedule (реальное расписание)**  
  - Док: `docs/API/real_schedule.md`
- **Users**
  - Док: `docs/API/users.md`

> Все разделы синхронизированы с текущими urls.py/views.py модулей.

---

## 🧭 Карта REST API (по модулям)

### Template (шаблонная неделя)
- Префикс: `/api/template/`
- `GET /api/template/active-week/` — активная неделя (или 404)【77†source】【78†source】
- `GET /api/template/weeks/`, `GET /api/template/weeks/:id/` — список/конкретная неделя【77†source】【78†source】
- CRUD по урокам: `/api/template/templatelesson/` (если зарегистрирован ViewSet)【77†source】

### Draft (черновики шаблонной недели)
- Префикс: `/api/draft/`
- Ручки: `template-drafts/`, `create-from/`, `create-empty/`, `update/`, `:draft_id/commit/`, `exists/`, `validate/`【67†source】【68†source】

### Core (справочники)
- Префикс: `/api/core/`
- ReadOnly: `grades/`, `subjects/`, `availabilities/`, `weekly-norms/`, `lesson-types`
- CRUD: `academic-years/`, `grade-subjects/`, `teacher-subjects/`, `teacher-grades/`, `student-subjects/`, `quarters/`, `holidays`

### КТП
- Префикс: `/api/ktp/`
- CRUD: `ktptemplate/`, `ktpsection/`, `ktpentry/`【88†source】

### Реальное расписание
- Префикс: `/api/real_schedule/`
- `GET /api/real_schedule/my/?from=&to=` — моё расписание (роль-зависимо)【125†source】
- `POST /api/real_schedule/generate/` — генерация (поддержка template_week_id, rewrite_from, debug)【124†source】
- `POST /api/real_schedule/lessons/:id/conduct/` — отметить урок проведённым【124†source】
- `POST /api/real_schedule/rooms/get-or-create/`, `POST /api/real_schedule/rooms/:id/end/` — видеокомнаты【124†source】

### Users
- Префикс: `/api/`
- Users (ReadOnly): `GET /api/users/`, `GET /api/users/:id/`
- Назначение роли: `POST /api/users/:id/set-role/` *(ADMIN, IsAdminRole)*
- Teachers (ReadOnly): `GET /api/teachers/`, `GET /api/teachers/:id/`
- Students (ReadOnly): `GET /api/students/`, `GET /api/students/:id/`
- Role Requests: `GET/POST /api/role-requests/`, `GET /api/role-requests/:id/`, `DELETE /api/role-requests/:id/`
  - Actions: `GET /api/role-requests/allowed-roles/`, `POST /api/role-requests/:id/approve/`, `POST /api/role-requests/:id/reject/`
- Текущий пользователь: `GET /api/users/me/` (алиас к Djoser `users/me/`)
- Регистрация (CSRF-exempt): `POST /api/registration/users/`
---

## 🔐 Аутентификация

- Djoser + JWT (`/api/auth/`):
  - `POST /api/auth/jwt/create/` — логин (username/password)
  - `POST /api/auth/jwt/refresh/` — обновление access-токена
  - `GET /api/auth/users/me/` — текущий пользователь  
- В Postman используйте заголовок: `Authorization: Bearer {{access_token}}`  
- Рекомендуется сохранять токен в Environment переменную `access_token`.

---

## 🚀 Быстрый старт (dev)

```powershell
# Windows PowerShell

# 1) Запуск
docker compose up -d --build

# 2) Миграции
docker compose exec backend bash -lc "python manage.py migrate"

# 3) (Опционально) суперпользователь
docker compose exec backend bash -lc "python manage.py createsuperuser"

# 4) Smoke-тест JWT авторизации
$resp = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/jwt/create/" `
  -Method POST -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin"}'
$token = $resp.access
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/api/core/grades/" -Headers $headers
```

---

## 🧩 Postman

1) Импортируйте коллекции из `docs/API/*.json`.  
2) Выберите Environment (например, `Local dev`) с переменными:
   - `baseUrl = http://localhost:8000`
   - `access_token` (после **Login** в Core сохраняется в *Environment*)  
3) Порядок:
   - **Login** (Core) → токен → {{access_token}}
   - Далее Draft/Template/KTP/Real Schedule работают автоматически.

---

## 🧪 Тесты

```powershell
# Все тесты backend
docker compose exec backend bash -lc "pytest -q"

# Запуск одного файла
docker compose exec backend bash -lc "pytest backend/schedule/real_schedule/tests/test_generate.py -q -k generate"
```

---

## 🌿 Git-процесс

- Базовые ветки: `main` (prod) ← `staging` ← `be/test`, `fe/test`
- Рабочие: `feature/be/<task>` от `be/test`, `feature/fe/<task>` от `fe/test`
- Маленькие PR (≤300 строк), один смысл

```powershell
git checkout be/test
git pull
git checkout -b feature/be/<task>
# ... правки ...
git add -A
git commit -m "be: <что сделали>"
git push -u origin feature/be/<task>
# PR → base: be/test
```

---

## 📁 Структура docs

```
docs/
└─ API/
   ├─ core.md
   ├─ draft.md
   ├─ template.md
   ├─ ktp.md
   ├─ real_schedule.md
   ├─ Cedar_core_postman_collection.json
   ├─ Cedar_draft_postman_collection_reuse_env_token.json
   ├─ Cedar_template_postman_collection.json
   ├─ Cedar_ktp_postman_collection.json
   └─ Cedar_real_schedule_postman_collection.json
```

---

### Ссылки на исходники маршрутов

- real_schedule/urls.py — my, generate, conduct, rooms【123†source】
- real_schedule/views.py — генерация, проведение, комнаты【124†source】
- real_schedule/views_my.py — моё расписание【125†source】
