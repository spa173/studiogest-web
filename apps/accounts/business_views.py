from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from appointments.models import Appointment
from services.forms import ServiceForm
from services.models import Professional, Service

from .permissions import can_change_appointment_status, can_manage_professionals, can_manage_services


def _business(user):
    if not settings.TENANT_BOOKING_ENABLED or not user.business_id or not user.business.is_active:
        raise PermissionDenied
    return user.business


def _appointments(business):
    return Appointment.objects.filter(
        business=business, customer__business=business,
        service__business=business, professional__business=business,
        professional__user__business=business,
    )


class ProfessionalScheduleForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = ('specialty', 'work_start_time', 'work_end_time', 'is_active')
        widgets = {
            'work_start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'work_end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }


@login_required
@require_GET
def panel(request):
    business = _business(request.user)
    appointments = _appointments(business).select_related(
        'customer', 'service', 'professional__user',
    ).order_by('-date', 'start_time', 'pk')
    page = Paginator(appointments, 25).get_page(request.GET.get('page'))
    return render(request, 'accounts/business_panel.html', {
        'business': business,
        'page': page,
        'services': Service.objects.filter(business=business),
        'professionals': Professional.objects.filter(
            business=business, user__business=business,
        ).select_related('user'),
        'can_manage_services': can_manage_services(request.user),
        'can_manage_professionals': can_manage_professionals(request.user),
    })


@login_required
@require_POST
@transaction.atomic
def appointment(request, pk):
    business = _business(request.user)
    item = get_object_or_404(_appointments(business).select_for_update(), pk=pk)
    if not can_change_appointment_status(request.user, item):
        raise PermissionDenied

    transitions = {
        'confirm': Appointment.Status.CONFIRMED,
        'reject': Appointment.Status.CANCELLED,
    }
    target = transitions.get(request.POST.get('action'))
    if item.status != Appointment.Status.PENDING or target is None:
        messages.error(request, 'La solicitud ya no está pendiente o la acción no es válida.')
    else:
        item.status = target
        item.save(update_fields=['status'])
        messages.success(request, f'Cita {item.get_status_display().lower()}.')
    return redirect('accounts:business_panel')


@login_required
@require_http_methods(['GET', 'POST'])
def service(request, pk=None):
    business = _business(request.user)
    if not can_manage_services(request.user):
        raise PermissionDenied
    instance = (
        Service(business=business) if pk is None
        else get_object_or_404(Service, pk=pk, business=business)
    )
    form = ServiceForm(request.POST if request.method == 'POST' else None, instance=instance)
    return _save_catalog_form(request, form, 'Servicio')


@login_required
@require_http_methods(['GET', 'POST'])
def professional(request, pk):
    business = _business(request.user)
    if not can_manage_professionals(request.user):
        raise PermissionDenied
    instance = get_object_or_404(Professional, pk=pk, business=business, user__business=business)
    form = ProfessionalScheduleForm(
        request.POST if request.method == 'POST' else None, instance=instance,
    )
    return _save_catalog_form(request, form, 'Profesional')


def _save_catalog_form(request, form, title):
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cambios guardados.')
        return redirect('accounts:business_panel')
    return render(request, 'accounts/business_catalog_form.html', {'form': form, 'title': title})
