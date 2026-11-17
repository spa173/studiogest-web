import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.permissions import can_change_appointment_status
from appointments.models import Appointment
from customers.models import Customer
from services.models import Professional, Service

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def pending_setup(django_user_model):
    admin = django_user_model.objects.create_user(
        username='pending-admin', email='padmin@test.co', role=User.Role.ADMIN,
    )
    owner_worker = django_user_model.objects.create_user(
        username='pending-owner', email='powner@test.co', role=User.Role.WORKER,
    )
    other_worker = django_user_model.objects.create_user(
        username='pending-other', email='pother@test.co', role=User.Role.WORKER,
    )
    cashier = django_user_model.objects.create_user(
        username='pending-cashier', email='pcashier@test.co', role=User.Role.CASHIER,
    )
    owner_prof = Professional.objects.create(user=owner_worker, is_active=True)
    other_prof = Professional.objects.create(user=other_worker, is_active=True)
    customer = Customer.objects.create(name='Cliente Pendiente', phone='3002223344')
    service = Service.objects.create(name='Tinte', duration_minutes=60, price_cop=40000, is_active=True)
    appt = Appointment.objects.create(
        customer=customer, service=service, professional=owner_prof,
        date=datetime.date.today() + datetime.timedelta(days=5),
        start_time=datetime.time(14, 0), end_time=datetime.time(15, 0),
        status=Appointment.Status.PENDING, price_cop=40000, notes='Reserva web',
    )
    return {
        'admin': admin, 'owner_worker': owner_worker, 'other_worker': other_worker,
        'cashier': cashier, 'owner_prof': owner_prof, 'other_prof': other_prof,
        'customer': customer, 'service': service, 'appt': appt,
    }


def test_pending_requests_visible_to_agenda_roles_with_key_data(client, pending_setup):
    client.force_login(pending_setup['cashier'])
    response = client.get(reverse('appointments:pending_requests'))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Cliente Pendiente' in content
    assert '3002223344' in content
    assert 'Tinte' in content
    assert pending_setup['owner_prof'].name in content
    assert 'Reserva web' in content
    assert 'Reserva pública' in content
    assert 'Pendiente' in content
    assert 'Confirmar' not in content  # cajero ve pero no gestiona según can_change_appointment_status


def test_calendar_distinguishes_pending_and_links_requests(client, pending_setup):
    client.force_login(pending_setup['admin'])
    response = client.get(reverse('appointments:calendar'), {'date': pending_setup['appt'].date.isoformat()})
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Solicitudes pendientes' in content
    assert 'Confirmar solicitud' in content
    assert 'Rechazar solicitud' in content
    assert 'Pendiente' in content


def test_admin_can_confirm_pending_appointment(client, pending_setup):
    client.force_login(pending_setup['admin'])
    response = client.post(reverse('appointments:confirm_pending', args=[pending_setup['appt'].pk]), follow=True)
    assert response.status_code == 200
    pending_setup['appt'].refresh_from_db()
    assert pending_setup['appt'].status == Appointment.Status.CONFIRMED
    assert 'Confirmada por pending-admin' in pending_setup['appt'].notes
    assert 'Reserva web' in pending_setup['appt'].notes


def test_owner_professional_can_reject_pending_appointment(client, pending_setup):
    client.force_login(pending_setup['owner_worker'])
    response = client.post(reverse('appointments:reject_pending', args=[pending_setup['appt'].pk]), follow=True)
    assert response.status_code == 200
    pending_setup['appt'].refresh_from_db()
    assert pending_setup['appt'].status == Appointment.Status.CANCELLED
    assert 'Rechazada por pending-owner' in pending_setup['appt'].notes


def test_other_worker_cannot_manage_pending_appointment(client, pending_setup):
    client.force_login(pending_setup['other_worker'])
    response = client.post(reverse('appointments:confirm_pending', args=[pending_setup['appt'].pk]))
    assert response.status_code == 403
    pending_setup['appt'].refresh_from_db()
    assert pending_setup['appt'].status == Appointment.Status.PENDING


@pytest.mark.parametrize('action,status', [
    ('confirm_pending', Appointment.Status.COMPLETED),
    ('confirm_pending', Appointment.Status.CANCELLED),
    ('reject_pending', Appointment.Status.CONFIRMED),
    ('reject_pending', Appointment.Status.COMPLETED),
])
def test_invalid_transitions_are_rejected(client, pending_setup, action, status):
    appt = pending_setup['appt']
    appt.status = status
    appt.save(update_fields=['status'])
    client.force_login(pending_setup['admin'])
    response = client.post(reverse(f'appointments:{action}', args=[appt.pk]), follow=True)
    assert response.status_code == 200
    appt.refresh_from_db()
    assert appt.status == status
    assert 'No se pudo' in response.content.decode()


def test_complete_rejects_pending_and_cancelled_states(client, pending_setup):
    client.force_login(pending_setup['admin'])
    appt = pending_setup['appt']
    response = client.post(reverse('appointments:complete', args=[appt.pk]), follow=True)
    assert response.status_code == 200
    appt.refresh_from_db()
    assert appt.status == Appointment.Status.PENDING
    appt.status = Appointment.Status.CANCELLED
    appt.save(update_fields=['status'])
    response = client.post(reverse('appointments:complete', args=[appt.pk]), follow=True)
    appt.refresh_from_db()
    assert appt.status == Appointment.Status.CANCELLED
    assert 'No se pudo' in response.content.decode()


def test_cancel_rejects_already_cancelled_or_completed(client, pending_setup):
    client.force_login(pending_setup['admin'])
    appt = pending_setup['appt']
    appt.status = Appointment.Status.COMPLETED
    appt.save(update_fields=['status'])
    response = client.post(reverse('appointments:cancel', args=[appt.pk]), follow=True)
    appt.refresh_from_db()
    assert appt.status == Appointment.Status.COMPLETED
    assert 'No se pudo' in response.content.decode()
