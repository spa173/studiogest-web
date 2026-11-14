"""Regresiones de Servicios, incluidas las correcciones SVC-01 y SVC-02."""

from datetime import datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from appointments.models import Appointment
from customers.models import Customer
from .forms import ServiceForm
from .models import Professional, Service


pytestmark = pytest.mark.django_db

INVALID_SERVICE_VALUES = [
    ('duration_minutes', 0), ('price_cop', -1),
    ('name', ''), ('name', ' \t\n '), ('name', 'a' * 151),
    ('duration_minutes', -1), ('duration_minutes', 2147483648),
    ('duration_minutes', 'abc'), ('price_cop', '1.5'),
    ('price_cop', '1000000000000'), ('price_cop', 'NaN'),
    ('price_cop', 'Infinity'),
]


def _service_data(**changes):
    data = {
        'name': 'Servicio de regresion', 'description': '',
        'duration_minutes': '45', 'price_cop': '35000', 'is_active': 'on',
    }
    return {**data, **changes}


@pytest.mark.parametrize('field,value', INVALID_SERVICE_VALUES)
def test_model_validation_rejects_invalid_service_values(field, value):
    service = Service(name='Modelo invalido', duration_minutes=45, price_cop=35000)
    setattr(service, field, value)
    with pytest.raises(ValidationError) as error:
        service.full_clean()
    assert field in error.value.message_dict


@pytest.mark.parametrize('field,value', INVALID_SERVICE_VALUES)
def test_direct_save_rejects_invalid_service_values(field, value):
    service = Service(name='Persistencia invalida', duration_minutes=45, price_cop=35000)
    setattr(service, field, value)
    with pytest.raises(ValidationError):
        service.save()
    assert not Service.objects.exists()


@pytest.fixture
def service_admin(db, client, django_user_model):
    admin = django_user_model.objects.create_user(
        username='regression-admin', email='regression-admin@example.test',
        role=django_user_model.Role.ADMIN,
    )
    client.force_login(admin)
    return admin


@pytest.mark.parametrize('field,value', [('duration_minutes', '0'), ('price_cop', '-1')])
def test_form_and_crud_reject_invalid_values_without_partial_writes(client, service_admin, field, value):
    invalid = _service_data(**{field: value})
    form = ServiceForm(data=invalid)
    assert not form.is_valid()
    assert field in form.errors

    response = client.post(reverse('services:create'), invalid)
    assert response.status_code == 200
    assert field in response.context['form'].errors
    assert not Service.objects.exists()

    response = client.post(reverse('services:create'), _service_data())
    assert response.status_code == 302
    service = Service.objects.get()
    before = Service.objects.values().get(pk=service.pk)
    response = client.post(reverse('services:update', args=[service.pk]), invalid)
    assert response.status_code == 200
    assert field in response.context['form'].errors
    assert Service.objects.values().get(pk=service.pk) == before


def test_minimum_positive_duration_and_free_price_remain_allowed(client, service_admin):
    data = _service_data(duration_minutes='1', price_cop='0')
    assert ServiceForm(data=data).is_valid()
    response = client.post(reverse('services:create'), data)
    assert response.status_code == 302
    service = Service.objects.get()
    service.full_clean()
    assert service.duration_minutes == 1
    assert service.price_cop == 0


@pytest.mark.parametrize('field,value', [('duration_minutes', 0), ('price_cop', -1)])
def test_invalid_direct_update_preserves_persisted_service(field, value):
    service = Service.objects.create(name='Servicio valido', duration_minutes=45, price_cop=35000)
    before = Service.objects.values().get(pk=service.pk)
    setattr(service, field, value)
    with pytest.raises(ValidationError):
        service.save()
    assert Service.objects.values().get(pk=service.pk) == before


