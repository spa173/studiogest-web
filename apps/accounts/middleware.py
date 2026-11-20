from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class RequireTermsAcceptance(MiddlewareMixin):
    public_routes = {
        'accounts:accept_terms',
        'accounts:logout',
        'appointments:public_booking',
        'privacy_notice',
        'terms',
    }

    def process_view(self, request, view_func, view_args, view_kwargs):
        version = settings.TERMS_VERSION
        if not version or request.resolver_match.view_name in self.public_routes:
            return None
        if not request.user.is_authenticated or request.user.terms_acceptances.filter(version=version).exists():
            return None

        return redirect('accounts:accept_terms')
