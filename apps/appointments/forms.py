import datetime
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from .models import Appointment, calculate_end_time
from customers.models import Customer
from services.models import Service, Professional
from .pricing import calculate_pricing


class AppointmentForm(forms.ModelForm):
    adjusted_price_cop = forms.DecimalField(
        label='Precio personalizado (COP)', max_digits=12, decimal_places=0,
        min_value=0, required=False,
    )
    discount_type = forms.ChoiceField(label='Tipo de descuento', choices=Appointment.DiscountType.choices, required=False)
    discount_value = forms.DecimalField(label='Descuento', max_digits=14, decimal_places=2, min_value=0, required=False)
    pricing_reason = forms.CharField(label='Motivo del ajuste o descuento', required=False, widget=forms.Textarea(attrs={'rows': 2}))
    EDITABLE_PRICING = ('adjusted_price_cop', 'discount_type', 'discount_value', 'pricing_reason')
    DERIVED_PRICING = ('price_cop', 'catalog_price_cop', 'discount_amount_cop')
    duration_minutes = forms.IntegerField(
        label='Duración planificada (minutos)', min_value=1, required=False,
        help_text='Puedes ajustar la duración para esta cita sin cambiar el servicio.',
        error_messages={'min_value': 'La duración debe ser mayor que cero.'},
        widget=forms.NumberInput(attrs={
            'id': 'durationInput', 'step': '1',
            'class': 'w-full py-2.5 px-3 bg-surface-container-lowest border border-outline-variant rounded-xl text-sm text-on-surface',
        }),
    )
    # Campo flexible: permite seleccionar cliente existente o crear uno nuevo al vuelo
    customer_name = forms.CharField(
        label='Nombre del Cliente',
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'clientInput',
            'placeholder': 'Ej. Juan Pérez (o 310 123 4567)',
            'class': 'w-full pl-9 pr-8 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium'
        })
    )
    customer_phone = forms.CharField(
        label='Teléfono del Cliente',
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'clientPhoneInput',
            'placeholder': '310 000 0000',
            'class': 'w-full pl-9 pr-3 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium'
        })
    )

    class Meta:
        model = Appointment
        fields = ['customer', 'service', 'professional', 'date', 'start_time', 'notes', 'send_whatsapp']
        widgets = {
            'customer': forms.Select(attrs={
                'id': 'customerSelect',
                'class': 'w-full pl-9 pr-8 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium appearance-none cursor-pointer'
            }),
            'service': forms.Select(attrs={
                'id': 'serviceSelect',
                'onchange': 'updateServiceDetails(true)',
                'class': 'w-full pl-9 pr-8 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium appearance-none cursor-pointer'
            }),
            'professional': forms.Select(attrs={
                'id': 'staffSelect',
                'class': 'w-full pl-9 pr-8 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium appearance-none cursor-pointer'
            }),
            'date': forms.DateInput(attrs={
                'id': 'dateInput',
                'type': 'date',
                'class': 'w-full pl-9 pr-3 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium'
            }),
            'start_time': forms.TimeInput(attrs={
                'id': 'timeInput',
                'type': 'time',
                'class': 'w-full pl-8 pr-2 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-md text-body-md text-on-surface focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium'
            }),
            'notes': forms.Textarea(attrs={
                'id': 'notesTextarea',
                'rows': 2,
                'placeholder': 'Observaciones, estilo deseado o alergias...',
                'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-xl font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10 transition-all font-medium resize-none'
            }),
            'send_whatsapp': forms.CheckboxInput(attrs={
                'class': 'rounded border-outline text-secondary focus:ring-secondary h-4 w-4 cursor-pointer'
            })
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_adjust_pricing = bool(user and user.is_authenticated and user.is_admin)
        if self.can_adjust_pricing:
            for name in self.EDITABLE_PRICING:
                field = self.fields[name]
                field.widget.attrs['class'] = 'w-full px-3 py-2.5 border border-outline-variant rounded-xl bg-surface-container-lowest text-sm'
                field.widget.attrs['id'] = name
            self.fields['adjusted_price_cop'].widget.attrs['step'] = '1'
            self.fields['discount_value'].widget.attrs['step'] = '0.01'
            self.initial.setdefault('discount_type', self.instance.discount_type or Appointment.DiscountType.NONE)
            self.initial.setdefault('discount_value', self.instance.discount_value if self.instance.discount_value is not None else 0)
        else:
            for name in self.EDITABLE_PRICING:
                self.fields.pop(name)
        self.fields['customer'].required = False
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        self.fields['professional'].queryset = Professional.objects.filter(is_active=True)
        if self.instance.pk and self.instance.start_time and self.instance.end_time:
            start = datetime.datetime.combine(self.instance.date, self.instance.start_time)
            end = datetime.datetime.combine(self.instance.date, self.instance.end_time)
            self.initial.setdefault('duration_minutes', int((end - start).total_seconds() // 60))

        # Valores por defecto para agilizar el agendamiento
        if not self.initial.get('date'):
            self.initial['date'] = datetime.date.today().isoformat()
        if not self.initial.get('start_time'):
            # Redondear a la siguiente hora en punto
            now = datetime.datetime.now()
            next_hour = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0).time()
            self.initial['start_time'] = next_hour.strftime('%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        if not self.can_adjust_pricing and any(name in self.data for name in self.EDITABLE_PRICING + self.DERIVED_PRICING):
            raise ValidationError('Solo un administrador puede modificar precios o descuentos.')
        customer = cleaned_data.get('customer')
        customer_name = cleaned_data.get('customer_name')
        customer_phone = cleaned_data.get('customer_phone')
        service = cleaned_data.get('service')
        professional = cleaned_data.get('professional')
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        if service and not any(name in self.errors for name in self.EDITABLE_PRICING):
            self._clean_pricing(cleaned_data, service)

        # Si no seleccionó cliente del dropdown pero escribió nombre
        if not customer:
            if customer_name:
                phone = customer_phone or '3000000000'
                customer, _ = Customer.objects.get_or_create(
                    name=customer_name.strip(),
                    defaults={'phone': phone}
                )
                cleaned_data['customer'] = customer
            else:
                self.add_error('customer', 'Debes seleccionar un cliente o escribir su nombre.')

        if service and start_time and 'duration_minutes' not in self.errors:
            duration = cleaned_data.get('duration_minutes')
            if duration is None:
                # Keep old HTTP clients working and preserve existing intervals.
                duration = self.initial.get('duration_minutes', service.duration_minutes)
            cleaned_data['duration_minutes'] = duration
            # Calcular hora de finalización
            try:
                end_time = calculate_end_time(start_time, duration)
            except ValidationError as error:
                self.add_error('duration_minutes', error)
                return cleaned_data
            self.calculated_end_time = end_time
            self.instance.end_time = end_time

            # Validar traslapes
            if professional and date:
                conflicts = Appointment.objects.filter(
                    professional=professional,
                    date=date,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(status=Appointment.Status.CANCELLED)
                if self.instance.pk:
                    conflicts = conflicts.exclude(pk=self.instance.pk)

                if conflicts.exists():
                    c = conflicts.first()
                    raise ValidationError(
                        f"¡Conflicto de horario! {professional.name} ya tiene una cita de "
                        f"{c.start_time.strftime('%I:%M %p')} a {c.end_time.strftime('%I:%M %p')} con {c.customer.name}."
                    )

        return cleaned_data

    def _clean_pricing(self, cleaned_data, service):
        if self.instance.pk:
            # Notes/status edits must not reconstruct or recalculate old pricing.
            if not any(name in self.data for name in self.EDITABLE_PRICING):
                return
            if self.instance.catalog_price_cop is None:
                self.add_error(None, 'Esta cita antigua no tiene detalle económico; no se reconstruye desde el catálogo actual.')
                return
        adjusted = cleaned_data.get('adjusted_price_cop')
        if adjusted is None:
            adjusted = self.instance.adjusted_price_cop if self.instance.pk else service.price_cop
        kind = cleaned_data.get('discount_type') or Appointment.DiscountType.NONE
        value = cleaned_data.get('discount_value')
        if value is None:
            value = Decimal('0')
        try:
            amount, total = calculate_pricing(adjusted, kind, value)
        except ValidationError as error:
            self.add_error(None, error)
            return
        self.instance.catalog_price_cop = self.instance.catalog_price_cop if self.instance.pk else service.price_cop
        self.instance.adjusted_price_cop = adjusted
        self.instance.discount_type = kind
        self.instance.discount_value = value
        self.instance.discount_amount_cop = amount
        self.instance.price_cop = total
        self.instance.pricing_reason = cleaned_data.get('pricing_reason', '')

    def save(self, commit=True):
        appointment = super().save(commit=False)
        if hasattr(self, 'calculated_end_time'):
            appointment.end_time = self.calculated_end_time
        if appointment.price_cop is None and appointment.service:
            appointment.price_cop = appointment.service.price_cop
        if commit:
            appointment.save()
        return appointment
