import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ProfessionalForm, ServiceForm
from .models import Professional, Service

POR_PAGINA = 10
URL_PROFESIONALES = 'services:professionals_list'
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


def _enlace_whatsapp(telefono):
    """Devuelve el enlace de WhatsApp si el teléfono tiene formato válido."""
    if not telefono:
        return None
    digitos = re.sub(r'\D', '', telefono)
    if len(digitos) == 10:
        digitos = '57' + digitos
    return f'https://wa.me/{digitos}' if digitos else None


@login_required
@require_GET
def professionals_list(request):
    texto = request.GET.get('q', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()

    profesionales = (
        Professional.objects
        .select_related('user')
        .annotate(num_citas=Count('appointments'))
        .order_by('user__first_name', 'user__last_name')
    )

    if texto:
        profesionales = profesionales.filter(
            Q(user__first_name__icontains=texto) |
            Q(user__last_name__icontains=texto) |
            Q(user__email__icontains=texto) |
            Q(user__phone__icontains=texto) |
            Q(specialty__icontains=texto)
        )

    if filtro_estado == 'activos':
        profesionales = profesionales.filter(is_active=True)
    elif filtro_estado == 'inactivos':
        profesionales = profesionales.filter(is_active=False)

    pagina = Paginator(profesionales, POR_PAGINA).get_page(request.GET.get('page'))
    for prof in pagina:
        prof.whatsapp = _enlace_whatsapp(prof.user.phone)

    contexto = {
        'pagina': pagina,
        'q': texto,
        'estado': filtro_estado,
        'total_profesionales': Professional.objects.count(),
        'total_activos': Professional.objects.filter(is_active=True).count(),
        'total_inactivos': Professional.objects.filter(is_active=False).count(),
    }
    return render(request, 'services/professionals_list.html', contexto)


@login_required
@require_http_methods(GET_POST)
def professional_create(request):
    if not request.user.is_admin:
        messages.error(request, 'Solo un administrador puede registrar nuevos profesionales.')
        return redirect(URL_PROFESIONALES)

    if request.method == 'POST':
        form = ProfessionalForm(request.POST)
        if form.is_valid():
            prof = form.save()
            messages.success(request, f'Profesional «{prof.name}» registrado correctamente.')
            return redirect(URL_PROFESIONALES)
    else:
        form = ProfessionalForm(initial={'color_tag': '#0D9488', 'is_active': True})

    return render(request, 'services/professional_form.html', {
        'form': form,
        'titulo': 'Nuevo profesional',
    })


@login_required
@require_http_methods(GET_POST)
def professional_update(request, pk):
    prof = get_object_or_404(Professional.objects.select_related('user'), pk=pk)

    if not request.user.is_admin:
        messages.error(request, 'Solo un administrador puede editar la información de profesionales.')
        return redirect(URL_PROFESIONALES)

    if request.method == 'POST':
        form = ProfessionalForm(request.POST, instance=prof)
        if form.is_valid():
            prof = form.save()
            messages.success(request, f'Los datos del profesional «{prof.name}» se actualizaron correctamente.')
            return redirect(URL_PROFESIONALES)
    else:
        form = ProfessionalForm(instance=prof)

    return render(request, 'services/professional_form.html', {
        'form': form,
        'titulo': f'Editar profesional — {prof.name}',
        'profesional': prof,
    })


@login_required
@require_http_methods(GET_POST)
def professional_delete(request, pk):
    prof = get_object_or_404(Professional.objects.select_related('user'), pk=pk)

    if not request.user.is_admin:
        messages.error(request, 'Solo un administrador puede eliminar o desactivar profesionales.')
        return redirect(URL_PROFESIONALES)

    num_citas = prof.appointments.count()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # Caso A: Desactivar profesional (con o sin citas)
        if accion == 'desactivar':
            prof.is_active = False
            prof.save()
            messages.success(request, f'Profesional «{prof.name}» desactivado. Ya no se agendarán nuevas citas para él.')
            return redirect(URL_PROFESIONALES)

        # Caso B: Eliminar permanentemente
        if num_citas > 0:
            messages.error(
                request,
                f'No es posible eliminar permanentemente a «{prof.name}» porque tiene {num_citas} cita(s) '
                f'registrada(s) en la agenda. Puedes desactivarlo para conservar el historial.'
            )
            return redirect(URL_PROFESIONALES)

        nombre = prof.name
        user = prof.user
        prof.delete()
        if user and not user.is_superuser:
            user.delete()

        messages.success(request, f'Profesional «{nombre}» eliminado definitivamente del sistema.')
        return redirect(URL_PROFESIONALES)

    return render(request, 'services/professional_confirm_delete.html', {
        'profesional': prof,
        'num_citas': num_citas,
    })


@login_required
@require_POST
def professional_toggle_status(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Solo un administrador puede cambiar el estado de los profesionales.')
        return redirect(URL_PROFESIONALES)

    prof = get_object_or_404(Professional, pk=pk)
    prof.is_active = not prof.is_active
    prof.save()

    estado_txt = 'activado' if prof.is_active else 'desactivado'
    messages.success(request, f'El profesional «{prof.name}» ha sido {estado_txt}.')
    return redirect(URL_PROFESIONALES)
