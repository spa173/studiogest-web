import secrets
from unittest.mock import patch
"""Pruebas de integración: autenticación, permisos por rol y persistencia.

Se ejecutan con pytest (``pytest``). Por defecto usan SQLite en memoria (config.settings_test);
para correrlas contra MySQL: ``pytest --ds=config.settings`` (ver README).
"""
import datetime

import pytest
from django.core.management import call_command
from django.db import connections
from django.utils import timezone
from django.urls import reverse

from appointments.models import Appointment
from customers.models import Customer
from services.models import Professional, Service

PASSWORD = secrets.token_urlsafe(32)

# Pantallas que exigen iniciar sesión
RUTAS_PROTEGIDAS = [
    'dashboard:index',
    'appointments:calendar',
    'customers:list',
    'services:list',
    'services:professionals_list',
    'inventory:list',
    'sales:index',
    'reports:index',
    'accounts:settings',
]

# Pantallas reservadas para administradores (el trabajador recibe 403)
RUTAS_SOLO_ADMIN = [
    'services:create',
    'inventory:create',
    'sales:index',
    'sales:cash_open',
    'reports:index',
]


@pytest.fixture
def admin_usuario(django_user_model):
    return django_user_model.objects.create_user(
        username='admin.test@studiogest.co', email='admin.test@studiogest.co',
        password=PASSWORD, role='ADMIN', first_name='Admin')


@pytest.fixture
def cajero(django_user_model):
    return django_user_model.objects.create_user(
        username='caja.test@studiogest.co', email='caja.test@studiogest.co',
        password=PASSWORD, role='CAJA_RECEPCION', first_name='Caja')


@pytest.fixture
def trabajador(django_user_model):
    return django_user_model.objects.create_user(
        username='barbero.test@studiogest.co', email='barbero.test@studiogest.co',
        password=PASSWORD, role='TRABAJADOR', first_name='Barbero')


# ---------------------------------------------------------------- Autenticación

@pytest.mark.django_db
def test_login_correcto_inicia_sesion_y_abre_el_panel(client, admin_usuario):
    respuesta = client.post(reverse('accounts:login'),
                            {'login': admin_usuario.email, 'password': PASSWORD})
    assert respuesta.status_code == 302
    assert client.get(reverse('dashboard:index')).status_code == 200


@pytest.mark.django_db
def test_login_con_clave_incorrecta_no_inicia_sesion(client, admin_usuario):
    respuesta = client.post(reverse('accounts:login'),
                            {'login': admin_usuario.email, 'password': secrets.token_urlsafe(32)})
    assert respuesta.status_code == 200  # vuelve al formulario
    assert client.get(reverse('dashboard:index')).status_code == 302


@pytest.mark.django_db
def test_cerrar_sesion_vuelve_a_proteger_las_paginas(client, admin_usuario):
    client.force_login(admin_usuario)
    assert client.get(reverse('customers:list')).status_code == 200
    assert client.post(reverse('accounts:logout')).status_code == 302
    respuesta = client.get(reverse('customers:list'))
    assert respuesta.status_code == 302
    assert reverse('accounts:login') in respuesta['Location']


@pytest.mark.django_db
@pytest.mark.parametrize('nombre_ruta', RUTAS_PROTEGIDAS)
def test_sin_sesion_se_redirige_al_login(client, nombre_ruta):
    respuesta = client.get(reverse(nombre_ruta))
    assert respuesta.status_code == 302
    assert reverse('accounts:login') in respuesta['Location']


@pytest.mark.django_db
def test_la_contrasena_se_guarda_cifrada(admin_usuario):
    assert admin_usuario.password != PASSWORD
    assert '$' in admin_usuario.password  # formato "algoritmo$sal$hash"
    assert admin_usuario.check_password(PASSWORD)


def test_la_aplicacion_usa_el_cifrado_seguro_por_defecto():
    """Las pruebas usan un cifrado rápido (conftest.py), pero el proyecto no lo cambia:
    sin PASSWORD_HASHERS propio, Django usa PBKDF2 (RNF-04)."""
    import config.settings as proyecto

    assert not hasattr(proyecto, 'PASSWORD_HASHERS')


@pytest.mark.django_db
def test_la_sesion_expira_a_los_30_minutos_de_inactividad(client, admin_usuario):
    """RNF-04: expiración de sesión tras 30 minutos de inactividad."""
    client.post(reverse('accounts:login'), {'login': admin_usuario.email, 'password': PASSWORD})
    assert client.session.get_expiry_age() == 1800


# ------------------------------------------------------------------- Permisos

@pytest.mark.django_db
@pytest.mark.parametrize('nombre_ruta', RUTAS_SOLO_ADMIN)
def test_trabajador_no_accede_a_pantallas_de_administrador(client, trabajador, nombre_ruta):
    client.force_login(trabajador)
    assert client.get(reverse(nombre_ruta)).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('nombre_ruta', RUTAS_SOLO_ADMIN)
def test_administrador_si_accede_a_pantallas_de_administrador(client, admin_usuario, nombre_ruta):
    client.force_login(admin_usuario)
    assert client.get(reverse(nombre_ruta)).status_code == 200


