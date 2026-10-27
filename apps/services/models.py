from django.db import models
from django.conf import settings


class Service(models.Model):
    name = models.CharField('Nombre del Servicio', max_length=150)
    description = models.TextField('Descripción', blank=True)
    duration_minutes = models.PositiveIntegerField('Duración (minutos)', default=45, help_text='Tiempo estimado en minutos')
    price_cop = models.DecimalField('Precio en COP', max_digits=12, decimal_places=0, help_text='Valor estándar en pesos colombianos')
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - ${int(self.price_cop):,} COP".replace(',', '.')

    @property
    def price_cop_formatted(self):
        return f"${int(self.price_cop):,} COP".replace(',', '.')


class Professional(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professional_profile',
        verbose_name='Usuario del Sistema'
    )
    specialty = models.CharField('Especialidad', max_length=120, default='Barbero Profesional')
    color_tag = models.CharField('Color Identificador (Hex)', max_length=20, default='#0D9488')
    is_active = models.BooleanField('Activo en Turnos', default=True)

    class Meta:
        verbose_name = 'Profesional'
        verbose_name_plural = 'Profesionales'
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} ({self.specialty})"

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username
