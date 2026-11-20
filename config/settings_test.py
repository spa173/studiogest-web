"""Isolated pytest settings: database operations stay in SQLite memory."""

import os

os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('SECRET_KEY', 'django-insecure-studiogest-test-secret-key')

from .settings import *  # noqa: F403

# Las pruebas se ejecutan en modo desarrollo para evitar redirecciones HTTPS y hosts restrictivos.
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Desactivar endurecimiento activado por settings base cuando DEBUG llega como False (p. ej. en CI).
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Replace all database settings, regardless of the engine selected in .env.
DB_ENGINE = 'sqlite'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:'},
    },
}

# Enable the terms gate explicitly in tests that exercise it.
TERMS_VERSION = ''

# Cifrado de contraseñas rápido solo para pruebas: PBKDF2 (el de producción) es lento a propósito
# y alarga mucho cada prueba que crea un usuario o inicia sesión.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
