from django.contrib.admin import AdminSite

from accounts.authentication import AdminLoginForm, has_admin_login


class StudioGestAdminSite(AdminSite):
    site_header = 'Administración de StudioGest'
    site_title = 'Administración de StudioGest'
    index_title = 'Panel de administración'
    login_form = AdminLoginForm
    has_permission = staticmethod(has_admin_login)

    def get_app_list(self, request, app_label=None):
        apps = super().get_app_list(request, app_label)
        for app in apps:
            if app['app_label'] == 'otp_totp':
                app['name'] = 'Seguridad'
                for model in app['models']:
                    if model['object_name'] == 'TOTPDevice':
                        model['name'] = 'Autenticadores'
        return apps
