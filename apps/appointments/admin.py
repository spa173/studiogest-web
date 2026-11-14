from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_admin:
            return ('price_cop', 'catalog_price_cop', 'adjusted_price_cop', 'discount_type',
                    'discount_value', 'discount_amount_cop', 'pricing_reason')
        return ()

    list_display = ('date', 'start_time', 'end_time', 'customer', 'service', 'professional', 'status', 'price_cop')
    list_filter = ('status', 'date', 'professional', 'service')
    search_fields = ('customer__name', 'customer__phone', 'professional__user__first_name', 'notes')
