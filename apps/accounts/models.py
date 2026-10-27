from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        WORKER = 'TRABAJADOR', 'Trabajador (Barbero / Estilista)'

    email = models.EmailField('Correo electrónico', unique=True)
    role = models.CharField(
        'Rol',
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        help_text='Define los permisos y nivel de acceso en StudioGest'
    )
    phone = models.CharField('Teléfono', max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_worker(self):
        return self.role == self.Role.WORKER
