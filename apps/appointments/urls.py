from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('pendientes/', views.pending_requests, name='pending_requests'),
    path('reserva/', views.public_booking, name='public_booking'),
    path('<int:pk>/cancelar/', views.cancel_appointment, name='cancel'),
    path('<int:pk>/completar/', views.complete_appointment, name='complete'),
    path('<int:pk>/confirmar/', views.confirm_pending_appointment, name='confirm_pending'),
    path('<int:pk>/rechazar/', views.reject_pending_appointment, name='reject_pending'),
]
