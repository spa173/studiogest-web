from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.views.decorators.http import require_GET

from appointments.models import Appointment
from inventory.models import Product
from sales.models import Sale, SaleDetail, SaleDetailType, SaleStatus
from django.db.models import F

from .forms import ReportDateFilterForm


@login_required
@require_GET
def report_index(request):
    if not request.user.is_admin:
        return render(request, 'reports/forbidden.html', status=403)

    form = ReportDateFilterForm(request.GET)
    context = {'form': form}
    if form.is_valid():
        appointments = Appointment.objects.all()
        start = form.cleaned_data['start_date']
        end = form.cleaned_data['end_date']
        if start:
            appointments = appointments.filter(date__gte=start)
        if end:
            appointments = appointments.filter(date__lte=end)

        summary = appointments.aggregate(
            total=Count('pk'),
            completed=Count('pk', filter=Q(status=Appointment.Status.COMPLETED)),
            cancelled=Count('pk', filter=Q(status=Appointment.Status.CANCELLED)),
            estimated_income=Sum('price_cop', filter=Q(status=Appointment.Status.COMPLETED)),
        )
        income = summary['estimated_income'] or Decimal('0')
        summary['estimated_income'] = income
        summary['estimated_income_formatted'] = f'${income:,.0f} COP'.replace(',', '.')
        sales_qs = Sale.objects.filter(status=SaleStatus.REGISTERED)
        if start:
            sales_qs = sales_qs.filter(created_at__date__gte=start)
        if end:
            sales_qs = sales_qs.filter(created_at__date__lte=end)

        sales_summary = sales_qs.aggregate(
            total=Sum('total'),
            count=Count('pk'),
        )
        sales_summary['total'] = sales_summary['total'] or Decimal('0')
        sales_by_payment = sales_qs.values('payment_method').annotate(
            total=Sum('total'), count=Count('pk')
        ).order_by('payment_method')

        popular_products = SaleDetail.objects.filter(
            sale__in=sales_qs, detail_type=SaleDetailType.PRODUCT,
        ).values('product__name').annotate(
            quantity=Sum('quantity'), total=Sum('subtotal'),
        ).order_by('-quantity', 'product__name')[:10]

        low_stock = Product.objects.filter(
            is_active=True, stock__lte=F('minimum_stock'),
        ).order_by('stock', 'name')[:10]

        context.update({
            'summary': summary,
            'start_date': start,
            'end_date': end,
            # Agrupar por ID evita mezclar servicios distintos con el mismo nombre.
            'popular_services': appointments.order_by().values('service_id', 'service__name')
                .annotate(total=Count('pk')).order_by('-total', 'service__name', 'service_id'),
            'sales_summary': sales_summary,
            'sales_by_payment': sales_by_payment,
            'popular_products': popular_products,
            'low_stock': low_stock,
        })
    return render(request, 'reports/index.html', context)
