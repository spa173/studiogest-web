from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('<int:pk>/cancelar/', views.cancel_appointment, name='cancel'),
    path('<int:pk>/completar/', views.complete_appointment, name='complete'),
]
