from django import forms
from .models import Performance

class PerformanceForm(forms.ModelForm):
    class Meta:
        model = Performance
        fields = ['name', 'venue', 'start_date', 'end_date', 'age_limit', 'running_time']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        } 