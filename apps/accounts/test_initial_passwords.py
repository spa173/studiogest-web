"""Bootstrap security regressions; all users and credentials are test-only."""
import getpass
import secrets
import warnings
from io import StringIO
from unittest.mock import Mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.management.passwords import initial_password
from appointments.models import Appointment

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_bootstrap_environment(monkeypatch):
    import os
    for name in list(os.environ):
        if name.startswith('INITIAL_') and name.endswith('_PASSWORD'):
            monkeypatch.delenv(name)


@pytest.fixture
def explicit_passwords(monkeypatch):
    values = {key: secrets.token_urlsafe(32) for key in
              ['INITIAL_ADMIN_PASSWORD', 'INITIAL_WORKER_PASSWORD']}
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return values


def test_explicit_password_is_used_and_not_printed(monkeypatch, django_user_model, capsys):
    value = secrets.token_urlsafe(32)
    monkeypatch.setenv('INITIAL_TEST_PASSWORD', value)
    user = django_user_model(username='test-bootstrap', email='bootstrap@example.invalid')
    assert initial_password('INITIAL_TEST_PASSWORD', user=user, interactive=False) == value
    captured = capsys.readouterr()
    assert value not in captured.out
    assert value not in captured.err


@pytest.mark.parametrize('interactive,tty', [(False, True), (False, False), (True, False)])
def test_missing_password_fails_without_an_unsafe_input(monkeypatch, django_user_model, interactive, tty):
    prompt = Mock()
    monkeypatch.setattr('accounts.management.passwords.getpass.getpass', prompt)
    monkeypatch.setattr('accounts.management.passwords.sys.stdin.isatty', lambda: tty)
    with pytest.raises(CommandError):
        initial_password('INITIAL_TEST_PASSWORD', user=django_user_model(), interactive=interactive)
    prompt.assert_not_called()


def test_hidden_input_requires_matching_confirmation(monkeypatch, django_user_model):
    value = secrets.token_urlsafe(32)
    prompt = Mock(side_effect=[value, value])
    monkeypatch.setattr('accounts.management.passwords.getpass.getpass', prompt)
    monkeypatch.setattr('accounts.management.passwords.sys.stdin.isatty', lambda: True)
    assert initial_password('INITIAL_TEST_PASSWORD', user=django_user_model(), interactive=True) == value
    assert prompt.call_count == 2
    for call in prompt.call_args_list:
        assert value not in str(call)


def test_hidden_input_mismatch_is_rejected(monkeypatch, django_user_model):
    monkeypatch.setattr('accounts.management.passwords.getpass.getpass',
                        Mock(side_effect=[secrets.token_urlsafe(32), secrets.token_urlsafe(32)]))
    monkeypatch.setattr('accounts.management.passwords.sys.stdin.isatty', lambda: True)
    with pytest.raises(CommandError, match='no coinciden'):
        initial_password('INITIAL_TEST_PASSWORD', user=django_user_model(), interactive=True)


def test_getpass_cannot_fall_back_to_echoing_input(monkeypatch, django_user_model):
    def unavailable_terminal(*args):
        warnings.warn('Hidden input unavailable', getpass.GetPassWarning)
        pytest.fail('Input must stop before an echoing fallback')
    monkeypatch.setattr('accounts.management.passwords.getpass.getpass', unavailable_terminal)
    monkeypatch.setattr('accounts.management.passwords.sys.stdin.isatty', lambda: True)
    with pytest.raises(CommandError, match='segura'):
        initial_password('INITIAL_TEST_PASSWORD', user=django_user_model(), interactive=True)


@pytest.mark.parametrize('value', ['', '   '])
def test_empty_explicit_password_is_rejected(monkeypatch, django_user_model, value):
    monkeypatch.setenv('INITIAL_TEST_PASSWORD', value)
    with pytest.raises(CommandError):
        initial_password('INITIAL_TEST_PASSWORD', user=django_user_model(), interactive=False)


