from django import forms
from apps.expedientes.models import Expediente
from apps.brands.models import BrandConfigVersion

class ProformaCreationForm(forms.Form):
    expediente = forms.ModelChoiceField(queryset=Expediente.objects.all(), label="Expediente")
    
    # We load modes dynamically based on Brand configuraton, or fallback to simple string inputs
    pricing_mode = forms.ChoiceField(
        choices=[
            ('FOB', 'FOB (Default Rana Walk)'),
            ('mode_b', 'Mode B (Marluvas)'),
            ('mode_c', 'Mode C (Marluvas)'),
            ('CIF', 'CIF'),
            ('DDP', 'DDP'),
        ],
        label="Pricing Mode"
    )
    
    urgency_days = forms.IntegerField(
        initial=7, 
        min_value=1,
        help_text="Antigüedad de vencimiento de proforma (días)"
    )

    def clean(self):
        cleaned_data = super().clean()
        # Add basic cross-validation here if needed
        return cleaned_data
