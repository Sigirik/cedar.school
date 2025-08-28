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
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

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

    "rest_framework",
    "corsheaders",
    "djoser",
    "rest_framework_simplejwt.token_blacklist",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",          # ⬅️ как можно выше
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "users.middleware.DisableCSRFMiddleware",         # ⬅️ ваш слой
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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

# Database
# Dev: форсим SQLite через USE_SQLITE=1 (общий db.sqlite3 в репозитории).
# Иначе: если заданы POSTGRES_* → Postgres, иначе — SQLite.
# -----------------------------------------------------------------------------
PG_NAME = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_HOST = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "db"))
PG_PORT = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))

USE_SQLITE = env_bool("USE_SQLITE", False)

if not USE_SQLITE and PG_NAME and PG_USER and PG_PASSWORD:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": PG_NAME,
            "USER": PG_USER,
            "PASSWORD": PG_PASSWORD,
            "HOST": PG_HOST,
            "PORT": PG_PORT,
            "CONN_MAX_AGE": 600,
            "OPTIONS": {"connect_timeout": 5},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
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
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

LOGIN_REDIRECT_URL = "/users/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# DRF / Auth
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

AUTHENTICATION_BACKENDS = [
    "users.auth_backends.UsernameOrEmailBackend",  # ← сначала ваш
    "django.contrib.auth.backends.ModelBackend",
]

# CORS / CSRF (dev)
CORS_ALLOW_ALL_ORIGINS = True  # для разработки
CORS_ALLOW_CREDENTIALS = True  # если используете cookies (админка)
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]  # не влияет при ALL=True, но пусть будет
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
]

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

# Email (dev)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
