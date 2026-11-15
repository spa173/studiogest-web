from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Product
from .services import consume_stock
from .calculations import MAX_STOCK, purchase_values

User = get_user_model()


class InventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='inventory-admin', email='admin@inventory.test',
            role=User.Role.ADMIN, is_staff=True)
        cls.worker = User.objects.create_user(
            username='inventory-worker', email='worker@inventory.test',
            role=User.Role.WORKER, is_staff=True)
        cls.product = Product.objects.create(
            code='PROD-001', name='Champú', description='Producto de cuidado capilar',
            base_unit=Product.BaseUnit.ML, minimum_stock=Decimal('12.500'),
            acquisition_cost=Decimal('7.25'), sale_price=Decimal('12.50'),
            service_usage_price=Decimal('15.75'))

    def setUp(self):
        self.url = reverse('inventory:list')
        self.client.force_login(self.admin)

    def product_data(self, **changes):
        data = dict(code='NEW-001', name='Nuevo producto', description='',
                    base_unit=Product.BaseUnit.UNIT, minimum_stock='2',
                    acquisition_cost='1000.00', sale_price='2000.00',
                    service_usage_price='500.00', is_active='on')
        data.update(changes)
        return data

    def test_authentication_required(self):
        self.client.logout()
        self.assertRedirects(self.client.get(self.url),
                             reverse('accounts:login') + '?next=' + self.url)

    def test_catalog_and_active_menu(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'base.html')
        for value in ['PROD-001', 'Champú', 'Producto de cuidado capilar', 'Activo',
                      'Costo adquisición (COP)', 'Venta directa (COP)', 'Uso en servicio (COP)']:
            self.assertContains(response, value)
        self.assertContains(response, 'href="/inventory/" aria-current="page"')
        self.assertContains(response, reverse('inventory:create'))

    def test_worker_sees_availability_but_not_acquisition_cost_or_admin_link(self):
        self.client.force_login(self.worker)
        response = self.client.get(self.url)
        self.assertContains(response, 'Champú')
        self.assertContains(response, 'Existencia')
        self.assertNotContains(response, 'Costo adquisición')
        self.assertNotContains(response, reverse('admin:inventory_product_changelist'))

    def test_inactive_product_and_all_units_display(self):
        self.product.is_active = False
        self.product.save(update_fields=['is_active'])
        for unit in [Product.BaseUnit.UNIT, Product.BaseUnit.G]:
            Product.objects.create(code=unit, name=unit, base_unit=unit,
                                   acquisition_cost=0, sale_price=0, service_usage_price=0)
        response = self.client.get(self.url)
        for value in ['Inactivo', 'Mililitros (ml)', 'Gramos (g)', 'Unidad']:
            self.assertContains(response, value)

    def test_empty_catalog(self):
        Product.objects.all().delete()
        self.assertContains(self.client.get(self.url), 'No hay productos registrados')

    def test_catalog_rejects_writes(self):
        self.assertEqual(self.client.post(self.url, {'stock': 100}).status_code, 405)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)

    def test_admin_cannot_use_a_second_registration_form(self):
        url = reverse('admin:inventory_product_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(url, self.product_data(stock='100')).status_code, 403)
        self.assertFalse(Product.objects.filter(code='NEW-001').exists())

    def test_django_admin_is_read_only(self):
        # Simula un saldo futuro solo en la base temporal de pruebas.
        Product.objects.filter(pk=self.product.pk).update(stock=Decimal('25.125'))
        url = reverse('admin:inventory_product_change', args=[self.product.pk])
        response = self.client.post(url, self.product_data(
            code='PROD-001', name='Champú actualizado', base_unit=Product.BaseUnit.ML,
            minimum_stock='12.500', stock='999'))
        self.assertEqual(response.status_code, 403)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Champú')
        self.assertEqual(self.product.stock, Decimal('25.125'))

    def test_worker_cannot_access_inventory_admin_even_with_django_permissions(self):
        self.worker.user_permissions.add(*Permission.objects.filter(content_type__app_label='inventory'))
        self.client.force_login(self.worker)
        login_url = reverse('admin:login')
        for name, args in [('admin:inventory_product_changelist', []),
                           ('admin:inventory_product_add', []),
                           ('admin:inventory_product_change', [self.product.pk])]:
            response = self.client.get(reverse(name, args=args))
            self.assertIn(response.status_code, (302, 403))
            if response.status_code == 302:
                self.assertIn(login_url, response.url)
        response = self.client.post(reverse('admin:inventory_product_add'), self.product_data())
        self.assertIn(response.status_code, (302, 403))
        if response.status_code == 302:
            self.assertIn(login_url, response.url)
        self.assertFalse(Product.objects.filter(code='NEW-001').exists())

    def test_code_is_unique_and_normalized_by_validation(self):
        duplicate = Product(**self.product_data(code='prod-001', is_active=True))
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(code=self.product.code, name='Duplicado',
                                   base_unit=Product.BaseUnit.UNIT, acquisition_cost=0,
                                   sale_price=0, service_usage_price=0)

    def test_negative_quantities_and_prices_rejected(self):
        for field in ['stock', 'minimum_stock', 'acquisition_cost', 'sale_price', 'service_usage_price']:
            with self.subTest(field=field):
                product = Product(**self.product_data(is_active=True))
                setattr(product, field, Decimal('-1'))
                with self.assertRaises(ValidationError):
                    product.full_clean()
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Product.objects.filter(pk=self.product.pk).update(**{field: -1})

    def test_fractional_unit_quantities_rejected_but_ml_and_g_allowed(self):
        for unit in Product.BaseUnit.values:
            product = Product(**self.product_data(base_unit=unit, minimum_stock='1.250', is_active=True))
            if unit == Product.BaseUnit.UNIT:
                with self.assertRaises(ValidationError):
                    product.full_clean()
            else:
                product.full_clean()
                self.assertEqual(product.minimum_stock, Decimal('1.250'))

    def test_admin_invalid_product_is_not_saved(self):
        response = self.client.post(reverse('admin:inventory_product_add'),
                                    self.product_data(sale_price='-1'))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(code='NEW-001').exists())

    def test_admin_cannot_delete_product(self):
        url = reverse('admin:inventory_product_delete', args=[self.product.pk])
        self.assertEqual(self.client.post(url, {'post': 'yes'}).status_code, 403)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())


class ConsumeStockTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            code='CONS-001', name='Pomada', description='',
            base_unit=Product.BaseUnit.UNIT, stock=Decimal('5'),
            minimum_stock=Decimal('2'), acquisition_cost=Decimal('10'),
            sale_price=Decimal('20'), service_usage_price=Decimal('5'))

    def test_consume_stock_reduces_stock(self):
        updated = consume_stock(product=self.product, quantity=Decimal('2'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('3'))
        self.assertEqual(updated.stock, Decimal('3'))

    def test_consume_stock_rejects_insufficient_stock(self):
        with self.assertRaises(ValidationError):
            consume_stock(product=self.product, quantity=Decimal('10'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('5'))

    def test_consume_stock_rejects_non_positive_quantity(self):
        with self.assertRaises(ValidationError):
            consume_stock(product=self.product, quantity=Decimal('0'))


class RestoreStockTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            code='REST-001', name='Gel', description='',
            base_unit=Product.BaseUnit.UNIT, stock=Decimal('3'),
            minimum_stock=Decimal('1'), acquisition_cost=Decimal('10'),
            sale_price=Decimal('20'), service_usage_price=Decimal('5'))

    def test_restore_stock_increases_stock(self):
        from .services import restore_stock
        updated = restore_stock(product=self.product, quantity=Decimal('2'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('5'))
        self.assertEqual(updated.stock, Decimal('5'))

    def test_restore_stock_rejects_non_positive_quantity(self):
        from .services import restore_stock
        with self.assertRaises(ValidationError):
            restore_stock(product=self.product, quantity=Decimal('0'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('3'))

    def test_restore_stock_rejects_inactive_product(self):
        from .services import restore_stock
        inactive = Product.objects.create(
            code='REST-INA', name='Inactivo', description='',
            base_unit=Product.BaseUnit.UNIT, stock=Decimal('1'),
            minimum_stock=Decimal('0'), acquisition_cost=Decimal('1'),
            sale_price=Decimal('2'), service_usage_price=Decimal('2'),
            is_active=False)
        with self.assertRaises(ValidationError):
            restore_stock(product=inactive, quantity=Decimal('1'))
        inactive.refresh_from_db()
        self.assertEqual(inactive.stock, Decimal('1'))


class PurchaseValuesTests(TestCase):
    def test_rejects_invalid_presentation_count(self):
        with self.assertRaises(ValueError):
            purchase_values(0, Decimal('100'), Decimal('100'), Decimal('100'))

    def test_rejects_negative_or_non_finite_values(self):
        with self.assertRaises(ValueError):
            purchase_values(1, Decimal('-1'), Decimal('100'), Decimal('100'))
        with self.assertRaises(ValueError):
            purchase_values(1, Decimal('100'), Decimal('100'), Decimal('NaN'))

    def test_rejects_zero_content(self):
        with self.assertRaises(ValueError):
            purchase_values(1, Decimal('0'), Decimal('100'), Decimal('100'))

    def test_rejects_amounts_above_max_stock(self):
        with self.assertRaises(ValueError):
            purchase_values(2, Decimal('1000000000000000'), Decimal('100'), Decimal('100'), Decimal('50'))


class InventoryRBACAdditionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='inv-admin-r', email='inv-admin-r@test.co', role=User.Role.ADMIN)
        cls.cashier = User.objects.create_user(
            username='inv-cashier-r', email='inv-cashier-r@test.co', role=User.Role.CASHIER)
        cls.worker = User.objects.create_user(
            username='inv-worker-r', email='inv-worker-r@test.co', role=User.Role.WORKER)
        cls.product = Product.objects.create(
            code='RBAC-001', name='Producto RBAC', description='',
            base_unit=Product.BaseUnit.UNIT, minimum_stock=Decimal('1'),
            acquisition_cost=Decimal('9.50'), sale_price=Decimal('12.00'),
            service_usage_price=Decimal('10.00'))

    def test_cashier_sees_acquisition_cost_in_inventory_list(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse('inventory:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Costo adquisición (COP)')

    def test_inventory_history_accessible_to_all_roles(self):
        for user in (self.admin, self.cashier, self.worker):
            self.client.force_login(user)
            response = self.client.get(reverse('inventory:history'))
            self.assertEqual(response.status_code, 200, user)

    def test_inventory_history_hides_costs_for_worker_but_shows_for_cashier(self):
        # Crear una entrada para que se renderice la tabla con encabezados.
        from .models import StockEntry
        StockEntry.objects.create(
            kind=StockEntry.Kind.INITIAL,
            product=self.product,
            operation_key='11111111-1111-1111-1111-111111111111',
            request_fingerprint='rbac-fp',
            presentation_count=1,
            content_per_presentation=Decimal('1.000'),
            base_unit=self.product.base_unit,
            quantity=Decimal('1.000'),
            total_cost=Decimal('10.00'),
            presentation_sale_price=Decimal('12.00'),
            usage_price=Decimal('10.00000000'),
            presentation=self.product.presentation or Product.Presentation.BOTTLE,
            created_by=self.admin,
        )
        self.client.force_login(self.worker)
        response = self.client.get(reverse('inventory:history'))
        self.assertNotContains(response, 'Costo total (COP)')
        self.assertNotContains(response, 'Costo por presentación (COP)')
        self.client.force_login(self.cashier)
        response = self.client.get(reverse('inventory:history'))
        self.assertContains(response, 'Costo total (COP)')
        self.assertContains(response, 'Costo por presentación (COP)')
