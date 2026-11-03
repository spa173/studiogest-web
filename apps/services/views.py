from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Professional, Service


@login_required
@require_GET
def service_list(request):
    services = Service.objects.all().order_by('name')
    return render(request, 'services/list.html', {'services': services})


@login_required
@require_GET
def professionals_list(request):
    professionals = Professional.objects.select_related('user').all()
    return render(request, 'services/professionals_list.html', {'professionals': professionals})
