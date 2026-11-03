from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET


@login_required
@require_GET
def sales_index(request):
    if not request.user.is_admin:
        return render(request, 'sales/forbidden.html', status=403)
    return render(request, 'sales/index.html')
