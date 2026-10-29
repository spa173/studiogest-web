import re

from django import forms

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
        fields = ['name', 'phone', 'email', 'notes', 'is_vip']
        widgets = {
            'name': forms.TextInput(attrs={'class': CLASE_INPUT, 'placeholder': 'Ej. Carlos Pérez', 'autofocus': True}),
            'phone': forms.TextInput(attrs={'class': CLASE_INPUT, 'placeholder': '310 123 4567', 'inputmode': 'tel'}),
            'email': forms.EmailInput(attrs={'class': CLASE_INPUT, 'placeholder': 'cliente@correo.com'}),
            'notes': forms.Textarea(attrs={'class': CLASE_INPUT + ' resize-none', 'rows': 3,
                                           'placeholder': 'Alergias, estilo preferido o notas especiales'}),
            'is_vip': forms.CheckboxInput(attrs={'class': 'rounded border-outline text-secondary focus:ring-secondary h-4 w-4 cursor-pointer'}),
        }

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
