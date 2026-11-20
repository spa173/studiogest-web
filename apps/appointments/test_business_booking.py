import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from appointments.models import Appointment
from customers.models import Customer
from services.models import BookingBusiness, Professional, Service


@override_settings(TENANT_BOOKING_ENABLED=True)
class BusinessBookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.business_a = BookingBusiness.objects.create(name='Salón Prisma', slug='prisma')
        cls.business_b = BookingBusiness.objects.create(name='Barbería Umbral', slug='umbral')
        cls.service_a, cls.professional_a = cls.make_catalog(cls.business_a, 'prisma')
        cls.service_b, cls.professional_b = cls.make_catalog(cls.business_b, 'umbral')

    @staticmethod
    def make_catalog(business, label):
        user = get_user_model().objects.create_user(username=label, email=f'{label}@example.test', business=business)
        professional = Professional.objects.create(business=business, user=user)
        service = Service.objects.create(
            business=business, name=f'Corte {label}', duration_minutes=30, price_cop=25000,
        )
        return service, professional

    def url(self, business):
        return reverse('appointments:business_booking', kwargs={'business_slug': business.slug})

    def payload(self, service, professional):
        return {
            'customer_name': 'Cliente de prueba',
            'customer_phone': '3005550101',
            'service': service.pk,
            'professional': professional.pk,
            'date': (datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
            'start_time': '10:00',
        }

    def test_catalogs_are_isolated_and_legacy_url_does_not_list_them(self):
        response = self.client.get(self.url(self.business_a))
        self.assertContains(response, self.business_a.name)
        self.assertContains(response, self.service_a.name)
        self.assertContains(response, self.professional_a.name)
        self.assertNotContains(response, self.service_b.name)
        self.assertNotContains(response, self.professional_b.name)
        response = self.client.get(reverse('appointments:public_booking'))
        self.assertNotContains(response, self.service_a.name)
        self.assertNotContains(response, self.service_b.name)

    def test_submitted_choices_must_belong_to_the_selected_business(self):
        for service, professional in ((self.service_a, self.professional_b), (self.service_b, self.professional_a)):
            response = self.client.post(self.url(self.business_a), self.payload(service, professional))
            self.assertContains(response, 'No se pudo enviar la reserva')
        self.assertFalse(Appointment.objects.exists())
        self.assertFalse(Customer.objects.exists())

    def test_both_businesses_can_book_the_same_time_for_the_same_phone(self):
        for business, service, professional in (
            (self.business_a, self.service_a, self.professional_a),
            (self.business_b, self.service_b, self.professional_b),
        ):
            response = self.client.post(self.url(business), self.payload(service, professional))
            self.assertContains(response, 'Solicitud de reserva recibida')
            self.assertContains(response, f'href="{self.url(business)}"')
            appointment = Appointment.objects.get(business=business)
            self.assertEqual(appointment.customer.business, business)
            self.assertEqual(appointment.service, service)
            self.assertEqual(appointment.professional, professional)
        self.assertEqual(Customer.objects.filter(phone='3005550101').count(), 2)

    def test_a_business_without_an_active_catalog_cannot_use_another_catalog(self):
        Service.objects.filter(pk=self.service_a.pk).update(is_active=False)
        response = self.client.get(self.url(self.business_a))
        self.assertContains(response, 'Las reservas en línea aún no están disponibles')
        self.assertNotContains(response, self.service_b.name)
        self.assertContains(self.client.get(self.url(self.business_b)), self.service_b.name)

    def test_model_rejects_reassigning_an_appointment_across_businesses(self):
        self.client.post(self.url(self.business_a), self.payload(self.service_a, self.professional_a))
        appointment = Appointment.objects.get(business=self.business_a)
        appointment.professional = self.professional_b
        with self.assertRaisesMessage(ValidationError, 'deben pertenecer al negocio de la cita'):
            appointment.save()

    def test_business_url_requires_feature_and_active_business(self):
        with self.settings(TENANT_BOOKING_ENABLED=False):
            self.assertEqual(self.client.get(self.url(self.business_a)).status_code, 404)
        BookingBusiness.objects.filter(pk=self.business_a.pk).update(is_active=False)
        self.assertEqual(self.client.get(self.url(self.business_a)).status_code, 404)
