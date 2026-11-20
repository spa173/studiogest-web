import base64
import hashlib
import ipaddress
import logging
import re
import secrets
import time
from io import BytesIO
from smtplib import SMTPException

import django_otp
import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import MFARecoveryCode


logger = logging.getLogger(__name__)
DEVICE_NAME = 'studiogest-privileged'
PENDING_SETUP = 'privileged_mfa_setup'
ADMIN_ALERT = 'django_admin_access_alerted'
PUBLIC_ROUTES = {
    'root', 'terms', 'privacy_notice', 'demo_request', 'appointments:public_booking',
    'appointments:business_booking', 'accounts:logout', 'accounts:mfa_setup', 'accounts:mfa_verify',
}


def _device(user, lock=False):
    devices = TOTPDevice.objects.filter(user=user, name=DEVICE_NAME, confirmed=True)
    if lock:
        devices = devices.select_for_update()
    return devices.order_by('pk').first()


def _verified(user, device):
    return getattr(user, 'otp_device', None) == device


def _start_verified_session(request, device):
    request.session.cycle_key()
    django_otp.login(request, device)


def _digest(code):
    return hashlib.sha256(code.encode('ascii')).hexdigest()


@transaction.atomic
def _enroll(user, key, token):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    if _device(user):
        return None, []
    generator = TOTP(bytes.fromhex(key))
    if not re.fullmatch(r'[0-9]{6}', token) or not generator.verify(int(token), tolerance=1):
        return None, []
    device = TOTPDevice.objects.create(
        user=user, name=DEVICE_NAME, key=key, last_t=generator.t(), drift=generator.drift,
    )
    codes = [secrets.token_hex(16) for _ in range(10)]
    MFARecoveryCode.objects.bulk_create(
        [MFARecoveryCode(device=device, digest=_digest(code)) for code in codes],
    )
    return device, codes


@transaction.atomic
def _verify_token(user, token):
    device = _device(user, lock=True)
    if not device or not device.verify_is_allowed()[0]:
        return None
    if re.fullmatch(r'[0-9a-f]{32}', token):
        used, _ = MFARecoveryCode.objects.filter(device=device, digest=_digest(token)).delete()
        if used:
            device.throttle_reset()
            return device
    return device if device.verify_token(token) else None


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def mfa_setup(request):
    user = request.user
    device = _device(user)
    if device:
        return redirect('dashboard:index' if _verified(user, device) else 'accounts:mfa_verify')

    pending = request.session.get(PENDING_SETUP)
    now = int(time.time())
    if pending and pending['expires'] <= now:
        request.session.pop(PENDING_SETUP, None)
        pending = None

    error = ''
    if request.method == 'POST' and not pending:
        last_attempt = request.session.get('privileged_mfa_password_attempt', 0)
        if now - last_attempt < 3:
            error = 'Espera unos segundos antes de intentarlo de nuevo.'
        else:
            request.session['privileged_mfa_password_attempt'] = now
            if user.check_password(request.POST.get('password', '')):
                pending = {'key': secrets.token_hex(20), 'expires': now + 600, 'attempts': 0}
                request.session[PENDING_SETUP] = pending
                return redirect('accounts:mfa_setup')
            error = 'La contraseña no es válida.'
    elif request.method == 'POST':
        token = request.POST.get('token', '').strip()
        device, codes = _enroll(user, pending['key'], token)
        if device:
            request.session.pop(PENDING_SETUP, None)
            _start_verified_session(request, device)
            return render(request, 'accounts/mfa.html', {'recovery_codes': codes})
        pending['attempts'] += 1
        if pending['attempts'] >= 5:
            request.session.pop(PENDING_SETUP, None)
            pending = None
            error = 'Vuelve a confirmar tu contraseña para generar una clave nueva.'
        else:
            request.session[PENDING_SETUP] = pending
            error = 'El código no es válido.'

    context = {'setup': True, 'error': error}
    if pending:
        key = bytes.fromhex(pending['key'])
        device = TOTPDevice(user=user, name=DEVICE_NAME, key=pending['key'])
        image = BytesIO()
        qrcode.make(device.config_url).save(image, format='PNG')
        context.update(
            manual_key=base64.b32encode(key).decode('ascii').rstrip('='),
            qr_image=base64.b64encode(image.getvalue()).decode('ascii'),
        )
    return render(request, 'accounts/mfa.html', context)


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def mfa_verify(request):
    if not _device(request.user):
        return redirect('dashboard:index')
    destination = request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        destination = reverse('dashboard:index')
    error = ''
    if request.method == 'POST':
        device = _verify_token(request.user, request.POST.get('token', '').strip().lower()[:80])
        if device:
            _start_verified_session(request, device)
            return redirect(destination)
        error = 'Código incorrecto, usado o temporalmente bloqueado. Espera antes de reintentar.'
    return render(request, 'accounts/mfa.html', {'error': error})


def _request_ip(request):
    candidate = request.META.get('REMOTE_ADDR', '')
    if settings.VERCEL_DEPLOYMENT:
        candidate = request.headers.get('X-Vercel-Forwarded-For', candidate)
    try:
        return str(ipaddress.ip_address(candidate.strip()))
    except ValueError:
        return 'Sin identificar'


class PrivilegedAccessMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            device = _device(request.user)
            if device and not _verified(request.user, device):
                match = request.resolver_match
                if match.view_name not in PUBLIC_ROUTES and not (
                    match.namespace == 'admin' and match.url_name == 'logout'
                ):
                    return redirect_to_login(request.get_full_path(), 'accounts:mfa_verify')
        return None

    def process_response(self, request, response):
        match = getattr(request, 'resolver_match', None)
        if (
            not settings.ADMIN_ACCESS_ALERT_EMAIL or not match or match.namespace != 'admin'
            or match.url_name in {'login', 'logout', 'jsi18n'}
            or response.status_code != 200 or not request.user.is_authenticated
            or not request.user.is_active or not request.user.is_admin
            or request.session.get(ADMIN_ALERT)
        ):
            return response

        agent = request.headers.get('User-Agent', 'Sin identificar')[:512]
        agent = ' '.join(agent.split())
        try:
            sent = send_mail(
                'StudioGest: acceso a Django Admin',
                f'Usuario: {request.user.get_username()}\n'
                f'Fecha UTC: {timezone.now():%Y-%m-%d %H:%M:%S}\n'
                f'IP: {_request_ip(request)}\n'
                f'Dispositivo o navegador declarado: {agent}\n',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_ACCESS_ALERT_EMAIL],
            )
        except (OSError, SMTPException):
            logger.warning('No se pudo enviar el aviso de acceso a Django Admin.')
        else:
            if sent:
                request.session[ADMIN_ALERT] = True
        return response
