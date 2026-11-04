import re

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Professional

User = get_user_model()

CLASE_INPUT = (
    'w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant '
    'rounded-xl font-body-md text-body-md text-on-surface placeholder:text-outline '
    'focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 '
    'transition-all font-medium'
)


class ProfessionalForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nombres',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': CLASE_INPUT,
            'placeholder': 'Ej. Andrés',
            'autofocus': True,
        })
    )
    last_name = forms.CharField(
        label='Apellidos',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': CLASE_INPUT,
            'placeholder': 'Ej. Martínez',
        })
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': CLASE_INPUT,
            'placeholder': 'profesional@studiogest.co',
            'autocomplete': 'email',
        }),
        help_text='Servirá para el inicio de sesión y notificaciones del sistema.'
    )
    phone = forms.CharField(
        label='Teléfono / WhatsApp',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': CLASE_INPUT,
            'placeholder': '310 123 4567',
            'inputmode': 'tel',
            'autocomplete': 'tel',
        }),
        help_text='Opcional. Entre 7 y 15 dígitos.'
    )
    password = forms.CharField(
        label='Contraseña de acceso',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': CLASE_INPUT,
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        }),
        help_text='Por defecto: «barbero123» si se deja en blanco al crear. Al editar, déjalo vacío para no cambiarla.'
    )

    class Meta:
        model = Professional
        fields = ['specialty', 'color_tag', 'is_active']
        labels = {
            'specialty': 'Especialidad',
            'color_tag': 'Color identificador en agenda',
            'is_active': 'Activo en turnos y agenda',
        }
        widgets = {
            'specialty': forms.TextInput(attrs={
                'class': CLASE_INPUT,
                'placeholder': 'Ej. Barbero Profesional, Colorista, Estilista Master',
            }),
            'color_tag': forms.TextInput(attrs={
                'class': CLASE_INPUT + ' h-11 cursor-pointer',
                'type': 'color',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-outline text-secondary focus:ring-secondary h-4 w-4 cursor-pointer',
            }),
        }
        help_texts = {
            'color_tag': 'Color asignado al profesional para distinguir sus citas en el calendario semanal.',
            'is_active': 'Si se desmarca, el profesional no estará disponible para nuevas citas.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and hasattr(self.instance, 'user'):
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = user.phone or ''

    def clean_first_name(self):
        nombre = ' '.join(self.cleaned_data['first_name'].split())
        if len(nombre) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 letras.')
        return nombre

    def clean_last_name(self):
        apellido = ' '.join(self.cleaned_data['last_name'].split())
        if len(apellido) < 2:
            raise forms.ValidationError('El apellido debe tener al menos 2 letras.')
        return apellido

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        query = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.user_id)
        if query.exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def clean_phone(self):
        telefono = ' '.join((self.cleaned_data.get('phone') or '').split())
        if not telefono:
            return ''
        digitos = re.sub(r'\D', '', telefono)
        if not re.fullmatch(r'[0-9 +()\-]+', telefono) or not 7 <= len(digitos) <= 15:
            raise forms.ValidationError('Escribe un teléfono válido (entre 7 y 15 dígitos).')
        return telefono

    def clean_color_tag(self):
        color = (self.cleaned_data.get('color_tag') or '').strip()
        if not re.fullmatch(r'^#[0-9a-fA-F]{6}$', color):
            return '#0D9488'
        return color.upper()

    def clean_specialty(self):
        esp = ' '.join((self.cleaned_data.get('specialty') or '').split())
        if not esp:
            return 'Barbero Profesional'
        return esp

    @transaction.atomic
    def save(self, commit=True):
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']
        phone = self.cleaned_data.get('phone', '')
        password = (self.cleaned_data.get('password') or '').strip()

        if self.instance and self.instance.pk:
            # Actualización
            user = self.instance.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.phone = phone
            if password:
                user.set_password(password)
            user.save()

            prof = super().save(commit=commit)
            return prof
        else:
            # Creación
            base_username = re.sub(r'[^a-z0-9_]', '', email.split('@')[0].lower()) or 'prof'
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=User.Role.WORKER,
            )
            user.set_password(password or 'barbero123')
            user.save()

            prof = super().save(commit=False)
            prof.user = user
            if commit:
                prof.save()
            return prof
