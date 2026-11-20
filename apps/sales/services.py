from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from appointments.models import Appointment
from inventory.models import Product
from inventory.services import consume_stock, restore_stock
from services.models import Service

from .models import CashRegisterSession, Sale, SaleDetail, SaleDetailType, SaleStatus


def _can_manage_sales(user):
    """Permite registrar ventas y operar caja a administradores y cajeros/recepción."""
    return bool(
        user
        and getattr(user, 'is_authenticated', False)
        and (getattr(user, 'is_admin', False) or getattr(user, 'is_cashier', False))
    )


def _to_decimal(value):
    return Decimal(str(value))


def _require_same_business(business_id, *records):
    if any(record is not None and record.business_id != business_id for record in records):
        raise ValidationError('La caja, el cliente, la cita y los artículos deben pertenecer al mismo negocio.')


def _lock_cash_session(session_id, business_id):
    current = CashRegisterSession.objects.select_for_update().filter(
        pk=session_id, business_id=business_id,
    ).first()
    if current is None:
        raise ValidationError('La sesión de caja no está disponible en este negocio.')
    return current


def _lock_billable_appointment(appointment_id, business_id):
    appointment = Appointment.objects.select_for_update().filter(
        pk=appointment_id, business_id=business_id,
    ).exclude(status=Appointment.Status.CANCELLED).first()
    if appointment is None:
        raise ValidationError('La cita no está disponible para cobro en este negocio.')
    if Sale.objects.filter(appointment=appointment, status=SaleStatus.REGISTERED).exists():
        raise ValidationError('Esta cita ya fue cobrada.')
    return appointment


@transaction.atomic
def create_sale(*, user, payment_method, details, customer=None, appointment=None,
                cash_session=None, notes=''):
    if not user or not getattr(user, 'is_authenticated', False):
        raise ValidationError('Debes iniciar sesión para registrar una venta.')
    if not _can_manage_sales(user):
        raise ValidationError('Solo los administradores y el personal de caja/recepción pueden registrar ventas.')
    if cash_session is None:
        raise ValidationError('Debes seleccionar una sesión de caja abierta para registrar la venta.')
    business_id = user.business_id
    _require_same_business(business_id, cash_session, customer, appointment)
    cash_session = _lock_cash_session(cash_session.pk, business_id)
    if not cash_session.is_open:
        raise ValidationError('No se puede registrar la venta porque la sesión de caja seleccionada está cerrada.')
    if not details:
        raise ValidationError('La venta debe tener al menos un detalle.')

    if appointment is not None:
        appointment = _lock_billable_appointment(appointment.pk, business_id)
        if customer is None:
            customer = appointment.customer
        _require_same_business(business_id, appointment.customer)

    sale = Sale.objects.create(
        business_id=business_id,
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
                service = Service.objects.filter(pk=service, business_id=business_id).first()
            if service is None:
                raise ValidationError('El detalle de servicio requiere un servicio.')
            _require_same_business(business_id, service)
            if quantity != Decimal('1'):
                raise ValidationError('La cantidad de un servicio debe ser 1.')
            product = None
        elif detail_type == SaleDetailType.PRODUCT:
            product = raw.get('product')
            if isinstance(product, int):
                product = Product.objects.filter(pk=product, business_id=business_id).first()
            if product is None:
                raise ValidationError('El detalle de producto requiere un producto.')
            _require_same_business(business_id, product)
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


def _require_cancel_sale_permission(user):
    if not user or not getattr(user, 'is_authenticated', False):
        raise ValidationError('Debes iniciar sesión para anular una venta.')
    if not _can_manage_sales(user):
        raise ValidationError('Solo los administradores y el personal de caja/recepción pueden anular ventas.')


def _validate_cancelable_sale(locked_sale):
    if locked_sale.status == SaleStatus.CANCELLED:
        raise ValidationError('La venta ya está anulada.')
    if locked_sale.status != SaleStatus.REGISTERED:
        raise ValidationError('Solo se pueden anular ventas registradas.')


def _restore_sale_products(locked_sale, user):
    for detail in locked_sale.details.select_related('product', 'service'):
        if detail.detail_type == SaleDetailType.PRODUCT and detail.product_id:
            restore_stock(product=detail.product, quantity=detail.quantity, user=user)


def _apply_cancellation_metadata(locked_sale, reason):
    update_fields = ['status']
    # Desvincular la cita para permitir un nuevo cobro sin violar OneToOne.
    if locked_sale.appointment_id is not None:
        locked_sale.appointment = None
        update_fields.append('appointment')
    reason_text = str(reason or '').strip()
    if reason_text:
        prefix = (locked_sale.notes or '').rstrip()
        note = f'Motivo de anulación: {reason_text}'
        locked_sale.notes = f'{prefix}\n{note}'.strip() if prefix else note
        update_fields.append('notes')
    return update_fields


@transaction.atomic
def cancel_sale(*, sale, user, reason=''):
    _require_cancel_sale_permission(user)
    sale_id = getattr(sale, 'pk', sale)
    business_id = user.business_id
    sales = Sale.objects.filter(pk=sale_id, business_id=business_id)
    original = sales.only('cash_session').first()
    if original is None:
        raise ValidationError('La venta no está disponible en este negocio.')
    if original.cash_session_id:
        _lock_cash_session(original.cash_session_id, business_id)
    locked_sale = sales.select_for_update().get()
    _validate_cancelable_sale(locked_sale)
    _restore_sale_products(locked_sale, user)

    locked_sale.status = SaleStatus.CANCELLED
    update_fields = _apply_cancellation_metadata(locked_sale, reason)
    locked_sale.save(update_fields=update_fields)
    return locked_sale