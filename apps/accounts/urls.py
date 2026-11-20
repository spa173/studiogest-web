from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('aceptar-terminos/', views.accept_terms, name='accept_terms'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('configuracion/', views.profile_settings, name='settings'),
]
