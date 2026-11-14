"""Isolated pytest settings: database operations stay in SQLite memory."""

from .settings import *  # noqa: F403

# Replace all database settings, regardless of the engine selected in .env.
DB_ENGINE = 'sqlite'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:'},
    },
}