@pytest.mark.django_db
def test_trabajador_no_puede_eliminar_clientes(client, trabajador):
    cliente = Customer.objects.create(name='Cliente Permisos', phone='3001234567')
    client.force_login(trabajador)
    client.post(reverse('customers:delete', args=[cliente.pk]))
    assert Customer.objects.filter(pk=cliente.pk).exists()


@pytest.mark.django_db
def test_trabajador_no_crea_profesionales(client, trabajador, django_user_model):
    client.force_login(trabajador)
    cantidad = django_user_model.objects.count()
    client.post(reverse('services:professional_create'), {
        'first_name': 'Intruso', 'last_name': 'Prueba', 'email': 'intruso@studiogest.co',
        'phone': '3101112233', 'password': PASSWORD, 'specialty': 'Barbero'})
    assert django_user_model.objects.count() == cantidad


# ------------------------------------------------- Permisos del rol Caja / Recepción

# Pantallas que sí puede abrir (ver apps/accounts/permissions.py)
RUTAS_CAJA_SI = [
    'customers:list',
    'inventory:list',
    'inventory:history',
    'appointments:calendar',
    'sales:index',
    'reports:index',
]

# Pantallas de gestión que no puede abrir
RUTAS_CAJA_NO = ['services:create', 'inventory:create']


@pytest.mark.django_db
@pytest.mark.parametrize('nombre_ruta', RUTAS_CAJA_SI)
def test_caja_accede_a_ventas_reportes_y_consultas(client, cajero, nombre_ruta):
    client.force_login(cajero)
    assert client.get(reverse(nombre_ruta)).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('nombre_ruta', RUTAS_CAJA_NO)
def test_caja_no_gestiona_servicios_ni_inventario(client, cajero, nombre_ruta):
    client.force_login(cajero)
    assert client.get(reverse(nombre_ruta)).status_code == 403


@pytest.mark.django_db
def test_caja_no_puede_eliminar_clientes(client, cajero):
    cliente = Customer.objects.create(name='Cliente Caja', phone='3001230000')
    client.force_login(cajero)
    client.post(reverse('customers:delete', args=[cliente.pk]))
    assert Customer.objects.filter(pk=cliente.pk).exists()


def _datos_de_cita():
    """Datos válidos para agendar una cita con el catálogo de prueba."""
    with patch('appointments.management.commands.seed_initial_catalog.initial_password', side_effect=lambda *args, **kwargs: secrets.token_urlsafe(32)):
        call_command('seed_initial_catalog', interactive=False, verbosity=0)
    dia = timezone.localdate() + datetime.timedelta(days=21)
    while dia.weekday() != 2:  # miércoles
        dia += datetime.timedelta(days=1)
    return {
        'customer': Customer.objects.first().pk,
        'service': Service.objects.filter(is_active=True).first().pk,
        'professional': Professional.objects.filter(is_active=True).first().pk,
        'date': dia.isoformat(),
        'start_time': '15:00',
    }


@pytest.mark.django_db
def test_caja_solo_consulta_la_agenda_y_no_crea_citas(client, cajero, admin_usuario):
    """La agenda es de solo lectura para Caja; el administrador sí agenda (control)."""
    datos = _datos_de_cita()
    antes = Appointment.objects.count()

    client.force_login(cajero)
    client.post(reverse('appointments:calendar'), datos)
    assert Appointment.objects.count() == antes

    client.force_login(admin_usuario)
    client.post(reverse('appointments:calendar'), datos)
    assert Appointment.objects.count() == antes + 1


# ---------------------------------------------------------------- Persistencia

@pytest.mark.django_db(transaction=True)
def test_cliente_creado_desde_la_interfaz_queda_guardado(client, admin_usuario):
    """El registro se confirma en la base de datos, no solo en memoria."""
    client.force_login(admin_usuario)
    respuesta = client.post(reverse('customers:create'),
                            {'name': 'Cliente Persistente', 'phone': '3209876543'})
    assert respuesta.status_code == 302

    connections.close_all()  # fuerza una conexión nueva a la base de datos
    guardado = Customer.objects.get(name='Cliente Persistente')
    assert guardado.phone == '3209876543'


@pytest.mark.django_db(transaction=True)
def test_cliente_editado_conserva_los_cambios(client, admin_usuario):
    cliente = Customer.objects.create(name='Antes', phone='3001112222')
    client.force_login(admin_usuario)
    client.post(reverse('customers:update', args=[cliente.pk]),
                {'name': 'Despues', 'phone': '3001112222', 'is_vip': 'on'})

    connections.close_all()
    cliente = Customer.objects.get(pk=cliente.pk)
    assert cliente.name == 'Despues'
    assert cliente.is_vip is True


@pytest.mark.django_db(transaction=True)
def test_cliente_eliminado_no_vuelve_a_aparecer(client, admin_usuario):
    cliente = Customer.objects.create(name='Para Borrar', phone='3005556677')
    client.force_login(admin_usuario)
    client.post(reverse('customers:delete', args=[cliente.pk]))

    connections.close_all()
    assert not Customer.objects.filter(pk=cliente.pk).exists()
