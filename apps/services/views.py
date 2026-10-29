from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Service


@login_required
@require_GET
def service_list(request):
    services = Service.objects.all().order_by('name')
    return render(request, 'services/list.html', {'services': services})
