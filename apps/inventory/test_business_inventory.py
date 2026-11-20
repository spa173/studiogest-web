from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from services.models import BookingBusiness

from .models import Product, StockEntry
from .services import consume_stock


@override_settings(TENANT_BOOKING_ENABLED=True)
class BusinessInventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alpha = BookingBusiness.objects.create(name='Prisma', slug='prisma')
        cls.beta = BookingBusiness.objects.create(name='Umbral', slug='umbral')
        user = get_user_model()
        cls.alpha_admin = user.objects.create_user(username='alpha', email='alpha@example.test', business=cls.alpha, role='ADMIN')
        cls.beta_admin = user.objects.create_user(username='beta', email='beta@example.test', business=cls.beta, role='ADMIN')
        cls.worker = user.objects.create_user(username='worker', email='worker@example.test', business=cls.alpha)
        cls.root = user.objects.create_superuser(username='platform', email='platform@example.test')

    def registration(self, path=None, **overrides):
        path = path or reverse('inventory:create')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return {
            'operation_token': response.context['form']['operation_token'].value(),
            'name': 'Tinte Prisma', 'code': 'TINTE-01', 'presentation': Product.Presentation.JAR,
            'base_unit': Product.BaseUnit.ML, 'content': '50', 'presentation_count': '2',
            'total_cost': '10000', 'presentation_sale_price': '8000', 'minimum_stock': '0',
            'is_active': 'on', **overrides,
        }

    def test_codes_and_movements_are_scoped_by_business(self):
        create = reverse('inventory:create')
        listing = reverse('inventory:list')
        history = reverse('inventory:history')
        self.client.force_login(self.alpha_admin)
        self.assertRedirects(self.client.post(create, self.registration(business=self.beta.pk)), listing)
        alpha_product = Product.objects.get(business=self.alpha)
        self.client.force_login(self.beta_admin)
        response = self.client.post(create, self.registration(name='Tinte Umbral'))
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        self.assertRedirects(response, listing)
        beta_product = Product.objects.get(business=self.beta)
        self.assertEqual(alpha_product.code, beta_product.code)
        self.assertContains(self.client.get(listing), 'Tinte Umbral')
        self.assertNotContains(self.client.get(listing), 'Tinte Prisma')
        self.assertNotContains(self.client.get(history), 'Tinte Prisma')
        for route in ('inventory:purchase', 'inventory:update'):
            foreign_url = reverse(route, args=[alpha_product.pk])
            self.assertEqual(self.client.get(foreign_url).status_code, 404)
            self.assertEqual(self.client.post(foreign_url).status_code, 404)
        purchase = reverse('inventory:purchase', args=[beta_product.pk])
        data = self.registration(purchase, presentation_count='3')
        self.assertRedirects(self.client.post(purchase, data), listing)
        self.assertRedirects(self.client.post(purchase, data), history)
        beta_product.refresh_from_db()
        alpha_product.refresh_from_db()
        self.assertEqual(beta_product.stock, Decimal('250'))
        self.assertEqual(alpha_product.stock, Decimal('100'))
        self.assertEqual(StockEntry.objects.filter(product__business=self.beta).count(), 2)
        self.assertContains(self.client.post(create, self.registration()), 'Ya existe un producto con este código.')
        self.client.force_login(self.root)
        self.assertNotContains(self.client.get(listing), 'Tinte Umbral')
        self.assertNotContains(self.client.get(history), 'Tinte Prisma')

    def test_moving_a_user_invalidates_a_previously_issued_registration_token(self):
        path = reverse('inventory:create')
        self.client.force_login(self.alpha_admin)
        data = self.registration()
        self.alpha_admin.business = self.beta
        self.alpha_admin.save(update_fields=['business'])
        self.assertContains(self.client.post(path, data), 'El formulario expiró o no es válido.')
        self.assertFalse(Product.objects.exists())

    def test_worker_can_read_own_stock_but_cannot_register_products(self):
        self.client.force_login(self.alpha_admin)
        self.client.post(reverse('inventory:create'), self.registration())
        self.client.force_login(self.worker)
        self.assertContains(self.client.get(reverse('inventory:list')), 'Tinte Prisma')
        self.assertNotContains(self.client.get(reverse('inventory:history')), 'Costo total')
        self.assertEqual(self.client.get(reverse('inventory:create')).status_code, 403)

    def test_database_enforces_codes_in_both_business_and_legacy_catalogs(self):
        for scope in (None, self.alpha):
            data = dict(business=scope, code='ABC', name='Tinte', base_unit=Product.BaseUnit.UNIT,
                        acquisition_cost=1, sale_price=2, service_usage_price=2)
            item = Product.objects.create(**data)
            with self.assertRaises(IntegrityError), transaction.atomic():
                Product.objects.create(**data)
            if scope:
                with self.assertRaises(ValidationError):
                    consume_stock(product=item, quantity=1, user=self.beta_admin)
