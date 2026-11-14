"""Integracion HTTP de Servicios y Agenda sobre la base de pruebas aislada."""

from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from appointments.models import Appointment
from customers.models import Customer
from .models import Professional, Service


pytestmark = pytest.mark.django_db


@pytest.fixture
def web_service(db, client, django_user_model):
    """Crear solo los prerrequisitos por ORM; registrar el servicio por HTTP."""
    admin = django_user_model.objects.create_user(
        username='integration-admin', email='admin@integration.test',
        role=django_user_model.Role.ADMIN,
    )
    worker = django_user_model.objects.create_user(
        username='integration-worker', email='worker@integration.test',
        first_name='Profesional', last_name='Integracion',
        role=django_user_model.Role.WORKER,
    )
    professional = Professional.objects.create(user=worker, is_active=True)
    customer = Customer.objects.create(
        name='Cliente Integracion', phone='3001234567',
    )
    client.force_login(admin)
    payload = {
        'name': 'Corte de integracion',
        'description': 'Servicio registrado desde la vista web',
        'duration_minutes': '45',
        'price_cop': '35000',
        'is_active': 'on',
    }
    response = client.post(reverse('services:create'), payload, follow=True)
    assertRedirects(response, reverse('services:list'))
    assertContains(response, 'creado correctamente')
    service = Service.objects.get(name=payload['name'])
    assert service.description == payload['description']
    assert service.duration_minutes == 45
    assert service.price_cop == Decimal('35000')
    assert service.is_active

    appointment_data = {
        'customer': str(customer.pk),
        'service': str(service.pk),
        'professional': str(professional.pk),
        'date': (timezone.localdate() + timedelta(days=7)).isoformat(),
        'start_time': '10:15',
        'notes': 'Cita registrada desde el formulario de Agenda',
        'send_whatsapp': 'on',
    }
    return {
        'admin': admin,
        'service': service,
        'service_data': payload,
        'appointment_data': appointment_data,
    }


def _book_appointment(client, data):
    """Enviar los campos reales de Agenda y comprobar su redireccion de exito."""
    response = client.post(reverse('appointments:calendar'), data, follow=True)
    assertRedirects(
        response, f"{reverse('appointments:calendar')}?date={data['date']}",
    )
    assertContains(response, 'Cita agendada exitosamente')
    return Appointment.objects.get(service_id=data['service'], date=data['date'])


def test_create_service_book_appointment_and_preserve_historical_price(client, web_service):
    """Caso 1: alta web, agendamiento y precio historico tras editar el catalogo."""
    service = web_service['service']
    data = web_service['appointment_data']
    calendar = client.get(reverse('appointments:calendar'), {'date': data['date']})
    assert calendar.status_code == 200
    assert service.pk in calendar.context['form'].fields['service'].queryset.values_list('pk', flat=True)

    appointment = _book_appointment(client, data)
    assert appointment.service_id == service.pk
    assert appointment.customer_id == int(data['customer'])
    assert appointment.professional_id == int(data['professional'])
    assert appointment.created_by_id == web_service['admin'].pk
    assert appointment.date.isoformat() == data['date']
    assert appointment.start_time == time(10, 15)
    assert appointment.end_time == time(11, 0)
    start = datetime.combine(appointment.date, appointment.start_time)
    end = datetime.combine(appointment.date, appointment.end_time)
    assert end - start == timedelta(minutes=45)
    assert appointment.price_cop == Decimal('35000')
    assert Appointment.objects.count() == 1

    response = client.post(
        reverse('services:update', args=[service.pk]),
        {**web_service['service_data'], 'price_cop': '50000'}, follow=True,
    )
    assertRedirects(response, reverse('services:list'))
    service.refresh_from_db()
    appointment.refresh_from_db()
    assert service.price_cop == Decimal('50000')
    assert appointment.price_cop == Decimal('35000')
    assert appointment.end_time == time(11, 0)


def test_deactivate_service_hides_choice_and_rejects_manual_booking(client, web_service):
    """Caso 2: desactivar conserva el historial y bloquea incluso un POST manual."""
    service = web_service['service']
    data = web_service['appointment_data']
    calendar_url = reverse('appointments:calendar')
    before = client.get(calendar_url, {'date': data['date']})
    assert before.status_code == 200
    assert service.pk in before.context['form'].fields['service'].queryset.values_list('pk', flat=True)
    appointment = _book_appointment(client, data)

    inactive_data = web_service['service_data'].copy()
    inactive_data.pop('is_active')
    response = client.post(
        reverse('services:update', args=[service.pk]), inactive_data, follow=True,
    )
    assertRedirects(response, reverse('services:list'))
    service.refresh_from_db()
    assert not service.is_active

    after = client.get(calendar_url, {'date': data['date']})
    assert after.status_code == 200
    assert service.pk not in after.context['form'].fields['service'].queryset.values_list('pk', flat=True)
    assert not after.context['services_list'].filter(pk=service.pk).exists()
    # The existing appointment can still show the name, so inspect the select itself.
    assert service.name not in str(after.context['form']['service'])

    previous_appointments = list(Appointment.objects.order_by('pk').values())
    response = client.post(calendar_url, {**data, 'start_time': '12:00'})
    assert response.status_code == 200
    errors = response.context['form'].errors.as_data()
    assert 'service' in errors
    assert errors['service'][0].code == 'invalid_choice'
    assert response.context['modal_has_errors']
    assertContains(response, 'No se pudo registrar la cita')
    assert list(Appointment.objects.order_by('pk').values()) == previous_appointments
    assert Appointment.objects.filter(pk=appointment.pk).exists()


def test_delete_service_with_web_appointment_protects_history_and_explains_reason(client, web_service):
    """Caso 3: la interfaz explica el bloqueo y un POST no elimina el historial."""
    service = web_service['service']
    appointment = _book_appointment(client, web_service['appointment_data'])
    delete_url = reverse('services:delete', args=[service.pk])
    previous_service = Service.objects.values().get(pk=service.pk)
    previous_appointment = Appointment.objects.values().get(pk=appointment.pk)

    confirmation = client.get(delete_url)
    assert confirmation.status_code == 200
    assertContains(confirmation, 'No se puede eliminar este servicio porque tiene citas asociadas')
    assertContains(confirmation, 'Citas asociadas: 1.')
    assertContains(confirmation, 'Editar para desactivar')
    assertNotContains(confirmation, 'Sí, eliminar servicio')

    response = client.post(delete_url, follow=True)
    assertRedirects(response, reverse('services:list'))
    assertContains(response, 'No se puede eliminar este servicio porque tiene citas asociadas')
    assertContains(response, 'Puedes desactivarlo desde Editar para conservar el historial.')
    assert Service.objects.values().get(pk=service.pk) == previous_service
    assert Appointment.objects.values().get(pk=appointment.pk) == previous_appointment
