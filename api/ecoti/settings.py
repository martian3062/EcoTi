"""Django settings for the EcoTi backend (ASGI + DRF + Channels + Celery)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "channels",
    # EcoTi apps
    "core",
    "orchestrator",
    "agents",
    "apiviews",
    "rag",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ecoti.urls"
WSGI_APPLICATION = "ecoti.wsgi.application"
ASGI_APPLICATION = "ecoti.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database: Postgres + pgvector, with a sqlite fallback for `manage.py` runs
if os.getenv("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "ecoti"),
            "USER": os.getenv("POSTGRES_USER", "ecoti"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "ecoti"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.getenv("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
        }
    }

# --- Channels (Redis layer, in-memory fallback) ------------------------
REDIS_URL = os.getenv("REDIS_URL", "")
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# --- Celery ------------------------------------------------------------
CELERY_BROKER_URL = REDIS_URL or "memory://"
CELERY_RESULT_BACKEND = REDIS_URL or "cache+memory://"
CELERY_BEAT_SCHEDULE = {
    "watchdog-heartbeat": {
        "task": "orchestrator.watchdog.heartbeat",
        "schedule": 10.0,
    },
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "EcoTi API",
    "DESCRIPTION": "Economic Trust Intelligence agent, fusion, evidence, and demo endpoints.",
    "VERSION": "0.2.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

CORS_ALLOW_ALL_ORIGINS = True

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- EcoTi config ------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "stub")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

# --- Real AI providers (all optional; blank key => that backend is skipped) ---
# Groq also serves fast Whisper ASR + Kimi/Llama for cloud reasoning.
GROQ_WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
# Sarvam — sovereign Indic AI: Saarika (ASR), Bulbul (TTS), Mayura (translate), Sarvam-M (chat)
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")
SARVAM_CHAT_MODEL = os.getenv("SARVAM_CHAT_MODEL", "sarvam-m")
# Hugging Face — real models (anti-spoof, embeddings, VLM, GNN weights)
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_EMBED_MODEL = os.getenv("HF_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
# Kimi / Moonshot — long-context cloud reasoning (OpenAI-compatible)
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k2-0711-preview")
KIMI_VISION_MODEL = os.getenv("KIMI_VISION_MODEL", "moonshot-v1-8k-vision-preview")
# Firecrawl — advisory RAG corpus ingestion
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
# TinyFish — web-agent portal monitoring (roadmap)
TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY", "")
# IPQualityScore — real-time phone reputation / fraud score (optional, free tier)
IPQS_API_KEY = os.getenv("IPQS_API_KEY", "")
# Real-ML (zero-training) providers
TABPFN_API_KEY = os.getenv("TABPFN_API_KEY", "")      # TabPFN hosted tabular classifier (fraud)
HF_VOICE_MODEL = os.getenv("HF_VOICE_MODEL", "garystafford/wav2vec2-deepfake-voice-detector")
VOICE_MODEL = os.getenv("VOICE_MODEL", "MelodyMachine/Deepfake-audio-detection-V2")  # local transformers
HF_VLM_MODEL = os.getenv("HF_VLM_MODEL", "Qwen/Qwen2-VL-7B-Instruct")
# OSINT enrichers
HIBP_API_KEY = os.getenv("HIBP_API_KEY", "")          # Have I Been Pwned (paid key for account lookups)
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")  # optional IP reputation
OSINT_CACHE_TTL = int(os.getenv("OSINT_CACHE_TTL", "21600"))  # 6h

NEO4J_ENABLED = os.getenv("NEO4J_ENABLED", "0") == "1"
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "ecotineo4j")
FORCE_GNN_FAILURE = os.getenv("FORCE_GNN_FAILURE", "0") == "1"

# Correlator: emit a FusedTrustRisk when >= N independent signals cross threshold
FUSION_MIN_SIGNALS = 2
FUSION_WINDOW_SECONDS = 120
FUSION_CONFIDENCE_THRESHOLD = 0.6
