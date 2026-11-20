from django import forms
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, ProfileForm
from .models import TermsAcceptance


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Manejo de la opción 'Recordarme'
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # La sesión expira al cerrar el navegador
            else:
                request.session.set_expiry(60 * 60 * 24 * 14)  # 2 semanas

            messages.success(request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")

            # Redirección segura
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard:index')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url
    })


@require_http_methods(['POST'])
def logout_view(request):
    if request.user.is_authenticated:
        nombre = request.user.first_name or request.user.username
        logout(request)
        messages.info(request, f"Sesión finalizada. ¡Hasta pronto, {nombre}!")
    return redirect('accounts:login')


@login_required
@require_http_methods(['GET', 'POST'])
def profile_settings(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save(update_fields=form.Meta.fields)
            messages.success(request, 'Tus datos personales se actualizaron correctamente.')
            return redirect('accounts:settings')
        messages.error(request, 'No se pudieron guardar los cambios. Revisa los campos indicados.')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/settings.html', {'form': form})


class TermsAcceptanceForm(forms.Form):
    version = forms.CharField(max_length=32, widget=forms.HiddenInput)
    accepted = forms.BooleanField(error_messages={'required': 'Marca la casilla para aceptar los términos.'})

    def clean_version(self):
        version = self.cleaned_data['version']
        if version != settings.TERMS_VERSION:
            raise forms.ValidationError('Los términos cambiaron. Vuelve a leer la versión vigente.')
        return version


@login_required
@require_http_methods(['GET', 'POST'])
def accept_terms(request):
    version = settings.TERMS_VERSION
    next_url = request.POST.get('next') if request.method == 'POST' else request.GET.get('next')
    if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        next_url = None

    if not version or request.user.terms_acceptances.filter(version=version).exists():
        return redirect(next_url or 'dashboard:index')

    form = TermsAcceptanceForm(
        request.POST if request.method == 'POST' else None,
        initial={'version': version},
    )
    if request.method == 'POST' and form.is_valid():
        TermsAcceptance.objects.get_or_create(user=request.user, version=form.cleaned_data['version'])
        return redirect(next_url or 'dashboard:index')

    return render(request, 'accounts/accept_terms.html', {
        'form': form,
        'terms_version': version,
        'next': next_url,
    })
