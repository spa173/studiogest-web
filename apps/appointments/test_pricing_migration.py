"""Upgrade old synthetic rows in SQLite only, without inventing economic history."""

from datetime import date, time

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_pricing_migration_preserves_legacy_amounts_and_unknown_details():
    assert connection.vendor == 'sqlite'
    assert connection.settings_dict['NAME'].startswith('file:memory') or connection.settings_dict['NAME'] == ':memory:'
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    old_target = [('accounts', '0001_initial'), ('customers', '0001_initial'), ('appointments', '0001_initial')]
    try:
        executor.migrate(old_target)
        old_apps = executor.loader.project_state(old_target).apps
        User = old_apps.get_model('accounts', 'User')
        Customer = old_apps.get_model('customers', 'Customer')
        Service = old_apps.get_model('services', 'Service')
        Professional = old_apps.get_model('services', 'Professional')
        Appointment = old_apps.get_model('appointments', 'Appointment')
        user = User.objects.create(username='migration-worker', email='migration@example.test', password='!')
        customer = Customer.objects.create(name='Cliente Migracion', phone='3000000004')
        service = Service.objects.create(name='Servicio Migracion', price_cop=250000, duration_minutes=30)
        professional = Professional.objects.create(user=user)
        records = []
        for hour, amount in [(10, 0), (11, 120000)]:
            appointment = Appointment.objects.create(customer=customer, service=service, professional=professional,
                date=date(2030, 6, 3), start_time=time(hour), end_time=time(hour, 30), price_cop=amount)
            records.append((appointment.pk, amount))
        executor = MigrationExecutor(connection)
        target = [('appointments', '0002_appointment_pricing')]
        executor.migrate(target)
        NewAppointment = executor.loader.project_state(target).apps.get_model('appointments', 'Appointment')
        for pk, amount in records:
            appointment = NewAppointment.objects.get(pk=pk)
            assert appointment.price_cop == amount
            for name in ('catalog_price_cop', 'adjusted_price_cop', 'discount_type', 'discount_value', 'discount_amount_cop'):
                assert getattr(appointment, name) is None
            assert appointment.pricing_reason == ''
    finally:
        MigrationExecutor(connection).migrate(latest)
