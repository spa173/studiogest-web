from decimal import Decimal

from django import forms

from .models import Service


class ServiceForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(
        label='Duración (minutos)', min_value=1, max_value=2147483647,
        widget=forms.NumberInput(attrs={'step': '1'}),
        error_messages={'min_value': 'La duración debe ser mayor que cero.'})
    price_cop = forms.DecimalField(
        label='Precio en COP', max_digits=12, decimal_places=0, min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={'step': '1'}),
        help_text='Pesos colombianos enteros, sin puntos de miles ni decimales. Ejemplo: 25000.',
        error_messages={
            'min_value': 'El precio no puede ser negativo.',
            'max_decimal_places': 'Ingresa un precio entero en COP, sin decimales.',
        })

    class Meta:
        model = Service
        fields = ['name', 'description', 'duration_minutes', 'price_cop', 'is_active']
        labels = {'name': 'Nombre', 'description': 'Descripción', 'is_active': 'Servicio activo'}
        widgets = {
            'name': forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Ej. Corte clásico'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.setdefault('duration_minutes', self.instance.duration_minutes)
        for name, field in self.fields.items():
            if name == 'is_active':
                field.widget.attrs['class'] = 'rounded border-outline text-secondary focus:ring-secondary h-4 w-4'
            else:
                field.widget.attrs['class'] = (
                    'w-full px-3.5 py-2.5 rounded-xl border border-outline-variant '
                    'bg-surface-container-lowest text-on-surface text-sm '
                    'focus:outline-none focus:border-secondary focus:ring-4 focus:ring-secondary/10'
                )

    def clean_name(self):
        name = ' '.join(self.cleaned_data['name'].split())
        if not name:
            raise forms.ValidationError('Escribe el nombre del servicio.')
        return name
