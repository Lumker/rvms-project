from django import forms
from django.forms import ModelForm, DateInput, TimeInput, Select
from .models import (
    Province, District, Municipality, TraditionalCouncil,
    Village, CouncilMember, CouncilMeeting, Resolution, WardCommittee, WardCommitteeMember
)

class DatePickerInput(DateInput):
    input_type = 'date'

class TimePickerInput(TimeInput):
    input_type = 'time'

class ProvinceForm(ModelForm):
    class Meta:
        model = Province
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DistrictForm(ModelForm):
    class Meta:
        model = District
        fields = ['name', 'code', 'province']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-control'}),
        }

# Update your existing MunicipalityForm
class MunicipalityForm(ModelForm):
    class Meta:
        model = Municipality
        fields = [
            'name', 'code', 'municipality_type', 'district', 'contact_info', 
            'website', 'mayor_name', 'municipal_manager', 'population', 
            'area_km2', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Municipality name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., JHB001'}),
            'municipality_type': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'contact_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'mayor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'municipal_manager': forms.TextInput(attrs={'class': 'form-control'}),
            'population': forms.NumberInput(attrs={'class': 'form-control'}),
            'area_km2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
class WardCommitteeForm(ModelForm):
    class Meta:
        model = WardCommittee
        fields = [
            'name', 'ward_number', 'ward_code', 'municipality', 
            'ward_councillor', 'councillor_contact', 'geographic_boundaries',
            'population', 'committee_secretary', 'meeting_venue', 
            'established_date', 'status', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ward Committee name'}),
            'ward_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 15'}),
            'ward_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., WRD015'}),
            'municipality': forms.Select(attrs={'class': 'form-control'}),
            'ward_councillor': forms.TextInput(attrs={'class': 'form-control'}),
            'councillor_contact': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'geographic_boundaries': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'population': forms.NumberInput(attrs={'class': 'form-control'}),
            'committee_secretary': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting_venue': forms.TextInput(attrs={'class': 'form-control'}),
            'established_date': DatePickerInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WardCommitteeMemberForm(ModelForm):
    class Meta:
        model = WardCommitteeMember
        fields = ['ward_committee', 'user', 'role', 'appointed_date', 'term_end_date', 'is_active']
        widgets = {
            'ward_committee': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'appointed_date': DatePickerInput(attrs={'class': 'form-control'}),
            'term_end_date': DatePickerInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Update your existing TraditionalCouncilForm
class TraditionalCouncilForm(ModelForm):
    class Meta:
        model = TraditionalCouncil
        fields = [
            'name', 'leader_name', 'leader_title', 'municipality', 'ward_committee',
            'contact_info', 'establishment_date', 'term_end_date', 
            'geographic_jurisdiction', 'status', 'recognition_certificate', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'leader_name': forms.TextInput(attrs={'class': 'form-control'}),
            'leader_title': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.Select(attrs={'class': 'form-control'}),
            'contact_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'establishment_date': DatePickerInput(attrs={'class': 'form-control'}),
            'term_end_date': DatePickerInput(attrs={'class': 'form-control'}),
            'geographic_jurisdiction': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'recognition_certificate': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ward_committee': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        establishment_date = cleaned_data.get('establishment_date')
        term_end_date = cleaned_data.get('term_end_date')
        
        if establishment_date and term_end_date:
            if term_end_date <= establishment_date:
                raise forms.ValidationError("Term end date must be after establishment date.")
        
        return cleaned_data

# Add is_active to your existing VillageForm
class VillageForm(ModelForm):
    class Meta:
        model = Village
        fields = ['name', 'code', 'traditional_council', 'location', 'population', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'traditional_council': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'population': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CouncilMemberForm(ModelForm):
    class Meta:
        model = CouncilMember
        fields = ['council', 'user', 'role', 'appointed_date', 'term_end_date', 'is_active']
        widgets = {
            'council': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'appointed_date': DatePickerInput(attrs={'class': 'form-control'}),
            'term_end_date': DatePickerInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CouncilMeetingForm(ModelForm):
    class Meta:
        model = CouncilMeeting
        fields = ['council', 'title', 'date', 'time', 'location', 'status', 'agenda', 'minutes']
        widgets = {
            'council': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'date': DatePickerInput(attrs={'class': 'form-control'}),
            'time': TimePickerInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'agenda': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'minutes': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class ResolutionForm(ModelForm):
    class Meta:
        model = Resolution
        fields = ['meeting', 'title', 'description', 'proposed_by', 'status', 'date_implemented']
        widgets = {
            'meeting': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'proposed_by': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'date_implemented': DatePickerInput(attrs={'class': 'form-control'}),
        }