import csv
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from openpyxl import Workbook

from accounts.permissions import can_view_reports
from appointments.models import Appointment
from inventory.models import Product
from sales.models import Sale, SaleDetail, SaleDetailType, SaleStatus

from .forms import ReportDateFilterForm

REPORT_TITLE = 'Reporte StudioGest'
PERIOD_LABEL = 'Período'
TOTAL_COP_LABEL = 'Total (COP)'
NO_DATA_LABEL = 'Sin datos'


def _filter_by_dates(queryset, field, start, end):
    if start:
        queryset = queryset.filter(**{f'{field}__gte': start})
    if end:
        queryset = queryset.filter(**{f'{field}__lte': end})
    return queryset


def _build_summary(appointments):
    summary = appointments.aggregate(
        total=Count('pk'),
        completed=Count('pk', filter=Q(status=Appointment.Status.COMPLETED)),
        cancelled=Count('pk', filter=Q(status=Appointment.Status.CANCELLED)),
        estimated_income=Sum('price_cop', filter=Q(status=Appointment.Status.COMPLETED)),
    )
    income = summary['estimated_income'] or Decimal('0')
    summary['estimated_income'] = income
    summary['estimated_income_formatted'] = f'${income:,.0f} COP'.replace(',', '.')
    return summary


def _build_sales_data(business_id, start, end):
    sales = Sale.objects.filter(business_id=business_id, status=SaleStatus.REGISTERED)
    sales_qs = _filter_by_dates(sales, 'created_at__date', start, end)
    sales_summary = sales_qs.aggregate(total=Sum('total'), count=Count('pk'))
    sales_summary['total'] = sales_summary['total'] or Decimal('0')
    sales_by_payment = list(sales_qs.values('payment_method').annotate(
        total=Sum('total'), count=Count('pk')
    ).order_by('payment_method'))
    popular_products = list(SaleDetail.objects.filter(
        sale__in=sales_qs, detail_type=SaleDetailType.PRODUCT,
        product__isnull=False, product__business_id=business_id,
    ).values('product__name').annotate(
        quantity=Sum('quantity'), total=Sum('subtotal'),
    ).order_by('-quantity', 'product__name')[:10])
    return sales_summary, sales_by_payment, popular_products


def _build_report_data(export, start, end, business):
    business_id = business.pk if business else None
    scoped_appointments = Appointment.objects.filter(
        business_id=business_id, service__business_id=business_id,
        customer__business_id=business_id, professional__business_id=business_id,
    )
    appointments = _filter_by_dates(scoped_appointments, 'date', start, end)
    summary = _build_summary(appointments)
    sales_summary, sales_by_payment, popular_products = _build_sales_data(business_id, start, end)
    low_stock = list(Product.objects.filter(
        business_id=business_id,
        is_active=True, stock__lte=F('minimum_stock'),
    ).order_by('stock', 'name')[:10])
    popular_services = list(appointments.order_by().values('service_id', 'service__name').annotate(
        total=Count('pk')
    ).order_by('-total', 'service__name', 'service_id'))
    data = {
        'report_title': f'{REPORT_TITLE} — {business.name}' if business else REPORT_TITLE,
        'start': start, 'end': end, 'summary': summary, 'popular_services': popular_services,
        'sales_summary': sales_summary, 'sales_by_payment': sales_by_payment,
        'popular_products': popular_products, 'low_stock': low_stock,
    }
    if export == 'csv':
        return _export_csv(**data), None
    if export in ('xlsx', 'excel'):
        return _export_xlsx(**data), None
    return None, data


