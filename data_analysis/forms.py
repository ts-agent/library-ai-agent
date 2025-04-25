from django import forms
from .models import Performance

class PerformanceForm(forms.ModelForm):
    class Meta:
        model = Performance
        fields = ['name', 'venue', 'start_date', 'end_date', 'age_limit', 'running_time', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '공연에 대한 설명을 입력해주세요.'
            }),
        } 