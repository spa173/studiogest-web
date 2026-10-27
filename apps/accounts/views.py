from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import LoginForm


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


def logout_view(request):
    if request.user.is_authenticated:
        nombre = request.user.first_name or request.user.username
        logout(request)
        messages.info(request, f"Sesión finalizada. ¡Hasta pronto, {nombre}!")
    return redirect('accounts:login')
