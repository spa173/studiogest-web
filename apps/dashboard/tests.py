from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class CheckDatabaseCommandTests(TestCase):
    def test_check_database_reports_success_with_current_database(self):
        out = StringIO()
        call_command('check_database', stdout=out)
        output = out.getvalue()
        self.assertIn('[OK] Conexión establecida', output)
        self.assertIn('Todas las migraciones están aplicadas', output)
        self.assertIn('Registros guardados por modelo', output)
