from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_vip', 'created_at')
    list_filter = ('is_vip', 'created_at')
    search_fields = ('name', 'phone', 'email')