@login_required
@require_GET
@never_cache
def report_index(request):
    business = request.user.business
    context = {'panel_business': business}
    if not can_view_reports(request.user):
        return render(request, 'reports/forbidden.html', context, status=403)

    form = ReportDateFilterForm(request.GET)
    context['form'] = form
    if form.is_valid():
        export = request.GET.get('export')
        start = form.cleaned_data['start_date']
        end = form.cleaned_data['end_date']
        response, data = _build_report_data(export, start, end, business)
        if response is not None:
            return response
        context.update({
            'summary': data['summary'],
            'start_date': start,
            'end_date': end,
            # Agrupar por ID evita mezclar servicios distintos con el mismo nombre.
            'popular_services': data['popular_services'],
            'sales_summary': data['sales_summary'],
            'sales_by_payment': data['sales_by_payment'],
            'popular_products': data['popular_products'],
            'low_stock': data['low_stock'],
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


def _csv_catalog_label(value):
    # Quote text that spreadsheet editors could otherwise interpret as a formula.
    if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
        return "'" + value
    return value


def _csv_section(writer, title):
    writer.writerow([])
    writer.writerow([title])


def _csv_table(writer, title, header, rows, empty_row):
    _csv_section(writer, title)
    writer.writerow(header)
    if rows:
        for row in rows:
            writer.writerow(row)
    else:
        writer.writerow(empty_row)


def _sheet_header(ws, period, report_title):
    ws.append([report_title])
    ws.append([PERIOD_LABEL, period])
    ws.append([])


def _sheet_table(ws, title, period, header, rows, empty_row, report_title):
    ws.title = title
    _sheet_header(ws, period, report_title)
    ws.append(header)
    if rows:
        for row_number, row in enumerate(rows, start=ws.max_row + 1):
            for column, value in enumerate(row, start=1):
                cell = ws.cell(row=row_number, column=column, value=value)
                if isinstance(value, str):
                    cell.data_type = 's'
    else:
        ws.append(empty_row)


def _export_csv(*, report_title, start, end, summary, popular_services, sales_summary, sales_by_payment,
                popular_products, low_stock):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{_report_filename(start, end, "csv")}"'
    response.write('\ufeff')
    writer = csv.writer(response)
    period = _period_label(start, end)
    writer.writerow([report_title])
    writer.writerow([PERIOD_LABEL, period])

    _csv_table(
        writer, 'Resumen de citas', ['Indicador', 'Valor'],
        [
            ['Total de citas', summary['total']],
            ['Citas completadas', summary['completed']],
            ['Citas canceladas', summary['cancelled']],
            ['Ingresos estimados (citas completadas, COP)', summary['estimated_income']],
        ],
        [NO_DATA_LABEL, 0],
    )
    _csv_table(
        writer, 'Servicios más solicitados', ['Servicio', 'Citas registradas'],
        [[_csv_catalog_label(row['service__name']), row['total']] for row in popular_services],
        [NO_DATA_LABEL, 0],
    )

    _csv_section(writer, 'Ventas registradas')
    writer.writerow(['Indicador', 'Valor'])
    writer.writerow(['Cantidad de ventas', sales_summary['count'] or 0])
    writer.writerow(['Total cobrado (COP)', sales_summary['total']])
    writer.writerow([])
    _csv_table(
        writer, 'Ventas por medio de pago', ['Medio de pago', 'Ventas', TOTAL_COP_LABEL],
        [[row['payment_method'], row['count'], row['total']] for row in sales_by_payment],
        ['Sin ventas registradas', 0, 0],
    )
    _csv_table(
        writer, 'Productos más vendidos', ['Producto', 'Cantidad', TOTAL_COP_LABEL],
        [[_csv_catalog_label(row['product__name']), row['quantity'], row['total']] for row in popular_products],
        ['Sin productos vendidos', 0, 0],
    )
    _csv_section(writer, 'Productos con stock bajo')
    writer.writerow(['Producto', 'Stock', 'Stock mínimo'])
    if low_stock:
        for p in low_stock:
            writer.writerow([_csv_catalog_label(p.name), p.stock, p.minimum_stock])
    else:
        writer.writerow(['Sin productos con stock bajo', '', ''])
    return response


def _export_xlsx(*, report_title, start, end, summary, popular_services, sales_summary, sales_by_payment,
                 popular_products, low_stock):
    wb = Workbook()
    period = _period_label(start, end)

    ws = wb.active
    _sheet_table(
        ws, 'Resumen citas', period, ['Indicador', 'Valor'],
        [
            ['Total de citas', summary['total']],
            ['Citas completadas', summary['completed']],
            ['Citas canceladas', summary['cancelled']],
            ['Ingresos estimados (citas completadas, COP)', summary['estimated_income']],
        ],
        [NO_DATA_LABEL, 0],
        report_title,
    )
    _sheet_table(
        wb.create_sheet('Servicios'), 'Servicios', period, ['Servicio', 'Citas registradas'],
        [[row['service__name'], row['total']] for row in popular_services],
        [NO_DATA_LABEL, 0],
        report_title,
    )

    ws_sales = wb.create_sheet('Ventas')
    _sheet_header(ws_sales, period, report_title)
    ws_sales.append(['Indicador', 'Valor'])
    ws_sales.append(['Cantidad de ventas', sales_summary['count'] or 0])
    ws_sales.append(['Total cobrado (COP)', sales_summary['total'] or Decimal('0')])
    ws_sales.append([])
    ws_sales.append(['Medio de pago', 'Ventas', TOTAL_COP_LABEL])
    if sales_by_payment:
        for row in sales_by_payment:
            ws_sales.append([row['payment_method'], row['count'], row['total']])
    else:
        ws_sales.append(['Sin ventas registradas', 0, 0])

    _sheet_table(
        wb.create_sheet('Productos vendidos'), 'Productos vendidos', period,
        ['Producto', 'Cantidad', TOTAL_COP_LABEL],
        [[row['product__name'], row['quantity'], row['total']] for row in popular_products],
        ['Sin productos vendidos', 0, 0],
        report_title,
    )
    _sheet_table(
        wb.create_sheet('Stock bajo'), 'Stock bajo', period,
        ['Producto', 'Stock', 'Stock mínimo'],
        [[p.name, p.stock, p.minimum_stock] for p in low_stock],
        ['Sin productos con stock bajo', '', ''],
        report_title,
    )

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{_report_filename(start, end, "xlsx")}"'
    return response
