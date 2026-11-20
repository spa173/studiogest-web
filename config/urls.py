"""
URL configuration for StudioGest project.
"""
from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import TemplateView


def _admin_has_permission(request):
    return request.user.is_active and getattr(request.user, 'is_admin', False)


# Restringe /admin/ a usuarios con rol ADMIN de negocio (o superuser).
admin.site.has_permission = _admin_has_permission


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')


urlpatterns = [
    path('terminos/', TemplateView.as_view(template_name='terms.html', extra_context={
        'terms_version': settings.TERMS_VERSION,
    }), name='terms'),
    path('privacidad/', TemplateView.as_view(template_name='privacy_notice.html'), name='privacy_notice'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('appointments/', include('appointments.urls')),
    path('customers/', include('customers.urls')),
    path('services/', include('services.urls')),
    path('reports/', include('reports.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    # Ruta raíz
    path('', root_redirect, name='root'),
]
