from django import forms
from django.contrib.auth import authenticate


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
