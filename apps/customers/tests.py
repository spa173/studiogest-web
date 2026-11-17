import secrets
from django.contrib.auth import get_user_model
from django.core.management import call_command
from unittest.mock import patch
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment
from customers.models import Customer

User = get_user_model()


class ClientesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = secrets.token_urlsafe(32)
        cls.admin = User.objects.create_user(
            username='admin@t.co', email='admin@t.co', password=cls.password, role=User.Role.ADMIN)
        cls.worker = User.objects.create_user(
            username='trab@t.co', email='trab@t.co', password=cls.password, role=User.Role.WORKER)
        cls.ana = Customer.objects.create(name='Ana Gómez', phone='3001112233', is_vip=True)
        cls.luis = Customer.objects.create(name='Luis Pérez', phone='3109998877')

    def entrar(self, usuario):
        self.client.force_login(usuario)

    def test_requiere_iniciar_sesion(self):
        r = self.client.get(reverse('customers:list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_lista_y_busqueda(self):
        self.entrar(self.worker)
        r = self.client.get(reverse('customers:list'))
        self.assertContains(r, 'Ana Gómez')
        self.assertContains(r, 'Luis Pérez')
        r = self.client.get(reverse('customers:list'), {'q': 'Ana'})
        self.assertContains(r, 'Ana Gómez')
        self.assertNotContains(r, 'Luis Pérez')

    def test_filtro_vip(self):
        self.entrar(self.worker)
        r = self.client.get(reverse('customers:list'), {'vip': '1'})
        self.assertContains(r, 'Ana Gómez')
        self.assertNotContains(r, 'Luis Pérez')

    def test_crear_cliente_valido(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:create'), {
            'name': 'Mario  Ruiz',
            'phone': '320 555 1212',
            'data_consent': 'on',
            'data_consent_method': Customer.ConsentMethod.PRESENCIAL,
            'data_consent_notes': 'Autorización informada en recepción',
        })
        self.assertRedirects(r, reverse('customers:list'))
        cliente = Customer.objects.get(name='Mario Ruiz')
        self.assertTrue(cliente.data_consent)
        self.assertIsNotNone(cliente.data_consent_at)
        self.assertLessEqual(cliente.data_consent_at, timezone.now())
        self.assertEqual(cliente.data_consent_method, Customer.ConsentMethod.PRESENCIAL)
        self.assertEqual(cliente.data_consent_notes, 'Autorización informada en recepción')
        self.assertEqual(cliente.data_consent_recorded_by, self.worker)

    def test_rechaza_telefono_repetido(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:create'), {'name': 'Otro Cliente', 'phone': '3001112233'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ya existe un cliente con este teléfono')

    def test_rechaza_telefono_invalido_y_nombre_corto(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:create'), {'name': 'Al', 'phone': 'abc'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Customer.objects.count(), 2)

    def test_editar_cliente(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:update', args=[self.luis.pk]),
                             {'name': 'Luis P. Pérez', 'phone': '3109998877', 'is_vip': 'on', 'data_consent': 'on'})
        self.assertRedirects(r, reverse('customers:list'))
        self.luis.refresh_from_db()
        self.assertEqual(self.luis.name, 'Luis P. Pérez')
        self.assertTrue(self.luis.is_vip)
        self.assertTrue(self.luis.data_consent)
        self.assertIsNotNone(self.luis.data_consent_at)
        self.assertEqual(self.luis.data_consent_recorded_by, self.worker)

    def test_otorgar_consentimiento_registra_evidencia_y_editar_no_la_sobrescribe(self):
        self.entrar(self.worker)
        self.client.post(reverse('customers:update', args=[self.luis.pk]), {
            'name': 'Luis Pérez', 'phone': '3109998877',
            'data_consent': 'on', 'data_consent_method': Customer.ConsentMethod.DIGITAL,
            'data_consent_notes': 'Aceptación por formulario',
        })
        self.luis.refresh_from_db()
        evidencia_at = self.luis.data_consent_at
        self.assertIsNotNone(evidencia_at)
        self.assertEqual(self.luis.data_consent_method, Customer.ConsentMethod.DIGITAL)

        self.client.post(reverse('customers:update', args=[self.luis.pk]), {
            'name': 'Luis Pérez', 'phone': '3109998877', 'is_vip': 'on',
            'data_consent': 'on', 'data_consent_method': Customer.ConsentMethod.ESCRITO,
            'data_consent_notes': 'Se actualiza medio en edición',
        })
        self.luis.refresh_from_db()
        self.assertTrue(self.luis.data_consent)
        self.assertEqual(self.luis.data_consent_at, evidencia_at)
        self.assertEqual(self.luis.data_consent_method, Customer.ConsentMethod.ESCRITO)
        self.assertEqual(self.luis.data_consent_notes, 'Se actualiza medio en edición')
        self.assertTrue(self.luis.is_vip)

    def test_revocar_consentimiento_conserva_evidencia_del_ultimo_otorgamiento(self):
        self.entrar(self.worker)
        self.client.post(reverse('customers:update', args=[self.luis.pk]), {
            'name': 'Luis Pérez', 'phone': '3109998877',
            'data_consent': 'on', 'data_consent_method': Customer.ConsentMethod.ESCRITO,
            'data_consent_notes': 'Autorización firmada',
        })
        self.luis.refresh_from_db()
        evidencia_at = self.luis.data_consent_at
        self.assertIsNotNone(evidencia_at)

        self.client.post(reverse('customers:update', args=[self.luis.pk]), {
            'name': 'Luis Pérez', 'phone': '3109998877',
            'data_consent_method': Customer.ConsentMethod.DIGITAL,
            'data_consent_notes': 'Revocación solicitada por el cliente',
        })
        self.luis.refresh_from_db()
        self.assertFalse(self.luis.data_consent)
        self.assertEqual(self.luis.data_consent_at, evidencia_at)
        self.assertEqual(self.luis.data_consent_method, Customer.ConsentMethod.ESCRITO)
        self.assertEqual(self.luis.data_consent_recorded_by, self.worker)
        self.assertEqual(self.luis.data_consent_notes, 'Revocación solicitada por el cliente')

    def test_trabajador_no_puede_eliminar(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:delete', args=[self.luis.pk]))
        self.assertRedirects(r, reverse('customers:list'))
        self.assertTrue(Customer.objects.filter(pk=self.luis.pk).exists())

    def test_admin_elimina_cliente_sin_citas(self):
        self.entrar(self.admin)
        r = self.client.post(reverse('customers:delete', args=[self.luis.pk]))
        self.assertRedirects(r, reverse('customers:list'))
        self.assertFalse(Customer.objects.filter(pk=self.luis.pk).exists())

    def test_admin_no_elimina_cliente_con_citas(self):
        with patch('appointments.management.commands.seed_initial_catalog.initial_password', side_effect=lambda *args, **kwargs: secrets.token_urlsafe(32)):
            call_command('seed_initial_catalog', interactive=False, verbosity=0)
        con_citas = Customer.objects.filter(appointments__isnull=False).first()
        self.assertIsNotNone(con_citas)
        self.entrar(self.admin)
        self.client.post(reverse('customers:delete', args=[con_citas.pk]))
        self.assertTrue(Customer.objects.filter(pk=con_citas.pk).exists())

    def test_cliente_con_solo_citas_canceladas_si_se_elimina(self):
        with patch('appointments.management.commands.seed_initial_catalog.initial_password', side_effect=lambda *args, **kwargs: secrets.token_urlsafe(32)):
            call_command('seed_initial_catalog', interactive=False, verbosity=0)
        cliente = Customer.objects.filter(appointments__isnull=False).first()
        cliente.appointments.update(status=Appointment.Status.CANCELLED)
        self.entrar(self.admin)
        r = self.client.get(reverse('customers:delete', args=[cliente.pk]))
        self.assertContains(r, 'También se eliminarán')
        r = self.client.post(reverse('customers:delete', args=[cliente.pk]))
        self.assertRedirects(r, reverse('customers:list'))
        self.assertFalse(Customer.objects.filter(pk=cliente.pk).exists())
        self.assertFalse(Appointment.objects.filter(customer_id=cliente.pk).exists())

    def test_cliente_con_una_cita_cancelada_y_otra_vigente_no_se_elimina(self):
        with patch('appointments.management.commands.seed_initial_catalog.initial_password', side_effect=lambda *args, **kwargs: secrets.token_urlsafe(32)):
            call_command('seed_initial_catalog', interactive=False, verbosity=0)
        cliente = Customer.objects.annotate(n=Count('appointments')).filter(n__gte=2).first()
        self.assertIsNotNone(cliente)
        primera = cliente.appointments.first()
        primera.status = Appointment.Status.CANCELLED
        primera.save(update_fields=['status'])
        self.entrar(self.admin)
        self.client.post(reverse('customers:delete', args=[cliente.pk]))
        self.assertTrue(Customer.objects.filter(pk=cliente.pk).exists())
        self.assertEqual(cliente.appointments.count(), 2)

    def test_detalle_cliente_oculta_historial_ventas_a_trabajador(self):
        from decimal import Decimal
        from sales.models import CashRegisterSession, PaymentMethod, SaleDetailType
        from services.models import Service
        from sales.services import create_sale
        # datos mínimos para una venta visible en historial
        service = Service.objects.create(name='Servicio detalle', price_cop=Decimal('10000'), duration_minutes=30)
        session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('0'))
        create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CASH,
            customer=self.ana,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': Decimal('10000')}],
        )
        self.entrar(self.worker)
        r = self.client.get(reverse('customers:detail', args=[self.ana.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Historial de compras')
        self.assertNotContains(r, 'Medio de pago')

    def test_detalle_cliente_muestra_historial_ventas_a_caja_y_admin(self):
        from decimal import Decimal
        from sales.models import CashRegisterSession, PaymentMethod, SaleDetailType
        from services.models import Service
        from sales.services import create_sale
        cashier = User.objects.create_user(
            username='caja@t.co', email='caja@t.co', password=self.password, role=User.Role.CASHIER)
        service = Service.objects.create(name='Servicio detalle 2', price_cop=Decimal('12000'), duration_minutes=30)
        session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('0'))
        sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CASH,
            customer=self.ana,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': Decimal('12000')}],
        )
        for user in (cashier, self.admin):
            self.entrar(user)
            r = self.client.get(reverse('customers:detail', args=[self.ana.pk]))
            self.assertEqual(r.status_code, 200, user)
            self.assertContains(r, 'Historial de compras')
            self.assertContains(r, 'Servicio detalle 2')
