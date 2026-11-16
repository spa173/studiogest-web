from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'phone', 'email', 'is_vip', 'data_consent',
        'data_consent_at', 'data_consent_method', 'data_consent_recorded_by', 'created_at',
    )
    list_filter = ('is_vip', 'data_consent', 'data_consent_method', 'created_at')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('data_consent_at', 'data_consent_recorded_by', 'created_at')
    fieldsets = (
        ('Cliente', {
            'fields': ('name', 'phone', 'email', 'notes', 'is_vip', 'created_at'),
        }),
        ('Autorización de datos personales', {
            'fields': (
                'data_consent', 'data_consent_method', 'data_consent_at',
                'data_consent_recorded_by', 'data_consent_notes',
            ),
        }),
    )

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
