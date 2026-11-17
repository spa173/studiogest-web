import datetime
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from customers.models import Customer
from services.models import Service, Professional
from .pricing import calculate_pricing, validate_cop


def calculate_end_time(start_time, duration_minutes):
    """Calculate a same-day interval without losing days or overflowing dates."""
    if duration_minutes <= 0:
        raise ValidationError('La duración debe ser mayor que cero.')
    seconds_left = (
        86400 - start_time.hour * 3600 - start_time.minute * 60
        - start_time.second - start_time.microsecond / 1000000
    )
    if duration_minutes * 60 >= seconds_left:
        raise ValidationError(
            'La cita debe comenzar y terminar el mismo día. '
            'Reduce la duración o elige una hora de inicio más temprana.'
        )
    start = datetime.datetime.combine(datetime.date(2000, 1, 1), start_time)
    return (start + datetime.timedelta(minutes=duration_minutes)).time()


class Appointment(models.Model):
    class DiscountType(models.TextChoices):
        NONE = 'NONE', 'Sin descuento'
        PERCENT = 'PERCENT', 'Porcentaje (%)'
        FIXED = 'FIXED', 'Valor fijo (COP)'

    class Status(models.TextChoices):
        PENDING = 'PENDIENTE', 'Pendiente'
        CONFIRMED = 'CONFIRMADA', 'Confirmada'
        IN_PROGRESS = 'EN_ATENCION', 'En Atención'
        COMPLETED = 'COMPLETADA', 'Completada'
        CANCELLED = 'CANCELADA', 'Cancelada'

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Cliente'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='Servicio'
    )
    professional = models.ForeignKey(
        Professional,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='Profesional Asignado'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments_created',
        verbose_name='Registrado por'
    )
    date = models.DateField('Fecha de Cita')
    start_time = models.TimeField('Hora de Inicio')
    end_time = models.TimeField('Hora de Fin')
    price_cop = models.DecimalField('Precio en COP', max_digits=12, decimal_places=0)
    # NULL means unknown for legacy rows; never reconstruct from today's catalog.
    catalog_price_cop = models.DecimalField('Precio de catálogo al registrar', max_digits=12, decimal_places=0, null=True, blank=True)
    adjusted_price_cop = models.DecimalField('Precio personalizado (COP)', max_digits=12, decimal_places=0, null=True, blank=True)
    # NULL is unknown legacy history; NONE is a known absence of discount.
    discount_type = models.CharField('Tipo de descuento', max_length=7, choices=DiscountType.choices, null=True, blank=True)
    discount_value = models.DecimalField('Descuento solicitado', max_digits=14, decimal_places=2, null=True, blank=True)
    discount_amount_cop = models.DecimalField('Valor descontado (COP)', max_digits=12, decimal_places=0, null=True, blank=True)
    pricing_reason = models.TextField('Motivo del ajuste o descuento', blank=True)
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED
    )
    notes = models.TextField('Observaciones', blank=True)
    send_whatsapp = models.BooleanField('Enviar recordatorio por WhatsApp', default=True)
    created_at = models.DateTimeField('Fecha de Registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time.strftime('%H:%M')} - {self.customer.name} con {self.professional.name}"

    @property
    def price_cop_formatted(self):
        return f"${int(self.price_cop):,} COP".replace(',', '.')

    def clean(self):
        super().clean()
        self._validate_pricing()
        self._validate_interval()
        self._validate_work_schedule()
        self._validate_conflicts()

    def _validate_pricing(self):
        if self.price_cop is not None:
            validate_cop(self.price_cop, 'price_cop')
        financial = (
            self.catalog_price_cop, self.adjusted_price_cop, self.discount_type,
            self.discount_value, self.discount_amount_cop,
        )
        if any(value is not None for value in financial):
            if any(value is None for value in financial):
                raise ValidationError('El detalle económico debe estar completo; no se reconstruye información histórica desconocida.')
            validate_cop(self.catalog_price_cop, 'catalog_price_cop')
            amount, total = calculate_pricing(self.adjusted_price_cop, self.discount_type, self.discount_value)
            if self.discount_amount_cop != amount or self.price_cop != total:
                raise ValidationError('El descuento y el total no coinciden con el precio personalizado.')

    def _validate_interval(self):
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError({
                    'end_time': 'La hora de finalización debe ser posterior a la hora de inicio.'
                })

    def _validate_work_schedule(self):
        if not (self.professional_id and self.start_time and self.end_time):
            return
        professional = self.professional
        work_start = getattr(professional, 'work_start_time', None)
        work_end = getattr(professional, 'work_end_time', None)
        if work_start is None or work_end is None:
            return
        start = self.start_time
        end = self.end_time
        if start < work_start or end > work_end:
            raise ValidationError({
                'start_time': (
                    f"La cita ({start.strftime('%H:%M')} - {end.strftime('%H:%M')}) está fuera del horario laboral de "
                    f"{professional.name} ({work_start.strftime('%H:%M')} - {work_end.strftime('%H:%M')})."
                )
            })

    def _validate_conflicts(self):
        # Regla de Oro: Validación de Solapamientos (Conflict Detection)
        if self.professional_id and self.date and self.start_time and self.end_time:
            conflicts = Appointment.objects.filter(
                professional=self.professional,
                date=self.date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(status=self.Status.CANCELLED)

            if self.pk:
                conflicts = conflicts.exclude(pk=self.pk)

            if conflicts.exists():
                conflict_item = conflicts.first()
                raise ValidationError(
                    f"Conflicto de horario: {self.professional.name} ya tiene una cita agendada de "
                    f"{conflict_item.start_time.strftime('%I:%M %p')} a {conflict_item.end_time.strftime('%I:%M %p')}."
                )

    def save(self, *args, **kwargs):
        # Auto-asignar el precio del servicio si no fue fijado manualmente
        if self.price_cop is None and self.service_id:
            self.price_cop = self.service.price_cop

        # Auto-calcular end_time si no fue especificado
        if self.start_time and not self.end_time and self.service_id:
            self.end_time = calculate_end_time(self.start_time, self.service.duration_minutes)

        self.full_clean()
        super().save(*args, **kwargs)
