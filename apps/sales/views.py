from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import CashRegisterSessionForm, SaleDetailForm, SaleForm
from .models import CashRegisterSession, Sale, SaleStatus
from .services import create_sale


def _can_manage_sales(user):
    return user.is_authenticated and (user.is_admin or getattr(user, 'is_cashier', False))


@login_required
@require_GET
def sales_index(request):
    if not _can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    open_sessions = CashRegisterSession.objects.filter(status=CashRegisterSession.Status.OPEN).order_by('-opened_at')
    recent_sales = Sale.objects.select_related('customer', 'user').order_by('-created_at')[:10]
    return render(request, 'sales/index.html', {
        'open_sessions': open_sessions,
        'recent_sales': recent_sales,
    })


@login_required
@require_GET
def sale_create(request):
    if not _can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    form = SaleForm()
    formset = SaleDetailFormSet(prefix='details')
    return render(request, 'sales/sale_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Registrar venta',
    })


SaleDetailFormSet = formset_factory(SaleDetailForm, extra=1, can_delete=True)


@login_required
@require_POST
def sale_store(request):
    if not _can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    form = SaleForm(request.POST)
    formset = SaleDetailFormSet(request.POST, prefix='details')
    if form.is_valid() and formset.is_valid():
        details = []
        for detail_form in formset:
            if not detail_form.cleaned_data or detail_form.cleaned_data.get('DELETE'):
                continue
            details.append({
                'type': detail_form.cleaned_data['detail_type'],
                'service': detail_form.cleaned_data.get('service'),
                'product': detail_form.cleaned_data.get('product'),
                'quantity': detail_form.cleaned_data['quantity'],
                'unit_price': detail_form.cleaned_data['unit_price'],
            })
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
    if not _can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    form = CashRegisterSessionForm()
    return render(request, 'sales/cash_session_open.html', {'form': form})


@login_required
@require_POST
def cash_session_store(request):
    if not _can_manage_sales(request.user):
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
    if not _can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    session = get_object_or_404(CashRegisterSession, pk=pk)
    sales = session.sales.filter(status=SaleStatus.REGISTERED)
    totals = {
        'cash': sum(s.total for s in sales if s.payment_method == 'EFECTIVO'),
        'card': sum(s.total for s in sales if s.payment_method == 'TARJETA'),
        'transfer': sum(s.total for s in sales if s.payment_method == 'TRANSFERENCIA'),
    }
    grand_total = sum(totals.values()) + session.opening_cash
    return render(request, 'sales/cash_session_close.html', {
        'session': session,
        'sales': sales,
        'totals': totals,
        'grand_total': grand_total,
    })


@login_required
@require_POST
def cash_session_finalize(request, pk):
    if not _can_manage_sales(request.user):
        return render(request, 'sales/forbidden.html', status=403)
    session = get_object_or_404(CashRegisterSession, pk=pk)
    if session.status == CashRegisterSession.Status.CLOSED:
        messages.info(request, 'La sesión ya está cerrada.')
        return redirect('sales:index')
    session.status = CashRegisterSession.Status.CLOSED
    session.closed_at = timezone.now()
    session.save(update_fields=['status', 'closed_at'])
    messages.success(request, 'Sesión de caja cerrada correctamente.')
    return redirect('sales:index')