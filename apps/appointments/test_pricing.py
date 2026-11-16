"""Pricing, access control and economic history through real Agenda HTTP forms."""

from datetime import date, time
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from customers.models import Customer
from services.models import Professional, Service
from .forms import AppointmentForm
from .models import Appointment
from .pricing import calculate_pricing

pytestmark = pytest.mark.django_db

FINANCIAL = ('price_cop', 'catalog_price_cop', 'adjusted_price_cop', 'discount_type',
             'discount_value', 'discount_amount_cop', 'pricing_reason')


@pytest.fixture
def pricing_booking(db, client, django_user_model):
    admin = django_user_model.objects.create_user(
        username='pricing-admin', email='admin@pricing.test', role=django_user_model.Role.ADMIN,
    )
    worker = django_user_model.objects.create_user(
        username='pricing-worker', email='worker@pricing.test', role=django_user_model.Role.WORKER,
    )
    professional = Professional.objects.create(user=worker)
    customer = Customer.objects.create(name='Cliente Precios', phone='3000000003')
    service = Service.objects.create(name='Balayage', duration_minutes=90, price_cop=250000)
    client.force_login(admin)
    data = {'customer': str(customer.pk), 'professional': str(professional.pk),
            'service': str(service.pk), 'date': '2030-06-03', 'start_time': '10:00'}
    return service, data, admin, worker


def _book(client, data):
    response = client.post(reverse('appointments:calendar'), data)
    assert response.status_code == 302
    return Appointment.objects.get()


def test_catalog_price_automatically_creates_pricing_snapshot(client, pricing_booking):
    service, data, _, _ = pricing_booking
    appointment = _book(client, data)
    assert appointment.catalog_price_cop == service.price_cop
    assert appointment.adjusted_price_cop == service.price_cop
    assert appointment.price_cop == 250000
    assert appointment.discount_type == 'NONE'
    assert appointment.discount_value == 0
    assert appointment.discount_amount_cop == 0
    assert appointment.end_time == time(11, 30)


@pytest.mark.parametrize('kind,value,discount,total', [
    ('NONE', '0', 0, 320000), ('PERCENT', '10', 32000, 288000),
    ('FIXED', '32000', 32000, 288000), ('PERCENT', '100', 320000, 0),
    ('FIXED', '320000', 320000, 0), ('PERCENT', '0', 0, 320000),
])
def test_personalized_price_and_discounts_are_persisted(client, pricing_booking, kind, value, discount, total):
    service, data, _, _ = pricing_booking
    appointment = _book(client, {**data, 'adjusted_price_cop': '320000',
        'discount_type': kind, 'discount_value': value, 'pricing_reason': 'Necesidades del cliente',
        'duration_minutes': '120'})
    assert appointment.catalog_price_cop == 250000
    assert appointment.adjusted_price_cop == 320000
    assert appointment.discount_value == Decimal(value)
    assert appointment.discount_amount_cop == discount
    assert appointment.price_cop == total
    assert appointment.pricing_reason == 'Necesidades del cliente'
    assert appointment.end_time == time(12)
    service.refresh_from_db()
    assert service.price_cop == 250000
    assert service.duration_minutes == 90


@pytest.mark.parametrize('base,percent,discount,total', [
    ('1', '50', 1, 0), ('101', '50', 51, 50), ('101', '0.5', 1, 100),
    ('999999999999', '99.99', 999899999999, 100000000),
])
def test_decimal_half_up_rounding(base, percent, discount, total):
    assert calculate_pricing(base, 'PERCENT', percent) == (Decimal(discount), Decimal(total))


@pytest.mark.parametrize('changes,field', [
    ({'adjusted_price_cop': '-1'}, 'adjusted_price_cop'),
    ({'adjusted_price_cop': '1.5'}, 'adjusted_price_cop'),
    ({'adjusted_price_cop': '1000000000000'}, 'adjusted_price_cop'),
    ({'adjusted_price_cop': 'NaN'}, 'adjusted_price_cop'),
    ({'adjusted_price_cop': 'Infinity'}, 'adjusted_price_cop'),
    ({'discount_type': 'PERCENT', 'discount_value': '-1'}, 'discount_value'),
    ({'discount_type': 'PERCENT', 'discount_value': '100.01'}, 'discount_value'),
    ({'discount_type': 'PERCENT', 'discount_value': '0.001'}, 'discount_value'),
    ({'discount_type': 'FIXED', 'discount_value': '250001'}, 'discount_value'),
    ({'discount_type': 'FIXED', 'discount_value': '0.5'}, 'discount_value'),
    ({'discount_type': 'NONE', 'discount_value': '10'}, 'discount_value'),
    ({'discount_type': 'OTHER', 'discount_value': '10'}, 'discount_type'),
    ({'discount_type': 'PERCENT', 'discount_value': 'NaN'}, 'discount_value'),
    ({'discount_type': 'PERCENT', 'discount_value': 'Infinity'}, 'discount_value'),
])
def test_invalid_amounts_are_rejected_without_saving(client, pricing_booking, changes, field):
    _, data, _, _ = pricing_booking
    response = client.post(reverse('appointments:calendar'), {**data, **changes})
    assert response.status_code == 200
    assert field in response.context['form'].errors
    assert not Appointment.objects.exists()


