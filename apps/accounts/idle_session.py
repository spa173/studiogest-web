from math import ceil
from time import time

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.views import redirect_to_login
from django.dispatch import receiver
from django.http import JsonResponse
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods


LAST_ACTIVITY = 'studiogest_last_activity'
ACTIVITY_ROUTE = 'accounts:session_activity'
PUBLIC_ROUTES = {
    'root', 'terms', 'privacy_notice', 'demo_request',
    'appointments:public_booking', 'appointments:business_booking',
}


@receiver(user_logged_in)
def initialize_activity(sender, request, user, **kwargs):
    if request is not None:
        request.session[LAST_ACTIVITY] = time()


class IdleSessionMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None

        match = request.resolver_match
        now = time()
        timeout = settings.SESSION_IDLE_SECONDS
        last_activity = request.session.get(LAST_ACTIVITY)
        if last_activity is not None and now - last_activity >= timeout:
            logout(request)
            if match.view_name == ACTIVITY_ROUTE or match.view_name in PUBLIC_ROUTES:
                return None
            if match.view_name in {'accounts:login', 'admin:login'}:
                return None
            login_url = 'admin:login' if match.namespace == 'admin' else 'accounts:login'
            return redirect_to_login(request.get_full_path(), login_url)

        if match.view_name == ACTIVITY_ROUTE:
            if request.method == 'POST' or last_activity is None:
                request.session[LAST_ACTIVITY] = now
                last_activity = now
            request.session_idle_remaining = max(1, ceil(timeout - (now - last_activity)))
        elif match.view_name not in PUBLIC_ROUTES:
            request.session[LAST_ACTIVITY] = now
            if match.namespace != 'admin':
                request.session_idle_remaining = timeout

        return None

    def process_response(self, request, response):
        cache_control = {value.strip().lower() for value in response.get('Cache-Control', '').split(',')}
        if getattr(request, 'session_idle_remaining', None) is not None and 'no-store' not in cache_control:
            add_never_cache_headers(response)
        return response


@never_cache
@require_http_methods(['GET', 'POST'])
def session_activity(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False}, status=401)
    return JsonResponse({'remaining_seconds': request.session_idle_remaining})
