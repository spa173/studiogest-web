"""HTTP method restrictions for the authenticated, read-only Dashboard."""
import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db
ROLES = ['ADMIN', 'CAJA_RECEPCION', 'TRABAJADOR']


@pytest.mark.parametrize('role', ROLES)
@pytest.mark.parametrize('method', ['GET', 'HEAD'])
def test_dashboard_allows_safe_methods_with_existing_financial_permissions(
    client, django_user_model, role, method,
):
    user = django_user_model.objects.create_user(
        username='dashboard-methods', email='methods@example.invalid', role=role,
    )
    client.force_login(user)

    response = client.generic(method, reverse('dashboard:index'))

    assert response.status_code == 200
    assert response.context['can_view_financial_dashboard'] == (role != 'TRABAJADOR')
    if method == 'HEAD':
        assert response.content == b''
    else:
        html = response.content.decode()
        assert ('Servicios atendidos' in html) == (role != 'TRABAJADOR')
        assert 'dashboard-kpis' in html


@pytest.mark.parametrize('method', ['GET', 'HEAD'])
def test_dashboard_safe_methods_still_require_login(client, method):
    url = reverse('dashboard:index')

    response = client.generic(method, url)

    assert response.status_code == 302
    assert response.url == reverse('accounts:login') + '?next=' + url
    if method == 'HEAD':
        assert response.content == b''


@pytest.mark.parametrize('role', [None, *ROLES])
@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'TRACE', 'CONNECT'])
def test_dashboard_rejects_unsupported_methods(client, django_user_model, role, method):
    if role is not None:
        user = django_user_model.objects.create_user(
            username='dashboard-methods', email='methods@example.invalid', role=role,
        )
        client.force_login(user)

    response = client.generic(method, reverse('dashboard:index'))

    assert response.status_code == 405
    assert set(response.headers['Allow'].split(', ')) == {'GET', 'HEAD'}
