"""Regression coverage for the visual merge and main's role restrictions."""
import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import resolve, reverse

from inventory.models import Product

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('role', ['ADMIN', 'CAJA_RECEPCION', 'TRABAJADOR'])
@pytest.mark.parametrize('menu', ['sidebar', 'mobile_menu', 'bottom_nav'])
def test_navigation_keeps_sales_access_by_role(django_user_model, role, menu):
    user = django_user_model.objects.create_user(username='navigation', role=role)
    request = RequestFactory().get(reverse('dashboard:index'))
    request.user = user
    request.resolver_match = resolve(request.path)
    html = render_to_string(f'includes/{menu}.html', request=request)
    assert (f'href="{reverse("sales:index")}"' in html) == (role != 'TRABAJADOR')
    if menu != 'bottom_nav':
        assert (f'href="{reverse("reports:index")}"' in html) == (role != 'TRABAJADOR')
    if menu == 'sidebar':
        assert ('Nuevo Turno' in html) == (role != 'CAJA_RECEPCION')
        assert 'img/branding/isotipo.png' in html


@pytest.mark.parametrize('role', ['ADMIN', 'CAJA_RECEPCION', 'TRABAJADOR'])
def test_dashboard_keeps_layout_real_inventory_and_financial_permissions(client, django_user_model, role):
    user = django_user_model.objects.create_user(username='dashboard-merge', role=role)
    Product.objects.create(
        code='QA-MERGE', name='Insumo de prueba', base_unit='ML', stock=0,
        minimum_stock=10, acquisition_cost=1, sale_price=2, service_usage_price=1,
    )
    client.force_login(user)
    response = client.get(reverse('dashboard:index'))
    assert response.status_code == 200
    html = response.content.decode()
    assert html.count('class="dashboard-kpi"') == (3 if role == 'TRABAJADOR' else 4)
    assert ('Servicios atendidos' in html) == (role != 'TRABAJADOR')
    assert ('Valor de citas de hoy' in html) == (role != 'TRABAJADOR')
    assert 'Insumo de prueba' in html
    assert len(response.context['inventory_alerts']) == 1
    assert 'Datos de ejemplo' not in html
    assert 'dashboard-aside' in html
    assert 'css/tailwind.out.css' in html
    assert 'css/theme.css' in html
    assert 'css/dashboard.css' in html
    assert 'favicon-32.png' in html
    assert 'cdn.tailwindcss.com' not in html
    assert 'tailwind.config' not in html
