"""
Django settings for the showcuts project.

Configuration is read from environment variables (12-factor style) so the
same code runs locally and on hosts like Render without editing this file.
For local development you can drop the variables into a ``.env`` file in the
project root (see ``.env.example``); it is loaded automatically.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file if present (no-op in production).
load_dotenv(BASE_DIR / '.env')


def env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name: str, default: str = '') -> list:
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


# --- Core ------------------------------------------------------------------

# A dev-only fallback key is used when DJANGO_SECRET_KEY is unset. Always set
# the env var in production (render.yaml generates one automatically).
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'dev-insecure-key-change-me-bnphip1ctmjei8svyokq9e7md0akxw',
)

DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

# Render exposes the public hostname here; trust it automatically.
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_HOST}')


# --- Applications ----------------------------------------------------------

INSTALLED_APPS = [
    'share',
    'api',

    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves static files in production, right after security.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'showcuts.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# This is a public viewer: the REST API needs no authentication. With the auth
# app removed, also disable DRF's anonymous-user model lookup.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'UNAUTHENTICATED_USER': None,
}

WSGI_APPLICATION = 'showcuts.wsgi.application'


# --- Database --------------------------------------------------------------
# Defaults to a local SQLite file. Set DATABASE_URL (e.g. a free Neon/Render
# Postgres) for persistent storage in production.

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Internationalization --------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True


# --- Static files ----------------------------------------------------------
# Source assets live in ``staticfiles/`` and are collected into
# ``static_collected/`` (served by WhiteNoise). SCSS is precompiled to CSS by
# ``manage.py compile_scss`` during the build.

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'staticfiles']
STATIC_ROOT = BASE_DIR / 'static_collected'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}


# --- Security (enabled when not in DEBUG) ----------------------------------

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# --- Application-specific ---------------------------------------------------

# Lowest Shortcuts "client version" the parser supports.
WORKFLOW_MINIMUM_VERSION = 1000

# When True, re-submitting an existing Shortcut re-fetches and rebuilds it.
# Handy in development; should stay False in production.
LIVE_RELOADING = env_bool('DJANGO_LIVE_RELOADING', DEBUG)

# When True, every action of a Shortcut is shown (the old 100-action "premium"
# gate is bypassed for everyone). Set DJANGO_SHOW_ALL_ACTIONS=False to restore
# the gated behaviour.
SHOW_ALL_ACTIONS = env_bool('DJANGO_SHOW_ALL_ACTIONS', True)


# --- Logging: keep request logs free of static-file noise ------------------

def skip_static_requests(record):
    try:
        return not record.args[0].startswith('GET /static/')
    except Exception:
        return True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'skip_static_requests': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_static_requests,
        }
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(server_time)s] %(message)s',
        }
    },
    'handlers': {
        'django.server': {
            'level': 'INFO',
            'filters': ['skip_static_requests'],
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
    },
    'loggers': {
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
