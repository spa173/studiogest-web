from django.contrib import admin

from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'business_name', 'name', 'email')
    search_fields = ('business_name', 'name', 'email')
    readonly_fields = ('request_id', 'name', 'business_name', 'email', 'phone', 'message', 'contact_consent', 'created_at')

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
