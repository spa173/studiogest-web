import re

from django import forms
from django.contrib.auth import authenticate, get_user_model


class LoginForm(forms.Form):
    login = forms.CharField(
        label="Correo electrónico o usuario",
        widget=forms.TextInput(attrs={
            'id': 'id_login',
            'class': 'w-full pl-10 pr-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl text-on-surface placeholder:text-outline focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 font-body-md text-body-md transition-all shadow-sm',
            'placeholder': 'admin@studiogest.co',
            'autocomplete': 'username',
            'required': True
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'id': 'id_password',
            'class': 'w-full pl-10 pr-11 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl text-on-surface placeholder:text-outline focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 font-body-md text-body-md transition-all shadow-sm',
            'placeholder': '••••••••••••',
            'autocomplete': 'current-password',
            'required': True
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Recordarme",
        widget=forms.CheckboxInput(attrs={
            'id': 'id_remember_me',
            'class': 'w-4 h-4 rounded text-secondary border-outline-variant focus:ring-secondary/20 focus:ring-offset-0 cursor-pointer'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        login_input = cleaned_data.get('login')
        password = cleaned_data.get('password')

        if login_input and password:
            # Primero intentar autenticar con username
            user = authenticate(username=login_input, password=password)
            
            # Si no funciona, intentar buscar usuario por email
            if user is None:
                from .models import User
                try:
                    user_obj = User.objects.get(email__iexact=login_input)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is None:
                raise forms.ValidationError("Credenciales inválidas. Verifica tu correo y contraseña.")
            elif not user.is_active:
                raise forms.ValidationError("Esta cuenta de usuario ha sido desactivada.")

            self.user_cache = user

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email', 'phone']
        labels = {'first_name': 'Nombres', 'last_name': 'Apellidos',
                  'email': 'Correo electrónico', 'phone': 'Teléfono'}
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['phone'].help_text = 'Opcional. Entre 7 y 15 dígitos; admite +, espacios, paréntesis y guiones.'
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant '
                'rounded-xl text-on-surface focus:outline-none focus:border-secondary '
                'focus:ring-4 focus:ring-secondary/10 transition-all text-sm'
            )

    def clean_first_name(self):
        return ' '.join(self.cleaned_data['first_name'].split())

    def clean_last_name(self):
        return ' '.join(self.cleaned_data['last_name'].split())

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if self._meta.model.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado por otro usuario.')
        return email

    def clean_phone(self):
        phone = ' '.join((self.cleaned_data.get('phone') or '').split())
        if not phone:
            return None
        digits = re.sub(r'\D', '', phone)
        if not re.fullmatch(r'[0-9 +()\-]+', phone) or not 7 <= len(digits) <= 15:
            raise forms.ValidationError('Escribe un teléfono válido de entre 7 y 15 dígitos.')
        return phone
