import os
import secrets

from django.conf import settings
from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = 'Crea usuarios iniciales (Administrador y Trabajador)'

    def _password_for(self, env_name, default=None):
        value = os.getenv(env_name)
        if value:
            return value, 'variable de entorno'
        if default is not None and settings.DEBUG:
            return default, 'valor de desarrollo'
        return secrets.token_urlsafe(12), 'generada automáticamente'

    def handle(self, *args, **kwargs):
        # 1. Administrador Principal
        admin_password, admin_source = self._password_for('INITIAL_ADMIN_PASSWORD', 'admin123')
        admin_user, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@studiogest.co',
                'first_name': 'Carlos',
                'last_name': 'Mendoza',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone': '3104567890'
            }
        )
        if created_admin:
            admin_user.set_password(admin_password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(
                f'[OK] Administrador creado: admin@studiogest.co (clave: {admin_password} [{admin_source}])'
            ))
            if admin_source != 'variable de entorno':
                self.stdout.write(self.style.WARNING(
                    'Cambia esta contraseña antes de usar el sistema en producción.'
                ))
        else:
            self.stdout.write(self.style.WARNING('[INFO] El administrador ya existe.'))

        # 2. Barbero / Trabajador
        worker_password, worker_source = self._password_for('INITIAL_WORKER_PASSWORD', 'barbero123')
        worker_user, created_worker = User.objects.get_or_create(
            username='julian',
            defaults={
                'email': 'julian@studiogest.co',
                'first_name': 'Julián',
                'last_name': 'Restrepo',
                'role': User.Role.WORKER,
                'is_staff': False,
                'is_superuser': False,
                'phone': '3209876543'
            }
        )
        if created_worker:
            worker_user.set_password(worker_password)
            worker_user.save()
            self.stdout.write(self.style.SUCCESS(
                f'[OK] Trabajador creado: julian@studiogest.co (clave: {worker_password} [{worker_source}])'
            ))
            if worker_source != 'variable de entorno':
                self.stdout.write(self.style.WARNING(
                    'Cambia esta contraseña antes de usar el sistema en producción.'
                ))
        else:
            self.stdout.write(self.style.WARNING('[INFO] El trabajador ya existe.'))
