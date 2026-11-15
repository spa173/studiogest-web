from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'customer', 'service', 'professional', 'status', 'price_cop')
    list_filter = ('status', 'date', 'professional', 'service')
    search_fields = ('customer__name', 'customer__phone', 'professional__user__first_name', 'notes')

    def _is_business_admin(self, request):
        return request.user.is_active and getattr(request.user, 'is_admin', False)

    def has_module_permission(self, request):
        return self._is_business_admin(request)

    def has_view_permission(self, request, obj=None):
        return self._is_business_admin(request)

    def has_add_permission(self, request):
        return self._is_business_admin(request)

    def has_change_permission(self, request, obj=None):
        return self._is_business_admin(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_business_admin(request)

    def get_readonly_fields(self, request, obj=None):
        if not self._is_business_admin(request):
            return ['price_cop', 'catalog_price_cop', 'adjusted_price_cop', 'discount_type',
                    'discount_value', 'discount_amount_cop', 'pricing_reason']
        return []
