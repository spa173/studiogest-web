from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Crea usuarios iniciales de prueba (Administrador y Trabajador)'

    def handle(self, *args, **kwargs):
        # 1. Administrador Principal
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
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('[OK] Administrador creado: admin@studiogest.co (clave: admin123)'))
        else:
            self.stdout.write(self.style.WARNING('[INFO] El administrador ya existe.'))

        # 2. Barbero / Trabajador
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
            worker_user.set_password('barbero123')
            worker_user.save()
            self.stdout.write(self.style.SUCCESS('[OK] Trabajador creado: julian@studiogest.co (clave: barbero123)'))
        else:
            self.stdout.write(self.style.WARNING('[INFO] El trabajador ya existe.'))
