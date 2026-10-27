import datetime
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from customers.models import Customer
from services.models import Service, Professional


class Appointment(models.Model):
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

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError({
                    'end_time': 'La hora de finalización debe ser posterior a la hora de inicio.'
                })

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
        if not self.price_cop and self.service_id:
            self.price_cop = self.service.price_cop

        # Auto-calcular end_time si no fue especificado
        if self.start_time and not self.end_time and self.service_id:
            start_dt = datetime.datetime.combine(datetime.date.today(), self.start_time)
            end_dt = start_dt + datetime.timedelta(minutes=self.service.duration_minutes)
            self.end_time = end_dt.time()

        self.full_clean()
        super().save(*args, **kwargs)