@pytest.mark.parametrize('field,value', [
    ('adjusted_price_cop', '1'), ('discount_type', 'PERCENT'), ('discount_value', '100'),
    ('pricing_reason', 'Manipulado'), ('price_cop', '0'),
    ('catalog_price_cop', '1'), ('discount_amount_cop', '250000'),
])
def test_worker_cannot_manipulate_any_economic_field(client, pricing_booking, field, value):
    _, data, _, worker = pricing_booking
    client.force_login(worker)
    response = client.post(reverse('appointments:calendar'), {**data, field: value})
    assert response.status_code == 200
    assert 'Solo un administrador' in str(response.context['form'].non_field_errors())
    assert not Appointment.objects.exists()


def test_worker_keeps_booking_permission_without_pricing_controls(client, pricing_booking):
    _, data, _, worker = pricing_booking
    client.force_login(worker)
    response = client.get(reverse('appointments:calendar'))
    assert not response.context['form'].can_adjust_pricing
    assert 'adjusted_price_cop' not in response.context['form'].fields
    assert 'id="pricingEditor"' not in response.content.decode()
    appointment = _book(client, {**data, 'duration_minutes': '30'})
    assert appointment.price_cop == 250000
    assert appointment.end_time == time(10, 30)


def test_superuser_with_worker_role_can_adjust_pricing(client, pricing_booking):
    _, data, _, worker = pricing_booking
    worker.is_superuser = True
    worker.save()
    client.force_login(worker)
    appointment = _book(client, {**data, 'adjusted_price_cop': '10000'})
    assert appointment.price_cop == 10000


def test_admin_cannot_forge_server_computed_totals(client, pricing_booking):
    _, data, _, _ = pricing_booking
    appointment = _book(client, {**data, 'adjusted_price_cop': '320000',
        'discount_type': 'PERCENT', 'discount_value': '10',
        'price_cop': '1', 'catalog_price_cop': '1', 'discount_amount_cop': '319999'})
    assert appointment.price_cop == 288000
    assert appointment.catalog_price_cop == 250000
    assert appointment.discount_amount_cop == 32000


@pytest.mark.parametrize('discount', ['10', '100'])
def test_economic_history_survives_catalog_and_repeated_status_updates(client, pricing_booking, discount):
    service, data, _, _ = pricing_booking
    appointment = _book(client, {**data, 'adjusted_price_cop': '320000',
        'discount_type': 'PERCENT', 'discount_value': discount, 'pricing_reason': 'Acuerdo inicial'})
    before = Appointment.objects.values(*FINANCIAL).get(pk=appointment.pk)
    service.price_cop = 500000
    service.save()
    for action in ['complete', 'complete', 'cancel']:
        assert client.post(reverse('appointments:' + action, args=[appointment.pk])).status_code == 302
        assert Appointment.objects.values(*FINANCIAL).get(pk=appointment.pk) == before
    appointment.refresh_from_db()
    form = AppointmentForm(data={**data, 'notes': 'Nueva nota'}, instance=appointment)
    assert form.is_valid(), form.errors
    form.save()
    assert Appointment.objects.values(*FINANCIAL).get(pk=appointment.pk) == before


@pytest.mark.parametrize('original', [0, 120000])
def test_legacy_price_and_unknown_details_are_preserved(client, pricing_booking, original):
    service, data, _, _ = pricing_booking
    appointment = Appointment.objects.create(
        customer_id=data['customer'], professional_id=data['professional'], service=service,
        date=date(2030, 6, 3), start_time=time(10), end_time=time(11), price_cop=original,
    )
    service.price_cop = 999000
    service.save()
    assert client.post(reverse('appointments:complete', args=[appointment.pk])).status_code == 302
    appointment.refresh_from_db()
    assert appointment.price_cop == original
    assert appointment.catalog_price_cop is None
    assert appointment.adjusted_price_cop is None
    assert appointment.discount_type is None
    assert appointment.discount_value is None
    assert appointment.discount_amount_cop is None


def test_zero_catalog_price_is_not_treated_as_missing(client, pricing_booking):
    service, data, _, _ = pricing_booking
    service.price_cop = 0
    service.save()
    appointment = _book(client, data)
    assert appointment.price_cop == 0
    assert appointment.catalog_price_cop == 0
    assert appointment.adjusted_price_cop == 0


