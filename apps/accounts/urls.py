from django.urls import path
from . import business_views, views

app_name = 'accounts'

urlpatterns = [
    path('negocio/', business_views.panel, name='business_panel'),
    path('negocio/citas/<int:pk>/', business_views.appointment, name='business_appointment'),
    path('negocio/servicios/nuevo/', business_views.service, name='business_service_create'),
    path('negocio/servicios/<int:pk>/', business_views.service, name='business_service_edit'),
    path('negocio/profesionales/<int:pk>/', business_views.professional, name='business_professional_edit'),
    path('aceptar-terminos/', views.accept_terms, name='accept_terms'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('configuracion/', views.profile_settings, name='settings'),
]
