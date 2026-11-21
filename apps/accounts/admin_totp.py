from django import forms
from django.contrib import admin
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django_otp.plugins.otp_totp.models import TOTPDevice


class AuthenticatorForm(forms.ModelForm):
    class Meta:
        model = TOTPDevice
        fields = '__all__'
        labels = {
            'user': 'Cuenta de usuario',
            'name': 'Nombre del autenticador',
            'confirmed': 'Confirmado',
            'key': 'Clave secreta',
            'step': 'Duración del código (segundos)',
            't0': 'Inicio del contador',
            'digits': 'Dígitos del código',
            'tolerance': 'Margen de tiempo permitido',
            'drift': 'Desfase detectado',
            'throttling_failure_timestamp': 'Último intento fallido',
            'throttling_failure_count': 'Intentos fallidos consecutivos',
        }
        help_texts = {
            'user': 'Selecciona la cuenta a la que pertenece el autenticador.',
            'name': 'Nombre para identificar el autenticador.',
            'confirmed': 'Indica si el autenticador está listo para usarse.',
            'key': 'Clave secreta en hexadecimal. No la compartas.',
            'step': 'Cada cuántos segundos cambia el código.',
            't0': 'Referencia interna del contador. Normalmente se deja en 0.',
            'digits': 'Cantidad de dígitos que muestra el autenticador.',
            'tolerance': 'Cuántos intervalos anteriores o posteriores se pueden aceptar.',
            'drift': 'Diferencia detectada entre el reloj del autenticador y el servidor, medida en intervalos.',
        }


class AuthenticatorAdmin(TOTPDeviceAdmin):
    form = AuthenticatorForm
    search_help_text = 'Busca por usuario o correo electrónico.'
    sections = {
        'Identity': 'Cuenta y estado',
        'Timestamps': 'Fechas de uso',
        'Configuration': 'Configuración de los códigos',
        'State': 'Sincronización',
        'Throttling': 'Intentos fallidos',
    }

    def get_fieldsets(self, request, obj=None):
        return [
            (self.sections.get(title, title), options)
            for title, options in super().get_fieldsets(request, obj)
        ]

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {**(extra_context or {}), 'title': 'Autenticadores'})

    def add_view(self, request, form_url='', extra_context=None):
        context = {**(extra_context or {}), 'title': 'Añadir autenticador'}
        return super().add_view(request, form_url, context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        context = {**(extra_context or {}), 'title': 'Detalles del autenticador'}
        return super().change_view(request, object_id, form_url, context)


admin.site.unregister(TOTPDevice)
admin.site.register(TOTPDevice, AuthenticatorAdmin)
