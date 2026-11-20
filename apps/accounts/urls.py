from django.urls import path
from . import business_views, idle_session, security, views

app_name = 'accounts'

urlpatterns = [
    path('negocio/', business_views.panel, name='business_panel'),
    path('negocio/citas/<int:pk>/', business_views.appointment, name='business_appointment'),
    path('negocio/servicios/nuevo/', business_views.service, name='business_service_create'),
    path('negocio/servicios/<int:pk>/', business_views.service, name='business_service_edit'),
    path('negocio/profesionales/<int:pk>/', business_views.professional, name='business_professional_edit'),
    path('aceptar-terminos/', views.accept_terms, name='accept_terms'),
    path('seguridad/multifactor/', security.mfa_setup, name='mfa_setup'),
    path('seguridad/verificar/', security.mfa_verify, name='mfa_verify'),
    path('login/', views.login_view, name='login'),
    path('sesion/actividad/', idle_session.session_activity, name='session_activity'),
    path('logout/', views.logout_view, name='logout'),
    path('configuracion/', views.profile_settings, name='settings'),
]
