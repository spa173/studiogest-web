from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.permissions import can_manage_sales

from .forms import CashRegisterSessionCloseForm, CashRegisterSessionForm, SaleDetailForm, SaleForm
from .models import CashRegisterSession, PaymentMethod, Sale, SaleStatus
from .services import cancel_sale, create_sale


def _cash_sessions(user):
    return CashRegisterSession.objects.filter(business_id=user.business_id)


def _sales(user):
    return Sale.objects.filter(business_id=user.business_id)


def _render_sales(request, template, context=None, **kwargs):
    return render(request, template, {
        **(context or {}),
        'panel_business': request.user.business,
    }, **kwargs)


def _cash_session_totals(session):
    sales = session.sales.filter(status=SaleStatus.REGISTERED, business_id=session.business_id).select_related('customer', 'user')
    totals = {
        'cash': sum((s.total for s in sales if s.payment_method == PaymentMethod.CASH), Decimal('0')),
        'card': sum((s.total for s in sales if s.payment_method == PaymentMethod.CARD), Decimal('0')),
        'transfer': sum((s.total for s in sales if s.payment_method == PaymentMethod.TRANSFER), Decimal('0')),
    }
    sales_total = totals['cash'] + totals['card'] + totals['transfer']
    expected_cash = session.opening_cash + totals['cash']
    grand_total = sales_total + session.opening_cash
    return sales, totals, sales_total, expected_cash, grand_total


@login_required
@require_GET
def sales_index(request):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    open_sessions = _cash_sessions(request.user).filter(status=CashRegisterSession.Status.OPEN).order_by('-opened_at')
    recent_sales = _sales(request.user).select_related('customer', 'user').order_by('-created_at')[:10]
    return _render_sales(request, 'sales/index.html', {
        'open_sessions': open_sessions,
        'recent_sales': recent_sales,
    })


@login_required
@require_GET
def cash_session_history(request):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    sessions = _cash_sessions(request.user).select_related('opened_by').order_by('-opened_at', '-pk')
    session_rows = []
    for session in sessions:
        _sales, totals, sales_total, expected_cash, _grand_total = _cash_session_totals(session)
        session_rows.append({
            'session': session,
            'totals': totals,
            'sales_total': sales_total,
            'expected_cash': expected_cash,
            'sales_count': _sales.count(),
        })
    return _render_sales(request, 'sales/cash_session_history.html', {
        'session_rows': session_rows,
    })


@login_required
@require_GET
def sale_create(request):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    if not _cash_sessions(request.user).filter(status=CashRegisterSession.Status.OPEN).exists():
        messages.warning(request, 'Debes abrir una sesión de caja antes de registrar ventas.')
        return redirect('sales:cash_open')
    form = SaleForm(business_id=request.user.business_id)
    formset = SaleDetailFormSet(prefix='details', form_kwargs={'business_id': request.user.business_id})
    return _render_sales(request, 'sales/sale_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Registrar venta',
    })


SaleDetailFormSet = formset_factory(SaleDetailForm, extra=1, can_delete=True)


def _collect_sale_details(formset):
    details = []
    for detail_form in formset:
        cleaned = detail_form.cleaned_data
        if not cleaned or cleaned.get('DELETE'):
            continue
        details.append({
            'type': cleaned['detail_type'],
            'service': cleaned.get('service'),
            'product': cleaned.get('product'),
            'quantity': cleaned['quantity'],
            'unit_price': cleaned['unit_price'],
        })
    return details


