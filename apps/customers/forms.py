import re

from django import forms
from django.utils import timezone

from .models import Customer

CLASE_INPUT = (
    'w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant '
    'rounded-xl font-body-md text-body-md text-on-surface placeholder:text-outline '
    'focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 '
    'transition-all font-medium'
)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'phone', 'email', 'notes', 'is_vip',
            'data_consent', 'data_consent_method', 'data_consent_notes',
        ]
        labels = {
            'data_consent': 'Autorizo el tratamiento de datos personales',
            'data_consent_method': 'Medio de autorización',
            'data_consent_notes': 'Observaciones de la autorización',
        }
        help_texts = {
            'data_consent': (
                'Autorización explícita para registrar nombre, teléfono, correo, notas y el '
                'historial de citas/compras en StudioGest, con el fin de agendar, contactar y '
                'gestionar la atención. Es opcional y puede actualizarse después.'
            ),
            'data_consent_method': 'Selecciona cómo se obtuvo la autorización (si aplica).',
            'data_consent_notes': 'Nota operativa breve, por ejemplo quién informó o si hubo revocación.',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': CLASE_INPUT, 'placeholder': 'Ej. Carlos Pérez', 'autofocus': True}),
            'phone': forms.TextInput(attrs={'class': CLASE_INPUT, 'placeholder': '310 123 4567', 'inputmode': 'tel'}),
            'email': forms.EmailInput(attrs={'class': CLASE_INPUT, 'placeholder': 'cliente@correo.com'}),
            'notes': forms.Textarea(attrs={'class': CLASE_INPUT + ' resize-none', 'rows': 3,
                                           'placeholder': 'Alergias, estilo preferido o notas especiales'}),
            'is_vip': forms.CheckboxInput(attrs={'class': 'rounded border-outline text-secondary focus:ring-secondary h-4 w-4 cursor-pointer'}),
            'data_consent': forms.CheckboxInput(attrs={
                'class': 'rounded border-outline text-secondary focus:ring-secondary h-4 w-4 cursor-pointer',
            }),
            'data_consent_method': forms.Select(attrs={'class': CLASE_INPUT}),
            'data_consent_notes': forms.TextInput(attrs={
                'class': CLASE_INPUT,
                'placeholder': 'Ej. Autorización verbal informada en recepción',
                'maxlength': '255',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._recorded_by_user = user
        self.fields['data_consent_method'].required = False
        self.fields['data_consent_notes'].required = False
        self.fields['data_consent_method'].choices = [('', 'Selecciona un medio (opcional)')] + list(
            Customer.ConsentMethod.choices
        )
        if self.instance and self.instance.pk:
            original = Customer.objects.filter(pk=self.instance.pk).values(
                'data_consent', 'data_consent_at', 'data_consent_method',
                'data_consent_notes', 'data_consent_recorded_by_id',
            ).first() or {}
            self._initial_data_consent = bool(original.get('data_consent'))
            self._initial_consent_evidence = original
        else:
            self._initial_data_consent = False
            self._initial_consent_evidence = {}

    def save(self, commit=True):
        cliente = super().save(commit=False)
        consentido = bool(self.cleaned_data.get('data_consent'))
        ahora = timezone.now()

        if consentido and (not self._initial_data_consent or not cliente.data_consent_at):
            cliente.data_consent_at = ahora
            if self._recorded_by_user and getattr(self._recorded_by_user, 'is_authenticated', False):
                cliente.data_consent_recorded_by = self._recorded_by_user

        # Si se revoca, se conserva la evidencia del último otorgamiento (fecha, medio y quién registró)
        # como trazabilidad básica; el estado vigente queda en "No registrada/no vigente".
        if self._initial_data_consent and not consentido and self._initial_consent_evidence:
            cliente.data_consent_at = self._initial_consent_evidence.get('data_consent_at')
            cliente.data_consent_method = self._initial_consent_evidence.get('data_consent_method') or ''
            cliente.data_consent_recorded_by_id = self._initial_consent_evidence.get('data_consent_recorded_by_id')
            # Se permite actualizar observaciones para dejar constancia operativa de la revocación.

        if commit:
            cliente.save()
        return cliente

    def clean_name(self):
        nombre = ' '.join(self.cleaned_data['name'].split())
        if len(nombre) < 3:
            raise forms.ValidationError('Escribe el nombre completo (mínimo 3 letras).')
        return nombre

    def clean_phone(self):
        telefono = ' '.join(self.cleaned_data['phone'].split())
        digitos = re.sub(r'\D', '', telefono)
        if not re.fullmatch(r'[0-9 +()\-]+', telefono) or not 7 <= len(digitos) <= 15:
            raise forms.ValidationError('Escribe un teléfono válido (entre 7 y 15 números).')
        repetido = Customer.objects.filter(phone=telefono).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError('Ya existe un cliente con este teléfono.')
        return telefono

    def clean_email(self):
        correo = self.cleaned_data.get('email')
        return correo.strip().lower() if correo else None
