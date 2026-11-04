from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import ServiceForm
from .models import Professional, Service

SERVICE_LIST = 'services:list'
GET_POST = ['GET', 'POST']
PROTECTED_MESSAGE = (
    'No se puede eliminar este servicio porque tiene citas asociadas, incluso si están '
    'canceladas o completadas. Puedes desactivarlo desde Editar para conservar el historial.'
)


@login_required
@require_GET
def service_list(request):
    services = Service.objects.all().order_by('name')
    return render(request, 'services/list.html', {'services': services, 'services_active': True})


def _require_service_admin(user):
    # is_admin incluye al rol ADMIN y a los superusuarios; is_staff por sí solo no basta.
    if not user.is_admin:
        raise PermissionDenied('Solo los administradores pueden gestionar servicios.')


def _service_form_response(request, service=None):
    data = None
    if request.method == 'POST':
        data = request.POST
    form = ServiceForm(data, instance=service)
    if request.method == 'POST':
        if form.is_valid():
            saved = form.save()
            action = 'creado' if service is None else 'actualizado'
            messages.success(request, f'El servicio «{saved.name}» se ha {action} correctamente.')
            return redirect(SERVICE_LIST)
        messages.error(request, 'No se pudo guardar el servicio. Revisa los campos indicados.')
    title = 'Nuevo servicio' if service is None else 'Editar servicio'
    return render(request, 'services/form.html', {
        'form': form, 'service': service, 'title': title, 'services_active': True,
    })


@login_required
@require_http_methods(GET_POST)
def service_create(request):
    _require_service_admin(request.user)
    return _service_form_response(request)


@login_required
@require_http_methods(GET_POST)
def service_update(request, pk):
    _require_service_admin(request.user)
    service = get_object_or_404(Service, pk=pk)
    return _service_form_response(request, service)


@login_required
@require_http_methods(GET_POST)
def service_delete(request, pk):
    _require_service_admin(request.user)
    service = get_object_or_404(Service, pk=pk)
    appointment_count = service.appointments.count()
    if request.method == 'POST':
        if appointment_count:
            messages.error(request, PROTECTED_MESSAGE)
            return redirect(SERVICE_LIST)
        try:
            with transaction.atomic():
                service.delete()
        except ProtectedError:
            # Mantener la protección si aparece una cita después de la consulta inicial.
            messages.error(request, PROTECTED_MESSAGE)
        else:
            messages.success(request, f'El servicio «{service.name}» se ha eliminado correctamente.')
        return redirect(SERVICE_LIST)
    return render(request, 'services/confirm_delete.html', {
        'service': service, 'appointment_count': appointment_count,
        'protected_message': PROTECTED_MESSAGE, 'services_active': True,
    })


@login_required
@require_GET
def professionals_list(request):
    professionals = Professional.objects.select_related('user').all()
    return render(request, 'services/professionals_list.html', {'professionals': professionals})
