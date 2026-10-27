from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'customer', 'service', 'professional', 'status', 'price_cop')
    list_filter = ('status', 'date', 'professional', 'service')
    search_fields = ('customer__name', 'customer__phone', 'professional__user__first_name', 'notes')
