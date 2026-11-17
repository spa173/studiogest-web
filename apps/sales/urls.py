from django.urls import path

from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_index, name='index'),
    path('nueva/', views.sale_create, name='create'),
    path('nueva/guardar/', views.sale_store, name='store'),
    path('<int:pk>/recibo/', views.sale_receipt, name='receipt'),
    path('<int:pk>/anular/', views.sale_cancel, name='cancel'),
    path('caja/abrir/', views.cash_session_open, name='cash_open'),
    path('caja/abrir/guardar/', views.cash_session_store, name='cash_store'),
    path('caja/historial/', views.cash_session_history, name='cash_history'),
    path('caja/<int:pk>/cerrar/', views.cash_session_close, name='cash_close'),
    path('caja/<int:pk>/cerrar/confirmar/', views.cash_session_finalize, name='cash_finalize'),
]