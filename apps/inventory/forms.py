from decimal import Decimal

from django import forms

from .calculations import purchase_values
from .models import Product


class ProductRegistrationForm(forms.Form):
    operation_token = forms.CharField(widget=forms.HiddenInput)
    code = forms.CharField(label='Código único', max_length=50)
    name = forms.CharField(label='Nombre', max_length=150)
    description = forms.CharField(label='Descripción', required=False, widget=forms.Textarea(attrs={'rows': 3}))
    presentation = forms.ChoiceField(label='Presentación', choices=Product.Presentation.choices)
    base_unit = forms.ChoiceField(label='Tipo de control', choices=Product.BaseUnit.choices)
    content = forms.DecimalField(label='Contenido por presentación (ml o g)', required=False,
                                max_digits=15, decimal_places=3, min_value=Decimal('0.001'))
    presentation_count = forms.IntegerField(label='Cantidad inicial', min_value=1, max_value=1000000000,
                                           help_text='Número de presentaciones completas al dar de alta el producto.')
    total_cost = forms.DecimalField(label='Costo total del inventario inicial (COP)', max_digits=18, decimal_places=2, min_value=Decimal('0'))
    presentation_sale_price = forms.DecimalField(label='Precio de venta de una presentación completa (COP)',
                                                max_digits=18, decimal_places=2, min_value=Decimal('0'))
    usage_price = forms.DecimalField(label='Precio por ml o gramo (opcional)', required=False,
                                     max_digits=24, decimal_places=8, min_value=Decimal('0'),
                                     help_text='Vacío: se usa el precio proporcional. Escribe un valor para cobrar una tarifa diferente.')
    minimum_stock = forms.DecimalField(label='Stock mínimo en la unidad de control', max_digits=15,
                                       decimal_places=3, min_value=Decimal('0'))
    is_active = forms.BooleanField(label='Producto activo', required=False, initial=True)

    def __init__(self, *args, product=None, mode='new', **kwargs):
        self.product = product
        self.mode = mode
        super().__init__(*args, **kwargs)
        if mode == 'edit':
            self.fields.pop('presentation_count')
            self.fields.pop('total_cost')
        elif mode == 'purchase':
            self.fields['presentation_count'].label = 'Cantidad de presentaciones recibidas'
            self.fields['presentation_count'].help_text = 'Presentaciones recibidas en esta entrada posterior.'
            self.fields['total_cost'].label = 'Costo total de la entrada (COP)'
        if product:
            self.initial.update({
                'code': product.code, 'name': product.name, 'description': product.description,
                'presentation': product.presentation, 'base_unit': product.base_unit,
                'content': product.content_per_presentation,
                'presentation_sale_price': product.presentation_sale_price,
                'minimum_stock': product.minimum_stock, 'is_active': product.is_active,
                'usage_price': product.usage_price_override if product.content_per_presentation is not None else product.service_usage_price,
            })
            self.fields['code'].disabled = True
            self.fields['base_unit'].disabled = True
            if product.content_per_presentation is not None:
                self.fields['content'].disabled = True
                self.fields['presentation'].disabled = True
        unit = product.base_unit if product else (self.data.get('base_unit') if self.is_bound else Product.BaseUnit.UNIT)
        self.fields['content'].widget.attrs['data-locked'] = 'true' if product and product.content_per_presentation is not None else 'false'
        if unit == Product.BaseUnit.UNIT:
            self.fields['content'].disabled = True
            self.fields['usage_price'].disabled = True
            self.initial['content'] = Decimal('1')
            self.initial['usage_price'] = None
        symbol = 'unidades' if unit == Product.BaseUnit.UNIT else 'ml' if unit == Product.BaseUnit.ML else 'g' if unit == Product.BaseUnit.G else 'unidad de control'
        self.fields['minimum_stock'].help_text = f'Se expresa en {symbol}, no en frascos ni tubos para productos divisibles.'
        for name, field in self.fields.items():
            if name == 'is_active':
                field.widget.attrs['class'] = 'rounded border-outline text-secondary focus:ring-secondary'
            else:
                field.widget.attrs['class'] = (
                    'w-full px-3 py-2.5 rounded-xl border border-outline-variant '
                    'bg-surface-container-lowest text-on-surface text-sm '
                    'focus:border-secondary focus:ring-secondary'
                )
            if isinstance(field, forms.DecimalField):
                field.widget.attrs['step'] = '0.00000001' if name == 'usage_price' else ('0.001' if name in ['content', 'minimum_stock'] else '0.01')

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        query = Product.objects.filter(code__iexact=code)
        if self.product:
            query = query.exclude(pk=self.product.pk)
        if query.exists():
            raise forms.ValidationError('Ya existe un producto con este código. Puedes editar su ficha sin volver a registrar el saldo inicial.')
        return code

    def clean(self):
        data = super().clean()
        unit = data.get('base_unit')
        if unit == Product.BaseUnit.UNIT:
            data['content'] = Decimal('1')
            minimum = data.get('minimum_stock')
            if minimum is not None and minimum != minimum.to_integral_value():
                self.add_error('minimum_stock', 'Para unidades, el stock mínimo debe ser entero.')
            # En productos completos no se solicita ni aplica una tarifa por ml o g.
            data['usage_price'] = None
        elif data.get('content') is None:
            self.add_error('content', 'Indica el contenido de cada presentación en ml o g.')
        if not self.errors and self.mode != 'edit':
            try:
                self.values = purchase_values(data['presentation_count'], data['content'],
                                              data['total_cost'], data['presentation_sale_price'], data['usage_price'])
            except ValueError as error:
                self.add_error(None, str(error))
        return data
