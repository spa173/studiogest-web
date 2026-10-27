from django.db import models


class Customer(models.Model):
    name = models.CharField('Nombre Completo', max_length=150)
    phone = models.CharField('Teléfono / WhatsApp', max_length=20)
    email = models.EmailField('Correo Electrónico', blank=True, null=True)
    notes = models.TextField('Notas y Preferencias', blank=True, help_text='Alergias, estilos preferidos o notas especiales')
    is_vip = models.BooleanField('Cliente VIP', default=False)
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
