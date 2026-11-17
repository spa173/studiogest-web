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

from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class DashboardRBACTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='dash-admin', email='dash-admin@test.co', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='dash-cashier', email='dash-cashier@test.co', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='dash-worker', email='dash-worker@test.co', role=User.Role.WORKER)

    def test_worker_dashboard_hides_financial_sales_kpi(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['can_view_financial_dashboard'])
        self.assertNotContains(response, 'Servicios atendidos')
        self.assertContains(response, 'Citas de hoy')

    def test_admin_and_cashier_dashboard_show_financial_sales_kpi(self):
        for user in (self.admin, self.cashier):
            self.client.force_login(user)
            response = self.client.get(reverse('dashboard:index'))
            self.assertEqual(response.status_code, 200, user)
            self.assertTrue(response.context['can_view_financial_dashboard'])
            self.assertContains(response, 'Servicios atendidos')
