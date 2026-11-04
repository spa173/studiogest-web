from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list, name='list'),
    path('nuevo/', views.service_create, name='create'),
    path('<int:pk>/editar/', views.service_update, name='update'),
    path('<int:pk>/eliminar/', views.service_delete, name='delete'),
    path('profesionales/', views.professionals_list, name='professionals_list'),
]
