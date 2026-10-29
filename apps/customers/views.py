import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CustomerForm
from .models import Customer

POR_PAGINA = 10
URL_LISTA = 'customers:list'
GET_POST = ['GET', 'POST']


def _enlace_whatsapp(telefono):
    """Devuelve el enlace de WhatsApp (asume Colombia, +57, si hay 10 dígitos)."""
    digitos = re.sub(r'\D', '', telefono)
    if len(digitos) == 10:
        digitos = '57' + digitos
    return f'https://wa.me/{digitos}'


@login_required
@require_GET
def customer_list(request):
    texto = request.GET.get('q', '').strip()
    solo_vip = request.GET.get('vip') == '1'

    clientes = Customer.objects.annotate(num_citas=Count('appointments')).order_by('name')
    if texto:
        clientes = clientes.filter(
            Q(name__icontains=texto) | Q(phone__icontains=texto) | Q(email__icontains=texto)
        )
    if solo_vip:
        clientes = clientes.filter(is_vip=True)

    pagina = Paginator(clientes, POR_PAGINA).get_page(request.GET.get('page'))
    for cliente in pagina:
        cliente.whatsapp = _enlace_whatsapp(cliente.phone)

    contexto = {
        'pagina': pagina,
        'q': texto,
        'solo_vip': solo_vip,
        'total_clientes': Customer.objects.count(),
        'total_vip': Customer.objects.filter(is_vip=True).count(),
    }
    return render(request, 'customers/list.html', contexto)


@login_required
@require_http_methods(GET_POST)
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente «{cliente.name}» registrado correctamente.')
            return redirect(URL_LISTA)
    else:
        form = CustomerForm()
    return render(request, 'customers/form.html', {'form': form, 'titulo': 'Nuevo cliente'})


@login_required
@require_http_methods(GET_POST)
def customer_update(request, pk):
    cliente = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Los datos de «{cliente.name}» se actualizaron.')
            return redirect(URL_LISTA)
    else:
        form = CustomerForm(instance=cliente)
    return render(request, 'customers/form.html',
                  {'form': form, 'titulo': 'Editar cliente', 'cliente': cliente})


@login_required
@require_http_methods(GET_POST)
def customer_delete(request, pk):
    cliente = get_object_or_404(Customer, pk=pk)

    # Solo el administrador puede eliminar clientes
    if not request.user.is_admin:
        messages.error(request, 'Solo un administrador puede eliminar clientes.')
        return redirect(URL_LISTA)

    # Eliminar un cliente borraría también sus citas, así que se bloquea
    num_citas = cliente.appointments.count()
    if num_citas:
        messages.error(
            request,
            f'No se puede eliminar a «{cliente.name}» porque tiene {num_citas} cita(s) registrada(s).'
        )
        return redirect(URL_LISTA)

    if request.method == 'POST':
        nombre = cliente.name
        cliente.delete()
        messages.success(request, f'Cliente «{nombre}» eliminado.')
        return redirect(URL_LISTA)
    return render(request, 'customers/confirm_delete.html', {'cliente': cliente})
