"""Isolated pytest settings: database operations stay in SQLite memory."""

import os

os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('SECRET_KEY', 'django-insecure-studiogest-test-secret-key')

from .settings import *  # noqa: F403

# Las pruebas se ejecutan en modo desarrollo para evitar redirecciones HTTPS y hosts restrictivos.
DEBUG = True

# Replace all database settings, regardless of the engine selected in .env.
DB_ENGINE = 'sqlite'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:'},
    },
}
