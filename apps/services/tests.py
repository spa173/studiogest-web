import datetime
import re
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse

from appointments.forms import AppointmentForm
from appointments.models import Appointment
from customers.models import Customer
from .forms import ServiceForm
from .models import Professional, Service

User = get_user_model()


class ServiceCrudTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # El administrador puede usar StudioGest sin acceso a Django Admin.
        cls.admin = User.objects.create_user(username='services-admin', email='admin@services.test', role=User.Role.ADMIN)
        cls.worker = User.objects.create_user(username='services-worker', email='worker@services.test',
                                             role=User.Role.WORKER, is_staff=True)
        cls.superuser = User.objects.create_user(username='services-super', email='super@services.test',
                                                role=User.Role.WORKER, is_superuser=True)
        cls.service = Service.objects.create(name='Corte clásico', description='Corte de cabello',
                                              duration_minutes=30, price_cop=Decimal('25000'))
        cls.inactive = Service.objects.create(name='Servicio inactivo', duration_minutes=45,
                                              price_cop=Decimal('40000'), is_active=False)
        cls.professional = Professional.objects.create(user=cls.worker)
        cls.customer = Customer.objects.create(name='Cliente de pruebas', phone='3001112233')

    def setUp(self):
        self.client.force_login(self.admin)

    def data(self, **changes):
        data = {'name': 'Coloración', 'description': 'Aplicación de color', 'duration_minutes': '60',
                'price_cop': '85000', 'is_active': 'on'}
        data.update(changes)
        return data

    def create_appointment(self, status=Appointment.Status.CONFIRMED, date='2026-11-03'):
        return Appointment.objects.create(
            customer=self.customer, professional=self.professional, service=self.service,
            date=datetime.date.fromisoformat(date), start_time=datetime.time(10), end_time=datetime.time(10, 30),
            price_cop=Decimal('20000'), status=status)

    def test_anonymous_requires_login_for_all_crud_routes(self):
        self.client.logout()
        for name, args in [('list', []), ('create', []), ('update', [self.service.pk]), ('delete', [self.service.pk])]:
            url = reverse('services:' + name, args=args)
            for method in [self.client.get, self.client.post]:
                with self.subTest(route=name, method=method.__name__):
                    self.assertRedirects(method(url), reverse('accounts:login') + '?next=' + url)

    def test_authenticated_worker_can_consult_active_and_inactive_services(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('services:list'))
        self.assertContains(response, 'Corte clásico')
        self.assertContains(response, 'Servicio inactivo')
        self.assertContains(response, 'Inactivo')
        self.assertNotContains(response, reverse('services:create'))
        self.assertNotContains(response, reverse('services:update', args=[self.service.pk]))
        self.assertNotContains(response, reverse('services:delete', args=[self.service.pk]))

    def test_list_is_read_only_and_has_admin_actions(self):
        response = self.client.get(reverse('services:list'))
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'Nuevo servicio')
        self.assertContains(response, reverse('services:update', args=[self.service.pk]))
        self.assertContains(response, reverse('services:delete', args=[self.service.pk]))
        self.assertEqual(self.client.post(reverse('services:list')).status_code, 405)

    def test_empty_list(self):
        Service.objects.all().delete()
        self.assertContains(self.client.get(reverse('services:list')), 'No hay servicios registrados')

    def test_worker_cannot_write_even_if_staff(self):
        self.client.force_login(self.worker)
        before = list(Service.objects.order_by('pk').values())
        for name, args in [('create', []), ('update', [self.service.pk]), ('delete', [self.service.pk])]:
            url = reverse('services:' + name, args=args)
            for method in [self.client.get, self.client.post]:
                with self.subTest(route=name, method=method.__name__):
                    self.assertEqual(method(url, self.data()).status_code, 403)
        self.assertEqual(list(Service.objects.order_by('pk').values()), before)

    def test_create_prefills_active_and_default_duration(self):
        response = self.client.get(reverse('services:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services/form.html')
        self.assertEqual(response.context['form']['duration_minutes'].value(), 45)
        self.assertTrue(response.context['form']['is_active'].value())
        self.assertEqual(Service.objects.count(), 2)

    def test_admin_creates_service_and_sees_confirmation(self):
        response = self.client.post(reverse('services:create'), self.data(name='  Coloración   completa  '), follow=True)
        self.assertContains(response, 'creado correctamente')
        service = Service.objects.get(name='Coloración completa')
        self.assertEqual(service.price_cop, Decimal('85000'))
        self.assertEqual(service.duration_minutes, 60)
        self.assertTrue(service.is_active)

    def test_optional_description_zero_price_and_inactive_state(self):
        data = self.data(description='', price_cop='0')
        data.pop('is_active')
        self.assertRedirects(self.client.post(reverse('services:create'), data), reverse('services:list'))
        service = Service.objects.get(name=data['name'])
        self.assertEqual(service.description, '')
        self.assertEqual(service.price_cop, 0)
        self.assertFalse(service.is_active)

    def test_invalid_create_does_not_save(self):
        for field, value in [('name', ''), ('name', ' \t\n '), ('name', 'a' * 151),
                             ('duration_minutes', '0'), ('duration_minutes', '-1'),
                             ('duration_minutes', '1.5'), ('duration_minutes', 'abc'),
                             ('price_cop', '-1'), ('price_cop', '25000.5'),
                             ('price_cop', 'NaN'), ('price_cop', 'Infinity'),
                             ('price_cop', '1000000000000')]:
            with self.subTest(field=field, value=value):
                response = self.client.post(reverse('services:create'), self.data(**{field: value}))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context['form'].errors)
                self.assertContains(response, 'No se pudo guardar el servicio')
                self.assertEqual(Service.objects.count(), 2)

    def test_only_authorized_fields_are_exposed(self):
        self.assertEqual(set(ServiceForm().fields), {'name', 'description', 'duration_minutes', 'price_cop', 'is_active'})

    def test_update_prefills_values_and_saves(self):
        url = reverse('services:update', args=[self.service.pk])
        response = self.client.get(url)
        self.assertEqual(response.context['form']['name'].value(), self.service.name)
        self.assertEqual(response.context['form']['price_cop'].value(), self.service.price_cop)
        response = self.client.post(url, self.data(), follow=True)
        self.assertContains(response, 'actualizado correctamente')
        self.service.refresh_from_db()
        self.assertEqual(self.service.name, 'Coloración')
        self.assertEqual(self.service.duration_minutes, 60)
        self.assertEqual(self.service.price_cop, Decimal('85000'))
        self.assertEqual(Service.objects.count(), 2)

    def test_invalid_update_preserves_all_previous_values(self):
        before = Service.objects.values().get(pk=self.service.pk)
        response = self.client.post(reverse('services:update', args=[self.service.pk]), self.data(price_cop='-1'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.values().get(pk=self.service.pk), before)

    def test_edit_does_not_change_historical_appointment_prices_or_times(self):
        self.create_appointment()
        self.create_appointment(status=Appointment.Status.COMPLETED, date='2026-11-04')
        before = list(Appointment.objects.order_by('pk').values())
        self.assertRedirects(self.client.post(reverse('services:update', args=[self.service.pk]), self.data()), reverse('services:list'))
        self.assertEqual(list(Appointment.objects.order_by('pk').values()), before)

    def test_deactivation_keeps_appointments_and_removes_service_from_new_choices(self):
        appointment = self.create_appointment()
        data = self.data()
        data.pop('is_active')
        self.assertRedirects(self.client.post(reverse('services:update', args=[self.service.pk]), data), reverse('services:list'))
        self.service.refresh_from_db()
        self.assertFalse(self.service.is_active)
        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())
        self.assertFalse(AppointmentForm().fields['service'].queryset.filter(pk=self.service.pk).exists())

    def test_delete_get_only_confirms_and_post_deletes_unused_service(self):
        url = reverse('services:delete', args=[self.service.pk])
        self.assertTemplateUsed(self.client.get(url), 'services/confirm_delete.html')
        self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())
        response = self.client.post(url, follow=True)
        self.assertContains(response, 'eliminado correctamente')
        self.assertFalse(Service.objects.filter(pk=self.service.pk).exists())
        self.assertTrue(Service.objects.filter(pk=self.inactive.pk).exists())

    def test_all_appointment_statuses_protect_service(self):
        for day, status in enumerate(Appointment.Status.values, start=1):
            with self.subTest(status=status):
                appointment = self.create_appointment(status=status, date=f'2026-11-{day:02d}')
                url = reverse('services:delete', args=[self.service.pk])
                response = self.client.get(url)
                self.assertContains(response, 'Puedes desactivarlo')
                self.assertNotContains(response, 'Sí, eliminar servicio')
                response = self.client.post(url, follow=True)
                self.assertContains(response, 'No se puede eliminar este servicio')
                self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())
                self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())
                appointment.delete()

    def test_protected_error_is_handled_if_relation_appears_after_check(self):
        url = reverse('services:delete', args=[self.service.pk])
        with patch.object(Service, 'delete', side_effect=ProtectedError('Servicio protegido', set())):
            response = self.client.post(url, follow=True)
        self.assertContains(response, 'Puedes desactivarlo')
        self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())

    def test_superuser_can_use_all_write_operations_with_worker_role(self):
        self.client.force_login(self.superuser)
        self.assertRedirects(self.client.post(reverse('services:create'), self.data()), reverse('services:list'))
        service = Service.objects.get(name='Coloración')
        self.assertRedirects(self.client.post(reverse('services:update', args=[service.pk]), self.data(name='Otro nombre')), reverse('services:list'))
        self.assertRedirects(self.client.post(reverse('services:delete', args=[service.pk])), reverse('services:list'))
        self.assertFalse(Service.objects.filter(pk=service.pk).exists())

    def test_missing_services_and_unsupported_methods(self):
        for name in ['update', 'delete']:
            url = reverse('services:' + name, args=[999999])
            self.assertEqual(self.client.get(url).status_code, 404)
        for name, args in [('create', []), ('update', [self.service.pk]), ('delete', [self.service.pk])]:
            self.assertEqual(self.client.delete(reverse('services:' + name, args=args)).status_code, 405)

    def test_csrf_protects_all_writes_and_valid_token_allows_registration(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for name, args in [('create', []), ('update', [self.service.pk]), ('delete', [self.service.pk])]:
            self.assertEqual(client.post(reverse('services:' + name, args=args), self.data()).status_code, 403)
        self.assertEqual(Service.objects.count(), 2)
        client.get(reverse('services:create'))
        data = self.data(csrfmiddlewaretoken=client.cookies['csrftoken'].value)
        self.assertRedirects(client.post(reverse('services:create'), data), reverse('services:list'))

    def test_service_menus_stay_active_without_highlighting_professionals(self):
        for name, args in [('list', []), ('create', []), ('update', [self.service.pk]), ('delete', [self.service.pk])]:
            response = self.client.get(reverse('services:' + name, args=args))
            html = response.content.decode()
            service_links = re.findall(r'<a href="/services/"[^>]*>', html)
            self.assertEqual(sum('aria-current="page"' in link for link in service_links), 2)
            professional_links = re.findall(r'<a href="/services/profesionales/"[^>]*>', html)
            self.assertTrue(all('aria-current="page"' not in link for link in professional_links))
        response = self.client.get(reverse('services:professionals_list'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertTrue(all('aria-current="page"' not in link for link in re.findall(r'<a href="/services/"[^>]*>', html)))
