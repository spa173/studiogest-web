from django.contrib import admin

from .models import Product, StockEntry
from .formatting import money_co, quantity_co


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'base_unit', 'display_stock', 'display_minimum',
                    'display_cost', 'display_sale', 'display_package_sale', 'display_usage', 'is_active')
    list_filter = ('base_unit', 'is_active')
    search_fields = ('code', 'name', 'description')
    fields = ('id', 'code', 'name', 'description', 'presentation', 'base_unit',
              'display_content', 'display_stock', 'display_minimum', 'display_cost',
              'display_sale', 'display_package_sale', 'display_usage', 'display_override', 'is_active')
    readonly_fields = fields
    actions = None

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_admin

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_admin

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Existencia', ordering='stock')
    def display_stock(self, obj):
        return quantity_co(obj.stock, obj.base_unit)

    @admin.display(description='Stock mínimo', ordering='minimum_stock')
    def display_minimum(self, obj):
        return quantity_co(obj.minimum_stock, obj.base_unit)

    @admin.display(description='Contenido por presentación')
    def display_content(self, obj):
        return quantity_co(obj.content_per_presentation, obj.base_unit)

    @admin.display(description='Costo por unidad de control', ordering='acquisition_cost')
    def display_cost(self, obj):
        return f'{money_co(obj.acquisition_cost)} / {obj.unit_symbol}'

    @admin.display(description='Precio proporcional por unidad de control', ordering='sale_price')
    def display_sale(self, obj):
        return f'{money_co(obj.sale_price)} / {obj.unit_symbol}'

    @admin.display(description='Venta de presentación completa', ordering='presentation_sale_price')
    def display_package_sale(self, obj):
        return money_co(obj.presentation_sale_price)

    @admin.display(description='Tarifa por unidad de control', ordering='service_usage_price')
    def display_usage(self, obj):
        return f'{money_co(obj.service_usage_price)} / {obj.unit_symbol}'

    @admin.display(description='Tarifa personalizada por unidad de control')
    def display_override(self, obj):
        return money_co(obj.usage_price_override)


@admin.register(StockEntry)
class StockEntryAdmin(ProductAdmin):
    list_display = ('id', 'kind', 'product', 'presentation_count', 'display_quantity', 'display_total', 'created_by', 'created_at')
    list_filter = ('kind', 'base_unit')
    list_select_related = ('product', 'created_by')
    search_fields = ('product__code', 'product__name')
    fields = ('id', 'kind', 'product', 'presentation_count', 'presentation', 'base_unit',
              'display_content', 'display_quantity', 'display_total', 'display_entry_package_cost',
              'display_entry_unit_cost', 'display_package_sale', 'display_entry_usage',
              'operation_key', 'request_fingerprint', 'created_by', 'created_at')
    readonly_fields = fields

    @admin.display(description='Cantidad registrada', ordering='quantity')
    def display_quantity(self, obj):
        return quantity_co(obj.quantity, obj.base_unit)

    @admin.display(description='Costo total registrado', ordering='total_cost')
    def display_total(self, obj):
        return money_co(obj.total_cost)

    @admin.display(description='Costo por presentación')
    def display_entry_package_cost(self, obj):
        return money_co(obj.cost_per_presentation)

    @admin.display(description='Costo por unidad de control')
    def display_entry_unit_cost(self, obj):
        return money_co(obj.cost_per_base_unit)

    @admin.display(description='Tarifa por unidad de control al registrar')
    def display_entry_usage(self, obj):
        return money_co(obj.usage_price)
