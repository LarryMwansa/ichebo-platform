"""
Local development settings - overrides base.py for SQLite development
"""
from .base import *

# Override database to use SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable some checks for development
ALLOWED_HOSTS = ['*']
