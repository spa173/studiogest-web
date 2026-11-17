from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información de StudioGest', {
            'fields': ('role', 'phone')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información de StudioGest', {
            'fields': ('role', 'phone', 'email')
        }),
    )
    privileged_fields = {'role', 'is_staff', 'is_superuser', 'groups', 'user_permissions'}

    def _filter_fieldsets(self, fieldsets):
        filtered = []
        for name, options in fieldsets:
            fields = options.get('fields', ())
            new_fields = tuple(field for field in fields if field not in self.privileged_fields)
            if new_fields:
                new_options = {**options, 'fields': new_fields}
                filtered.append((name, new_options))
        return tuple(filtered)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets
        return self._filter_fieldsets(fieldsets)

    def get_add_fieldsets(self, request):
        # Compatible con Django 5 BaseUserAdmin, que expone add_fieldsets por defecto.
        fieldsets = getattr(super(), 'get_add_fieldsets', lambda req: self.add_fieldsets)(request)
        if request.user.is_superuser:
            return fieldsets
        return self._filter_fieldsets(fieldsets)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            for field in self.privileged_fields:
                if field not in readonly:
                    readonly.append(field)
        return tuple(readonly)
