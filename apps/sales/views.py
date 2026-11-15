from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.permissions import can_manage_sales

from .forms import CashRegisterSessionCloseForm, CashRegisterSessionForm, SaleDetailForm, SaleForm
from .models import CashRegisterSession, PaymentMethod, Sale, SaleStatus
from .services import cancel_sale, create_sale


def _cash_session_totals(session):
    sales = session.sales.filter(status=SaleStatus.REGISTERED).select_related('customer', 'user')
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
        return render(request, 'sales/forbidden.html', status=403)
    open_sessions = CashRegisterSession.objects.filter(status=CashRegisterSession.Status.OPEN).order_by('-opened_at')
    recent_sales = Sale.objects.select_related('customer', 'user').order_by('-created_at')[:10]
    return render(request, 'sales/index.html', {
        'open_sessions': open_sessions,
        'recent_sales': recent_sales,
    })


@login_required
@require_GET
def cash_session_history(request):
    if not can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    sessions = CashRegisterSession.objects.select_related('opened_by').order_by('-opened_at', '-pk')
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
    return render(request, 'sales/cash_session_history.html', {
        'session_rows': session_rows,
    })


@login_required
@require_GET
def sale_create(request):
    if not can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    if not CashRegisterSession.objects.filter(status=CashRegisterSession.Status.OPEN).exists():
        messages.warning(request, 'Debes abrir una sesión de caja antes de registrar ventas.')
        return redirect('sales:cash_open')
    form = SaleForm()
    formset = SaleDetailFormSet(prefix='details')
    return render(request, 'sales/sale_form.html', {
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
        return render(request, 'sales/forbidden.html', status=403)
    if not CashRegisterSession.objects.filter(status=CashRegisterSession.Status.OPEN).exists():
        messages.warning(request, 'Debes abrir una sesión de caja antes de registrar ventas.')
        return redirect('sales:cash_open')

    form = SaleForm(request.POST)
    formset = SaleDetailFormSet(request.POST, prefix='details')
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
            except Exception as exc:
                form.add_error(None, str(exc))

    # Re-render with errors
    formset = SaleDetailFormSet(request.POST, prefix='details')
    return render(request, 'sales/sale_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Registrar venta',
    })


@login_required
@require_GET
def cash_session_open(request):
    if not can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    form = CashRegisterSessionForm()
    return render(request, 'sales/cash_session_open.html', {'form': form})


@login_required
@require_POST
def cash_session_store(request):
    if not can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    form = CashRegisterSessionForm(request.POST)
    if form.is_valid():
        session = form.save(commit=False)
        session.opened_by = request.user
        session.save()
        messages.success(request, 'Sesión de caja abierta correctamente.')
        return redirect('sales:index')
    return render(request, 'sales/cash_session_open.html', {'form': form})


@login_required
@require_GET
def cash_session_close(request, pk):
    if not can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    session = get_object_or_404(CashRegisterSession, pk=pk)
    sales, totals, sales_total, expected_cash, grand_total = _cash_session_totals(session)
    close_form = None
    if session.is_open:
        initial = {}
        if session.counted_cash is not None:
            initial['counted_cash'] = session.counted_cash
        close_form = CashRegisterSessionCloseForm(initial=initial)
    return render(request, 'sales/cash_session_close.html', {
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
        return render(request, 'sales/forbidden.html', status=403)
    sale = get_object_or_404(
        Sale.objects.select_related(
            'customer', 'appointment', 'user', 'cash_session',
        ).prefetch_related(
            'details__service', 'details__product',
        ),
        pk=pk,
    )
    response = render(request, 'sales/sale_receipt.html', {'sale': sale})
    response['Cache-Control'] = 'private, no-store, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


@login_required
@require_POST
@transaction.atomic
def cash_session_finalize(request, pk):
    if not can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    session = get_object_or_404(CashRegisterSession.objects.select_for_update(), pk=pk)
    if session.status == CashRegisterSession.Status.CLOSED:
        messages.info(request, 'La sesión ya está cerrada.')
        return redirect('sales:index')

    form = CashRegisterSessionCloseForm(request.POST)
    sales, totals, sales_total, expected_cash, grand_total = _cash_session_totals(session)
    if not form.is_valid():
        return render(request, 'sales/cash_session_close.html', {
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
        return render(request, 'sales/forbidden.html', status=403)
    sale = get_object_or_404(Sale, pk=pk)
    try:
        cancel_sale(sale=sale, user=request.user)
        messages.success(request, f'Venta #{sale.pk} anulada correctamente.')
    except Exception as exc:
        messages.error(request, str(exc))
    return redirect('sales:index')
