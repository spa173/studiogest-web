from django.contrib import admin

from .models import Professional, Service


class BusinessAdminAccessMixin:
    def _is_business_admin(self, request):
        return request.user.is_active and getattr(request.user, 'is_admin', False)

    def has_module_permission(self, request):
        return self._is_business_admin(request)

    def has_view_permission(self, request, obj=None):
        del obj
        return self._is_business_admin(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        del obj
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        del obj
        return self.has_module_permission(request)


@admin.register(Service)
class ServiceAdmin(BusinessAdminAccessMixin, admin.ModelAdmin):
    list_display = ('name', 'duration_minutes', 'price_cop', 'is_active', 'created_at')
    list_filter = ('is_active', 'duration_minutes')
    search_fields = ('name', 'description')


@admin.register(Professional)
class ProfessionalAdmin(BusinessAdminAccessMixin, admin.ModelAdmin):
    list_display = ('name', 'specialty', 'work_start_time', 'work_end_time', 'color_tag', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'specialty')
    fields = ('user', 'specialty', 'work_start_time', 'work_end_time', 'color_tag', 'is_active')
