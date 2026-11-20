from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from services.models import BookingBusiness


class RequireTermsAcceptance(MiddlewareMixin):
    public_routes = {
        'accounts:accept_terms',
        'accounts:logout',
        'appointments:public_booking',
        'appointments:business_booking',
        'privacy_notice',
        'demo_request',
        'terms',
    }

    def process_view(self, request, view_func, view_args, view_kwargs):
        version = settings.TERMS_VERSION
        if not version or request.resolver_match.view_name in self.public_routes:
            return None
        if not request.user.is_authenticated or request.user.terms_acceptances.filter(version=version).exists():
            return None

        return redirect('accounts:accept_terms')


class IsolateBusinessPanel(MiddlewareMixin):
    public_routes = RequireTermsAcceptance.public_routes | {'root', 'accounts:login'}
    business_routes = {
        'accounts:business_panel',
        'accounts:business_appointment',
        'accounts:business_service_create',
        'accounts:business_service_edit',
        'accounts:business_professional_edit',
        'inventory:list',
        'inventory:create',
        'inventory:history',
        'inventory:purchase',
        'inventory:update',
        'sales:index',
        'sales:create',
        'sales:store',
        'sales:receipt',
        'sales:cancel',
        'sales:cash_open',
        'sales:cash_store',
        'sales:cash_history',
        'sales:cash_close',
        'sales:cash_finalize',
        'reports:index',
    }

    def process_view(self, request, view_func, view_args, view_kwargs):
        route = request.resolver_match.view_name
        user = request.user
        if route in self.public_routes or not user.is_authenticated or user.is_superuser:
            return None

        if not user.business_id:
            if not BookingBusiness.objects.exists():
                return None
            raise PermissionDenied

        if not settings.TENANT_BOOKING_ENABLED or not user.business.is_active:
            raise PermissionDenied

        if route == 'dashboard:index':
            return redirect('accounts:business_panel')
        if route not in self.business_routes:
            raise PermissionDenied
        return None
