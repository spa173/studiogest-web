import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from services.models import Professional, Service
from customers.models import Customer
from inventory.models import Product
from django.db.models import F


@login_required
def dashboard_view(request):
    today = datetime.date.today()

    # 1. Citas del día
    today_appointments = Appointment.objects.filter(
        date=today
    ).exclude(
        status=Appointment.Status.CANCELLED
    ).select_related('customer', 'service', 'professional', 'professional__user')

    today_count = today_appointments.count()
    completed_appointments = today_appointments.filter(status=Appointment.Status.COMPLETED)
    completed_count = completed_appointments.count()

    # 2. Ventas calculadas del día (Suma de servicios atendidos hoy)
    total_sales_cop = sum(app.price_cop for app in completed_appointments)
    projected_sales_cop = sum(app.price_cop for app in today_appointments)

    # 3. Próximas citas de hoy ordenadas por hora
    upcoming_appointments = today_appointments.filter(
        status__in=[Appointment.Status.CONFIRMED, Appointment.Status.PENDING]
    ).order_by('start_time')[:6]

    # 4. Profesionales activos
    professionals = Professional.objects.filter(is_active=True).select_related('user')

    # 5. Clientes registrados
    total_customers = Customer.objects.count()

    # 6. Alertas de inventario desde la base de datos (RF-09)
    low_stock_products = Product.objects.filter(
        is_active=True, stock__lte=F('minimum_stock')
    ).order_by('stock', 'name')
    inventory_alerts = []
    for product in low_stock_products:
        if product.minimum_stock > 0:
            deficit_pct = int(round((1 - product.stock / product.minimum_stock) * 100))
            deficit = f'-{deficit_pct}%'
        else:
            deficit = '0%'
        inventory_alerts.append({
            'name': product.name,
            'stock': product.stock,
            'min_stock': product.minimum_stock,
            'deficit': deficit,
            'critical': product.stock == 0 or product.stock * 2 <= product.minimum_stock,
        })

    context = {
        'today': today,
        'today_count': today_count,
        'completed_count': completed_count,
        'total_sales_cop': total_sales_cop,
        'total_sales_formatted': f"${int(total_sales_cop):,} COP".replace(',', '.'),
        'projected_sales_formatted': f"${int(projected_sales_cop):,} COP".replace(',', '.'),
        'upcoming_appointments': upcoming_appointments,
        'professionals': professionals,
        'total_customers': total_customers,
        'inventory_alerts': inventory_alerts,
    }
    return render(request, 'dashboard/index.html', context)
