from django.urls import path

from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='list'),
    path('nuevo/', views.customer_create, name='create'),
    path('<int:pk>/editar/', views.customer_update, name='update'),
    path('<int:pk>/eliminar/', views.customer_delete, name='delete'),
]
