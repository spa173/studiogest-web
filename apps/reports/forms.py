from django import forms


class ReportDateFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Desde', required=False, input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        error_messages={'invalid': 'Introduce una fecha inicial válida (AAAA-MM-DD).'},
    )
    end_date = forms.DateField(
        label='Hasta', required=False, input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        error_messages={'invalid': 'Introduce una fecha final válida (AAAA-MM-DD).'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2.5 rounded-xl border border-outline-variant '
                'bg-surface-container-lowest text-on-surface text-sm '
                'focus:border-secondary focus:ring-secondary'
            )

    def clean(self):
        data = super().clean()
        start = data.get('start_date')
        end = data.get('end_date')
        if start and end and start > end:
            raise forms.ValidationError('La fecha inicial no puede ser posterior a la fecha final.')
        return data
