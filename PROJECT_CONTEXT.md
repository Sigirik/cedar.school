# Cedar.school — Project Context

## 🎯 Цель проекта
Cedar.school — система для онлайн-школы, которая управляет:
- шаблонными неделями расписания (TemplateWeek),
- реальным расписанием (RealLesson),
- календарно-тематическим планированием (КТП),
- ролями пользователей (учитель, ученик, родитель, завуч, директор),
- видеозанятиями (интеграция Jitsi/BBB),
- административными справочниками (классы, предметы, годы, четверти).

Технологии: **Backend — Django/DRF**, **Frontend — React + TypeScript (Vite), FullCalendar**.  
Процесс: GitHub flow (ветка → PR → ревью → merge).  

---
## 🔧 Ссылки
api.dev.cedar.school - бек для разработки
dev.cedar.school - адрес для фонта разработки, если понадобится

api.beta.cedar.school - бек для бетаверсии
beta.cedar.school - адрес для фонта бетаверсии

api.cedar.school - бек для продакшена
cedar.school - адрес для фонта продакшена

---
## 🔧 Архитектура
- **Backend**  
  - Модули: `template/`, `draft/`, `real_schedule/`, `ktp/`, `core/`.  
  - API:
    - `/api/template/` — работа с шаблонной неделей  
    - `/api/draft/` — черновики недели  
    - `/api/real-schedule/` — реальное расписание  
    - `/api/lessons/{id}/` — карточка урока  
    - `/api/rooms/` — вебинарные комнаты  
    - `/api/auth/` — роли, доступы  

- **Frontend**  
  - `WeekViewSwitcher` — переключение режимов (по классам, по учителям, нормы)  
  - `FullCalendarTemplateView` — универсальный календарь (drag-n-drop)  
  - `TemplateWeekEditor` — редактор шаблонной недели  
  - `KtpEditor` — календарно-тематическое планирование  
  - `SchedulePage` — просмотр реального расписания  
  - `LessonPage` — карточка урока  

---

## 👥 Роли пользователей
- **STUDENT / PARENT** — видят своё расписание, темы уроков, доступ к вебинару.  
- **TEACHER** — своё расписание, темы и домашки.  
- **HEAD_TEACHER / DIRECTOR** — управление шаблонными неделями, доступ к расписанию классов/учителей.  
- **ADMIN** — выдача ролей и управление справочниками.  

---

## 📅 План спринта (25–31 августа)

### 1) RealLesson pipeline (Backend)
- Генерация `RealLesson` из активной недели + КТП  
- `commit_draft`: маппинг `type → LessonType`  
- Синхронизация тем КТП в `RealLesson`  

### 2) `/schedule` — Моё расписание (MVP)
**Backend**
- `GET /api/real-schedule/my/?from=&to=` (роль-специфично, student/parent/teacher)  
- Правила доступа: чужие данные → 403  
**Frontend**
- Роут `/schedule`, FullCalendar (без dnd), хук `useMyRealSchedule`  
- Пустое состояние «Нет уроков», клик по событию → `/lesson/:id`  
- 403 → редирект на `/forbidden`  

### 3) Роли и доступы
**Backend**
- Выдача/смена ролей админом  
- Единообразные 403 на защищённых эндпоинтах  
**Frontend**
- Глобальный перехват 403  
- Страница `/forbidden`: «Страница недоступна для роли …»  

### 4) Страница урока
**Backend**
- `GET /api/lessons/{id}/`: тема, участники, материалы, `webinar_url`, `homework_summary?`  
**Frontend**
- Роут `/lesson/:id`, карточка урока  
- Кнопка «Вебинар» (disabled если `null`)  
- Блок «Домашка» (заглушка)  

### 5) TemplateWeekEditor — проверка коллизий (Frontend)
- Кнопка «Проверить коллизии» → вызов `/validate/`  
- Панель проблем (ошибки/варнинги), клик → подсветка/скролл в календаре  

### 6) Вебинарные комнаты
**Backend**
- Модель `Room (lesson_id, join_url, provider)`  
- Эндпоинт создания/получения комнаты  
**Frontend**
- Кнопка «Вебинар» на `/lesson/:id` открывает `join_url`  

### 7) Фильтры/поиск в календарях
**Backend**
- `GET /api/real-schedule/?teacher_id=&grade_id=&subject_id=&from=&to=`  
- `GET /api/template/teachers/?q=` — поиск по ФИО  
**Frontend**
- Панель фильтров (Teacher/Grade/Subject), применение к FullCalendar  

### 8) Тесты
**Backend**
- Юнит-тесты: `_collect_overlap_ids`, `check_collisions`  
**Frontend**
- e2e happy-path: «/schedule → клик → /lesson/:id»  
- Компонентные тесты панели проблем  

---

## ✅ Definition of Done для спринта
- `/schedule` показывает «моё расписание» для student/parent/teacher.  
- Страница урока работает и открывается из расписания.  
- В TemplateWeekEditor можно вручную проверить коллизии.  
- 403 возвращается и ведёт на `/forbidden`.  
- Вебинарные комнаты подключены (кнопка работает).  
- Фильтры работают в расписании (минимально teacher/grade).  
- Бэкенд и фронт покрыты базовыми тестами.  
