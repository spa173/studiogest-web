from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.management.passwords import initial_password
from accounts.models import User


class Command(BaseCommand):
    help = 'Crea usuarios iniciales con contraseñas explícitas y sin alterar cuentas existentes'

    def add_arguments(self, parser):
        parser.add_argument('--no-input', '--noinput', action='store_false', dest='interactive', default=True)

    @transaction.atomic
    def handle(self, *args, **options):
        accounts = [
            ('INITIAL_ADMIN_PASSWORD', 'admin', {
                'email': 'admin@studiogest.co',
                'first_name': 'Carlos',
                'last_name': 'Mendoza',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone': '3104567890'
            }),
            ('INITIAL_WORKER_PASSWORD', 'julian', {
                'email': 'julian@studiogest.co',
                'first_name': 'Julián',
                'last_name': 'Restrepo',
                'role': User.Role.WORKER,
                'is_staff': False,
                'is_superuser': False,
                'phone': '3209876543'
            }),
        ]
        pending = []
        for env_name, username, defaults in accounts:
            if User.objects.filter(username=username).exists():
                self.stdout.write('[INFO] Cuenta inicial existente; se conserva sin cambios.')
                continue
            user = User(username=username, **defaults)
            password = initial_password(env_name, user=user, interactive=options['interactive'])
            user.set_password(password)
            pending.append(user)

        # Resolve every required password before persisting any account.
        for user in pending:
            user.save()
            self.stdout.write(self.style.SUCCESS('[OK] Cuenta inicial creada. La contraseña no se muestra.'))
