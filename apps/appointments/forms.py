import datetime
from django import forms
from django.core.exceptions import ValidationError
from .models import Appointment
from customers.models import Customer
from services.models import Service, Professional


class AppointmentForm(forms.ModelForm):
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
                'onchange': 'updateServiceDetails()',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].required = False
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        self.fields['professional'].queryset = Professional.objects.filter(is_active=True)

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
        customer = cleaned_data.get('customer')
        customer_name = cleaned_data.get('customer_name')
        customer_phone = cleaned_data.get('customer_phone')
        service = cleaned_data.get('service')
        professional = cleaned_data.get('professional')
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')

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

        if service and start_time:
            # Calcular hora de finalización
            start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
            end_dt = start_dt + datetime.timedelta(minutes=service.duration_minutes)
            end_time = end_dt.time()
            self.calculated_end_time = end_time

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

    def save(self, commit=True):
        appointment = super().save(commit=False)
        if hasattr(self, 'calculated_end_time'):
            appointment.end_time = self.calculated_end_time
        if not appointment.price_cop and appointment.service:
            appointment.price_cop = appointment.service.price_cop
        if commit:
            appointment.save()
        return appointment
