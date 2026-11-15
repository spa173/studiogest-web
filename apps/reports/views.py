import csv
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from openpyxl import Workbook

from appointments.models import Appointment
from inventory.models import Product
from sales.models import Sale, SaleDetail, SaleDetailType, SaleStatus
from accounts.permissions import can_view_reports

from .forms import ReportDateFilterForm


@login_required
@require_GET
def report_index(request):
    if not can_view_reports(request.user):
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
        sales_by_payment = list(sales_qs.values('payment_method').annotate(
            total=Sum('total'), count=Count('pk')
        ).order_by('payment_method'))

        popular_products = list(SaleDetail.objects.filter(
            sale__in=sales_qs, detail_type=SaleDetailType.PRODUCT,
        ).values('product__name').annotate(
            quantity=Sum('quantity'), total=Sum('subtotal'),
        ).order_by('-quantity', 'product__name')[:10])

        low_stock = list(Product.objects.filter(
            is_active=True, stock__lte=F('minimum_stock'),
        ).order_by('stock', 'name')[:10])

        popular_services = list(appointments.order_by().values('service_id', 'service__name')
            .annotate(total=Count('pk')).order_by('-total', 'service__name', 'service_id'))

        export = request.GET.get('export')
        if export == 'csv':
            return _export_csv(
                start=start, end=end, summary=summary, popular_services=popular_services,
                sales_summary=sales_summary, sales_by_payment=sales_by_payment,
                popular_products=popular_products, low_stock=low_stock,
            )
        if export in ('xlsx', 'excel'):
            return _export_xlsx(
                start=start, end=end, summary=summary, popular_services=popular_services,
                sales_summary=sales_summary, sales_by_payment=sales_by_payment,
                popular_products=popular_products, low_stock=low_stock,
            )

        context.update({
            'summary': summary,
            'start_date': start,
            'end_date': end,
            # Agrupar por ID evita mezclar servicios distintos con el mismo nombre.
            'popular_services': popular_services,
            'sales_summary': sales_summary,
            'sales_by_payment': sales_by_payment,
            'popular_products': popular_products,
            'low_stock': low_stock,
        })
    return render(request, 'reports/index.html', context)


def _report_filename(start, end, extension):
    filename = 'reporte_studiogest'
    if start:
        filename += f'_desde_{start:%Y%m%d}'
    if end:
        filename += f'_hasta_{end:%Y%m%d}'
    return f'{filename}.{extension}'


def _period_label(start, end):
    if start or end:
        periodo = f"Desde {start:%d/%m/%Y}" if start else 'Desde inicio'
        if end:
            periodo += f" hasta {end:%d/%m/%Y}"
        return periodo
    return 'Todo el historial'


def _export_csv(*, start, end, summary, popular_services, sales_summary, sales_by_payment,
                popular_products, low_stock):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{_report_filename(start, end, "csv")}"'
    response.write('\ufeff')
    writer = csv.writer(response)

    def section(title):
        writer.writerow([])
        writer.writerow([title])

    writer.writerow(['Reporte StudioGest'])
    writer.writerow(['Período', _period_label(start, end)])

    section('Resumen de citas')
    writer.writerow(['Indicador', 'Valor'])
    writer.writerow(['Total de citas', summary['total']])
    writer.writerow(['Citas completadas', summary['completed']])
    writer.writerow(['Citas canceladas', summary['cancelled']])
    writer.writerow(['Ingresos estimados (citas completadas, COP)', summary['estimated_income']])

    section('Servicios más solicitados')
    writer.writerow(['Servicio', 'Citas registradas'])
    if popular_services:
        for row in popular_services:
            writer.writerow([row['service__name'], row['total']])
    else:
        writer.writerow(['Sin datos', 0])

    section('Ventas registradas')
    writer.writerow(['Indicador', 'Valor'])
    writer.writerow(['Cantidad de ventas', sales_summary['count'] or 0])
    writer.writerow(['Total cobrado (COP)', sales_summary['total']])
    writer.writerow([])
    writer.writerow(['Medio de pago', 'Ventas', 'Total (COP)'])
    if sales_by_payment:
        for row in sales_by_payment:
            writer.writerow([row['payment_method'], row['count'], row['total']])
    else:
        writer.writerow(['Sin ventas registradas', 0, 0])

    section('Productos más vendidos')
    writer.writerow(['Producto', 'Cantidad', 'Total (COP)'])
    if popular_products:
        for row in popular_products:
            writer.writerow([row['product__name'], row['quantity'], row['total']])
    else:
        writer.writerow(['Sin productos vendidos', 0, 0])

    section('Productos con stock bajo')
    writer.writerow(['Producto', 'Stock', 'Stock mínimo'])
    if low_stock:
        for p in low_stock:
            writer.writerow([p.name, p.stock, p.minimum_stock])
    else:
        writer.writerow(['Sin productos con stock bajo', '', ''])

    return response


def _export_xlsx(*, start, end, summary, popular_services, sales_summary, sales_by_payment,
                 popular_products, low_stock):
    wb = Workbook()
    period = _period_label(start, end)

    ws = wb.active
    ws.title = 'Resumen citas'
    ws.append(['Reporte StudioGest'])
    ws.append(['Período', period])
    ws.append([])
    ws.append(['Indicador', 'Valor'])
    ws.append(['Total de citas', summary['total']])
    ws.append(['Citas completadas', summary['completed']])
    ws.append(['Citas canceladas', summary['cancelled']])
    ws.append(['Ingresos estimados (citas completadas, COP)', summary['estimated_income']])

    ws_services = wb.create_sheet('Servicios')
    ws_services.append(['Reporte StudioGest'])
    ws_services.append(['Período', period])
    ws_services.append([])
    ws_services.append(['Servicio', 'Citas registradas'])
    if popular_services:
        for row in popular_services:
            ws_services.append([row['service__name'], row['total']])
    else:
        ws_services.append(['Sin datos', 0])

    ws_sales = wb.create_sheet('Ventas')
    ws_sales.append(['Reporte StudioGest'])
    ws_sales.append(['Período', period])
    ws_sales.append([])
    ws_sales.append(['Indicador', 'Valor'])
    ws_sales.append(['Cantidad de ventas', sales_summary['count'] or 0])
    ws_sales.append(['Total cobrado (COP)', sales_summary['total'] or Decimal('0')])
    ws_sales.append([])
    ws_sales.append(['Medio de pago', 'Ventas', 'Total (COP)'])
    if sales_by_payment:
        for row in sales_by_payment:
            ws_sales.append([row['payment_method'], row['count'], row['total']])
    else:
        ws_sales.append(['Sin ventas registradas', 0, 0])

    ws_products = wb.create_sheet('Productos vendidos')
    ws_products.append(['Reporte StudioGest'])
    ws_products.append(['Período', period])
    ws_products.append([])
    ws_products.append(['Producto', 'Cantidad', 'Total (COP)'])
    if popular_products:
        for row in popular_products:
            ws_products.append([row['product__name'], row['quantity'], row['total']])
    else:
        ws_products.append(['Sin productos vendidos', 0, 0])

    ws_stock = wb.create_sheet('Stock bajo')
    ws_stock.append(['Reporte StudioGest'])
    ws_stock.append(['Período', period])
    ws_stock.append([])
    ws_stock.append(['Producto', 'Stock', 'Stock mínimo'])
    if low_stock:
        for p in low_stock:
            ws_stock.append([p.name, p.stock, p.minimum_stock])
    else:
        ws_stock.append(['Sin productos con stock bajo', '', ''])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{_report_filename(start, end, "xlsx")}"'
    return response
