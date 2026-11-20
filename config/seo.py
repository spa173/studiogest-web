from django.conf import settings


def public_site(request):
    return {'public_site_origin': settings.PUBLIC_SITE_ORIGIN}
