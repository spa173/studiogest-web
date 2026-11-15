from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from appointments.models import Appointment
from inventory.models import Product
from inventory.services import consume_stock
from services.models import Service

from .models import CashRegisterSession, Sale, SaleDetail, SaleDetailType, SaleStatus


def _to_decimal(value):
    return Decimal(str(value))


@transaction.atomic
def create_sale(*, user, payment_method, details, customer=None, appointment=None,
                cash_session=None, notes=''):
    if not user or not getattr(user, 'is_authenticated', False):
        raise ValidationError('Debes iniciar sesión para registrar una venta.')
    if not details:
        raise ValidationError('La venta debe tener al menos un detalle.')

    if appointment is not None:
        if Sale.objects.filter(appointment=appointment).exists():
            raise ValidationError('Esta cita ya fue cobrada.')
        if customer is None:
            customer = appointment.customer

    if cash_session is not None and not cash_session.is_open:
        raise ValidationError('La sesión de caja está cerrada.')

    sale = Sale.objects.create(
        customer=customer,
        appointment=appointment,
        user=user,
        cash_session=cash_session,
        payment_method=payment_method,
        status=SaleStatus.REGISTERED,
        notes=notes or '',
    )

    total = Decimal('0')
    for raw in details:
        detail_type = raw['type']
        quantity = _to_decimal(raw.get('quantity', 1))
        unit_price = _to_decimal(raw['unit_price'])
        if quantity <= 0:
            raise ValidationError('La cantidad debe ser mayor que cero.')
        if unit_price < 0:
            raise ValidationError('El precio unitario no puede ser negativo.')

        service = None
        product = None
        if detail_type == SaleDetailType.SERVICE:
            service = raw.get('service')
            if isinstance(service, int):
                service = Service.objects.get(pk=service)
            if service is None:
                raise ValidationError('El detalle de servicio requiere un servicio.')
            if quantity != Decimal('1'):
                raise ValidationError('La cantidad de un servicio debe ser 1.')
            product = None
        elif detail_type == SaleDetailType.PRODUCT:
            product = raw.get('product')
            if isinstance(product, int):
                product = Product.objects.get(pk=product)
            if product is None:
                raise ValidationError('El detalle de producto requiere un producto.')
            service = None
            consume_stock(product=product, quantity=quantity, user=user)
        else:
            raise ValidationError('Tipo de detalle no válido.')

        subtotal = (quantity * unit_price).quantize(Decimal('1'))
        SaleDetail.objects.create(
            sale=sale,
            detail_type=detail_type,
            service=service,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        total += subtotal

    sale.total = total
    sale.save(update_fields=['total'])
    return sale