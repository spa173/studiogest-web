import uuid

from django.db import models


class DemoRequest(models.Model):
    request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField('Nombre', max_length=120)
    business_name = models.CharField('Negocio', max_length=150)
    email = models.EmailField('Correo electrónico')
    phone = models.CharField('Teléfono', max_length=25, blank=True)
    message = models.TextField('Mensaje', max_length=1000, blank=True)
    contact_consent = models.BooleanField('Autorizó el contacto')
    created_at = models.DateTimeField('Recibida', auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-pk')
        verbose_name = 'Solicitud de demostración'
        verbose_name_plural = 'Solicitudes de demostración'

    def __str__(self):
        return self.business_name
