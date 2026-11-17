from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


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

    def clean(self):
        super().clean()
        errors = {}
        if isinstance(self.name, str):
            self.name = ' '.join(self.name.split())
        if not self.name:
            errors['name'] = 'Escribe el nombre del servicio.'

        # full_clean calls clean even when a field has already failed conversion.
        # Leave those field errors intact rather than raising a TypeError here.
        for field_name in ('duration_minutes', 'price_cop'):
            try:
                value = self._meta.get_field(field_name).to_python(getattr(self, field_name))
            except ValidationError:
                continue
            if value is None:
                continue
            if field_name == 'duration_minutes':
                if value <= 0:
                    errors[field_name] = 'La duración debe ser mayor que cero.'
                elif value > 2147483647:
                    errors[field_name] = 'La duración no puede superar 2147483647 minutos.'
            elif value < 0:
                errors[field_name] = 'El precio no puede ser negativo.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

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
    work_start_time = models.TimeField(
        'Hora de inicio laboral',
        null=True,
        blank=True,
        help_text='Inicio de la jornada del profesional. Déjalo vacío junto con la hora de fin para no restringir horarios.'
    )
    work_end_time = models.TimeField(
        'Hora de fin laboral',
        null=True,
        blank=True,
        help_text='Fin de la jornada del profesional. Debe ser posterior a la hora de inicio.'
    )
    is_active = models.BooleanField('Activo en Turnos', default=True)

    class Meta:
        verbose_name = 'Profesional'
        verbose_name_plural = 'Profesionales'
        ordering = ['user__first_name', 'user__last_name']

    def clean(self):
        super().clean()
        errors = {}
        start = self.work_start_time
        end = self.work_end_time
        if (start is None) != (end is None):
            msg = 'Define la hora de inicio y de fin laboral, o deja ambas vacías para no restringir horarios.'
            errors['work_start_time'] = msg
            errors['work_end_time'] = msg
        elif start is not None and end is not None and end <= start:
            errors['work_end_time'] = 'La hora de fin laboral debe ser posterior a la hora de inicio.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} ({self.specialty})"

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def has_work_schedule(self):
        return self.work_start_time is not None and self.work_end_time is not None

    @property
    def work_schedule_display(self):
        if self.has_work_schedule:
            return f"{self.work_start_time.strftime('%H:%M')} - {self.work_end_time.strftime('%H:%M')}"
        return 'Sin horario definido'
