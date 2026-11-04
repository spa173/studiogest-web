import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ProfessionalForm
from .models import Professional, Service

POR_PAGINA = 10
URL_PROFESIONALES = 'services:professionals_list'
METODOS_FORM = ['GET', 'POST']


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
def service_list(request):
    services = Service.objects.all().order_by('name')
    return render(request, 'services/list.html', {'services': services})


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
@require_http_methods(METODOS_FORM)
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
@require_http_methods(METODOS_FORM)
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
@require_http_methods(METODOS_FORM)
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
