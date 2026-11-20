import uuid

from django import forms


class DemoRequestForm(forms.Form):
    request_id = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput)
    name = forms.CharField(label='Tu nombre', max_length=120, widget=forms.TextInput(attrs={'autocomplete': 'name'}))
    business_name = forms.CharField(
        label='Nombre de tu negocio', max_length=150,
        widget=forms.TextInput(attrs={'autocomplete': 'organization'}),
    )
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    phone = forms.CharField(
        label='Teléfono (opcional)', max_length=25, required=False,
        widget=forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel'}),
    )
    message = forms.CharField(
        label='¿Qué quieres conocer? (opcional)', max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    contact_consent = forms.BooleanField(label='Autorizo a Envision One a contactarme sobre esta solicitud.')
    website = forms.CharField(
        required=False, widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
    )
