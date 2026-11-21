"""
URL configuration for StudioGest project.
"""
from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import include, path
from django.views.generic import TemplateView

from dashboard.demo import demo_request
from dashboard.forms import DemoRequestForm


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'landing.html', {'demo_form': DemoRequestForm()})


urlpatterns = [
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('sitemap.xml', TemplateView.as_view(template_name='sitemap.xml', content_type='application/xml')),
    path('solicitar-demo/', demo_request, name='demo_request'),
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
