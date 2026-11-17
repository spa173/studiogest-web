import datetime
import re
from decimal import Decimal
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import resolve, reverse

from appointments.models import Appointment
from customers.models import Customer
from inventory.models import Product, StockEntry
from services.models import Service
from .models import PaymentMethod, Sale, SaleDetail, SaleDetailType, CashRegisterSession, SaleStatus
from .services import create_sale, cancel_sale

User = get_user_model()


class LinkParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


class SalesNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='sales-admin', email='admin@sales.test', role=User.Role.ADMIN)
        cls.worker = User.objects.create_user(username='sales-worker', email='worker@sales.test',
                                             role=User.Role.WORKER, is_staff=True)
        cls.cashier = User.objects.create_user(username='sales-cashier', email='cashier@sales.test',
                                               role=User.Role.CASHIER)
        cls.superuser = User.objects.create_user(username='sales-super', email='super@sales.test',
                                                role=User.Role.WORKER, is_superuser=True)
        Product.objects.create(code='SALES-CHECK', name='Producto existente', base_unit=Product.BaseUnit.UNIT,
                               stock=Decimal('12'), acquisition_cost=1, sale_price=2, service_usage_price=2)

    def setUp(self):
        self.url = reverse('sales:index')
        self.client.force_login(self.admin)

    def mobile_links(self, response):
        html = response.content.decode()
        menu = re.search(r'<dialog id="mobile-menu"[\s\S]*?</dialog>', html).group()
        return LinkParser(menu).links

    def test_anonymous_redirects_to_login(self):
        self.client.logout()
        self.assertRedirects(self.client.get(self.url), reverse('accounts:login') + '?next=' + self.url)

    def test_admin_gets_three_sections_with_no_sales_data(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'sales/index.html')
        for text in ['Ventas de productos', 'Cobros por servicios', 'Movimientos de caja',
                     'Una cita completada no acredita un pago recibido']:
            self.assertContains(response, text)
        self.assertNotContains(response, 'href="#"')
        self.assertNotContains(response, '$')
        self.assertContains(response, 'href="/sales/" aria-current="page"', count=3)

    def test_worker_denied_despite_staff_flag(self):
        self.client.force_login(self.worker)
        response = self.client.get(self.url)
        self.assertContains(response, 'Acceso restringido', status_code=403)
        self.assertNotContains(response, 'href="/sales/"', status_code=403)
        self.assertNotContains(response, 'href="/reports/"', status_code=403)

    def test_cashier_can_access_sales_index(self):
        self.client.force_login(self.cashier)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sales/index.html')

    def test_superuser_uses_existing_admin_permission(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_no_operations_or_stock_changes(self):
        products_before = list(Product.objects.values())
        entries_before = list(StockEntry.objects.values())
        appointments_before = list(Appointment.objects.values())
        self.client.get(self.url)
        self.assertEqual(self.client.post(self.url, {'quantity': 1, 'amount': 10}).status_code, 405)
        self.assertEqual(list(Product.objects.values()), products_before)
        self.assertEqual(list(StockEntry.objects.values()), entries_before)
        self.assertEqual(list(Appointment.objects.values()), appointments_before)

    def test_admin_mobile_menu_reaches_all_modules(self):
        response = self.client.get(self.url)
        links = self.mobile_links(response)
        expected = ['dashboard:index', 'appointments:calendar', 'customers:list', 'services:list',
                    'services:professionals_list', 'inventory:list', 'sales:index',
                    'reports:index', 'accounts:settings']
        self.assertEqual(len(links), len(expected))
        urls = {link['href'] for link in links}
        for name in expected:
            with self.subTest(route=name):
                url = reverse(name)
                self.assertIn(url, urls)
                self.assertEqual(resolve(url).view_name, name)
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual([link['href'] for link in links if link.get('aria-current') == 'page'], [self.url])

    def test_worker_mobile_menu_keeps_personal_and_operational_modules(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('services:list'))
        links = self.mobile_links(response)
        self.assertEqual(len(links), 7)
        self.assertEqual([link['href'] for link in links if link.get('aria-current') == 'page'], [reverse('services:list')])
        self.assertIn(reverse('accounts:settings'), {link['href'] for link in links})
        self.assertIn(reverse('inventory:list'), {link['href'] for link in links})

    def test_notifications_and_menu_have_accessible_controls(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-open-dialog="mobile-menu"')
        self.assertContains(response, 'data-open-dialog="notifications-panel"')
        self.assertContains(response, 'aria-labelledby="notifications-title"')
        self.assertContains(response, 'Las notificaciones todavía no están disponibles')
        self.assertNotContains(response, 'ring-2 ring-surface-container-lowest')
        self.assertContains(response, '/static/js/navigation.js')

    def test_new_appointment_link_reaches_calendar_without_creating_records(self):
        before = Appointment.objects.count()
        response = self.client.get(reverse('appointments:calendar'), {'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="appointmentModal"')
        self.assertContains(response, 'window.openAppointmentModal')
        self.assertContains(response, '/static/js/navigation.js')
        self.assertEqual(Appointment.objects.count(), before)


class CreateSaleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='sale-admin', email='admin@sale.test', role=User.Role.ADMIN, is_staff=True)
        cls.cashier = User.objects.create_user(username='sale-cashier', email='cashier@sale.test', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='sale-worker', email='worker@sale.test', role=User.Role.WORKER)
        cls.customer = Customer.objects.create(name='Cliente Venta', phone='3001234567')
        cls.service = Service.objects.create(name='Corte', price_cop=25000, duration_minutes=30)
        cls.product = Product.objects.create(code='P-1', name='Pomada', base_unit=Product.BaseUnit.UNIT,
                                            stock=Decimal('10'), acquisition_cost=Decimal('5'),
                                            sale_price=Decimal('15'), service_usage_price=Decimal('15'))

    def setUp(self):
        self.cash_session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('0'))

    def test_create_sale_registers_total_and_discounts_stock(self):
        sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CASH,
            customer=self.customer,
            cash_session=self.cash_session,
            details=[
                {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 25000},
                {'type': SaleDetailType.PRODUCT, 'product': self.product, 'quantity': 2, 'unit_price': 15},
            ],
        )
        self.assertEqual(sale.total, Decimal('25030'))
        self.assertEqual(sale.details.count(), 2)
        self.assertEqual(sale.cash_session, self.cash_session)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('8'))

    def test_create_sale_rejects_insufficient_stock(self):
        with self.assertRaises(ValidationError):
            create_sale(
                user=self.admin,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=self.cash_session,
                details=[
                    {'type': SaleDetailType.PRODUCT, 'product': self.product, 'quantity': 100, 'unit_price': 15},
                ],
            )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('10'))

    def test_cashier_can_create_sale_via_service(self):
        product = Product.objects.create(code='P-CASH', name='Gel', base_unit=Product.BaseUnit.UNIT,
                                         stock=Decimal('5'), acquisition_cost=Decimal('1'),
                                         sale_price=Decimal('10'), service_usage_price=Decimal('10'))
        sale = create_sale(
            user=self.cashier,
            payment_method=PaymentMethod.CASH,
            customer=self.customer,
            cash_session=self.cash_session,
            details=[
                {'type': SaleDetailType.PRODUCT, 'product': product, 'quantity': 1, 'unit_price': 10},
            ],
        )
        self.assertEqual(sale.user, self.cashier)
        self.assertEqual(sale.total, Decimal('10'))

    def test_worker_cannot_create_sale_via_service(self):
        with self.assertRaises(ValidationError):
            create_sale(
                user=self.worker,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=self.cash_session,
                details=[
                    {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 25000},
                ],
            )
        self.assertEqual(Sale.objects.count(), 0)

    def test_create_sale_requires_open_cash_session(self):
        with self.assertRaisesMessage(ValidationError, 'Debes seleccionar una sesión de caja abierta para registrar la venta.'):
            create_sale(
                user=self.admin,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=None,
                details=[
                    {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 25000},
                ],
            )
        self.assertEqual(Sale.objects.count(), 0)

    def test_create_sale_rejects_closed_cash_session(self):
        closed_session = CashRegisterSession.objects.create(
            opened_by=self.admin, opening_cash=Decimal('0'),
            status=CashRegisterSession.Status.CLOSED,
        )
        with self.assertRaisesMessage(ValidationError, 'No se puede registrar la venta porque la sesión de caja seleccionada está cerrada.'):
            create_sale(
                user=self.admin,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=closed_session,
                details=[
                    {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 25000},
                ],
            )
        self.assertEqual(Sale.objects.count(), 0)


class SalesAccessPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='policy-admin', email='policy-admin@sales.test', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='policy-cashier', email='policy-cashier@sales.test', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='policy-worker', email='policy-worker@sales.test', role=User.Role.WORKER)

    def test_anonymous_redirects_on_sales_endpoints(self):
        endpoints = [
            ('get', reverse('sales:index')),
            ('get', reverse('sales:create')),
            ('post', reverse('sales:store')),
            ('get', reverse('sales:cash_open')),
            ('post', reverse('sales:cash_store')),
        ]
        for method, url in endpoints:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('accounts:login'), response.url)

    def test_worker_forbidden_on_sales_and_cash_endpoints(self):
        self.client.force_login(self.worker)
        session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=0)
        endpoints = [
            ('get', reverse('sales:index')),
            ('get', reverse('sales:create')),
            ('post', reverse('sales:store')),
            ('get', reverse('sales:cash_open')),
            ('post', reverse('sales:cash_store')),
            ('get', reverse('sales:cash_close', args=[session.pk])),
            ('post', reverse('sales:cash_finalize', args=[session.pk])),
        ]
        for method, url in endpoints:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 403)

    def test_cashier_can_access_sales_create_and_cash_pages(self):
        self.client.force_login(self.cashier)
        session = CashRegisterSession.objects.create(opened_by=self.cashier, opening_cash=0)
        self.assertEqual(self.client.get(reverse('sales:create')).status_code, 200)
        self.assertEqual(self.client.get(reverse('sales:cash_open')).status_code, 200)
        self.assertEqual(self.client.get(reverse('sales:cash_close', args=[session.pk])).status_code, 200)
        # Acceso a registrar venta (POST invÃƒÂ¡lido sin detalles): pasa control de permisos y re-renderiza formulario.
        response = self.client.post(reverse('sales:store'), {
            'payment_method': PaymentMethod.CASH,
            'cash_session': session.pk,
            'details-TOTAL_FORMS': '0',
            'details-INITIAL_FORMS': '0',
            'details-MIN_NUM_FORMS': '0',
            'details-MAX_NUM_FORMS': '1000',
        })
        self.assertEqual(response.status_code, 200)

    def test_sale_create_redirects_to_open_cash_when_no_open_session(self):
        from django.contrib.messages import get_messages

        self.client.force_login(self.cashier)
        response = self.client.get(reverse('sales:create'))
        self.assertRedirects(response, reverse('sales:cash_open'), fetch_redirect_response=False)
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn('Debes abrir una sesión de caja antes de registrar ventas.', messages)

    def test_sale_store_redirects_to_open_cash_when_no_open_session(self):
        self.client.force_login(self.cashier)
        response = self.client.post(reverse('sales:store'), {
            'payment_method': PaymentMethod.CASH,
            'details-TOTAL_FORMS': '0',
            'details-INITIAL_FORMS': '0',
            'details-MIN_NUM_FORMS': '0',
            'details-MAX_NUM_FORMS': '1000',
        })
        self.assertRedirects(response, reverse('sales:cash_open'))

    def test_cashier_can_open_and_close_cash_session(self):
        self.client.force_login(self.cashier)
        open_response = self.client.post(reverse('sales:cash_store'), {'opening_cash': '50000', 'notes': 'Apertura'})
        self.assertRedirects(open_response, reverse('sales:index'))
        session = CashRegisterSession.objects.get(opened_by=self.cashier)
        self.assertTrue(session.is_open)
        close_response = self.client.post(reverse('sales:cash_finalize', args=[session.pk]), {'counted_cash': '50000'})
        self.assertRedirects(close_response, reverse('sales:index'))
        session.refresh_from_db()
        self.assertFalse(session.is_open)
        self.assertEqual(session.counted_cash, Decimal('50000'))
        self.assertEqual(session.cash_difference, Decimal('0'))


class SaleServiceCriticalFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='flow-admin', email='flow-admin@sales.test', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='flow-cashier', email='flow-cashier@sales.test', role=User.Role.CASHIER)
        cls.customer = Customer.objects.create(name='Cliente Flujo', phone='3000000001')
        cls.service = Service.objects.create(name='Peinado', price_cop=30000, duration_minutes=45)

    def setUp(self):
        self.product = Product.objects.create(
            code='FLOW-P1', name='Shampoo', base_unit=Product.BaseUnit.UNIT,
            stock=Decimal('5'), acquisition_cost=Decimal('1000'),
            sale_price=Decimal('12000'), service_usage_price=Decimal('12000'),
        )
        self.cash_session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('0'))

    def test_mixed_sale_discounts_each_product_quantity_and_keeps_totals(self):
        sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CARD,
            customer=self.customer,
            cash_session=self.cash_session,
            details=[
                {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 30000},
                {'type': SaleDetailType.PRODUCT, 'product': self.product, 'quantity': 2, 'unit_price': 12000},
            ],
        )
        self.product.refresh_from_db()
        self.assertEqual(sale.total, Decimal('54000'))
        self.assertEqual(sale.details.count(), 2)
        self.assertEqual(self.product.stock, Decimal('3'))
        service_detail = sale.details.get(detail_type=SaleDetailType.SERVICE)
        product_detail = sale.details.get(detail_type=SaleDetailType.PRODUCT)
        self.assertEqual(service_detail.subtotal, Decimal('30000'))
        self.assertEqual(product_detail.subtotal, Decimal('24000'))

    def test_insufficient_stock_rolls_back_sale_and_preserves_stock(self):
        with self.assertRaises(ValidationError):
            create_sale(
                user=self.admin,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=self.cash_session,
                details=[
                    {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 30000},
                    {'type': SaleDetailType.PRODUCT, 'product': self.product, 'quantity': 10, 'unit_price': 12000},
                ],
            )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('5'))
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(SaleDetail.objects.count(), 0)

    def test_sale_rejects_closed_cash_session(self):
        session = CashRegisterSession.objects.create(
            opened_by=self.admin, opening_cash=Decimal('20000'),
            status=CashRegisterSession.Status.CLOSED,
        )
        with self.assertRaisesMessage(ValidationError, 'No se puede registrar la venta porque la sesión de caja seleccionada está cerrada.'):
            create_sale(
                user=self.admin,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=session,
                details=[
                    {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 30000},
                ],
            )
        self.assertEqual(Sale.objects.count(), 0)

    def test_sale_requires_at_least_one_detail(self):
        with self.assertRaisesMessage(ValidationError, 'La venta debe tener al menos un detalle.'):
            create_sale(
                user=self.admin,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=self.cash_session,
                details=[],
            )
        self.assertEqual(Sale.objects.count(), 0)

    def test_service_detail_quantity_must_be_one(self):
        with self.assertRaises(ValidationError):
            create_sale(
                user=self.admin,
                payment_method=PaymentMethod.CASH,
                customer=self.customer,
                cash_session=self.cash_session,
                details=[
                    {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 2, 'unit_price': 30000},
                ],
            )
        self.assertEqual(Sale.objects.count(), 0)

    def _create_professional(self, username):
        from services.models import Professional

        user = User.objects.create_user(
            username=username,
            email=f'{username}@sales.test',
            role=User.Role.WORKER,
        )
        return Professional.objects.create(user=user)

    def test_cannot_charge_same_appointment_twice(self):
        from appointments.models import Appointment

        pro = self._create_professional('pro-flujo')
        appt = Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            professional=pro,
            date=datetime.date(2026, 11, 20),
            start_time=datetime.time(10, 0),
            created_by=self.admin,
            status=Appointment.Status.COMPLETED,
        )
        create_sale(
            user=self.cashier,
            payment_method=PaymentMethod.CASH,
            appointment=appt,
            cash_session=self.cash_session,
            details=[
                {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': appt.price_cop},
            ],
        )
        self.assertEqual(Sale.objects.filter(appointment=appt).count(), 1)
        with self.assertRaises(ValidationError):
            create_sale(
                user=self.cashier,
                payment_method=PaymentMethod.CASH,
                appointment=appt,
                cash_session=self.cash_session,
                details=[
                    {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': appt.price_cop},
                ],
            )
        self.assertEqual(Sale.objects.filter(appointment=appt).count(), 1)

    def test_sale_with_appointment_inherits_customer_when_missing(self):
        from appointments.models import Appointment

        pro = self._create_professional('pro-herencia')
        appt = Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            professional=pro,
            date=datetime.date(2026, 11, 21),
            start_time=datetime.time(11, 0),
            created_by=self.admin,
            status=Appointment.Status.COMPLETED,
        )

        sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.TRANSFER,
            appointment=appt,
            cash_session=self.cash_session,
            details=[
                {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': appt.price_cop},
            ],
        )
        self.assertEqual(sale.customer, self.customer)
        self.assertEqual(sale.appointment, appt)



class CashSessionTotalsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='cash-admin', email='cash-admin@sales.test', role=User.Role.ADMIN)

    def test_close_view_groups_registered_sales_by_payment_method(self):
        customer = Customer.objects.create(name='Cliente Caja', phone='3000000002')
        service = Service.objects.create(name='Servicio Caja', price_cop=10000, duration_minutes=30)
        session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('50000'))
        create_sale(
            user=self.admin, payment_method=PaymentMethod.CASH, customer=customer,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': 10000}],
        )
        create_sale(
            user=self.admin, payment_method=PaymentMethod.CARD, customer=customer,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': 15000}],
        )
        create_sale(
            user=self.admin, payment_method=PaymentMethod.TRANSFER, customer=customer,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': 20000}],
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:cash_close', args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['totals']['cash'], Decimal('10000'))
        self.assertEqual(response.context['totals']['card'], Decimal('15000'))
        self.assertEqual(response.context['totals']['transfer'], Decimal('20000'))
        self.assertEqual(response.context['sales_total'], Decimal('45000'))
        self.assertEqual(response.context['expected_cash'], Decimal('60000'))
        self.assertEqual(response.context['grand_total'], Decimal('95000'))
        self.assertEqual(response.context['sales'].count(), 3)
        self.assertContains(response, 'Arqueo detallado')
        self.assertContains(response, 'Total ventas (todos los medios)')
        self.assertContains(response, 'Efectivo esperado en caja (base inicial + ventas en efectivo)')
        self.assertContains(response, 'Efectivo contado al cierre')
        self.assertIn('close_form', response.context)


class CashSessionCloseWithCountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='count-admin', email='count-admin@sales.test', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='count-cashier', email='count-cashier@sales.test', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='count-worker', email='count-worker@sales.test', role=User.Role.WORKER)
        cls.customer = Customer.objects.create(name='Cliente Conteo', phone='3000000099')
        cls.service = Service.objects.create(name='Servicio Conteo', price_cop=10000, duration_minutes=30)

    def _create_session_with_sales(self):
        session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('50000'))
        create_sale(
            user=self.admin, payment_method=PaymentMethod.CASH, customer=self.customer,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 10000}],
        )
        create_sale(
            user=self.admin, payment_method=PaymentMethod.CARD, customer=self.customer,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 15000}],
        )
        return session

    def test_finalize_saves_counted_cash_and_negative_difference(self):
        session = self._create_session_with_sales()
        self.client.force_login(self.cashier)
        response = self.client.post(reverse('sales:cash_finalize', args=[session.pk]), {'counted_cash': '58000'})
        self.assertRedirects(response, reverse('sales:index'))
        session.refresh_from_db()
        self.assertEqual(session.status, CashRegisterSession.Status.CLOSED)
        self.assertIsNotNone(session.closed_at)
        self.assertEqual(session.counted_cash, Decimal('58000'))
        self.assertEqual(session.cash_difference, Decimal('-2000'))  # esperado 60000

    def test_finalize_saves_surplus_difference(self):
        session = self._create_session_with_sales()
        self.client.force_login(self.admin)
        response = self.client.post(reverse('sales:cash_finalize', args=[session.pk]), {'counted_cash': '62000'})
        self.assertRedirects(response, reverse('sales:index'))
        session.refresh_from_db()
        self.assertEqual(session.counted_cash, Decimal('62000'))
        self.assertEqual(session.cash_difference, Decimal('2000'))

    def test_finalize_requires_counted_cash(self):
        session = self._create_session_with_sales()
        self.client.force_login(self.admin)
        response = self.client.post(reverse('sales:cash_finalize', args=[session.pk]), {})
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.status, CashRegisterSession.Status.OPEN)
        self.assertIsNone(session.counted_cash)
        self.assertIsNone(session.cash_difference)
        self.assertContains(response, 'Ingresa el efectivo contado al cierre.')

    def test_finalize_already_closed_is_coherent_without_count(self):
        session = CashRegisterSession.objects.create(
            opened_by=self.admin, opening_cash=Decimal('10000'),
            status=CashRegisterSession.Status.CLOSED,
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse('sales:cash_finalize', args=[session.pk]), {})
        self.assertRedirects(response, reverse('sales:index'))

    def test_worker_cannot_finalize_with_count(self):
        session = self._create_session_with_sales()
        self.client.force_login(self.worker)
        response = self.client.post(reverse('sales:cash_finalize', args=[session.pk]), {'counted_cash': '60000'})
        self.assertEqual(response.status_code, 403)
        session.refresh_from_db()
        self.assertEqual(session.status, CashRegisterSession.Status.OPEN)
        self.assertIsNone(session.counted_cash)

    def test_closed_session_detail_shows_count_and_difference(self):
        session = self._create_session_with_sales()
        session.status = CashRegisterSession.Status.CLOSED
        session.counted_cash = Decimal('59000')
        session.cash_difference = Decimal('-1000')
        session.closed_at = session.opened_at
        session.save(update_fields=['status', 'counted_cash', 'cash_difference', 'closed_at'])
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:cash_close', args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Efectivo contado')
        self.assertContains(response, '59000')
        self.assertContains(response, 'Diferencia (contado - esperado)')
        self.assertNotContains(response, 'Efectivo contado al cierre')
        self.assertIsNone(response.context['close_form'])


class CancelSaleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='cancel-admin', email='cancel-admin@sales.test', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='cancel-cashier', email='cancel-cashier@sales.test', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='cancel-worker', email='cancel-worker@sales.test', role=User.Role.WORKER)
        cls.customer = Customer.objects.create(name='Cliente Anulacion', phone='3009990000')
        cls.service = Service.objects.create(name='Servicio Anulable', price_cop=20000, duration_minutes=30)

    def setUp(self):
        self.product = Product.objects.create(
            code='CAN-P1', name='Producto Anulable', base_unit=Product.BaseUnit.UNIT,
            stock=Decimal('5'), acquisition_cost=Decimal('1000'),
            sale_price=Decimal('8000'), service_usage_price=Decimal('8000'),
        )
        self.session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('0'))

    def _create_professional(self, username):
        from services.models import Professional
        user = User.objects.create_user(username=username, email=f'{username}@sales.test', role=User.Role.WORKER)
        return Professional.objects.create(user=user)

    def test_cancel_sale_restores_product_stock_marks_cancelled_and_allows_rebilling(self):
        pro = self._create_professional('pro-cancel-1')
        appt = Appointment.objects.create(
            customer=self.customer, service=self.service, professional=pro,
            date=datetime.date(2026, 11, 22), start_time=datetime.time(9, 0),
            created_by=self.admin, status=Appointment.Status.COMPLETED,
        )
        sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CASH,
            appointment=appt,
            cash_session=self.session,
            details=[
                {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 20000},
                {'type': SaleDetailType.PRODUCT, 'product': self.product, 'quantity': Decimal('2'), 'unit_price': 8000},
            ],
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('3'))
        self.assertEqual(sale.appointment_id, appt.pk)

        cancelled = cancel_sale(sale=sale, user=self.cashier, reason='Error de cobro')
        cancelled.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(cancelled.status, SaleStatus.CANCELLED)
        self.assertIsNone(cancelled.appointment_id)
        self.assertEqual(self.product.stock, Decimal('5'))
        self.assertIn('Error de cobro', cancelled.notes)

        new_sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CARD,
            appointment=appt,
            cash_session=self.session,
            details=[
                {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 20000},
            ],
        )
        self.assertEqual(new_sale.status, SaleStatus.REGISTERED)
        self.assertEqual(new_sale.appointment_id, appt.pk)
        self.assertEqual(Sale.objects.filter(status=SaleStatus.REGISTERED, appointment=appt).count(), 1)

    def test_cancel_sale_permissions(self):
        sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CASH,
            customer=self.customer,
            cash_session=self.session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 20000}],
        )
        with self.assertRaisesMessage(ValidationError, 'Solo los administradores y el personal de caja/recepción pueden anular ventas.'):
            cancel_sale(sale=sale, user=self.worker)
        sale.refresh_from_db()
        self.assertEqual(sale.status, SaleStatus.REGISTERED)

        cancelled = cancel_sale(sale=sale, user=self.admin)
        self.assertEqual(cancelled.status, SaleStatus.CANCELLED)

    def test_cannot_cancel_sale_twice(self):
        sale = create_sale(
            user=self.cashier,
            payment_method=PaymentMethod.CASH,
            customer=self.customer,
            cash_session=self.session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 20000}],
        )
        cancel_sale(sale=sale, user=self.cashier)
        with self.assertRaisesMessage(ValidationError, 'La venta ya está anulada.'):
            cancel_sale(sale=sale, user=self.cashier)

    def test_cash_session_totals_ignore_cancelled_sales(self):
        service = Service.objects.create(name='Servicio Caja Cancel', price_cop=10000, duration_minutes=30)
        session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('50000'))
        sale_cash = create_sale(
            user=self.admin, payment_method=PaymentMethod.CASH, customer=self.customer,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': 10000}],
        )
        create_sale(
            user=self.admin, payment_method=PaymentMethod.CARD, customer=self.customer,
            cash_session=session,
            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': 15000}],
        )
        cancel_sale(sale=sale_cash, user=self.admin)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:cash_close', args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['totals']['cash'], Decimal('0'))
        self.assertEqual(response.context['totals']['card'], Decimal('15000'))
        self.assertEqual(response.context['totals']['transfer'], Decimal('0'))
        self.assertEqual(response.context['sales_total'], Decimal('15000'))
        self.assertEqual(response.context['expected_cash'], Decimal('50000'))
        self.assertEqual(response.context['grand_total'], Decimal('65000'))
        self.assertEqual(response.context['sales'].count(), 1)

    def test_sale_cancel_view_post_permissions_and_success(self):
        sale = create_sale(
            user=self.admin, payment_method=PaymentMethod.CASH, customer=self.customer,
            cash_session=self.session,
            details=[{'type': SaleDetailType.PRODUCT, 'product': self.product, 'quantity': 1, 'unit_price': 8000}],
        )
        url = reverse('sales:cancel', args=[sale.pk])

        self.client.force_login(self.worker)
        self.assertEqual(self.client.post(url).status_code, 403)
        sale.refresh_from_db()
        self.assertEqual(sale.status, SaleStatus.REGISTERED)

        self.client.force_login(self.cashier)
        response = self.client.post(url)
        self.assertRedirects(response, reverse('sales:index'))
        sale.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(sale.status, SaleStatus.CANCELLED)
        self.assertEqual(self.product.stock, Decimal('5'))

    def test_cancel_sale_requires_authentication(self):
        sale = create_sale(
            user=self.admin, payment_method=PaymentMethod.CASH, customer=self.customer,
            cash_session=self.session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 20000}],
        )
        with self.assertRaisesMessage(ValidationError, 'Debes iniciar sesión para anular una venta.'):
            cancel_sale(sale=sale, user=None)


class SaleReceiptViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='receipt-admin', email='receipt-admin@sales.test', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='receipt-cashier', email='receipt-cashier@sales.test', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='receipt-worker', email='receipt-worker@sales.test', role=User.Role.WORKER)
        cls.customer = Customer.objects.create(name='Cliente Recibo', phone='3001112233')
        cls.service = Service.objects.create(name='Corte Recibo', price_cop=25000, duration_minutes=30)
        pro_user = User.objects.create_user(username='receipt-pro', email='receipt-pro@sales.test', role=User.Role.WORKER)
        from services.models import Professional
        cls.professional = Professional.objects.create(user=pro_user)

    def setUp(self):
        self.product = Product.objects.create(
            code='REC-P1', name='Cera Recibo', base_unit=Product.BaseUnit.UNIT,
            stock=Decimal('10'), acquisition_cost=Decimal('1000'),
            sale_price=Decimal('12000'), service_usage_price=Decimal('12000'),
        )
        self.session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('20000'))
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            service=self.service,
            professional=self.professional,
            date=datetime.date(2026, 11, 25),
            start_time=datetime.time(14, 0),
            created_by=self.admin,
            status=Appointment.Status.COMPLETED,
        )
        self.sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CARD,
            customer=self.customer,
            appointment=self.appointment,
            cash_session=self.session,
            notes='Observación de recibo',
            details=[
                {'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 25000},
                {'type': SaleDetailType.PRODUCT, 'product': self.product, 'quantity': Decimal('2'), 'unit_price': 12000},
            ],
        )

    def test_anonymous_redirects_to_login(self):
        url = reverse('sales:receipt', args=[self.sale.pk])
        self.assertRedirects(self.client.get(url), reverse('accounts:login') + '?next=' + url)

    def test_worker_forbidden(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('sales:receipt', args=[self.sale.pk]))
        self.assertContains(response, 'Acceso restringido', status_code=403)

    def test_admin_can_view_receipt_with_expected_content(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:receipt', args=[self.sale.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sales/sale_receipt.html')
        self.assertContains(response, 'StudioGest')
        self.assertContains(response, self.sale.receipt_number)
        self.assertContains(response, f'#{self.sale.pk}')
        self.assertContains(response, 'Corte Recibo')
        self.assertContains(response, 'Cera Recibo')
        self.assertContains(response, 'Cliente Recibo')
        self.assertContains(response, 'Atendido por')
        self.assertContains(response, self.sale.get_payment_method_display())
        self.assertContains(response, self.sale.get_status_display())
        self.assertContains(response, 'Observación de recibo')
        self.assertContains(response, 'Sesión de caja')
        self.assertContains(response, 'Cita cobrada')
        self.assertContains(response, 'Imprimir')

    def test_cashier_can_view_receipt(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse('sales:receipt', args=[self.sale.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sale.receipt_number)

    def test_receipt_returns_404_for_missing_sale(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:receipt', args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_sales_index_shows_receipt_link(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('sales:receipt', args=[self.sale.pk]))
        self.assertContains(response, 'Ver recibo')
        self.assertContains(response, self.sale.receipt_number)
        self.assertContains(response, reverse('sales:cash_history'))


class SaleReceiptHardeningAndNumberingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='receipt-h-admin', email='receipt-h-admin@sales.test', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='receipt-h-cashier', email='receipt-h-cashier@sales.test', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='receipt-h-worker', email='receipt-h-worker@sales.test', role=User.Role.WORKER)
        cls.customer = Customer.objects.create(name='Cliente Hardening', phone='3002223344')
        cls.service = Service.objects.create(name='Servicio Hardening', price_cop=15000, duration_minutes=30)

    def setUp(self):
        self.session = CashRegisterSession.objects.create(opened_by=self.admin, opening_cash=Decimal('10000'))
        self.sale = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CASH,
            customer=self.customer,
            cash_session=self.session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 15000}],
        )

    def test_receipt_number_is_stable_and_based_on_id(self):
        self.assertEqual(self.sale.receipt_number, f'V-{self.sale.pk:06d}')
        self.assertIn(str(self.sale.pk), self.sale.receipt_number)

    def test_receipt_returns_anti_cache_headers(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:receipt', args=[self.sale.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'private, no-store, max-age=0')
        self.assertEqual(response['Pragma'], 'no-cache')
        self.assertContains(response, self.sale.receipt_number)
        self.assertContains(response, 'Comprobante')


class CashSessionHistoryViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='history-admin', email='history-admin@sales.test', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(username='history-cashier', email='history-cashier@sales.test', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(username='history-worker', email='history-worker@sales.test', role=User.Role.WORKER)
        cls.customer = Customer.objects.create(name='Cliente Historial', phone='3003334455')
        cls.service = Service.objects.create(name='Servicio Historial', price_cop=20000, duration_minutes=30)

    def setUp(self):
        self.open_session = CashRegisterSession.objects.create(
            opened_by=self.cashier,
            opening_cash=Decimal('50000'),
            status=CashRegisterSession.Status.OPEN,
        )
        self.closed_session = CashRegisterSession.objects.create(
            opened_by=self.admin,
            opening_cash=Decimal('30000'),
            status=CashRegisterSession.Status.OPEN,
        )
        self.closed_sale_cash = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CASH,
            customer=self.customer,
            cash_session=self.closed_session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 20000}],
        )
        self.closed_sale_card = create_sale(
            user=self.admin,
            payment_method=PaymentMethod.CARD,
            customer=self.customer,
            cash_session=self.closed_session,
            details=[{'type': SaleDetailType.SERVICE, 'service': self.service, 'quantity': 1, 'unit_price': 15000}],
        )
        self.client.force_login(self.admin)
        close_response = self.client.post(
            reverse('sales:cash_finalize', args=[self.closed_session.pk]),
            {'counted_cash': '48000'},
        )
        self.assertEqual(close_response.status_code, 302)
        self.closed_session.refresh_from_db()
        self.client.logout()

    def test_anonymous_redirects_to_login(self):
        url = reverse('sales:cash_history')
        self.assertRedirects(self.client.get(url), reverse('accounts:login') + '?next=' + url)

    def test_worker_forbidden(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('sales:cash_history'))
        self.assertContains(response, 'Acceso restringido', status_code=403)

    def test_cashier_can_view_history_with_open_and_closed_sessions(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse('sales:cash_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sales/cash_session_history.html')
        self.assertContains(response, 'Historial de sesiones de caja')
        self.assertContains(response, f'#{self.open_session.pk}')
        self.assertContains(response, f'#{self.closed_session.pk}')
        self.assertContains(response, 'Abierta')
        self.assertContains(response, 'Cerrada')
        # Arqueo sesión cerrada: base 30000, efectivo 20000, tarjeta 15000, total 35000, esperado 50000, contado 48000, diferencia -2000
        self.assertContains(response, '$30000')
        self.assertContains(response, '$20000')
        self.assertContains(response, '$15000')
        self.assertContains(response, '$35000')
        self.assertContains(response, '$50000')
        self.assertContains(response, '$48000')
        self.assertContains(response, '$-2000')
        self.assertContains(response, reverse('sales:cash_close', args=[self.closed_session.pk]))

    def test_history_detail_shows_associated_sales_for_closed_session(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:cash_close', args=[self.closed_session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sales/cash_session_close.html')
        self.assertContains(response, 'Ventas asociadas')
        self.assertContains(response, self.closed_sale_cash.receipt_number)
        self.assertContains(response, self.closed_sale_card.receipt_number)
        self.assertContains(response, reverse('sales:receipt', args=[self.closed_sale_cash.pk]))
        self.assertContains(response, '$48000')  # contado
        self.assertContains(response, '$-2000')  # diferencia
        self.assertContains(response, '$35000')  # total ventas

    def test_sales_index_links_to_history(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('sales:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('sales:cash_history'))
        self.assertContains(response, 'Ver historial')
