"""
Production settings — imported in addition to base.py on the VPS.

Usage:
  export DJANGO_SETTINGS_MODULE=ics_project.settings.production
"""
from .base import *  # noqa: F401,F403

# ── Security ──────────────────────────────────────────────────────────────────

DEBUG = False

# Gunicorn + Nginx sit in front; trust the X-Forwarded-Proto header they set
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = True              # redirect bare HTTP → HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ── Cache — use file-based cache; dir must exist on the VPS ───────────────────
# Run once on VPS: mkdir -p /var/cache/ics && chown www-data:www-data /var/cache/ics
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/cache/ics',
    }
}

# ── Logging ───────────────────────────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/ics/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
}
