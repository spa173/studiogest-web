from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Verifica la conexión a la base de datos, las migraciones y los registros guardados.'

    def handle(self, *args, **options):
        config = settings.DATABASES['default']
        motor = config['ENGINE'].rsplit('.', 1)[-1]

        # 1. Conexión
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception as error:  # noqa: BLE001 - se informa cualquier fallo de conexión
            self.stderr.write(self.style.ERROR(f'[ERROR] No se pudo conectar a la base de datos: {error}'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS(f'[OK] Conexión establecida con {motor}.'))
        self.stdout.write(f'     Base de datos: {config["NAME"]}')
        if motor == 'mysql':
            with connection.cursor() as cursor:
                cursor.execute('SELECT VERSION()')
                self.stdout.write(f'     Versión del servidor: {cursor.fetchone()[0]}')
                cursor.execute('SELECT @@character_set_database')
                self.stdout.write(f'     Codificación: {cursor.fetchone()[0]}')

        # 2. Migraciones pendientes
        ejecutor = MigrationExecutor(connection)
        pendientes = ejecutor.migration_plan(ejecutor.loader.graph.leaf_nodes())
        if pendientes:
            self.stdout.write(self.style.WARNING(
                f'[AVISO] Hay {len(pendientes)} migración(es) pendiente(s). Ejecuta: python manage.py migrate'))
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Todas las migraciones están aplicadas.'))

        # 3. Registros por modelo (si hay migraciones pendientes puede que las tablas no existan)
        self.stdout.write('Registros guardados por modelo:')
        tablas = set(connection.introspection.table_names())
        for modelo in apps.get_models():
            if modelo._meta.app_label not in ('accounts', 'customers', 'services', 'appointments'):
                continue
            if modelo._meta.db_table not in tablas:
                self.stdout.write(f'  - {modelo._meta.label}: (tabla no creada)')
                continue
            self.stdout.write(f'  - {modelo._meta.label}: {modelo.objects.count()}')
