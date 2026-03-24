from django import forms
from .models import ChartAnalysis

class ChartAnalysisForm(forms.ModelForm):
    class Meta:
        model = ChartAnalysis
        fields = ['chart_image', 'risk_percent', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional: any extra context — news events, your own observations...'
            }),
            'risk_percent': forms.NumberInput(attrs={
                'step': '0.5', 'min': '0.5', 'max': '5'
            }),
        }
