"""Django settings for the Testownik AI backend.

All environment-specific values are read from environment variables
(or a local ``.env`` file, see ``.env.example``).
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    AI_PROVIDER=(str, "mock"),
    OLLAMA_BASE_URL=(str, "http://localhost:11434"),
    OLLAMA_MODEL=(str, "llama3.1:8b"),
    GEMINI_API_KEY=(str, ""),
    GEMINI_MODEL=(str, "gemini-3.5-flash-lite"),
    MAX_UPLOAD_SIZE_MB=(int, 100),
    MOCK_GENERATION_SECONDS=(float, 4.0),
    AI_LOG_LEVEL=(str, "INFO"),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    # Local
    "apps.generation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

# Stage 1 has no persistent data, so SQLite is enough. Set DATABASE_URL to
# e.g. postgres://testownik:testownik@localhost:5432/testownik to use PostgreSQL.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Uploads ---------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = env("MAX_UPLOAD_SIZE_MB")
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# REST framework / OpenAPI ----------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Stage 1 has no user accounts.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Testownik AI API",
    "DESCRIPTION": "REST API generating Testownik quiz databases from study materials.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# CORS (only needed when the frontend is not served through the Vite proxy) -----
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

# AI module ---------------------------------------------------------------------
AI_PROVIDER = env("AI_PROVIDER")  # "mock" | "gemini" | "ollama"
OLLAMA_BASE_URL = env("OLLAMA_BASE_URL")
OLLAMA_MODEL = env("OLLAMA_MODEL")
GEMINI_API_KEY = env("GEMINI_API_KEY")
GEMINI_MODEL = env("GEMINI_MODEL")
# How long a mocked generation job pretends to run (to exercise the progress bar).
MOCK_GENERATION_SECONDS = env("MOCK_GENERATION_SECONDS")
# Run generation jobs in a background thread (tests switch this off).
GENERATION_RUN_IN_BACKGROUND = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        # DEBUG logs the material sent to the model and its raw response.
        "ai_engine": {"handlers": ["console"], "level": env("AI_LOG_LEVEL")},
        "apps": {"handlers": ["console"], "level": "INFO"},
    },
}