def test_configured_password_validators_are_enforced(monkeypatch, django_user_model, settings):
    settings.AUTH_PASSWORD_VALIDATORS = [{
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 100},
    }]
    monkeypatch.setenv('INITIAL_TEST_PASSWORD', secrets.token_urlsafe(32))
    with pytest.raises(CommandError, match='seguridad'):
        initial_password('INITIAL_TEST_PASSWORD', user=django_user_model(), interactive=False)


def test_bootstrap_missing_password_does_not_create_any_user(django_user_model):
    with pytest.raises(CommandError):
        call_command('create_initial_users', interactive=False, stdout=StringIO())
    assert django_user_model.objects.count() == 0


def test_second_missing_password_cannot_leave_a_partial_admin(monkeypatch, django_user_model):
    monkeypatch.setenv('INITIAL_ADMIN_PASSWORD', secrets.token_urlsafe(32))
    with pytest.raises(CommandError):
        call_command('create_initial_users', interactive=False, stdout=StringIO())
    assert django_user_model.objects.count() == 0


def test_bootstrap_preserves_existing_accounts_roles_and_passwords(monkeypatch, django_user_model, explicit_passwords):
    out = StringIO()
    call_command('create_initial_users', interactive=False, stdout=out)
    admin = django_user_model.objects.get(role=django_user_model.Role.ADMIN)
    worker = django_user_model.objects.get(role=django_user_model.Role.WORKER)
    assert admin.check_password(explicit_passwords['INITIAL_ADMIN_PASSWORD'])
    assert worker.check_password(explicit_passwords['INITIAL_WORKER_PASSWORD'])
    # An existing account's role/flags must not be reset, even if its role changed.
    worker.role = django_user_model.Role.CASHIER
    worker.save(update_fields=['role'])
    before = list(django_user_model.objects.order_by('pk').values())
    for name in explicit_passwords:
        monkeypatch.delenv(name)
    call_command('create_initial_users', interactive=False, stdout=out)
    assert list(django_user_model.objects.order_by('pk').values()) == before
    for value in explicit_passwords.values():
        assert value not in out.getvalue()


def test_catalog_requires_passwords_before_writing_any_data(django_user_model):
    from services.models import Service
    with pytest.raises(CommandError):
        call_command('seed_initial_catalog', interactive=False, stdout=StringIO())
    assert django_user_model.objects.count() == 0
    assert Service.objects.count() == 0
    assert Appointment.objects.count() == 0


def test_catalog_repeat_preserves_passwords_roles_and_historical_appointments(monkeypatch, django_user_model):
    values = []
    def generated_password(*args, **kwargs):
        value = secrets.token_urlsafe(32)
        values.append(value)
        return value
    prompt = Mock(side_effect=generated_password)
    monkeypatch.setattr('appointments.management.commands.seed_initial_catalog.initial_password', prompt)
    out = StringIO()
    call_command('seed_initial_catalog', interactive=False, stdout=out)
    assert prompt.call_count == 3
    assert django_user_model.objects.count() == 3
    assert all(user.is_worker for user in django_user_model.objects.all())
    changed = django_user_model.objects.first()
    changed.role = django_user_model.Role.CASHIER
    changed.save(update_fields=['role'])
    # Preserve a price and date that differ from the catalog's samples.
    historical = Appointment.objects.first()
    import datetime
    historical.date -= datetime.timedelta(days=60)
    historical.price_cop = 123456
    historical.save(update_fields=['date', 'price_cop'])
    users_before = list(django_user_model.objects.order_by('pk').values())
    appointments_before = {row['id']: row for row in Appointment.objects.values()}
    prompt.reset_mock()
    call_command('seed_initial_catalog', interactive=False, stdout=out)
    prompt.assert_not_called()
    assert list(django_user_model.objects.order_by('pk').values()) == users_before
    for row in Appointment.objects.filter(pk__in=appointments_before).values():
        assert row == appointments_before[row['id']]
    ids_before = set(Appointment.objects.values_list('pk', flat=True))
    call_command('seed_initial_catalog', interactive=False, stdout=out)
    assert set(Appointment.objects.values_list('pk', flat=True)) == ids_before
    for value in values:
        assert value not in out.getvalue()
