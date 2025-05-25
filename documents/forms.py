from django import forms
from django.core.exceptions import ValidationError
from .models import ProofOfResidence, DocumentTemplate, BatchProcess
from governance.models import Village
from households.models import Resident, Household

class ProofOfResidenceForm(forms.ModelForm):
    class Meta:
        model = ProofOfResidence
        fields = [
            'village', 'household', 'resident', 'purpose', 
            'template', 'valid_from', 'valid_until', 'notes'
        ]
        widgets = {
            'village': forms.Select(attrs={'class': 'form-control', 'id': 'id_village'}),
            'household': forms.Select(attrs={'class': 'form-control', 'id': 'id_household'}),
            'resident': forms.Select(attrs={'class': 'form-control', 'id': 'id_resident'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bank account opening, School enrollment'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['village'].queryset = Village.objects.all()
        self.fields['household'].queryset = Household.objects.none()
        self.fields['resident'].queryset = Resident.objects.none()
        self.fields['template'].queryset = DocumentTemplate.objects.filter(is_active=True)
        
        # If village is selected, populate households
        if 'village' in self.data:
            try:
                village_id = int(self.data.get('village'))
                self.fields['household'].queryset = Household.objects.filter(village_id=village_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.village:
            self.fields['household'].queryset = self.instance.village.households.all()
        
        # If household is selected, populate residents
        if 'household' in self.data:
            try:
                household_id = int(self.data.get('household'))
                self.fields['resident'].queryset = Resident.objects.filter(household_id=household_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.household:
            self.fields['resident'].queryset = self.instance.household.residents.all()
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        
        if valid_from and valid_until and valid_from >= valid_until:
            raise ValidationError("Valid until date must be after valid from date.")
        
        return cleaned_data

class DocumentTemplateForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = ['name', 'description', 'template_file', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template_file': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., documents/templates/proof_of_residence.html'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BatchProcessForm(forms.ModelForm):
    class Meta:
        model = BatchProcess
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }