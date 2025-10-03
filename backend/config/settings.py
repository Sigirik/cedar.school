"""
Django settings for config project.
"""
from pathlib import Path
from datetime import timedelta
import os

def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Core
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [
    "api.beta.cedar.school",
    "beta.cedar.school",
    "api.dev.cedar.school",
    "dev.cedar.school",
    "127.0.0.1",
    "localhost",
]

# Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "users",
    "schedule.core",
    "schedule.template",
    "schedule.draft",
    "schedule.ktp",
    "schedule.real_schedule.apps.RealScheduleConfig",
    "schedule.webinar",

    "rest_framework",
    "corsheaders",
    "djoser",
    "rest_framework_simplejwt.token_blacklist",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "users.middleware.DisableCSRFMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database: prefer Postgres; fallback to SQLite if envs not set
PG_NAME = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME")
PG_USER = os.getenv("POSTGRES_USER") or os.getenv("DB_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
PG_HOST = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "db"))
PG_PORT = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))
USE_SQLITE = env_bool("USE_SQLITE", False)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        import dj_database_url  # добавь в requirements.txt: dj-database-url==2.2.0 (или убери try/except и парси сам)
        DATABASES = {
            "default": dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
                ssl_require=False,  # включи True, если к внешней БД со строгим SSL
            )
        }
    except Exception:
        # Фоллбек, если dj-database-url не доступен (или не нужен)
        from urllib.parse import urlparse
        u = urlparse(DATABASE_URL)
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": u.path.lstrip("/"),
                "USER": u.username,
                "PASSWORD": u.password,
                "HOST": u.hostname,
                "PORT": u.port or 5432,
                "CONN_MAX_AGE": 600,
                "OPTIONS": {"connect_timeout": 5},
            }
        }
else:
    # Старый вариант через POSTGRES_* для совместимости
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "cedar_beta"),
            "USER": os.getenv("POSTGRES_USER", "cedar_beta"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "CHANGE_ME"),
            "HOST": os.getenv("POSTGRES_HOST", "pg-beta"),
            "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
            "CONN_MAX_AGE": 600,
            "OPTIONS": {"connect_timeout": 5},
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# I18N / TZ
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Moscow")
USE_I18N = True
USE_TZ = True

# Static / Media
STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles"))
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# === Recordings & media serving (DEV) ===
RECORDING_STORAGE = os.getenv("RECORDING_STORAGE", "LOCAL").upper()  # LOCAL | SFTP
RECORDING_LOCAL_DIR = os.getenv("RECORDING_LOCAL_DIR", "/app/recordings")
RECORDING_WEBHOOK_SECRET = os.getenv("RECORDING_WEBHOOK_SECRET", "dev-webhook-secret")
# In DEV we can serve recordings via Django without Nginx
SERVE_RECORDINGS_VIA_DJANGO = env_bool("SERVE_RECORDINGS_VIA_DJANGO", DEBUG)

# Auth / Users
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "/users/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# DRF / Auth
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

AUTHENTICATION_BACKENDS = [
    "users.auth_backends.UsernameOrEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# CORS / CSRF (dev)
# CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
# CSRF_COOKIE_SECURE = False
# CSRF_TRUSTED_ORIGINS = ["http://localhost:5173"]
def _split_csv(name, default=""):
    v = os.getenv(name, default).strip()
    return [x.strip() for x in v.split(",") if x.strip()]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # в dev можно "всё", в prod — нет
CORS_ALLOWED_ORIGINS = _split_csv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173" if DEBUG else ""
)

CSRF_TRUSTED_ORIGINS = _split_csv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:5173" if DEBUG else ""
)
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# За reverse proxy (Nginx) с HTTPS
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REDIRECT_EXEMPT = [r"^health/?$"]
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
X_FRAME_OPTIONS = "DENY"

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# Djoser
DJOSER = {
    "LOGIN_FIELD": "username",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SERIALIZERS": {
        "user": "users.serializers.CustomUserSerializer",
        "current_user": "users.serializers.CustomUserSerializer",
        "password_reset": "users.serializers.PasswordResetUsernameEmailSerializer",
    },
    "PERMISSIONS": {
        "user_create": ["rest_framework.permissions.AllowAny"],
        "user": ["rest_framework.permissions.IsAuthenticated"],
        "user_delete": ["rest_framework.permissions.IsAuthenticated"],
    },
    "PASSWORD_RESET_CONFIRM_URL": "reset-password/{uid}/{token}",
    "EMAIL": {
        "password_reset": "users.emails.CustomPasswordResetEmail",
    },
}

# === Jitsi / JWT (опционально) ===
JITSI_JWT_ENABLED = os.getenv("JITSI_JWT_ENABLED", "0").lower() in ("1","true","yes","on")
JITSI_JWT_APP_ID = os.getenv("JITSI_JWT_APP_ID", "cedar")            # iss
JITSI_JWT_AUD = os.getenv("JITSI_JWT_AUD", "jitsi")                  # aud
JITSI_JWT_SUB = os.getenv("JITSI_JWT_SUB", "jitsi.school.edu")       # sub = ваш домен/tenant
JITSI_JWT_SECRET = os.getenv("JITSI_JWT_SECRET", "")                 # HS256 секрет (для self-hosted mod_auth_token)
JITSI_JWT_TTL_MIN = int(os.getenv("JITSI_JWT_TTL_MIN", "120"))       # срок жизни токена
