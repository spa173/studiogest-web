from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from appointments.models import Appointment
from customers.models import Customer
from inventory.models import Product
from services.models import Service


class PaymentMethod(models.TextChoices):
    CASH = 'EFECTIVO', 'Efectivo'
    CARD = 'TARJETA', 'Tarjeta'
    TRANSFER = 'TRANSFERENCIA', 'Transferencia'


class SaleStatus(models.TextChoices):
    REGISTERED = 'REGISTRADA', 'Registrada'
    CANCELLED = 'ANULADA', 'Anulada'


class SaleDetailType(models.TextChoices):
    SERVICE = 'SERVICIO', 'Servicio'
    PRODUCT = 'PRODUCTO', 'Producto'


class CashRegisterSession(models.Model):
    class Status(models.TextChoices):
        OPEN = 'ABIERTA', 'Abierta'
        CLOSED = 'CERRADA', 'Cerrada'

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cash_sessions_opened',
        verbose_name='Abierta por',
    )
    opened_at = models.DateTimeField('Apertura', auto_now_add=True)
    closed_at = models.DateTimeField('Cierre', null=True, blank=True)
    opening_cash = models.DecimalField(
        'Base inicial en efectivo', max_digits=12, decimal_places=0,
        default=Decimal('0'), validators=[MinValueValidator(0)],
    )
    counted_cash = models.DecimalField(
        'Efectivo contado al cierre', max_digits=12, decimal_places=0,
        null=True, blank=True, validators=[MinValueValidator(0)],
    )
    cash_difference = models.DecimalField(
        'Diferencia de efectivo', max_digits=12, decimal_places=0,
        null=True, blank=True,
    )
    status = models.CharField(
        'Estado', max_length=10, choices=Status.choices, default=Status.OPEN,
    )
    notes = models.TextField('Observaciones', blank=True)

    class Meta:
        verbose_name = 'Sesión de caja'
        verbose_name_plural = 'Sesiones de caja'
        ordering = ['-opened_at']

    def __str__(self):
        return f'Caja {self.opened_at:%Y-%m-%d %H:%M} ({self.get_status_display()})'

    @property
    def is_open(self):
        return self.status == self.Status.OPEN


class Sale(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sales', verbose_name='Cliente',
    )
    appointment = models.OneToOneField(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sale', verbose_name='Cita cobrada',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='sales_registered', verbose_name='Atendido por',
    )
    cash_session = models.ForeignKey(
        CashRegisterSession, on_delete=models.PROTECT, null=True, blank=True,
        related_name='sales', verbose_name='Sesión de caja',
    )
    created_at = models.DateTimeField('Fecha y hora', auto_now_add=True)
    payment_method = models.CharField(
        'Medio de pago', max_length=14, choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    status = models.CharField(
        'Estado', max_length=11, choices=SaleStatus.choices,
        default=SaleStatus.REGISTERED,
    )
    total = models.DecimalField(
        'Total', max_digits=12, decimal_places=0, default=Decimal('0'),
        validators=[MinValueValidator(0)],
    )
    notes = models.TextField('Observaciones', blank=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(total__gte=0), name='sales_total_nonnegative'),
        ]

    def __str__(self):
        return f'Venta #{self.pk} - {self.get_payment_method_display()} - ${int(self.total):,}'.replace(',', '.')

    @property
    def is_registered(self):
        return self.status == SaleStatus.REGISTERED

    @property
    def receipt_number(self):
        """Identificador operativo estable del comprobante basado en el ID existente (no fiscal)."""
        if self.pk is None:
            return 'V-000000'
        return f'V-{self.pk:06d}'


class SaleDetail(models.Model):
    sale = models.ForeignKey(
        Sale, on_delete=models.CASCADE, related_name='details',
        verbose_name='Venta',
    )
    detail_type = models.CharField(
        'Tipo', max_length=9, choices=SaleDetailType.choices,
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, null=True, blank=True,
        related_name='sale_details', verbose_name='Servicio',
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, blank=True,
        related_name='sale_details', verbose_name='Producto',
    )
    quantity = models.DecimalField(
        'Cantidad', max_digits=12, decimal_places=3, default=Decimal('1'),
        validators=[MinValueValidator(Decimal('0.001'))],
    )
    unit_price = models.DecimalField(
        'Precio unitario', max_digits=12, decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    subtotal = models.DecimalField(
        'Subtotal', max_digits=12, decimal_places=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Detalle de venta'
        verbose_name_plural = 'Detalles de venta'
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='sales_detail_quantity_positive'),
            models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='sales_detail_unit_price_nonnegative'),
            models.CheckConstraint(condition=models.Q(subtotal__gte=0), name='sales_detail_subtotal_nonnegative'),
        ]

    def clean(self):
        super().clean()
        if self.detail_type == SaleDetailType.SERVICE:
            if self.service is None or self.product is not None:
                raise ValidationError('Un detalle de servicio debe referenciar un servicio y no un producto.')
            if self.quantity != Decimal('1'):
                raise ValidationError('La cantidad de un servicio debe ser 1.')
        elif self.detail_type == SaleDetailType.PRODUCT:
            if self.product is None or self.service is not None:
                raise ValidationError('Un detalle de producto debe referenciar un producto y no un servicio.')
        else:
            raise ValidationError('Tipo de detalle no válido.')
        if self.subtotal != self.quantity * self.unit_price:
            raise ValidationError('El subtotal no coincide con cantidad y precio unitario.')

    def __str__(self):
        item = self.service or self.product
        return f'{item} x{self.quantity}'