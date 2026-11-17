"""Pruebas contra la base de datos real configurada en .env (por ejemplo, MySQL).

Uso:  pytest --ds=config.settings_test_mysql

Mantiene las opciones de config.settings_test (cifrado de contraseñas rápido, hosts de
prueba, etc.) pero usa la base de datos de config.settings en lugar de SQLite en memoria.
Django crea una base temporal "test_<nombre>" y la elimina al terminar.
"""
from .settings_test import *  # noqa: F401,F403
from .settings import DATABASES  # noqa: F401  (la base de .env; reemplaza a SQLite en memoria)
