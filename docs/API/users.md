# Cedar.school API — Users

Эндпоинты пользователей, учителей, учеников, заявок на роль и упрощённой регистрации.

---

## 👤 Текущий пользователь
- `GET /api/users/me/` — алиас, отдаёт текущего пользователя (удобно фронту).  
- `GET /api/auth/users/me/` — каноничный эндпоинт Djoser.

## 👥 Users (ReadOnly) + set-role
- `GET /api/users/` — список пользователей.  
- `GET /api/users/:id/` — пользователь по id.  
- `POST /api/users/:id/set-role/` — назначение роли (**только ADMIN**).  
  **Body пример:** `{ "role": "TEACHER" }`

## 👩‍🏫 Teachers (ReadOnly)
- `GET /api/teachers/` — список учителей.  
- `GET /api/teachers/:id/` — учитель по id.

## 🧒 Students (ReadOnly)
- `GET /api/students/` — список учеников.  
- `GET /api/students/:id/` — ученик по id.

## 📝 Role Requests
- `GET /api/role-requests/` — список заявок (DIRECTOR — все, HEAD_TEACHER — STUDENT/PARENT, остальные — свои).  
- `POST /api/role-requests/` — создать заявку (обычно STUDENT или PARENT).  
- `GET /api/role-requests/allowed-roles/` — роли, доступные текущему пользователю.  
- `POST /api/role-requests/:id/approve/` — утвердить заявку.  
- `POST /api/role-requests/:id/reject/` — отклонить заявку.

## 🪪 Регистрация (CSRF‑exempt)
- `POST /api/registration/users/` — упрощённая регистрация без CSRF (Djoser).  
  **Body пример:**  
  ```json
  {
    "username": "newuser",
    "password": "pass12345",
    "re_password": "pass12345"
  }
  ```

## 🔐 Права доступа
- `IsAdminRole` — проверяет, что у пользователя роль = ADMIN.  
- Остальные эндпоинты — минимум `IsAuthenticated`.