def test_final_price_is_used_once_by_reports_and_dashboard(client, pricing_booking):
    _, data, _, _ = pricing_booking
    appointment = _book(client, {**data, 'adjusted_price_cop': '320000',
        'discount_type': 'PERCENT', 'discount_value': '10'})
    client.post(reverse('appointments:complete', args=[appointment.pk]))
    response = client.get(reverse('reports:index'), {'start_date': data['date'], 'end_date': data['date']})
    assert response.context['summary']['estimated_income'] == 288000
    from unittest.mock import patch
    with patch('dashboard.views.datetime') as calendar:
        calendar.date.today.return_value = date(2030, 6, 3)
        response = client.get(reverse('dashboard:index'))
    assert response.context['total_sales_cop'] == 288000
    appointment.refresh_from_db()
    assert appointment.price_cop == 288000


def test_price_and_duration_errors_preserve_admin_inputs(client, pricing_booking):
    _, data, _, _ = pricing_booking
    response = client.post(reverse('appointments:calendar'), {**data,
        'adjusted_price_cop': '320000', 'discount_type': 'PERCENT', 'discount_value': '10',
        'pricing_reason': 'Conservar motivo', 'duration_minutes': '1500'})
    assert response.status_code == 200
    assert 'duration_minutes' in response.context['form'].errors
    assert response.context['form']['adjusted_price_cop'].value() == '320000'
    assert response.context['form']['discount_value'].value() == '10'
    assert response.context['form']['pricing_reason'].value() == 'Conservar motivo'
    assert not Appointment.objects.exists()


def test_direct_model_rejects_inconsistent_discount_snapshot(pricing_booking):
    service, data, _, _ = pricing_booking
    appointment = Appointment(
        customer_id=data['customer'], professional_id=data['professional'], service=service,
        date=date(2030, 6, 3), start_time=time(10), end_time=time(11), price_cop=1,
        catalog_price_cop=250000, adjusted_price_cop=320000, discount_type='PERCENT',
        discount_value=10, discount_amount_cop=32000,
    )
    with pytest.raises(ValidationError, match='no coinciden'):
        appointment.save()
    assert not Appointment.objects.exists()


@pytest.mark.parametrize('changes', [
    {'price_cop': -1}, {'catalog_price_cop': -1}, {'adjusted_price_cop': -1},
    {'discount_value': -1}, {'discount_value': 101}, {'discount_amount_cop': -1},
    {'discount_type': 'FIXED', 'discount_value': 320001},
    {'catalog_price_cop': None},
])
def test_model_rejects_invalid_or_incomplete_pricing_snapshot(pricing_booking, changes):
    service, data, _, _ = pricing_booking
    values = dict(customer_id=data['customer'], professional_id=data['professional'], service=service,
        date=date(2030, 6, 3), start_time=time(10), end_time=time(11), price_cop=288000,
        catalog_price_cop=250000, adjusted_price_cop=320000, discount_type='PERCENT',
        discount_value=10, discount_amount_cop=32000)
    with pytest.raises(ValidationError):
        Appointment.objects.create(**{**values, **changes})
    assert not Appointment.objects.exists()


def test_staff_worker_cannot_access_or_edit_appointment_in_django_admin(client, pricing_booking):
    _, data, _, worker = pricing_booking
    appointment = _book(client, data)
    from django.contrib.auth.models import Permission
    worker.is_staff = True
    worker.save()
    worker.user_permissions.add(Permission.objects.get(codename='change_appointment'))
    client.force_login(worker)
    response = client.post(reverse('admin:appointments_appointment_change', args=[appointment.pk]), {
        **data, 'end_time': '11:30', 'status': 'CONFIRMADA', 'price_cop': '1',
        'adjusted_price_cop': '1', 'discount_type': 'PERCENT', 'discount_value': '100',
    })
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert reverse('admin:login') in response.url
    appointment.refresh_from_db()
    assert appointment.price_cop == 250000
    assert appointment.adjusted_price_cop == 250000


@pytest.mark.parametrize('role', ['admin', 'worker', 'superuser'])
def test_admin_readonly_fields_and_columns_preserve_role_contract(rf, pricing_booking, role):
    from django.contrib import admin as django_admin
    from .admin import AppointmentAdmin

    _, _, admin_user, worker = pricing_booking
    user = admin_user if role == 'admin' else worker
    if role == 'superuser':
        user.is_superuser = True
    request = rf.get('/admin/appointments/appointment/')
    request.user = user
    model_admin = AppointmentAdmin(Appointment, django_admin.site)
    readonly = model_admin.get_readonly_fields(request)
    assert isinstance(readonly, list)
    assert readonly == (list(FINANCIAL) if role == 'worker' else [])
    assert model_admin.list_display == (
        'date', 'start_time', 'end_time', 'customer', 'service', 'professional', 'status', 'price_cop',
    )
