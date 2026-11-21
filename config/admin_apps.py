from django.contrib.admin.apps import AdminConfig


class StudioGestAdminConfig(AdminConfig):
    default_site = 'config.admin_site.StudioGestAdminSite'
