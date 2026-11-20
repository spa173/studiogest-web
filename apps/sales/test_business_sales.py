import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from appointments.models import Appointment
from customers.models import Customer
from inventory.models import Product
from services.models import BookingBusiness, Professional, Service

from .models import CashRegisterSession, PaymentMethod, Sale, SaleDetailType, SaleStatus
from .services import create_sale


@override_settings(TENANT_BOOKING_ENABLED=True)
class BusinessSalesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alpha, cls.admin, cls.customer, cls.product, cls.service = cls.make_business('Prisma', 'alpha', 'ADMIN')
        cls.beta, cls.cashier, cls.other_customer, cls.other_product, cls.other_service = cls.make_business('Umbral', 'beta', 'CAJA_RECEPCION')
        cls.worker = get_user_model().objects.create_user(username='worker', email='worker@example.test', business=cls.alpha)

    @staticmethod
    def make_business(name, slug, role):
        business = BookingBusiness.objects.create(name=name, slug=slug)
        user = get_user_model().objects.create_user(
            username=slug, email=f'{slug}@example.test', business=business, role=role,
        )
        customer = Customer.objects.create(business=business, name=f'Cliente {name}', phone='3005550101')
        product = Product.objects.create(
            business=business, code='SKU-01', name=f'Tinte {name}', base_unit=Product.BaseUnit.UNIT,
            stock=10, acquisition_cost=1000, sale_price=5000, service_usage_price=5000,
        )
        service = Service.objects.create(business=business, name=f'Servicio {name}', price_cop=25000)
        return business, user, customer, product, service

    def open_cash(self, user, notes):
        self.client.force_login(user)
        response = self.client.post(reverse('sales:cash_store'), {'opening_cash': 10000, 'notes': notes, 'business': self.beta.pk})
        self.assertRedirects(response, reverse('sales:index'))
        return CashRegisterSession.objects.get(business=user.business)

    @staticmethod
    def payload(session, customer, product):
        return {
            'cash_session': session.pk, 'customer': customer.pk, 'payment_method': PaymentMethod.CASH,
            'details-TOTAL_FORMS': '1', 'details-INITIAL_FORMS': '0',
            'details-0-detail_type': SaleDetailType.PRODUCT, 'details-0-product': product.pk,
            'details-0-quantity': '2', 'details-0-unit_price': '',
        }

    def test_independent_sales_receipts_closing_and_stock_restoration(self):
        first = self.open_cash(self.admin, 'Caja Prisma')
        second = self.open_cash(self.cashier, 'Caja Umbral')
        listing = reverse('sales:index')
        store = reverse('sales:store')
        self.assertRedirects(self.client.post(store, self.payload(second, self.other_customer, self.other_product)), listing)
        second_sale = Sale.objects.get(business=self.beta)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.post(store, self.payload(first, self.customer, self.product)), listing)
        first_sale = Sale.objects.get(business=self.alpha)
        receipt = self.client.get(reverse('sales:receipt', args=[first_sale.pk]))
        self.assertContains(receipt, 'Tinte Prisma')
        self.assertNotContains(self.client.get(listing), 'Cliente Umbral')
        history = self.client.get(reverse('sales:cash_history'))
        self.assertNotContains(history, self.cashier.username)
        for route, pk in [('sales:receipt', second_sale.pk), ('sales:cash_close', second.pk)]:
            self.assertEqual(self.client.get(reverse(route,args=[pk])).status_code, 404)
        for route, pk in [('sales:cancel', second_sale.pk), ('sales:cash_finalize', second.pk)]:
            self.assertEqual(self.client.post(reverse(route,args=[pk]), {'counted_cash': 0}).status_code, 404)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('8'))
        self.assertRedirects(self.client.post(reverse('sales:cancel',args=[first_sale.pk])), listing)
        self.product.refresh_from_db()
        self.other_product.refresh_from_db()
        self.assertEqual(self.product.stock, Decimal('10'))
        self.assertEqual(self.other_product.stock, Decimal('8'))
        second_sale.refresh_from_db()
        self.assertEqual(second_sale.status, SaleStatus.REGISTERED)
        self.assertRedirects(self.client.post(reverse('sales:cash_finalize',args=[first.pk]), {'counted_cash': 10000}), listing)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.cash_difference, Decimal('0'))
        self.assertTrue(second.is_open)

    def test_forms_and_service_reject_foreign_references(self):
        own = self.open_cash(self.admin, 'Caja Prisma')
        foreign = self.open_cash(self.cashier, 'Caja Umbral')
        self.client.force_login(self.admin)
        html = self.client.get(reverse('sales:create'))
        self.assertContains(html, 'Tinte Prisma')
        self.assertNotContains(html, 'Tinte Umbral')
        self.assertNotContains(html, 'Servicio Umbral')
        self.assertNotContains(html, 'Cliente Umbral')
        store = reverse('sales:store')
        for session, customer, product in [
            (foreign, self.customer, self.product), (own, self.other_customer, self.product), (own, self.customer, self.other_product),
        ]:
            self.assertEqual(self.client.post(store, self.payload(session, customer, product)).status_code, 200)
        cases = [
            {'cash_session': foreign, 'customer': self.customer, 'product': self.product},
            {'cash_session': own, 'customer': self.other_customer, 'product': self.product},
            {'cash_session': own, 'customer': self.customer, 'product': self.other_product},
        ]
        for case in cases:
            with self.assertRaises(ValidationError):
                create_sale(user=self.admin, payment_method=PaymentMethod.CASH,
                            cash_session=case['cash_session'], customer=case['customer'],
                            details=[{'type': SaleDetailType.PRODUCT, 'product': case['product'], 'quantity': 1, 'unit_price': 5000}])
        self.assertFalse(Sale.objects.exists())
        self.assertEqual(Product.objects.get(pk=self.other_product.pk).stock, Decimal('10'))

    def test_foreign_appointment_and_service_cannot_be_charged(self):
        own = self.open_cash(self.admin, 'Caja Prisma')
        professional = Professional.objects.create(user=self.cashier, business=self.beta)
        appointment = Appointment.objects.create(
            business=self.beta, customer=self.other_customer, service=self.other_service,
            professional=professional, date=datetime.date.today(), start_time=datetime.time(10),
        )
        for selected_appointment, service in ((appointment, self.service), (None, self.other_service)):
            with self.assertRaises(ValidationError):
                create_sale(user=self.admin, payment_method=PaymentMethod.CASH, cash_session=own,
                            appointment=selected_appointment,
                            details=[{'type': SaleDetailType.SERVICE, 'service': service, 'quantity': 1, 'unit_price': 25000}])
        payload = self.payload(own, self.customer, self.product)
        payload['appointment'] = appointment.pk
        response = self.client.post(reverse('sales:store'), payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('appointment', 'invalid_choice'))
        self.assertFalse(Sale.objects.exists())

    def test_worker_cannot_manage_sales_or_see_sales_navigation(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(reverse('sales:index')).status_code, 403)
        self.assertNotContains(self.client.get(reverse('accounts:business_panel')), f'href="{reverse("sales:index")}"')
