import datetime

from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from customers.models import Customer
from services.models import Professional, Service
from django.contrib.auth import get_user_model

User = get_user_model()


class PublicBookingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='pro1', email='pro1@test.co', role=User.Role.WORKER)
        cls.professional = Professional.objects.create(user=cls.user, is_active=True)
        cls.service = Service.objects.create(name='Corte', duration_minutes=30, price_cop=25000, is_active=True)
        cls.url = reverse('appointments:public_booking')

    def test_public_booking_page_is_accessible_without_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reserva tu cita')
        self.assertContains(response, f'href="{reverse("privacy_notice")}"')

    def test_public_booking_creates_pending_appointment_and_customer(self):
        payload = {
            'customer_name': 'Ana Cliente',
            'customer_phone': '3001234567',
            'service': self.service.pk,
            'professional': self.professional.pk,
            'date': (datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
            'start_time': '10:00',
            'notes': 'Primera vez',
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Solicitud de reserva recibida')
        self.assertEqual(Appointment.objects.count(), 1)
        appt = Appointment.objects.get()
        self.assertEqual(appt.status, Appointment.Status.PENDING)
        self.assertEqual(appt.service, self.service)
        self.assertEqual(appt.professional, self.professional)
        self.assertEqual(appt.customer.name, 'Ana Cliente')
        self.assertEqual(appt.customer.phone, '3001234567')
        self.assertEqual(appt.start_time.strftime('%H:%M'), '10:00')
        self.assertEqual(appt.end_time.strftime('%H:%M'), '10:30')

    def test_public_booking_rejects_conflicting_slot(self):
        date = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
        customer = Customer.objects.create(name='Existente', phone='3000000000')
        Appointment.objects.create(
            customer=customer, service=self.service, professional=self.professional,
            date=date, start_time=datetime.time(11, 0), end_time=datetime.time(11, 30),
            status=Appointment.Status.CONFIRMED, price_cop=25000,
        )
        payload = {
            'customer_name': 'Otra Persona',
            'customer_phone': '3009999999',
            'service': self.service.pk,
            'professional': self.professional.pk,
            'date': date,
            'start_time': '11:00',
            'notes': '',
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no está disponible', status_code=200)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_public_booking_does_not_mutate_existing_customer_name(self):
        date = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        existing = Customer.objects.create(name='Nombre Registrado', phone='3001112233')
        payload = {
            'customer_name': 'Nombre Declarado Distinto',
            'customer_phone': '3001112233',
            'service': self.service.pk,
            'professional': self.professional.pk,
            'date': date,
            'start_time': '09:00',
            'notes': 'Prefiere silla cerca a la ventana',
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 1)
        appt = Appointment.objects.get()
        existing.refresh_from_db()
        self.assertEqual(appt.customer_id, existing.id)
        self.assertEqual(existing.name, 'Nombre Registrado')
        self.assertEqual(appt.status, Appointment.Status.PENDING)
        self.assertIn('Nombre declarado en reserva pública: Nombre Declarado Distinto', appt.notes)
        self.assertIn('Prefiere silla cerca a la ventana', appt.notes)
