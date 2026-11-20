import csv
import datetime
from io import BytesIO, StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from appointments.models import Appointment
from customers.models import Customer
from inventory.models import Product
from sales.models import CashRegisterSession, PaymentMethod, Sale, SaleDetail, SaleDetailType
from services.models import BookingBusiness, Professional, Service


@override_settings(TENANT_BOOKING_ENABLED=True)
class BusinessReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alpha = BookingBusiness.objects.create(name='Salón Prisma', slug='prisma')
        cls.beta = BookingBusiness.objects.create(name='Barbería Umbral', slug='umbral')
        cls.admin = cls.create_records(cls.alpha, 'Prisma', 12000, 'ADMIN')
        cls.cashier = cls.create_records(cls.beta, 'Umbral', 35000, 'CAJA_RECEPCION')
        cls.platform = cls.create_records(None, 'Histórico', 9800, 'ADMIN', is_superuser=True)
        cls.worker = get_user_model().objects.create_user(username='worker', email='worker@example.test', business=cls.alpha)
        cls.url = reverse('reports:index')

    @staticmethod
    def create_records(business, label, amount, role, **flags):
        user = get_user_model().objects.create_user(
            username=label, email=f'{label}@example.test', role=role, business=business, **flags,
        )
        service = Service.objects.create(business=business, name=f'Corte {label}', price_cop=amount)
        product = Product.objects.create(
            business=business, code='SKU-01', name=f'Tinte {label}', base_unit=Product.BaseUnit.UNIT,
            stock=1, minimum_stock=2, acquisition_cost=1000, sale_price=amount, service_usage_price=amount,
        )
        client = Customer.objects.create(business=business, name=f'Cliente {label}', phone='3005550101')
        worker = Professional.objects.create(business=business, user=user)
        appointment = Appointment.objects.create(
            business=business, customer=client, service=service, professional=worker,
            date=timezone.localdate(), start_time=datetime.time(11), status=Appointment.Status.COMPLETED,
        )
        session = CashRegisterSession.objects.create(business=business, opened_by=user)
        sale = Sale.objects.create(
            business=business, user=user, customer=client, appointment=appointment,
            cash_session=session, total=amount, payment_method=PaymentMethod.CASH,
        )
        SaleDetail.objects.create(
            sale=sale, product=product, detail_type=SaleDetailType.PRODUCT,
            quantity=1, unit_price=amount, subtotal=amount,
        )
        return user

    def test_reports_and_downloads_only_use_the_signed_in_business(self):
        for user, label, amount, excluded in (
            (self.admin, 'Prisma', 12000, ('Umbral', 'Histórico')),
            (self.cashier, 'Umbral', 35000, ('Prisma', 'Histórico')),
            (self.platform, 'Histórico', 9800, ('Prisma', 'Umbral')),
        ):
            self.client.force_login(user)
            params = {'business_id': self.beta.pk, 'end_date': timezone.localdate().isoformat()}
            response = self.client.get(self.url, params)
            self.assertContains(response, f'Corte {label}')
            self.assertContains(response, f'Tinte {label}')
            self.assertEqual(response.context['summary']['total'], 1)
            self.assertEqual(response.context['summary']['estimated_income'], amount)
            self.assertEqual(response.context['sales_summary']['total'], amount)
            for word in excluded:
                self.assertNotContains(response, word)

            csv_response = self.client.get(self.url, {**params, 'export': 'csv'})
            csv_rows = list(csv.reader(StringIO(csv_response.content.decode('utf-8-sig'))))
            self.assertIn(['Total cobrado (COP)', str(amount)], csv_rows)
            self.assertIn([f'Corte {label}', '1'], csv_rows)

            xlsx_response = self.client.get(self.url, {**params, 'export': 'xlsx'})
            book = load_workbook(BytesIO(xlsx_response.content), read_only=True)
            self.assertIn((f'Corte {label}', 1), list(book['Servicios'].values))
            self.assertIn(('Total cobrado (COP)', amount, None), list(book['Ventas'].values))
            names = [str(cell) for ws in book for row in ws.values for cell in row]
            self.assertIn(f'Tinte {label}', names)
            for word in excluded:
                self.assertNotContains(csv_response, word)
                self.assertFalse(any(word in cell for cell in names))
            for result in (response, csv_response, xlsx_response):
                self.assertIn('no-store', result.headers['Cache-Control'])

    def test_worker_cannot_view_or_download_reports(self):
        self.client.force_login(self.worker)
        for params in ({}, {'export':'csv'}, {'export':'xlsx'}):
            self.assertEqual(self.client.get(self.url, params).status_code, 403)
        panel = self.client.get(reverse('accounts:business_panel'))
        self.assertNotContains(panel, f'href="{self.url}"')

    def test_report_uses_literal_text_for_catalog_names(self):
        Service.objects.filter(business=self.alpha).update(name='=Prisma')
        Product.objects.filter(business=self.alpha).update(name='-Tinte')
        self.client.force_login(self.admin)
        csv_response = self.client.get(self.url, {'export':'csv'})
        self.assertContains(csv_response, "'=Prisma")
        self.assertContains(csv_response, "'-Tinte")
        xlsx_response = self.client.get(self.url, {'export':'xlsx'})
        book = load_workbook(BytesIO(xlsx_response.content))
        service = next(c for row in book['Servicios'] for c in row if c.value == '=Prisma')
        self.assertEqual(service.data_type, 's')
