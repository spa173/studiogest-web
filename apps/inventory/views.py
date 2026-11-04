from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import ProductRegistrationForm
from .models import Product, StockEntry
from .services import operation_token, request_fingerprint, save_registration, verify_token


@login_required
@require_GET
def product_list(request):
    products = Product.objects.annotate(has_entries=Exists(StockEntry.objects.filter(product_id=OuterRef('pk'))))
    if not request.user.is_admin:
        products = products.defer('acquisition_cost')
    return render(request, 'inventory/list.html', {'products': products})


@login_required
@require_http_methods(['GET', 'POST'])
def register_product(request, pk=None, mode='new'):
    if not request.user.is_admin:
        raise PermissionDenied('Solo los administradores pueden registrar productos y actualizar sus datos y precios.')
    product = None
    if pk:
        product = get_object_or_404(Product, pk=pk)
    data = None
    if request.method == 'POST':
        data = request.POST
    form = ProductRegistrationForm(data, product=product, mode=mode,
                                   initial={'operation_token': operation_token(request.user, product, mode)})
    if request.method == 'POST':
        response = _handle_registration_post(request, form, product, mode)
        if response is not None:
            return response
    return render(request, 'inventory/form.html', {'form': form, 'product': product, 'mode': mode})


def _duplicate_registration_response(request):
    messages.info(request, 'Este registro ya estaba guardado. No se volvió a aumentar el stock.')
    return redirect('inventory:history')


def _registration_success_message(mode, created):
    if mode == 'edit':
        return 'Datos y precios actualizados sin cambiar existencias.'
    if not created:
        return 'El registro ya estaba guardado.'
    if mode == 'new':
        return 'Producto registrado con su saldo inicial.'
    return 'Entrada registrada y existencias actualizadas.'


def _save_registration_form(request, form, product, mode, key, fingerprint):
    try:
        _, created = save_registration(data=form.cleaned_data, user=request.user, key=key,
                                      fingerprint=fingerprint, product=product, mode=mode)
    except IntegrityError as error:
        duplicate = StockEntry.objects.filter(operation_key=key, created_by=request.user,
                                              request_fingerprint=fingerprint).exists()
        if duplicate:
            return _duplicate_registration_response(request)
        raise ValidationError('No se pudo guardar: el código o la operación ya existen. Revisa el inventario.') from error
    messages.success(request, _registration_success_message(mode, created))
    return redirect('inventory:list')


def _process_registration_post(request, form, product, mode):
    key = verify_token(request.POST.get('operation_token'), request.user, product, mode)
    fingerprint = request_fingerprint(request.POST)
    previous = StockEntry.objects.filter(operation_key=key).first()
    if previous:
        if previous.request_fingerprint != fingerprint or previous.created_by_id != request.user.pk:
            raise ValidationError('Esta operación ya se registró con otros datos. Abre un formulario nuevo.')
        return _duplicate_registration_response(request)
    if not form.is_valid():
        return None
    return _save_registration_form(request, form, product, mode, key, fingerprint)


def _handle_registration_post(request, form, product, mode):
    try:
        return _process_registration_post(request, form, product, mode)
    except ValidationError as error:
        form.is_valid()
        form.add_error(None, error.messages)
    except OperationalError:
        form.is_valid()
        form.add_error(None, 'La base de datos está ocupada. Intenta guardar otra vez; no se registró una entrada parcial.')
    return None


@login_required
@require_GET
def entry_history(request):
    if not request.user.is_admin:
        raise PermissionDenied('El historial de inventario está reservado para administradores.')
    entries = StockEntry.objects.select_related('product', 'created_by')
    return render(request, 'inventory/history.html', {'page': Paginator(entries, 25).get_page(request.GET.get('page'))})
