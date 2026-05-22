"""
Production settings — imported in addition to base.py on the VPS.

Usage:
  export DJANGO_SETTINGS_MODULE=ics_project.settings.production

Pre-flight checklist (run once on VPS before first start):
  mkdir -p /var/log/ics /var/cache/ics /var/log/gunicorn
  chown -R www-data:www-data /var/log/ics /var/cache/ics /var/log/gunicorn
  python manage.py collectstatic --noinput
  python manage.py migrate
"""
from .base import *  # noqa: F401,F403

# ── Core ──────────────────────────────────────────────────────────────────────

DEBUG = False

# ── Security ──────────────────────────────────────────────────────────────────

# Gunicorn + Nginx sit in front; trust the X-Forwarded-Proto header they set
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = True              # redirect bare HTTP → HTTPS
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True      # prevent MIME-type sniffing
SECURE_REFERRER_POLICY = 'same-origin'

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

X_FRAME_OPTIONS = 'DENY'

# ── Database ──────────────────────────────────────────────────────────────────

# Reuse DB connections across requests; avoids a TCP round-trip per query.
# Value is seconds; 0 = close after every request (Django default).
DATABASES['default']['CONN_MAX_AGE'] = 60  # noqa: F405

# ── Static files — ManifestStaticFilesStorage adds content hashes ─────────────
# Fingerprinted filenames (e.g. main.abc123.css) allow infinite cache TTL in Nginx.
# Requires `python manage.py collectstatic` to have been run before deployment.

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# ── Logging ───────────────────────────────────────────────────────────────────
# Run once: mkdir -p /var/log/ics && chown www-data:www-data /var/log/ics
# Logs rotate at 10 MB, keeping 5 backups (~50 MB max).

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ics/django.log',
            'maxBytes': 10 * 1024 * 1024,   # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ics/security.log',
            'maxBytes': 5 * 1024 * 1024,    # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
}
