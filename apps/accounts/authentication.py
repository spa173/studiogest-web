from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django_otp import DEVICE_ID_SESSION_KEY


ADMIN_LOGIN_USER = 'django_admin_login_user'
ADMIN_ALERT = 'django_admin_access_alerted'


def has_admin_login(request):
    user = request.user
    return (
        user.is_active and user.is_staff and user.is_admin
        and request.session.get(ADMIN_LOGIN_USER) == str(user.pk)
    )


@receiver(user_logged_in)
def register_admin_login(sender, request, user, **kwargs):
    match = getattr(request, 'resolver_match', None)
    if not match or match.view_name != 'admin:login' or request.method != 'POST':
        return
    if user.is_active and user.is_staff and user.is_admin:
        request.session.cycle_key()
        request.session[ADMIN_LOGIN_USER] = str(user.pk)
        request.session.pop(DEVICE_ID_SESSION_KEY, None)
        request.session.pop(ADMIN_ALERT, None)


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or '@' not in username or password is None:
            return None
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email__iexact=username)
        except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
            user_model().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


class AdminLoginForm(AdminAuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Correo electrónico o usuario'
