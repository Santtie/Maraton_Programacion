"""
Django settings for config project (ProyectadurIA backend).
"""
import datetime
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-w)1+jpr&k&ajo10wm6#gb86mgy5v8_$#zj)lgpz)u11w%6uoy0")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "apps.accounts",
    "apps.chat",
    "apps.documents",
    "apps.rag",
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


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Auth

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# Static & media

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Email

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(hours=6),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# CORS (frontend en desarrollo)

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173", "http://127.0.0.1:5173"]
)


# ---------------------------------------------------------------------------
# ProyectadurIA - configuración de la arquitectura RAG y del generador de
# documentos de Habeas Data. Ver apps/rag/services/ para su uso.
# ---------------------------------------------------------------------------

DOMAIN_NAME = "Derechos Fundamentales, Protección de Datos e Intimidad"

RAG_CORPUS_DIR = (BASE_DIR / env("RAG_CORPUS_DIR", default="../corpus")).resolve()
RAG_CHROMA_DIR = str((BASE_DIR / env("RAG_CHROMA_DIR", default="./chroma_db")).resolve())
RAG_EMBEDDING_PROVIDER = env("RAG_EMBEDDING_PROVIDER", default="local")  # "local" | "gemini"
RAG_EMBEDDING_MODEL = env("RAG_EMBEDDING_MODEL", default="all-MiniLM-L6-v2")
RAG_TOP_K = env.int("RAG_TOP_K", default=5)
# Umbral BAJO a propósito: solo filtra ruido evidente (texto sin sentido/sin relación
# alguna), no decide dominio (ver nota de diseño en apps/rag/services/domain_guard.py).
RAG_DOMAIN_SCORE_THRESHOLD = env.float("RAG_DOMAIN_SCORE_THRESHOLD", default=0.30)

LLM_PROVIDER = env("LLM_PROVIDER", default="ollama")  # "ollama" | "gemini" | "groq"
LLM_FALLBACK_PROVIDER = env("LLM_FALLBACK_PROVIDER", default="gemini")

OLLAMA_BASE_URL = env("OLLAMA_BASE_URL", default="http://localhost:11434")
OLLAMA_MODEL = env("OLLAMA_MODEL", default="proyectaduria-qwen")

GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
GEMINI_MODEL = env("GEMINI_MODEL", default="gemini-2.0-flash")

GROQ_API_KEY = env("GROQ_API_KEY", default="")
GROQ_MODEL = env("GROQ_MODEL", default="llama-3.1-8b-instant")

# Casos dorados / adversariales usados por `python manage.py run_eval` (comparten fuente con ML/)
EVAL_GOLD_CASES_PATH = (REPO_ROOT / "ML" / "data" / "gold_cases" / "gold_cases.jsonl").resolve()
EVAL_ADVERSARIAL_CASES_PATH = (
    REPO_ROOT / "ML" / "data" / "gold_cases" / "adversarial_cases.jsonl"
).resolve()
