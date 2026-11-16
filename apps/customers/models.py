from django.conf import settings
from django.db import models


class Customer(models.Model):
    class ConsentMethod(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        ESCRITO = 'escrito', 'Escrito'
        DIGITAL = 'digital', 'Digital'
        OTRO = 'otro', 'Otro'

    name = models.CharField('Nombre Completo', max_length=150)
    phone = models.CharField('Teléfono / WhatsApp', max_length=20)
    email = models.EmailField('Correo Electrónico', blank=True, null=True)
    notes = models.TextField('Notas y Preferencias', blank=True, help_text='Alergias, estilos preferidos o notas especiales')
    is_vip = models.BooleanField('Cliente VIP', default=False)
    data_consent = models.BooleanField(
        'Autorización de tratamiento de datos personales',
        default=False,
        help_text=(
            'Indica si la persona autoriza de forma explícita el registro y uso de sus datos '
            'de contacto e historial de atención en StudioGest para agendar, comunicarse y '
            'gestionar los servicios.'
        ),
    )
    data_consent_at = models.DateTimeField(
        'Fecha y hora de evidencia del consentimiento',
        null=True,
        blank=True,
        help_text='Fecha y hora en que se registró la autorización otorgada.',
    )
    data_consent_method = models.CharField(
        'Medio de autorización',
        max_length=20,
        choices=ConsentMethod.choices,
        blank=True,
        help_text='Medio por el cual la persona otorgó la autorización.',
    )
    data_consent_notes = models.CharField(
        'Observaciones de la autorización',
        max_length=255,
        blank=True,
        help_text='Nota operativa breve sobre la autorización (opcional).',
    )
    data_consent_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_customer_consents',
        verbose_name='Registrado por',
        help_text='Usuario que registró la evidencia del consentimiento.',
    )
    created_at = models.DateTimeField('Fecha de Registro', auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def total_appointments(self):
        return self.appointments.count()
