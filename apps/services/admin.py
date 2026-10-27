from django.contrib import admin
from .models import Service, Professional


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_minutes', 'price_cop', 'is_active', 'created_at')
    list_filter = ('is_active', 'duration_minutes')
    search_fields = ('name', 'description')


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'color_tag', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'specialty')