def test_valid_direct_creation_update_and_partial_save():
    service = Service.objects.create(name='  Corte   clasico  ', duration_minutes=1, price_cop=0)
    service.refresh_from_db()
    assert service.name == 'Corte clasico'
    service.duration_minutes = 60
    service.price_cop = 50000
    service.save()
    service.refresh_from_db()
    assert service.duration_minutes == 60
    assert service.price_cop == 50000
    service.name = 'Corte actualizado'
    service.save(update_fields=['name'])
    service.refresh_from_db()
    assert service.name == 'Corte actualizado'
    assert service.duration_minutes == 60
    assert service.price_cop == 50000


def test_partial_save_validates_the_complete_instance():
    service = Service.objects.create(name='Servicio valido', duration_minutes=45, price_cop=35000)
    before = Service.objects.values().get(pk=service.pk)
    service.name = 'Cambio parcial'
    service.price_cop = -1
    with pytest.raises(ValidationError):
        service.save(update_fields=['name'])
    assert Service.objects.values().get(pk=service.pk) == before


@pytest.mark.parametrize('field,value', [
    ('duration_minutes', '0'), ('price_cop', '-1'), ('name', '   '),
    ('duration_minutes', '2147483648'), ('price_cop', '1000000000000'),
])
def test_django_admin_rejects_invalid_service_values(admin_client, field, value):
    response = admin_client.post(
        reverse('admin:services_service_add'), _service_data(**{field: value}),
    )
    assert response.status_code == 200
    assert field in response.context['adminform'].form.errors
    assert not Service.objects.exists()


def test_django_admin_creates_and_edits_valid_service(admin_client):
    response = admin_client.post(
        reverse('admin:services_service_add'),
        _service_data(duration_minutes='1', price_cop='0'),
    )
    assert response.status_code == 302
    service = Service.objects.get()
    assert service.duration_minutes == 1
    assert service.price_cop == 0
    response = admin_client.post(
        reverse('admin:services_service_change', args=[service.pk]),
        _service_data(name='Editado desde Admin', duration_minutes='60', price_cop='50000'),
    )
    assert response.status_code == 302
    service.refresh_from_db()
    assert service.name == 'Editado desde Admin'
    assert service.duration_minutes == 60
    assert service.price_cop == 50000


@pytest.fixture
def booking_data(db, django_user_model):
    worker = django_user_model.objects.create_user(
        username='regression-worker', email='regression-worker@example.test',
        role=django_user_model.Role.WORKER,
    )
    professional = Professional.objects.create(user=worker)
    customer = Customer.objects.create(name='Cliente sintetico', phone='3000000001')
    return {
        'customer': str(customer.pk), 'professional': str(professional.pk),
        'date': '2030-06-03', 'start_time': '10:00', 'notes': '',
    }


@pytest.mark.parametrize('duration,start_time', [('1440', '10:00'), ('90', '23:30')])
def test_unrepresentable_duration_does_not_cause_server_error(client, service_admin, booking_data, duration, start_time):
    response = client.post(reverse('services:create'), _service_data(duration_minutes=duration))
    assert response.status_code == 302
    service = Service.objects.get()
    client.raise_request_exception = False
    response = client.post(
        reverse('appointments:calendar'),
        {**booking_data, 'service': str(service.pk), 'start_time': start_time},
    )
    # Un intervalo no representable debe volver al formulario con errores.
    assert response.status_code == 200
    assert 'duration_minutes' in response.context['form'].errors
    assert 'mismo día' in str(response.context['form'].errors)
    assert not Appointment.objects.exists()


def test_saved_appointment_preserves_full_service_duration(client, service_admin, booking_data):
    response = client.post(reverse('services:create'), _service_data(duration_minutes='1500'))
    assert response.status_code == 302
    service = Service.objects.get()
    response = client.post(
        reverse('appointments:calendar'), {**booking_data, 'service': str(service.pk)},
    )
    assert response.status_code == 200
    assert 'duration_minutes' in response.context['form'].errors
    assert 'mismo día' in str(response.context['form'].errors)
    assert not Appointment.objects.exists()
