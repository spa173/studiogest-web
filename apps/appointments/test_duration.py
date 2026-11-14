"""Duración planificada independiente del catálogo, con persistencia HTTP."""

from datetime import date, time
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from customers.models import Customer
from services.models import Professional, Service
from .forms import AppointmentForm
from .models import Appointment


pytestmark = pytest.mark.django_db


@pytest.fixture
def booking(db, client, django_user_model):
    admin = django_user_model.objects.create_user(
        username='duration-admin', email='admin@duration.test', role=django_user_model.Role.ADMIN,
    )
    worker = django_user_model.objects.create_user(
        username='duration-worker', email='worker@duration.test', role=django_user_model.Role.WORKER,
    )
    professional = Professional.objects.create(user=worker)
    customer = Customer.objects.create(name='Cliente Duracion', phone='3000000002')
    service = Service.objects.create(name='Servicio Duracion', duration_minutes=45, price_cop=35000)
    client.force_login(admin)
    data = {
        'customer': str(customer.pk), 'professional': str(professional.pk),
        'service': str(service.pk), 'date': '2030-06-03', 'start_time': '10:00',
        'notes': 'Datos sintéticos',
    }
    return service, data, worker


def _book(client, data):
    response = client.post(reverse('appointments:calendar'), data)
    assert response.status_code == 302
    assert response.url == f"{reverse('appointments:calendar')}?date={data['date']}"
    return Appointment.objects.latest('pk')


@pytest.mark.parametrize('duration,end', [('15', time(10, 15)), ('90', time(11, 30)), ('120', time(12))])
def test_custom_duration_is_saved_without_changing_catalog(client, booking, duration, end):
    service, data, _ = booking
    appointment = _book(client, {**data, 'duration_minutes': duration})
    assert appointment.start_time == time(10)
    assert appointment.end_time == end
    assert appointment.price_cop == Decimal('35000')
    service.refresh_from_db()
    assert service.duration_minutes == 45


@pytest.mark.parametrize('duration_data', [{}, {'duration_minutes': ''}])
def test_missing_duration_uses_service_estimate(client, booking, duration_data):
    _, data, _ = booking
    appointment = _book(client, {**data, **duration_data})
    assert appointment.end_time == time(10, 45)


@pytest.mark.parametrize('duration', ['0', '-1', '1.5', 'abc', 'NaN', 'Infinity'])
def test_invalid_custom_duration_returns_form_errors(client, booking, duration):
    _, data, _ = booking
    response = client.post(reverse('appointments:calendar'), {**data, 'duration_minutes': duration})
    assert response.status_code == 200
    assert 'duration_minutes' in response.context['form'].errors
    assert response.context['modal_has_errors']
    assert not Appointment.objects.exists()
    assert str(response.context['form']['duration_minutes'].value()) == duration


@pytest.mark.parametrize('duration,start', [
    ('30', '23:30'), ('31', '23:30'), ('1440', '00:00'),
    ('1500', '10:00'), ('99999999999999999999999999999999999', '10:00'),
])
def test_midnight_or_excessive_duration_is_rejected_without_500(client, booking, duration, start):
    _, data, _ = booking
    response = client.post(reverse('appointments:calendar'), {
        **data, 'duration_minutes': duration, 'start_time': start,
    })
    assert response.status_code == 200
    assert 'mismo día' in str(response.context['form'].errors['duration_minutes'])
    assert not Appointment.objects.exists()


@pytest.mark.parametrize('duration,start', [('29', '23:30'), ('1439', '00:00')])
def test_same_day_interval_can_end_at_2359(client, booking, duration, start):
    _, data, _ = booking
    appointment = _book(client, {**data, 'duration_minutes': duration, 'start_time': start})
    assert appointment.end_time == time(23, 59)


def test_long_service_can_have_shorter_planned_appointment(client, booking):
    service, data, _ = booking
    service.duration_minutes = 2147483647
    service.save()
    appointment = _book(client, {**data, 'duration_minutes': '30'})
    assert appointment.end_time == time(10, 30)
    service.refresh_from_db()
    assert service.duration_minutes == 2147483647


def test_custom_extension_detects_conflict(client, booking):
    _, data, _ = booking
    existing = _book(client, {**data, 'start_time': '11:00', 'duration_minutes': '30'})
    response = client.post(reverse('appointments:calendar'), {**data, 'duration_minutes': '90'})
    assert response.status_code == 200
    assert 'Conflicto' in str(response.context['form'].non_field_errors())
    assert list(Appointment.objects.values_list('pk', flat=True)) == [existing.pk]


@pytest.mark.parametrize('duration', ['30', '60'])
def test_custom_shortening_and_adjacent_intervals_are_allowed(client, booking, duration):
    service, data, _ = booking
    service.duration_minutes = 120
    service.save()
    _book(client, {**data, 'start_time': '11:00', 'duration_minutes': '30'})
    _book(client, {**data, 'duration_minutes': duration})
    assert Appointment.objects.count() == 2


def test_cancelled_appointment_does_not_block_custom_duration(client, booking):
    _, data, _ = booking
    appointment = _book(client, {**data, 'duration_minutes': '90'})
    assert client.post(reverse('appointments:cancel', args=[appointment.pk])).status_code == 302
    _book(client, {**data, 'duration_minutes': '90'})
    assert Appointment.objects.count() == 2


def test_historical_interval_survives_catalog_changes_and_status_updates(client, booking):
    service, data, _ = booking
    appointment = _book(client, {**data, 'duration_minutes': '90'})
    service.duration_minutes = 20
    service.price_cop = 50000
    service.save()
    assert client.post(reverse('appointments:complete', args=[appointment.pk])).status_code == 302
    appointment.refresh_from_db()
    assert appointment.start_time == time(10)
    assert appointment.end_time == time(11, 30)
    assert appointment.price_cop == Decimal('35000')
    assert AppointmentForm(instance=appointment)['duration_minutes'].value() == 90
    form = AppointmentForm(data={**data, 'notes': 'Solo cambia la nota'}, instance=appointment)
    assert form.is_valid(), form.errors
    form.save()
    appointment.refresh_from_db()
    assert appointment.end_time == time(11, 30)


def test_worker_keeps_permission_to_book_custom_duration(client, booking):
    _, data, worker = booking
    client.force_login(worker)
    appointment = _book(client, {**data, 'duration_minutes': '60'})
    assert appointment.created_by_id == worker.pk
    assert appointment.end_time == time(11)


@pytest.mark.parametrize('duration', [1440, 1500, 2147483647])
def test_model_auto_calculation_rejects_cross_day_interval(booking, duration):
    service, data, _ = booking
    service.duration_minutes = duration
    service.save()
    appointment = Appointment(
        customer_id=int(data['customer']), professional_id=int(data['professional']),
        service=service, date=date(2030, 6, 3), start_time=time(10),
    )
    with pytest.raises(ValidationError, match='mismo día'):
        appointment.save()
    assert not Appointment.objects.exists()


def test_calendar_renders_editable_duration_and_end_time_preview(client, booking):
    response = client.get(reverse('appointments:calendar'))
    assert response.status_code == 200
    field = str(response.context['form']['duration_minutes'])
    assert 'name="duration_minutes"' in field
    assert 'readonly' not in field
    assert 'id="endTimeDisplay"' in response.content.decode()
