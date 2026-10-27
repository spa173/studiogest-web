"""
URL configuration for StudioGest project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    # Ruta raíz
    path('', root_redirect, name='root'),
]
