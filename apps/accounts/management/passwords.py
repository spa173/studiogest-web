"""Password input for initial accounts; no defaults, logging or file storage."""
import getpass
import os
import sys
import warnings

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError


def initial_password(env_name, *, user, interactive):
    password = os.environ.get(env_name)
    if password is None:
        if not interactive or not sys.stdin.isatty():
            raise CommandError(
                f'Define {env_name} explícitamente o utiliza una terminal interactiva. '
                'No se crearon cuentas con contraseñas predeterminadas.'
            )
        try:
            # Abort before getpass falls back to an input that could echo text.
            with warnings.catch_warnings():
                warnings.simplefilter('error', getpass.GetPassWarning)
                password = getpass.getpass(f'Nueva contraseña ({env_name}): ')
                confirmation = getpass.getpass('Repite la contraseña: ')
        except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
            raise CommandError('Entrada segura de contraseña cancelada o no disponible.') from None
        if password != confirmation:
            raise CommandError('Las contraseñas no coinciden.')
    if not password.strip():
        raise CommandError('La contraseña no puede estar vacía.')
    try:
        validate_password(password, user=user)
    except ValidationError:
        raise CommandError('La contraseña no cumple los requisitos de seguridad configurados.') from None
    return password
