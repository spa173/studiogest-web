import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from .models import Appointment
from .forms import AppointmentForm, PublicBookingForm
from services.models import Service, Professional
from customers.models import Customer
from accounts.permissions import can_change_appointment_status, can_create_appointments, can_view_agenda


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
    can_create = can_create_appointments(request.user)
    if request.method == 'POST':
        if not can_create:
            raise PermissionDenied('No tienes permisos para crear citas.')
        form = AppointmentForm(request.POST, user=request.user)
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
        form = AppointmentForm(initial={'date': current_date.isoformat()}, user=request.user)

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

    can_view_pending = can_view_agenda(request.user)
    pending_count = Appointment.objects.filter(status=Appointment.Status.PENDING).count() if can_view_pending else 0

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
        'can_create_appointments': can_create,
        'can_view_pending_requests': can_view_pending,
        'pending_requests_count': pending_count,
    }
    return render(request, 'appointments/calendar.html', context)


def _management_note(appointment, action, user):
    actor = getattr(user, 'get_username', lambda: str(user))()
    stamp = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    note = f"[Gestión interna] {action} por {actor} el {stamp}."
    current = (appointment.notes or '').strip()
    return f"{current}\n{note}".strip() if current else note


def _transition_appointment(request, pk, allowed_statuses, target_status, action_label, success_level='success'):
    appointment = get_object_or_404(Appointment, pk=pk)
    if not can_change_appointment_status(request.user, appointment):
        raise PermissionDenied
    with transaction.atomic():
        current = Appointment.objects.select_for_update().get(pk=pk)
        if current.status not in allowed_statuses:
            messages.error(
                request,
                f"No se pudo {action_label} la cita de {current.customer.name}: su estado actual es {current.get_status_display()}."
            )
            return redirect(request.POST.get('next') or 'appointments:calendar')
        current.status = target_status
        # Solo registra auditoría ligera en transiciones de solicitudes pendientes.
        if Appointment.Status.PENDING in allowed_statuses:
            current.notes = _management_note(current, action_label.capitalize(), request.user)
        current.save()
    getattr(messages, success_level)(request, f"La cita de {current.customer.name} fue {action_label}.")
    return redirect(request.POST.get('next') or 'appointments:calendar')


@login_required
@require_POST
def cancel_appointment(request, pk):
    # Cancelación operativa: no permite cancelar lo ya cancelado/completado.
    return _transition_appointment(
        request, pk,
        allowed_statuses={Appointment.Status.PENDING, Appointment.Status.CONFIRMED, Appointment.Status.IN_PROGRESS},
        target_status=Appointment.Status.CANCELLED,
        action_label='cancelada',
        success_level='info',
    )


@login_required
@require_POST
def complete_appointment(request, pk):
    # Completar: solo citas activas/confirmadas o en atención.
    return _transition_appointment(
        request, pk,
        allowed_statuses={Appointment.Status.CONFIRMED, Appointment.Status.IN_PROGRESS},
        target_status=Appointment.Status.COMPLETED,
        action_label='completada',
        success_level='success',
    )


@login_required
@require_POST
def confirm_pending_appointment(request, pk):
    return _transition_appointment(
        request, pk,
        allowed_statuses={Appointment.Status.PENDING},
        target_status=Appointment.Status.CONFIRMED,
        action_label='confirmada',
        success_level='success',
    )


@login_required
@require_POST
def reject_pending_appointment(request, pk):
    return _transition_appointment(
        request, pk,
        allowed_statuses={Appointment.Status.PENDING},
        target_status=Appointment.Status.CANCELLED,
        action_label='rechazada',
        success_level='info',
    )


@login_required
def pending_requests(request):
    if not can_view_agenda(request.user):
        raise PermissionDenied('No tienes permisos para ver solicitudes de agenda.')
    pending_qs = Appointment.objects.filter(
        status=Appointment.Status.PENDING
    ).select_related('customer', 'service', 'professional', 'professional__user').order_by('date', 'start_time', 'created_at')
    appointments = []
    for appointment in pending_qs:
        appointments.append({
            'obj': appointment,
            'can_manage': can_change_appointment_status(request.user, appointment),
        })
    return render(request, 'appointments/pending_requests.html', {
        'pending_appointments': appointments,
        'pending_count': pending_qs.count(),
    })


@require_http_methods(['GET', 'POST'])
def public_booking(request):
    """Reserva pública de cita (RF-14, MVP): sin autenticación."""
    if request.method == 'POST':
        form = PublicBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            return render(request, 'appointments/public_booking_success.html', {
                'appointment': appointment,
            })
    else:
        form = PublicBookingForm()
    return render(request, 'appointments/public_booking.html', {'form': form})
