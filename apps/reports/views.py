from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.views.decorators.http import require_GET

from appointments.models import Appointment
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
        context.update({
            'summary': summary,
            'start_date': start,
            'end_date': end,
            # Agrupar por ID evita mezclar servicios distintos con el mismo nombre.
            'popular_services': appointments.order_by().values('service_id', 'service__name')
                .annotate(total=Count('pk')).order_by('-total', 'service__name', 'service_id'),
        })
    return render(request, 'reports/index.html', context)
