from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('registrar/', views.register_product, name='create'),
    path('historial/', views.entry_history, name='history'),
    path('<int:pk>/compra/', views.register_product, {'mode': 'purchase'}, name='purchase'),
    path('<int:pk>/editar/', views.register_product, {'mode': 'edit'}, name='update'),
]
