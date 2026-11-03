import re
from decimal import Decimal
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from appointments.models import Appointment
from inventory.models import Product, StockEntry

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
                     'El registro de ventas todavía no está habilitado',
                     'Una cita completada no acredita un pago recibido']:
            self.assertContains(response, text)
        self.assertNotContains(response, 'href="#"')
        self.assertNotContains(response, '$')
        self.assertContains(response, 'href="/sales/" aria-current="page"', count=3)

    def test_worker_denied_despite_staff_flag(self):
        self.client.force_login(self.worker)
        response = self.client.get(self.url)
        self.assertContains(response, 'Solo los administradores pueden acceder', status_code=403)
        self.assertNotContains(response, 'href="/sales/"', status_code=403)
        self.assertNotContains(response, 'href="/reports/"', status_code=403)

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
        self.assertContains(response, 'function openAppointmentModal()')
        self.assertContains(response, '/static/js/navigation.js')
        self.assertEqual(Appointment.objects.count(), before)
