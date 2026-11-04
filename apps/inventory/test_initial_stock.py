import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .formatting import money_co, number_co, quantity_co
from .models import Product, StockEntry

User = get_user_model()


class InitialStockTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='initial-admin', email='initial@inventory.test',
                                           role=User.Role.ADMIN, is_staff=True)

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse('inventory:create')

    def data(self):
        response = self.client.get(self.url)
        return {
            'operation_token': response.context['form']['operation_token'].value(),
            'code': 'TINTE-INICIAL', 'name': 'Tinte inicial', 'description': 'Tubo de tinte',
            'presentation': Product.Presentation.TUBE, 'base_unit': Product.BaseUnit.ML,
            'content': '250', 'presentation_count': '3', 'total_cost': '150000',
            'presentation_sale_price': '85000', 'usage_price': '', 'minimum_stock': '250', 'is_active': 'on',
        }

    def create(self, **changes):
        data = self.data()
        data.update(changes)
        self.assertRedirects(self.client.post(self.url, data), reverse('inventory:list'))
        return Product.objects.get(code='TINTE-INICIAL'), data

    def test_form_text_and_hidden_purchase_action(self):
        response = self.client.get(self.url)
        for text in ['Registrar producto', 'Cantidad inicial', 'Costo total del inventario inicial', 'Guardar producto']:
            self.assertContains(response, text)
        self.assertNotContains(response, 'Registrar producto y compra')
        self.assertNotContains(response, 'Cantidad de presentaciones compradas')
        product, _ = self.create()
        response = self.client.get(reverse('inventory:list'))
        self.assertNotContains(response, 'Registrar compra')
        self.assertNotContains(response, reverse('inventory:purchase', args=[product.pk]))

    def test_example_initial_balance_and_costs(self):
        product, _ = self.create()
        entry = StockEntry.objects.get()
        self.assertEqual(entry.kind, StockEntry.Kind.INITIAL)
        self.assertEqual(product.stock, Decimal('750'))
        self.assertEqual(entry.quantity, Decimal('750'))
        self.assertEqual(entry.cost_per_presentation, Decimal('50000'))
        self.assertEqual(product.acquisition_cost, Decimal('200'))
        self.assertEqual(product.sale_price, Decimal('340'))
        self.assertEqual(product.service_usage_price, Decimal('340'))

    def test_custom_usage_rate(self):
        product, _ = self.create(usage_price='400.125')
        self.assertEqual(product.sale_price, Decimal('340'))
        self.assertEqual(product.service_usage_price, Decimal('400.125'))

    def test_refresh_resubmit_and_edit_do_not_duplicate_stock(self):
        product, data = self.create()
        for _ in range(2):
            self.client.get(reverse('inventory:list'))
            self.assertRedirects(self.client.post(self.url, data), reverse('inventory:history'))
        url = reverse('inventory:update', args=[product.pk])
        response = self.client.get(url)
        data.update(operation_token=response.context['form']['operation_token'].value(),
                    name='Tinte actualizado', presentation_count='999', stock='99999')
        self.assertRedirects(self.client.post(url, data), reverse('inventory:list'))
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('750'))
        self.assertEqual(StockEntry.objects.count(), 1)

    def test_only_one_initial_entry_per_product(self):
        self.create()
        entry = StockEntry.objects.get()
        data = {field.name: getattr(entry, field.name) for field in StockEntry._meta.fields if field.name not in ['id', 'created_at']}
        data['operation_key'] = uuid.uuid4()
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockEntry.objects.create(**data)
        self.assertEqual(StockEntry.objects.count(), 1)

    def test_historical_purchase_data_remains_unchanged(self):
        product, _ = self.create()
        # Una compra posterior usa el flujo existente, sin reclasificar el saldo inicial.
        url = reverse('inventory:purchase', args=[product.pk])
        response = self.client.get(url)
        data = self.data()
        data.update(operation_token=response.context['form']['operation_token'].value(),
                    presentation_count='2', total_cost='100000')
        self.assertRedirects(self.client.post(url, data), reverse('inventory:list'))
        purchase = StockEntry.objects.get(kind=StockEntry.Kind.PURCHASE)
        before = StockEntry.objects.values().get(pk=purchase.pk)
        response = self.client.get(reverse('inventory:history'))
        self.assertContains(response, 'Saldo inicial')
        self.assertContains(response, 'Compra')
        self.assertEqual(StockEntry.objects.values().get(pk=purchase.pk), before)

    def test_catalog_formats_money_and_quantity(self):
        self.create()
        response = self.client.get(reverse('inventory:list'))
        for text in ['$85.000', '$200', '$340', '750 ml', '250 ml']:
            self.assertContains(response, text)
        for text in ['200,00000000', '750,000', '85000,00']:
            self.assertNotContains(response, text)

    def test_admin_list_and_detail_formats(self):
        product, _ = self.create()
        urls = [reverse('admin:inventory_product_changelist'),
                reverse('admin:inventory_product_change', args=[product.pk]),
                reverse('admin:inventory_stockentry_changelist'),
                reverse('admin:inventory_stockentry_change', args=[StockEntry.objects.get().pk])]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, '750 ml')
                self.assertNotContains(response, '750,000')
                self.assertNotContains(response, '200,00000000')
        response = self.client.get(urls[1])
        self.assertContains(response, '$85.000')
        self.assertContains(response, '$200')
        response = self.client.get(urls[3])
        self.assertContains(response, '$150.000')
        self.assertContains(response, 'Saldo inicial')

    def test_units_and_grams_initial_stock(self):
        for unit, content, expected in [(Product.BaseUnit.UNIT, '', Decimal('3')),
                                         (Product.BaseUnit.G, '250', Decimal('750'))]:
            with self.subTest(unit=unit):
                data = self.data()
                data.update(code=unit, base_unit=unit, content=content, minimum_stock='1')
                self.assertRedirects(self.client.post(self.url, data), reverse('inventory:list'))
                self.assertEqual(Product.objects.get(code=unit).stock, expected)

    def test_colombian_formatting_preserves_fractional_precision(self):
        self.assertEqual(money_co(Decimal('30000.00000000')), '$30.000')
        self.assertEqual(money_co(Decimal('200.00000000')), '$200')
        self.assertEqual(money_co(Decimal('0.12345678')), '$0,12345678')
        self.assertEqual(money_co(Decimal('0')), '$0')
        self.assertEqual(money_co(None), '—')
        self.assertEqual(quantity_co(Decimal('750.000'), 'ML'), '750 ml')
        self.assertEqual(quantity_co(Decimal('1250.125'), 'G'), '1.250,125 g')
        self.assertEqual(number_co(Decimal('1000000.50')), '1.000.000,5')
