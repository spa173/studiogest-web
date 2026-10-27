import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from services.models import Professional, Service
from customers.models import Customer


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

    # 6. Alertas de inventario (Estructura preparada para conectar con módulo de inventario)
    inventory_alerts = [
        {
            'name': 'Pomada Mate Reuzel 100g',
            'stock': 2,
            'min_stock': 5,
            'deficit': '-60%',
            'critical': True
        },
        {
            'name': 'Tinte Keratina 7.1 Castaño',
            'stock': 1,
            'min_stock': 4,
            'deficit': '-75%',
            'critical': True
        },
        {
            'name': 'Aceite para Barba Suavecito',
            'stock': 3,
            'min_stock': 6,
            'deficit': '-50%',
            'critical': False
        }
    ]

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
