# cedar.school

## 📦 Структура API

Проект разделён на логические зоны по назначению:

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

---

## ✅ Общие принципы
- Все API построены на DRF (Django REST Framework)
- ViewSet'ы регистрируются через `DefaultRouter`
- Одно namespace = один модуль (web / template / draft / ktp)

---

📁 Структура внутри `schedule/` соответствует маршрутам:
```
schedule/
├── web_views.py / web_urls.py
├── template_api_views.py / template_api_urls.py
├── draft_api_views.py / draft_api_urls.py
├── ktp_api_views.py / ktp_api_urls.py
```

---

🔗 В `config/urls.py` это выглядит так:
```py
urlpatterns = [
    path("schedule/", include("schedule.web_urls")),
    path("api/template/", include("schedule.template_api_urls")),
    path("api/draft/", include("schedule.draft_api_urls")),
    path("api/ktp/", include("schedule.ktp_api_urls")),
]
```