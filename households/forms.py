from django import forms
from django.core.exceptions import ValidationError
from .models import Household, Resident, HouseholdService
from governance.models import Village, WardCommittee

class DateInput(forms.DateInput):
    input_type = 'date'

class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = [
            'village', 'ward_committee', 'physical_address', 'postal_address',
            'gps_coordinates', 'housing_type', 'land_tenure', 'rooms_count',
            'plot_size', 'water_source', 'electricity_source', 'has_toilet',
            'toilet_type', 'waste_disposal', 'estimated_monthly_income',
            'main_income_source', 'established_date', 'special_circumstances',
            'notes', 'is_active'
        ]
        widgets = {
            'village': forms.Select(attrs={'class': 'form-control'}),
            'ward_committee': forms.Select(attrs={'class': 'form-control'}),
            'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'postal_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gps_coordinates': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'latitude,longitude (e.g., -25.7479, 28.2293)'
            }),
            'housing_type': forms.Select(attrs={'class': 'form-control'}),
            'land_tenure': forms.Select(attrs={'class': 'form-control'}),
            'rooms_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'plot_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'water_source': forms.Select(attrs={'class': 'form-control'}),
            'electricity_source': forms.Select(attrs={'class': 'form-control'}),
            'has_toilet': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'toilet_type': forms.TextInput(attrs={'class': 'form-control'}),
            'waste_disposal': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_monthly_income': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01'
            }),
            'main_income_source': forms.TextInput(attrs={'class': 'form-control'}),
            'established_date': DateInput(attrs={'class': 'form-control'}),
            'special_circumstances': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamic ward committee filtering based on village
        if 'village' in self.data:
            try:
                village_id = int(self.data.get('village'))
                village = Village.objects.get(pk=village_id)
                if village.traditional_council:
                    self.fields['ward_committee'].queryset = WardCommittee.objects.filter(
                        traditional_councils=village.traditional_council
                    )
            except (ValueError, TypeError, Village.DoesNotExist):
                pass
        elif self.instance.pk:
            if self.instance.village and self.instance.village.traditional_council:
                self.fields['ward_committee'].queryset = WardCommittee.objects.filter(
                    traditional_councils=self.instance.village.traditional_council
                )

class ResidentForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = [
            'id_number', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'household', 'is_head_of_household', 'relationship_to_head',
            'phone_number', 'email', 'alternative_contact', 'marital_status',
            'education_level', 'employment_status', 'occupation', 'employer',
            'monthly_income', 'receives_grants', 'grant_types', 'grant_amount',
            'has_disability', 'disability_type', 'chronic_illnesses',
            'special_needs', 'date_moved_in', 'notes', 'is_active'
        ]
        widgets = {
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234567890123',
                'maxlength': '13'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': DateInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'household': forms.Select(attrs={'class': 'form-control'}),
            'is_head_of_household': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'relationship_to_head': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'alternative_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'education_level': forms.Select(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'employer': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'receives_grants': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grant_types': forms.TextInput(attrs={'class': 'form-control'}),
            'grant_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'has_disability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'disability_type': forms.TextInput(attrs={'class': 'form-control'}),
            'chronic_illnesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'special_needs': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'date_moved_in': DateInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Auto-extract date of birth from ID if not provided
        id_number = cleaned_data.get('id_number')
        date_of_birth = cleaned_data.get('date_of_birth')
        
        if id_number and not date_of_birth:
            # Try to extract from ID number
            try:
                from datetime import date
                year_part = int(id_number[:2])
                month = int(id_number[2:4])
                day = int(id_number[4:6])
                
                current_year = date.today().year
                if year_part <= (current_year % 100):
                    year = 2000 + year_part
                else:
                    year = 1900 + year_part
                
                cleaned_data['date_of_birth'] = date(year, month, day)
            except (ValueError, IndexError):
                pass
        
        return cleaned_data

class HouseholdServiceForm(forms.ModelForm):
    class Meta:
        model = HouseholdService
        fields = [
            'household', 'service_type', 'status', 'quality_rating',
            'distance_to_service', 'monthly_cost', 'notes'
        ]
        widgets = {
            'household': forms.Select(attrs={'class': 'form-control'}),
            'service_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'quality_rating': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1, 
                'max': 5
            }),
            'distance_to_service': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01'
            }),
            'monthly_cost': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class HouseholdSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search households...'
        })
    )
    village = forms.ModelChoiceField(
        queryset=Village.objects.filter(is_active=True),
        required=False,
        empty_label="All Villages",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    housing_type = forms.ChoiceField(
        choices=[('', 'All Housing Types')] + Household.HOUSING_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    verified = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Verified'), ('false', 'Unverified')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ResidentSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search residents...'
        })
    )
    household = forms.ModelChoiceField(
        queryset=Household.objects.filter(is_active=True),
        required=False,
        empty_label="All Households",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=[('', 'All Employment Status')] + Resident.EMPLOYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    age_group = forms.ChoiceField(
        choices=[
            ('', 'All Ages'),
            ('child', 'Children (0-17)'),
            ('adult', 'Adults (18-59)'),
            ('senior', 'Seniors (60+)')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )