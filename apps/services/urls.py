from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    # CRUD de Servicios
    path('', views.service_list, name='list'),
    path('nuevo/', views.service_create, name='create'),
    path('<int:pk>/editar/', views.service_update, name='update'),
    path('<int:pk>/eliminar/', views.service_delete, name='delete'),

    # CRUD de Profesionales
    path('profesionales/', views.professionals_list, name='professionals_list'),
    path('profesionales/nuevo/', views.professional_create, name='professional_create'),
    path('profesionales/<int:pk>/editar/', views.professional_update, name='professional_update'),
    path('profesionales/<int:pk>/eliminar/', views.professional_delete, name='professional_delete'),
    path('profesionales/<int:pk>/alternar-estado/', views.professional_toggle_status, name='professional_toggle_status'),
]
