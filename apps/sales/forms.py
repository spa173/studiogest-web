from decimal import Decimal

from django import forms

from appointments.models import Appointment
from customers.models import Customer
from inventory.models import Product
from services.models import Service

from .models import CashRegisterSession, PaymentMethod, Sale, SaleDetail, SaleDetailType, SaleStatus

CLASE_INPUT = (
    'w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant '
    'rounded-xl font-body-md text-body-md text-on-surface placeholder:text-outline '
    'focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 '
    'transition-all font-medium'
)


class CashRegisterSessionCloseForm(forms.Form):
    counted_cash = forms.DecimalField(
        min_value=Decimal('0'),
        label='Efectivo contado',
        widget=forms.NumberInput(attrs={'class': CLASE_INPUT, 'min': '0', 'step': '1'}),
        error_messages={
            'required': 'Ingresa el efectivo contado al cierre.',
            'min_value': 'El efectivo contado no puede ser negativo.',
            'invalid': 'Ingresa un monto válido.',
        },
    )

    def clean_counted_cash(self):
        value = self.cleaned_data['counted_cash']
        if value < 0:
            raise forms.ValidationError('El efectivo contado no puede ser negativo.')
        return value


class CashRegisterSessionForm(forms.ModelForm):
    class Meta:
        model = CashRegisterSession
        fields = ['opening_cash', 'notes']
        widgets = {
            'opening_cash': forms.NumberInput(attrs={'class': CLASE_INPUT, 'min': '0', 'step': '1'}),
            'notes': forms.Textarea(attrs={'class': CLASE_INPUT + ' resize-none', 'rows': 2}),
        }

    def clean_opening_cash(self):
        value = self.cleaned_data['opening_cash']
        if value < 0:
            raise forms.ValidationError('La base inicial no puede ser negativa.')
        return value


class SaleForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.order_by('name'),
        required=False,
        label='Cliente',
        widget=forms.Select(attrs={'class': CLASE_INPUT}),
    )
    appointment = forms.ModelChoiceField(
        queryset=Appointment.objects.none(),
        required=False,
        label='Cita cobrada',
        widget=forms.Select(attrs={'class': CLASE_INPUT}),
    )
    payment_method = forms.ChoiceField(
        choices=PaymentMethod.choices,
        label='Medio de pago',
        widget=forms.Select(attrs={'class': CLASE_INPUT}),
    )
    cash_session = forms.ModelChoiceField(
        queryset=CashRegisterSession.objects.filter(status=CashRegisterSession.Status.OPEN).order_by('-opened_at'),
        required=True,
        label='Sesión de caja',
        empty_label='Selecciona una sesión de caja abierta',
        widget=forms.Select(attrs={'class': CLASE_INPUT}),
        error_messages={'required': 'Debes seleccionar una sesión de caja abierta.'},
    )
    notes = forms.CharField(
        required=False,
        label='Observaciones',
        widget=forms.Textarea(attrs={'class': CLASE_INPUT + ' resize-none', 'rows': 2}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo citas no cobradas (venta registrada) y no canceladas pueden cobrarse.
        self.fields['appointment'].queryset = Appointment.objects.exclude(
            status=Appointment.Status.CANCELLED,
        ).exclude(sale__status=SaleStatus.REGISTERED).select_related('customer', 'service').order_by('-date', '-start_time')
        open_sessions = self.fields['cash_session'].queryset
        if not self.is_bound and not self.initial.get('cash_session') and open_sessions.count() == 1:
            self.initial['cash_session'] = open_sessions.first()

    def clean(self):
        cleaned = super().clean()
        appointment = cleaned.get('appointment')
        customer = cleaned.get('customer')
        if appointment and not customer:
            cleaned['customer'] = appointment.customer
        return cleaned


class SaleDetailForm(forms.Form):
    detail_type = forms.ChoiceField(
        choices=SaleDetailType.choices,
        label='Tipo',
        widget=forms.Select(attrs={'class': CLASE_INPUT}),
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True).order_by('name'),
        required=False,
        label='Servicio',
        widget=forms.Select(attrs={'class': CLASE_INPUT}),
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        required=False,
        label='Producto',
        widget=forms.Select(attrs={'class': CLASE_INPUT}),
    )
    quantity = forms.DecimalField(
        min_value=Decimal('0.001'), initial=Decimal('1'),
        label='Cantidad',
        widget=forms.NumberInput(attrs={'class': CLASE_INPUT, 'min': '0.001', 'step': '0.001'}),
    )
    unit_price = forms.DecimalField(
        min_value=Decimal('0'), required=False,
        label='Precio unitario',
        widget=forms.NumberInput(attrs={'class': CLASE_INPUT, 'min': '0', 'step': '1'}),
    )

    def clean(self):
        cleaned = super().clean()
        detail_type = cleaned.get('detail_type')
        service = cleaned.get('service')
        product = cleaned.get('product')
        quantity = cleaned.get('quantity') or Decimal('1')
        unit_price = cleaned.get('unit_price')

        if detail_type == SaleDetailType.SERVICE:
            if service is None:
                raise forms.ValidationError('Selecciona un servicio.')
            if product is not None:
                raise forms.ValidationError('Un servicio no puede tener producto asociado.')
            if quantity != Decimal('1'):
                raise forms.ValidationError('La cantidad de un servicio debe ser 1.')
            if unit_price is None:
                unit_price = service.price_cop
        elif detail_type == SaleDetailType.PRODUCT:
            if product is None:
                raise forms.ValidationError('Selecciona un producto.')
            if service is not None:
                raise forms.ValidationError('Un producto no puede tener servicio asociado.')
            if unit_price is None:
                unit_price = product.sale_price
        else:
            raise forms.ValidationError('Tipo de detalle no válido.')

        if unit_price is None or unit_price < 0:
            raise forms.ValidationError('El precio unitario no es válido.')
        cleaned['unit_price'] = unit_price
        cleaned['quantity'] = quantity
        return cleaned