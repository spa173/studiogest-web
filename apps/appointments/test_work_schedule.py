"""Validación de citas contra horario laboral del profesional (RF-07)."""

from datetime import date, time
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from customers.models import Customer
from services.models import Professional, Service

from .models import Appointment

pytestmark = pytest.mark.django_db


@pytest.fixture
def schedule_booking(db, client, django_user_model):
    admin = django_user_model.objects.create_user(
        username='schedule-admin', email='admin@schedule.test', role=django_user_model.Role.ADMIN,
    )
    worker = django_user_model.objects.create_user(
        username='schedule-worker', email='worker@schedule.test', role=django_user_model.Role.WORKER,
    )
    professional = Professional.objects.create(
        user=worker,
        work_start_time=time(9, 0),
        work_end_time=time(18, 0),
    )
    customer = Customer.objects.create(name='Cliente Horario', phone='3000000009')
    service = Service.objects.create(name='Servicio Horario', duration_minutes=60, price_cop=30000)
    client.force_login(admin)
    data = {
        'customer': str(customer.pk),
        'professional': str(professional.pk),
        'service': str(service.pk),
        'date': '2030-07-10',
        'start_time': '10:00',
        'notes': 'Prueba horario laboral',
    }
    return professional, service, customer, data


def _book(client, data):
    response = client.post(reverse('appointments:calendar'), data)
    assert response.status_code == 302
    assert response.url == f"{reverse('appointments:calendar')}?date={data['date']}"
    return Appointment.objects.latest('pk')


def test_appointment_within_professional_work_schedule_is_allowed(client, schedule_booking):
    _, _, _, data = schedule_booking
    appointment = _book(client, {**data, 'start_time': '09:00', 'duration_minutes': '60'})
    assert appointment.start_time == time(9, 0)
    assert appointment.end_time == time(10, 0)

    appointment = _book(client, {**data, 'date': '2030-07-11', 'start_time': '17:00', 'duration_minutes': '60'})
    assert appointment.start_time == time(17, 0)
    assert appointment.end_time == time(18, 0)


@pytest.mark.parametrize('start,duration', [
    ('08:00', '60'),   # empieza antes de la jornada
    ('08:30', '60'),   # cruza el inicio de la jornada
    ('17:30', '60'),   # termina después de la jornada
    ('18:00', '30'),   # empieza exactamente al cierre
])
def test_appointment_outside_professional_work_schedule_is_rejected(client, schedule_booking, start, duration):
    professional, _, _, data = schedule_booking
    response = client.post(reverse('appointments:calendar'), {
        **data, 'start_time': start, 'duration_minutes': duration,
    })
    assert response.status_code == 200
    assert 'fuera del horario laboral' in str(response.context['form'].errors)
    assert professional.name in str(response.context['form'].errors)
    assert '09:00 - 18:00' in str(response.context['form'].errors)
    assert not Appointment.objects.exists()


def test_professional_without_work_schedule_keeps_allowing_any_time(client, django_user_model):
    admin = django_user_model.objects.create_user(
        username='noschedule-admin', email='admin@noschedule.test', role=django_user_model.Role.ADMIN,
    )
    worker = django_user_model.objects.create_user(
        username='noschedule-worker', email='worker@noschedule.test', role=django_user_model.Role.WORKER,
    )
    # Sin horario definido: comportamiento compatible con datos existentes.
    professional = Professional.objects.create(user=worker)
    customer = Customer.objects.create(name='Cliente Sin Horario', phone='3000000010')
    service = Service.objects.create(name='Servicio Sin Horario', duration_minutes=60, price_cop=20000)
    client.force_login(admin)
    data = {
        'customer': str(customer.pk),
        'professional': str(professional.pk),
        'service': str(service.pk),
        'date': '2030-07-12',
        'start_time': '06:30',
        'duration_minutes': '60',
    }
    response = client.post(reverse('appointments:calendar'), data)
    assert response.status_code == 302
    appointment = Appointment.objects.get()
    assert appointment.start_time == time(6, 30)
    assert appointment.end_time == time(7, 30)
    assert professional.work_start_time is None
    assert professional.work_end_time is None


def test_overlaps_are_still_detected_inside_work_schedule(client, schedule_booking):
    _, _, _, data = schedule_booking
    first = _book(client, {**data, 'start_time': '10:00', 'duration_minutes': '60'})
    response = client.post(reverse('appointments:calendar'), {
        **data, 'start_time': '10:30', 'duration_minutes': '30',
    })
    assert response.status_code == 200
    assert 'Conflicto' in str(response.context['form'].non_field_errors())
    assert list(Appointment.objects.values_list('pk', flat=True)) == [first.pk]


def test_adjacent_appointments_inside_work_schedule_are_allowed(client, schedule_booking):
    _, _, _, data = schedule_booking
    _book(client, {**data, 'start_time': '10:00', 'duration_minutes': '60'})
    _book(client, {**data, 'start_time': '11:00', 'duration_minutes': '60'})
    assert Appointment.objects.count() == 2


def test_model_rejects_appointment_outside_work_schedule(schedule_booking):
    professional, service, customer, _ = schedule_booking
    appointment = Appointment(
        customer=customer,
        professional=professional,
        service=service,
        date=date(2030, 7, 13),
        start_time=time(8, 0),
        end_time=time(9, 0),
        price_cop=Decimal('30000'),
    )
    with pytest.raises(ValidationError, match='fuera del horario laboral'):
        appointment.save()
    assert not Appointment.objects.exists()
