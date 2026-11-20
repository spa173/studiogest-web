from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import DemoRequestForm
from .models import DemoRequest


@require_POST
def demo_request(request):
    form = DemoRequestForm(request.POST)
    if not form.is_valid():
        return render(request, 'landing.html', {'demo_form': form})

    data = form.cleaned_data.copy()
    if not data.pop('website'):
        DemoRequest.objects.get_or_create(request_id=data.pop('request_id'), defaults=data)

    messages.success(request, 'Recibimos tu solicitud de demostración.', extra_tags='demo-request')
    return redirect(f"{reverse('root')}#demo")
