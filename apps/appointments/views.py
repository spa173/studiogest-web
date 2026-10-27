import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Appointment
from .forms import AppointmentForm
from services.models import Service, Professional
from customers.models import Customer


@login_required
def calendar_view(request):
    # Obtener fecha de referencia (por defecto hoy en Colombia)
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            current_date = datetime.date.today()
    else:
        current_date = datetime.date.today()

    # Calcular inicio de semana (Lunes) y fin (Domingo)
    start_of_week = current_date - datetime.timedelta(days=current_date.weekday())
    week_days = [start_of_week + datetime.timedelta(days=i) for i in range(7)]

    # Citas de la semana
    appointments_qs = Appointment.objects.filter(
        date__range=[week_days[0], week_days[-1]]
    ).exclude(
        status=Appointment.Status.CANCELLED
    ).select_related('customer', 'service', 'professional', 'professional__user')

    # Filtrar por profesional si viene en query params
    prof_id = request.GET.get('professional')
    if prof_id and prof_id.isdigit():
        appointments_qs = appointments_qs.filter(professional_id=int(prof_id))

    # Manejar creación de cita desde el modal (POST)
    modal_has_errors = False
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.created_by = request.user
            cita.save()
            messages.success(request, f"¡Cita agendada exitosamente para {cita.customer.name} a las {cita.start_time.strftime('%I:%M %p')}!")
            return redirect(f"{request.path}?date={cita.date.isoformat()}")
        else:
            modal_has_errors = True
            messages.error(request, "No se pudo registrar la cita. Revisa los datos ingresados en el formulario.")
    else:
        form = AppointmentForm(initial={'date': current_date.isoformat()})

    # Horarios estándar de operación: 8 AM a 8 PM (en bloques de 1 hora)
    time_slots = [datetime.time(hour=h, minute=0) for h in range(8, 20)]

    # Estructurar citas por día para renderizar en la grilla semanal
    appointments_by_day = {day: [] for day in week_days}
    for app in appointments_qs:
        if app.date in appointments_by_day:
            appointments_by_day[app.date].append(app)

    # Catálogo de servicios para interactividad en el formulario (precio/duración dinámica)
    services_list = Service.objects.filter(is_active=True)
    professionals_list = Professional.objects.filter(is_active=True)
    customers_list = Customer.objects.all().order_by('name')

    # Navegación entre semanas
    prev_week = (current_date - datetime.timedelta(days=7)).isoformat()
    next_week = (current_date + datetime.timedelta(days=7)).isoformat()

    context = {
        'form': form,
        'current_date': current_date,
        'week_days': week_days,
        'time_slots': time_slots,
        'appointments_by_day': appointments_by_day,
        'services_list': services_list,
        'professionals_list': professionals_list,
        'customers_list': customers_list,
        'prev_week': prev_week,
        'next_week': next_week,
        'selected_professional': prof_id or '',
        'modal_has_errors': modal_has_errors,
        'total_week_appointments': appointments_qs.count(),
    }
    return render(request, 'appointments/calendar.html', context)


@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        messages.info(request, f"La cita de {appointment.customer.name} ha sido cancelada.")
    return redirect('appointments:calendar')


@login_required
def complete_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.status = Appointment.Status.COMPLETED
        appointment.save()
        messages.success(request, f"Cita completada. Cobro registrado: {appointment.price_cop_formatted}.")
    return redirect('appointments:calendar')
