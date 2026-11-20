import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from appointments.models import Appointment
from customers.models import Customer
from services.models import BookingBusiness, Professional, Service


@override_settings(TENANT_BOOKING_ENABLED=True)
class BusinessPanelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alpha, cls.alpha_admin, cls.alpha_appointment = cls.make_business('prisma')
        cls.beta, cls.beta_admin, cls.beta_appointment = cls.make_business('umbral')
        cls.unassigned = get_user_model().objects.create_user(
            username='sin-negocio', email='unassigned@example.test', role='ADMIN', is_staff=True,
        )

    @staticmethod
    def make_business(slug):
        business = BookingBusiness.objects.create(name=slug.title(), slug=slug)
        user = get_user_model().objects.create_user(
            username=slug, email=f'{slug}@example.test', role='ADMIN', business=business,
            is_staff=True, password='test-password',
        )
        customer = Customer.objects.create(business=business, name=f'Cliente {slug}', phone='3005550101')
        service = Service.objects.create(business=business, name=f'Servicio {slug}', price_cop=25000)
        professional = Professional.objects.create(business=business, user=user)
        appointment = Appointment.objects.create(
            business=business, customer=customer, service=service, professional=professional,
            date=datetime.date.today(), start_time=datetime.time(10), status=Appointment.Status.PENDING,
        )
        return business, user, appointment

    def test_login_leads_to_panel_with_only_own_business_data(self):
        response = self.client.post(reverse('accounts:login'), {
            'login': self.alpha_admin.username, 'password': 'test-password',
        }, follow=True)
        self.assertEqual(response.request['PATH_INFO'], reverse('accounts:business_panel'))
        self.assertContains(response, self.alpha_appointment.customer.name)
        self.assertContains(response, self.alpha_appointment.service.name)
        self.assertNotContains(response, self.beta_appointment.customer.name)
        self.assertNotContains(response, self.beta_appointment.service.name)

    def test_cross_business_changes_are_rejected(self):
        self.client.force_login(self.alpha_admin)
        for route, obj in (
            ('accounts:business_appointment', self.beta_appointment),
            ('accounts:business_service_edit', self.beta_appointment.service),
            ('accounts:business_professional_edit', self.beta_appointment.professional),
        ):
            self.assertEqual(self.client.post(reverse(route, args=[obj.pk]), {'action': 'confirm'}).status_code, 404)
        self.beta_appointment.refresh_from_db()
        self.assertEqual(self.beta_appointment.status, Appointment.Status.PENDING)

    def test_admin_can_manage_own_appointment_and_service(self):
        self.client.force_login(self.alpha_admin)
        self.assertRedirects(self.client.post(
            reverse('accounts:business_appointment', args=[self.alpha_appointment.pk]),
            {'action': 'confirm'},
        ), reverse('accounts:business_panel'))
        self.alpha_appointment.refresh_from_db()
        self.assertEqual(self.alpha_appointment.status, Appointment.Status.CONFIRMED)
        self.assertRedirects(self.client.post(reverse('accounts:business_service_create'), {
            'name': 'Nuevo servicio', 'duration_minutes': 30, 'price_cop': 25000,
            'is_active': 'on', 'business': self.beta.pk,
        }), reverse('accounts:business_panel'))
        self.assertEqual(Service.objects.get(name='Nuevo servicio').business, self.alpha)

    def test_legacy_private_modules_do_not_expose_tenant_rows(self):
        for user in (self.alpha_admin, self.unassigned):
            self.client.force_login(user)
            for route in ('admin:index', 'customers:list', 'appointments:calendar'):
                self.assertEqual(self.client.get(reverse(route)).status_code, 403)

    def test_inactive_business_cannot_access_panel(self):
        self.client.force_login(self.alpha_admin)
        BookingBusiness.objects.filter(pk=self.alpha.pk).update(is_active=False)
        self.assertEqual(self.client.get(reverse('accounts:business_panel')).status_code, 403)
        self.assertEqual(self.client.get(reverse('dashboard:index')).status_code, 403)

    def test_non_admin_cannot_change_catalog_or_others_appointments(self):
        self.alpha_admin.role = 'TRABAJADOR'
        self.alpha_admin.save(update_fields=['role'])
        worker = get_user_model().objects.create_user(
            username='profesional2', email='worker@example.test', business=self.alpha, role='TRABAJADOR',
        )
        self.client.force_login(worker)
        for route, args in (
            ('accounts:business_appointment', [self.alpha_appointment.pk]),
            ('accounts:business_service_create', []),
            ('accounts:business_professional_edit', [self.alpha_appointment.professional_id]),
        ):
            self.assertEqual(self.client.post(reverse(route, args=args), {'action': 'confirm'}).status_code, 403)
        self.alpha_appointment.refresh_from_db()
        self.assertEqual(self.alpha_appointment.status, Appointment.Status.PENDING)

    def test_admin_can_change_own_schedule_and_reject_a_request(self):
        self.client.force_login(self.alpha_admin)
        schedule = reverse('accounts:business_professional_edit', args=[self.alpha_appointment.professional_id])
        self.assertContains(self.client.get(schedule), 'Guardar')
        self.assertRedirects(self.client.post(schedule, {
            'specialty': 'Estilista', 'work_start_time': '09:00', 'work_end_time': '18:00',
            'is_active': 'on',
        }), reverse('accounts:business_panel'))
        self.alpha_appointment.professional.refresh_from_db()
        self.assertEqual(self.alpha_appointment.professional.work_start_time, datetime.time(9))
        action = reverse('accounts:business_appointment', args=[self.alpha_appointment.pk])
        self.client.post(action, {'action': 'reject'})
        self.client.post(action, {'action': 'confirm'})
        self.alpha_appointment.refresh_from_db()
        self.assertEqual(self.alpha_appointment.status, Appointment.Status.CANCELLED)

    def test_platform_superuser_can_provision_businesses(self):
        root = get_user_model().objects.create_superuser(
            username='platform', email='platform@example.test',
        )
        self.client.force_login(root)
        self.assertContains(self.client.get(reverse('admin:services_bookingbusiness_add')), 'Identificador público')
        self.assertEqual(self.client.get(reverse('dashboard:index')).status_code, 200)
        self.assertRedirects(
            self.client.get(reverse('accounts:business_panel')),
            reverse('admin:services_bookingbusiness_changelist'),
        )

    def test_terms_gate_precedes_private_panel(self):
        self.client.force_login(self.alpha_admin)
        with self.settings(TERMS_VERSION='1.0'):
            self.assertRedirects(self.client.get(reverse('accounts:business_panel')), reverse('accounts:accept_terms'))
        with self.settings(TENANT_BOOKING_ENABLED=False):
            self.assertEqual(self.client.get(reverse('accounts:business_panel')).status_code, 403)

    def test_professional_must_have_account_from_same_business(self):
        from django.core.exceptions import ValidationError

        professional = Professional(user=self.unassigned, business=self.alpha)
        with self.assertRaisesMessage(ValidationError, 'deben pertenecer al mismo negocio'):
            professional.save()
