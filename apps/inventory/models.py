from decimal import Decimal

from django.conf import settings

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Round


class Product(models.Model):
    class Presentation(models.TextChoices):
        JAR = 'JAR', 'Frasco'
        SACHET = 'SACHET', 'Sobre'
        TUBE = 'TUBE', 'Tubo'
        BOX = 'BOX', 'Caja'
        BOTTLE = 'BOTTLE', 'Botella'
        UNIT = 'UNIT', 'Unidad'

    class BaseUnit(models.TextChoices):
        UNIT = 'UNIT', 'Unidad'
        ML = 'ML', 'Mililitros (ml)'
        G = 'G', 'Gramos (g)'

    code = models.CharField('Código', max_length=50, unique=True)
    name = models.CharField('Nombre', max_length=150)
    description = models.TextField('Descripción', blank=True)
    presentation = models.CharField('Presentación', max_length=6, choices=Presentation.choices, blank=True)
    content_per_presentation = models.DecimalField(
        'Contenido por presentación', max_digits=15, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.001'))])
    presentation_sale_price = models.DecimalField(
        'Precio de venta de la presentación completa', max_digits=18, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(0)])
    usage_price_override = models.DecimalField(
        'Precio por unidad base personalizado', max_digits=24, decimal_places=8,
        null=True, blank=True, validators=[MinValueValidator(0)])
    base_unit = models.CharField('Unidad base', max_length=4, choices=BaseUnit.choices)
    stock = models.DecimalField(
        'Existencia', max_digits=15, decimal_places=3, default=Decimal('0'),
        editable=False, validators=[MinValueValidator(0)],
        help_text='Solo lectura. Se actualizará mediante movimientos de inventario.')
    minimum_stock = models.DecimalField(
        'Stock mínimo', max_digits=15, decimal_places=3, default=Decimal('0'),
        validators=[MinValueValidator(0)])
    acquisition_cost = models.DecimalField(
        'Costo de adquisición (COP por unidad base)', max_digits=24, decimal_places=8,
        validators=[MinValueValidator(0)])
    sale_price = models.DecimalField(
        'Precio de venta directa (COP por unidad base)', max_digits=24, decimal_places=8,
        validators=[MinValueValidator(0)])
    service_usage_price = models.DecimalField(
        'Tarifa por uso en servicio (COP por unidad base)', max_digits=24, decimal_places=8,
        validators=[MinValueValidator(0)])
    is_active = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name', 'code']
        constraints = [
            models.CheckConstraint(condition=models.Q(content_per_presentation__isnull=True) | models.Q(content_per_presentation__gt=0), name='inventory_content_positive'),
            models.CheckConstraint(condition=models.Q(presentation_sale_price__isnull=True) | models.Q(presentation_sale_price__gte=0), name='inventory_package_price_nonnegative'),
            models.CheckConstraint(condition=models.Q(usage_price_override__isnull=True) | models.Q(usage_price_override__gte=0), name='inventory_override_nonnegative'),
            models.CheckConstraint(condition=models.Q(stock__gte=0), name='inventory_stock_nonnegative'),
            models.CheckConstraint(condition=models.Q(minimum_stock__gte=0), name='inventory_minimum_nonnegative'),
            models.CheckConstraint(condition=models.Q(acquisition_cost__gte=0), name='inventory_cost_nonnegative'),
            models.CheckConstraint(condition=models.Q(sale_price__gte=0), name='inventory_sale_nonnegative'),
            models.CheckConstraint(condition=models.Q(service_usage_price__gte=0), name='inventory_usage_nonnegative'),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'

    def clean(self):
        super().clean()
        if self.code:
            self.code = self.code.strip().upper()
        if self.base_unit == self.BaseUnit.UNIT:
            errors = {}
            for field in ['stock', 'minimum_stock']:
                value = getattr(self, field)
                if isinstance(value, Decimal) and value != value.to_integral_value():
                    errors[field] = 'Los productos por unidad requieren cantidades enteras.'
            if errors:
                raise ValidationError(errors)

    @property
    def unit_symbol(self):
        return {self.BaseUnit.UNIT: 'ud.', self.BaseUnit.ML: 'ml', self.BaseUnit.G: 'g'}[self.base_unit]


class StockEntry(models.Model):
    class Kind(models.TextChoices):
        PURCHASE = 'PURCHASE', 'Compra'
        INITIAL = 'INITIAL', 'Saldo inicial'

    kind = models.CharField('Tipo de entrada', max_length=8, choices=Kind.choices, default=Kind.PURCHASE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='entries', verbose_name='Producto')
    operation_key = models.UUIDField('Clave de operación', unique=True, editable=False)
    request_fingerprint = models.CharField(max_length=64, editable=False)
    presentation_count = models.PositiveIntegerField('Presentaciones recibidas', validators=[MinValueValidator(1)])
    content_per_presentation = models.DecimalField('Contenido recibido por presentación', max_digits=15, decimal_places=3)
    base_unit = models.CharField('Unidad de la entrada', max_length=4, choices=Product.BaseUnit.choices)
    quantity = models.DecimalField('Cantidad recibida en unidad base', max_digits=15, decimal_places=3)
    total_cost = models.DecimalField('Costo total de compra (COP)', max_digits=18, decimal_places=2)
    presentation_sale_price = models.DecimalField('Precio de venta completo al registrar (COP)', max_digits=18, decimal_places=2)
    usage_price = models.DecimalField('Tarifa de uso al registrar (COP)', max_digits=24, decimal_places=8)
    presentation = models.CharField('Presentación recibida', max_length=6, choices=Product.Presentation.choices)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='Registrada por')
    created_at = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Entrada de inventario'
        verbose_name_plural = 'Entradas de inventario'
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(fields=['product'], condition=models.Q(kind='INITIAL'), name='inventory_one_initial_per_product'),
            models.CheckConstraint(condition=models.Q(presentation_count__gt=0), name='inventory_entry_count_positive'),
            models.CheckConstraint(condition=models.Q(content_per_presentation__gt=0), name='inventory_entry_content_positive'),
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='inventory_entry_quantity_positive'),
            models.CheckConstraint(condition=models.Q(total_cost__gte=0), name='inventory_entry_cost_nonnegative'),
            models.CheckConstraint(condition=models.Q(presentation_sale_price__gte=0), name='inventory_entry_sale_nonnegative'),
            models.CheckConstraint(condition=models.Q(usage_price__gte=0), name='inventory_entry_usage_nonnegative'),
            models.CheckConstraint(condition=models.Q(quantity=Round(models.F('content_per_presentation') * models.F('presentation_count'), precision=3)), name='inventory_entry_quantity_matches'),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Las entradas confirmadas no se pueden modificar.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Las entradas confirmadas no se pueden eliminar.')

    def __str__(self):
        return f'Entrada {self.pk} - {self.product}'

    @property
    def cost_per_presentation(self):
        from .calculations import purchase_values
        return purchase_values(self.presentation_count, self.content_per_presentation,
                               self.total_cost, self.presentation_sale_price, self.usage_price)['cost_per_presentation']

    @property
    def cost_per_base_unit(self):
        from .calculations import purchase_values
        return purchase_values(self.presentation_count, self.content_per_presentation,
                               self.total_cost, self.presentation_sale_price, self.usage_price)['cost_per_base_unit']