@login_required
@require_POST
def sale_store(request):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    if not _cash_sessions(request.user).filter(status=CashRegisterSession.Status.OPEN).exists():
        messages.warning(request, 'Debes abrir una sesión de caja antes de registrar ventas.')
        return redirect('sales:cash_open')

    business_id = request.user.business_id
    form = SaleForm(request.POST, business_id=business_id)
    formset = SaleDetailFormSet(request.POST, prefix='details', form_kwargs={'business_id': business_id})
    if form.is_valid() and formset.is_valid():
        details = _collect_sale_details(formset)
        if not details:
            form.add_error(None, 'Agrega al menos un detalle a la venta.')
        else:
            try:
                sale = create_sale(
                    user=request.user,
                    payment_method=form.cleaned_data['payment_method'],
                    customer=form.cleaned_data.get('customer'),
                    appointment=form.cleaned_data.get('appointment'),
                    cash_session=form.cleaned_data.get('cash_session'),
                    notes=form.cleaned_data.get('notes', ''),
                    details=details,
                )
                messages.success(request, f'Venta #{sale.pk} registrada correctamente.')
                return redirect('sales:index')
            except ValidationError as error:
                form.add_error(None, error.messages)

    return _render_sales(request, 'sales/sale_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Registrar venta',
    })


@login_required
@require_GET
def cash_session_open(request):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    form = CashRegisterSessionForm()
    return _render_sales(request, 'sales/cash_session_open.html', {'form': form})


@login_required
@require_POST
def cash_session_store(request):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    form = CashRegisterSessionForm(request.POST)
    if form.is_valid():
        session = form.save(commit=False)
        session.opened_by = request.user
        session.business_id = request.user.business_id
        session.save()
        messages.success(request, 'Sesión de caja abierta correctamente.')
        return redirect('sales:index')
    return _render_sales(request, 'sales/cash_session_open.html', {'form': form})


@login_required
@require_GET
def cash_session_close(request, pk):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    session = get_object_or_404(_cash_sessions(request.user), pk=pk)
    sales, totals, sales_total, expected_cash, grand_total = _cash_session_totals(session)
    close_form = None
    if session.is_open:
        initial = {}
        if session.counted_cash is not None:
            initial['counted_cash'] = session.counted_cash
        close_form = CashRegisterSessionCloseForm(initial=initial)
    return _render_sales(request, 'sales/cash_session_close.html', {
        'session': session,
        'sales': sales,
        'totals': totals,
        'sales_total': sales_total,
        'expected_cash': expected_cash,
        'grand_total': grand_total,
        'close_form': close_form,
    })


@login_required
@require_GET
def sale_receipt(request, pk):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    sale = get_object_or_404(
        _sales(request.user).select_related(
            'customer', 'appointment', 'user', 'cash_session', 'business',
        ).prefetch_related(
            'details__service', 'details__product',
        ),
        pk=pk,
    )
    response = _render_sales(request, 'sales/sale_receipt.html', {'sale': sale})
    response['Cache-Control'] = 'private, no-store, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


@login_required
@require_POST
@transaction.atomic
def cash_session_finalize(request, pk):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    session = get_object_or_404(_cash_sessions(request.user).select_for_update(), pk=pk)
    if session.status == CashRegisterSession.Status.CLOSED:
        messages.info(request, 'La sesión ya está cerrada.')
        return redirect('sales:index')

    form = CashRegisterSessionCloseForm(request.POST)
    sales, totals, sales_total, expected_cash, grand_total = _cash_session_totals(session)
    if not form.is_valid():
        return _render_sales(request, 'sales/cash_session_close.html', {
            'session': session,
            'sales': sales,
            'totals': totals,
            'sales_total': sales_total,
            'expected_cash': expected_cash,
            'grand_total': grand_total,
            'close_form': form,
        })

    counted_cash = form.cleaned_data['counted_cash']
    session.counted_cash = counted_cash
    session.cash_difference = counted_cash - expected_cash
    session.status = CashRegisterSession.Status.CLOSED
    session.closed_at = timezone.now()
    session.save(update_fields=['counted_cash', 'cash_difference', 'status', 'closed_at'])
    messages.success(request, 'Sesión de caja cerrada correctamente.')
    return redirect('sales:index')


@login_required
@require_POST
def sale_cancel(request, pk):
    if not can_manage_sales(request.user):
        return _render_sales(request, 'sales/forbidden.html', status=403)
    sale = get_object_or_404(_sales(request.user), pk=pk)
    try:
        cancel_sale(sale=sale, user=request.user)
        messages.success(request, f'Venta #{sale.pk} anulada correctamente.')
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    return redirect('sales:index')
