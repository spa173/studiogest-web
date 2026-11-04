import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from customers.models import Customer
from services.models import Professional, Service

User = get_user_model()


class ReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='report-admin', email='admin@reports.test', role=User.Role.ADMIN)
        cls.worker = User.objects.create_user(
            username='report-worker', email='worker@reports.test',
            role=User.Role.WORKER, is_staff=True)
        cls.superuser = User.objects.create_user(
            username='report-super', email='super@reports.test',
            role=User.Role.WORKER, is_superuser=True)
        cls.professional = Professional.objects.create(user=cls.worker)
        cls.customer = Customer.objects.create(name='Cliente de prueba', phone='3001112233')
        cls.cut = Service.objects.create(name='Corte', price_cop=90000)
        cls.beard = Service.objects.create(name='Barba', price_cop=80000)
        # Estos registros solo existen en la base aislada de pruebas.
        for date, status, service, price in [
            ('2026-11-01', Appointment.Status.COMPLETED, cls.cut, 20000),
            ('2026-11-02', Appointment.Status.CANCELLED, cls.cut, 90000),
            ('2026-11-03', Appointment.Status.PENDING, cls.cut, 90000),
            ('2026-11-04', Appointment.Status.CONFIRMED, cls.beard, 80000),
            ('2026-11-05', Appointment.Status.IN_PROGRESS, cls.beard, 80000),
            ('2026-11-06', Appointment.Status.COMPLETED, cls.beard, 30000),
            ('2026-12-01', Appointment.Status.COMPLETED, cls.cut, 70000),
        ]:
            cls.make_appointment(date, status, service, price)

    @classmethod
    def make_appointment(cls, date, status, service, price):
        return Appointment.objects.create(
            customer=cls.customer, professional=cls.professional, service=service,
            date=datetime.date.fromisoformat(date), start_time=datetime.time(10),
            end_time=datetime.time(10, 45), status=status, price_cop=price)

    def setUp(self):
        self.url = reverse('reports:index')
        self.client.force_login(self.admin)

    def test_anonymous_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('accounts:login') + '?next=/reports/')

    def test_staff_worker_cannot_access_or_see_menu_link(self):
        self.client.force_login(self.worker)
        response = self.client.get(self.url)
        self.assertContains(response, 'Solo los administradores', status_code=403)
        self.assertNotContains(response, 'Ingresos estimados', status_code=403)
        self.assertNotContains(response, 'href="/reports/"', status_code=403)

    def test_superuser_uses_existing_admin_permission(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_counts_income_and_menu(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        summary = response.context['summary']
        self.assertEqual(summary['total'], 7)
        self.assertEqual(summary['completed'], 3)
        self.assertEqual(summary['cancelled'], 1)
        # Usa el precio histórico de la cita, no la tarifa actual del servicio.
        self.assertEqual(summary['estimated_income'], Decimal('120000'))
        self.assertContains(response, '$120.000 COP')
        self.assertContains(response, 'No representan pagos efectivamente recibidos')
        self.assertContains(response, 'href="/reports/" aria-current="page"')

    def test_service_ranking_includes_all_statuses(self):
        response = self.client.get(self.url)
        ranking = list(response.context['popular_services'])
        self.assertEqual([(r['service__name'], r['total']) for r in ranking],
                         [('Corte', 4), ('Barba', 3)])
        self.assertContains(response, 'incluidas las canceladas')

    def test_date_range_includes_both_boundaries_and_filters_ranking(self):
        response = self.client.get(self.url, {'start_date': '2026-11-01', 'end_date': '2026-11-06'})
        summary = response.context['summary']
        self.assertEqual(summary['total'], 6)
        self.assertEqual(summary['completed'], 2)
        self.assertEqual(summary['cancelled'], 1)
        self.assertEqual(summary['estimated_income'], Decimal('50000'))
        self.assertEqual([r['total'] for r in response.context['popular_services']], [3, 3])

    def test_single_day(self):
        response = self.client.get(self.url, {'start_date': '2026-11-01', 'end_date': '2026-11-01'})
        self.assertEqual(response.context['summary']['total'], 1)
        self.assertEqual(response.context['summary']['estimated_income'], Decimal('20000'))

    def test_optional_date_boundaries_and_clear(self):
        for params, total in [({'start_date': '2026-11-06'}, 2),
                              ({'end_date': '2026-11-02'}, 2),
                              ({'start_date': '', 'end_date': ''}, 7)]:
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertEqual(response.context['summary']['total'], total)

    def test_invalid_dates_hide_indicators(self):
        for params in [
            {'start_date': 'no-es-fecha'},
            {'end_date': '2026-02-30'},
            {'start_date': '2026-11-06', 'end_date': '2026-11-01'},
        ]:
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertNotIn('summary', response.context)
                self.assertContains(response, 'Revisa el filtro de fechas')
                self.assertNotContains(response, 'Ingresos estimados')

    def test_period_without_appointments(self):
        response = self.client.get(self.url, {'end_date': '2020-01-01'})
        self.assertEqual(response.context['summary']['total'], 0)
        self.assertEqual(response.context['summary']['estimated_income'], Decimal('0'))
        self.assertContains(response, '$0 COP')
        self.assertContains(response, 'No hay citas registradas en el período seleccionado.')

    def test_empty_database(self):
        Appointment.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.context['summary']['total'], 0)
        self.assertEqual(response.context['summary']['completed'], 0)
        self.assertEqual(response.context['summary']['cancelled'], 0)
        self.assertContains(response, 'No hay citas registradas en el período seleccionado.')

    def test_no_completed_appointments_means_zero_income(self):
        response = self.client.get(self.url, {'start_date': '2026-11-02', 'end_date': '2026-11-05'})
        self.assertEqual(response.context['summary']['total'], 4)
        self.assertEqual(response.context['summary']['completed'], 0)
        self.assertEqual(response.context['summary']['estimated_income'], Decimal('0'))

    def test_services_with_same_name_remain_separate(self):
        other_cut = Service.objects.create(name='Corte', price_cop=40000)
        self.make_appointment('2026-11-07', Appointment.Status.PENDING, other_cut, 40000)
        response = self.client.get(self.url)
        ranking = list(response.context['popular_services'])
        self.assertEqual(len(ranking), 3)
        self.assertEqual({r['service_id'] for r in ranking}, {self.cut.pk, self.beard.pk, other_cut.pk})

    def test_read_only_page_rejects_post(self):
        before = Appointment.objects.count()
        self.assertEqual(self.client.post(self.url).status_code, 405)
        self.assertEqual(Appointment.objects.count(), before)
