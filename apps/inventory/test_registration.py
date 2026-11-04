from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from .calculations import MAX_STOCK, purchase_values
from .models import Product, StockEntry

User = get_user_model()


class RegistrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='purchase-admin', email='admin@purchase.test', role=User.Role.ADMIN)
        cls.worker = User.objects.create_user(username='purchase-worker', email='worker@purchase.test', role=User.Role.WORKER, is_staff=True)

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse('inventory:create')

    def data(self, url=None, **changes):
        response = self.client.get(url or self.url)
        self.assertEqual(response.status_code, 200)
        data = {'operation_token': response.context['form']['operation_token'].value(),
                'code': 'TINTE-001', 'name': 'Tinte', 'description': 'Tinte de 50 ml',
                'presentation': Product.Presentation.JAR, 'base_unit': Product.BaseUnit.ML,
                'content': '50', 'presentation_count': '10', 'total_cost': '100',
                'presentation_sale_price': '20', 'usage_price': '', 'minimum_stock': '100', 'is_active': 'on'}
        data.update(changes)
        return data

    def create_product(self, **changes):
        data = self.data(**changes)
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('inventory:list'))
        return Product.objects.get(code='TINTE-001'), data

    def test_example_calculations(self):
        result = purchase_values(10, Decimal('50'), Decimal('100'), Decimal('20'))
        self.assertEqual(result['cost_per_presentation'], Decimal('10'))
        self.assertEqual(result['cost_per_base_unit'], Decimal('0.20'))
        self.assertEqual(result['proportional_price'], Decimal('0.40'))
        self.assertEqual(result['usage_price'], Decimal('0.40'))
        self.assertEqual(result['quantity'], Decimal('500'))

    def test_create_product_and_initial_entry(self):
        product, _ = self.create_product(stock='9999', acquisition_cost='9999')
        self.assertEqual(product.stock, Decimal('500'))
        self.assertEqual(product.acquisition_cost, Decimal('0.20'))
        self.assertEqual(product.sale_price, Decimal('0.40'))
        self.assertEqual(product.service_usage_price, Decimal('0.40'))
        self.assertEqual(product.presentation_sale_price, Decimal('20'))
        entry = StockEntry.objects.get()
        self.assertEqual(entry.quantity, Decimal('500'))
        self.assertEqual(entry.created_by, self.admin)
        self.assertEqual(entry.cost_per_presentation, Decimal('10'))
        self.assertEqual(entry.cost_per_base_unit, Decimal('0.2'))

    def test_override_price(self):
        product, _ = self.create_product(usage_price='0.75')
        self.assertEqual(product.sale_price, Decimal('0.4'))
        self.assertEqual(product.service_usage_price, Decimal('0.75'))
        self.assertEqual(product.usage_price_override, Decimal('0.75'))

    def test_automatic_rate_follows_price_changes_until_overridden(self):
        product, _ = self.create_product()
        url = reverse('inventory:update', args=[product.pk])
        response = self.client.get(url)
        self.assertIsNone(response.context['form']['usage_price'].value())
        self.assertRedirects(self.client.post(url, self.data(url, presentation_sale_price='30')), reverse('inventory:list'))
        product.refresh_from_db()
        self.assertEqual(product.service_usage_price, Decimal('0.6'))
        self.assertIsNone(product.usage_price_override)

    def test_zero_price_and_cost_are_allowed(self):
        product, _ = self.create_product(total_cost='0', usage_price='0', presentation_sale_price='0')
        self.assertEqual(product.acquisition_cost, 0)
        self.assertEqual(product.service_usage_price, 0)

    def test_units_need_no_volume_fields(self):
        product, _ = self.create_product(base_unit=Product.BaseUnit.UNIT, content='', usage_price='', minimum_stock='2')
        self.assertEqual(product.content_per_presentation, Decimal('1'))
        self.assertEqual(product.stock, Decimal('10'))
        self.assertEqual(product.acquisition_cost, Decimal('10'))
        self.assertEqual(product.sale_price, Decimal('20'))
        self.assertEqual(product.service_usage_price, Decimal('20'))

    def test_grams_and_fractional_content(self):
        product, _ = self.create_product(base_unit=Product.BaseUnit.G, content='0.1', presentation_count='3')
        self.assertEqual(product.stock, Decimal('0.3'))
        self.assertEqual(StockEntry.objects.get().quantity, Decimal('0.3'))

    def test_duplicate_submission_does_not_duplicate_initial_purchase(self):
        product, data = self.create_product()
        self.assertRedirects(self.client.post(self.url, data), reverse('inventory:history'))
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('500'))
        self.assertEqual(StockEntry.objects.count(), 1)
        self.assertEqual(Product.objects.count(), 1)

    def test_token_reuse_with_different_data_is_rejected(self):
        product, data = self.create_product()
        data['presentation_count'] = '20'
        response = self.client.post(self.url, data)
        self.assertContains(response, 'otros datos')
        self.assertEqual(StockEntry.objects.count(), 1)
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('500'))

    def test_existing_product_purchase_adds_stock_without_another_product(self):
        product, _ = self.create_product()
        url = reverse('inventory:purchase', args=[product.pk])
        data = self.data(url, presentation_count='2', total_cost='30')
        self.assertRedirects(self.client.post(url, data), reverse('inventory:list'))
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('600'))
        self.assertEqual(product.acquisition_cost, Decimal('0.3'))
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(StockEntry.objects.count(), 2)
        first = StockEntry.objects.order_by('pk').first()
        self.assertEqual(first.total_cost, Decimal('100'))
        self.assertEqual(first.cost_per_presentation, Decimal('10'))
        self.assertRedirects(self.client.post(url, data), reverse('inventory:history'))
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('600'))

    def test_price_edit_does_not_create_entry_or_change_stock(self):
        product, _ = self.create_product()
        url = reverse('inventory:update', args=[product.pk])
        data = self.data(url, name='Tinte actualizado', presentation_sale_price='25', usage_price='0.6', stock='999')
        self.assertRedirects(self.client.post(url, data), reverse('inventory:list'))
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('500'))
        self.assertEqual(product.name, 'Tinte actualizado')
        self.assertEqual(product.acquisition_cost, Decimal('0.2'))
        self.assertEqual(product.sale_price, Decimal('0.5'))
        self.assertEqual(product.service_usage_price, Decimal('0.6'))
        self.assertEqual(StockEntry.objects.count(), 1)

    def test_legacy_stock_is_preserved_when_configuring(self):
        product = Product.objects.create(code='LEGACY', name='Anterior', base_unit=Product.BaseUnit.ML,
                                         stock=Decimal('12.125'), acquisition_cost=Decimal('7.25'),
                                         sale_price=Decimal('12.50'), service_usage_price=Decimal('15.75'))
        response = self.client.get(reverse('inventory:list'))
        self.assertContains(response, 'Sin configurar (producto anterior)')
        self.assertEqual(StockEntry.objects.count(), 0)
        url = reverse('inventory:update', args=[product.pk])
        data = self.data(url)
        self.assertRedirects(self.client.post(url, data), reverse('inventory:list'))
        product.refresh_from_db()
        self.assertEqual(product.stock, Decimal('12.125'))
        self.assertEqual(product.acquisition_cost, Decimal('7.25'))
        self.assertEqual(StockEntry.objects.count(), 0)

    def test_invalid_values_create_nothing(self):
        for field, value in [('presentation_count', '0'), ('presentation_count', '1.5'),
                             ('total_cost', '-1'), ('content', '0'), ('content', ''),
                             ('presentation_sale_price', '-1'), ('usage_price', '-1'),
                             ('total_cost', 'NaN'), ('minimum_stock', '-1')]:
            with self.subTest(field=field, value=value):
                data = self.data(**{field: value})
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertFalse(Product.objects.exists())
                self.assertFalse(StockEntry.objects.exists())

    def test_duplicate_code_requires_purchase_of_existing_product(self):
        self.create_product()
        response = self.client.post(self.url, self.data(code='tinte-001'))
        self.assertContains(response, 'Ya existe un producto con este código')
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(StockEntry.objects.count(), 1)

    def test_tampered_token_and_another_user_token_rejected(self):
        data = self.data()
        for token in ['bad-token', data['operation_token'] + 'modified']:
            response = self.client.post(self.url, dict(data, operation_token=token))
            self.assertContains(response, 'no es válido')
        other = User.objects.create_user(username='second-admin', email='second@purchase.test', role=User.Role.ADMIN)
        self.client.force_login(other)
        self.assertContains(self.client.post(self.url, data), 'no es válido')
        self.assertFalse(Product.objects.exists())

    def test_stock_limit_rejects_entire_transaction(self):
        product, _ = self.create_product()
        Product.objects.filter(pk=product.pk).update(stock=MAX_STOCK)
        url = reverse('inventory:purchase', args=[product.pk])
        response = self.client.post(url, self.data(url))
        self.assertContains(response, 'límite de existencias')
        self.assertEqual(StockEntry.objects.count(), 1)
        product.refresh_from_db()
        self.assertEqual(product.stock, MAX_STOCK)

    def test_derived_prices_exceeding_field_precision_are_a_form_error(self):
        data = self.data(presentation_count='1', content='0.001', total_cost='9999999999999999.99')
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(Product.objects.exists())
        self.assertFalse(StockEntry.objects.exists())

    def test_atomicity_on_stock_update_failure(self):
        data = self.data()
        with patch('django.db.models.query.QuerySet.update', return_value=0):
            response = self.client.post(self.url, data)
        self.assertContains(response, 'No se pudo actualizar el stock')
        self.assertFalse(Product.objects.exists())
        self.assertFalse(StockEntry.objects.exists())

    def test_entry_immutable_and_unique_operation(self):
        self.create_product()
        entry = StockEntry.objects.get()
        with self.assertRaises(ValidationError):
            entry.save()
        with self.assertRaises(ValidationError):
            entry.delete()
        copy = {field.name: getattr(entry, field.name) for field in StockEntry._meta.fields if field.name not in ['id', 'created_at']}
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockEntry.objects.create(**copy)

    def test_worker_and_anonymous_permissions(self):
        self.client.force_login(self.worker)
        for url in [self.url, reverse('inventory:history')]:
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {}).status_code in [403, 405], True)
        response = self.client.get(reverse('inventory:list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Registrar producto y compra')
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        data = self.data()
        self.assertEqual(client.post(self.url, data).status_code, 403)
        self.assertFalse(Product.objects.exists())

    def test_history_shows_real_entry(self):
        self.create_product()
        response = self.client.get(reverse('inventory:history'))
        self.assertContains(response, 'TINTE-001')
        self.assertContains(response, 'purchase-admin')
        self.assertContains(response, 'Entrada #')
        self.assertEqual(len(response.context['page']), 1)
