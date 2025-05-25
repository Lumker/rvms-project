# infrastructure/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    InfrastructureAsset, WaterSource, WaterDistributionPoint,
    MaintenanceRecord, ServiceInterruption, AssetInspection
)
from governance.models import Village, WardCommittee
from households.models import Household
from users.models import CustomUser


class InfrastructureAssetForm(forms.ModelForm):
    """Base form for infrastructure assets"""
    
    class Meta:
        model = InfrastructureAsset
        fields = [
            'name', 'category', 'description', 'village', 'ward_committee',
            'gps_coordinates', 'physical_address', 'condition', 'operational_status',
            'ownership_type', 'owner_details', 'custodian', 'estimated_value',
            'annual_maintenance_cost', 'installation_date', 'expected_lifespan_years',
            'contractor', 'warranty_expiry', 'asset_photo', 'technical_documents'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asset name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'village': forms.Select(attrs={'class': 'form-control'}),
            'ward_committee': forms.Select(attrs={'class': 'form-control'}),
            'gps_coordinates': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '-26.1234, 28.5678'
            }),
            'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'operational_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ownership_type': forms.Select(attrs={'class': 'form-control'}),
            'owner_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'custodian': forms.Select(attrs={'class': 'form-control'}),
            'estimated_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'annual_maintenance_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'installation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expected_lifespan_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Years'
            }),
            'contractor': forms.TextInput(attrs={'class': 'form-control'}),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'asset_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'technical_documents': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['village'].queryset = Village.objects.filter(is_active=True).order_by('name')
        self.fields['ward_committee'].queryset = WardCommittee.objects.filter(is_active=True).order_by('name')
        self.fields['custodian'].queryset = CustomUser.objects.filter(is_active=True).order_by('first_name')
        self.fields['custodian'].empty_label = "Select custodian..."
        
        # Make some fields optional
        self.fields['ward_committee'].required = False
        self.fields['custodian'].required = False
        self.fields['estimated_value'].required = False
        self.fields['annual_maintenance_cost'].required = False
        self.fields['installation_date'].required = False
        self.fields['expected_lifespan_years'].required = False
        self.fields['contractor'].required = False
        self.fields['warranty_expiry'].required = False
    
    def clean_gps_coordinates(self):
        coordinates = self.cleaned_data.get('gps_coordinates')
        if coordinates:
            try:
                parts = coordinates.split(',')
                if len(parts) != 2:
                    raise ValidationError("Coordinates must be in format: latitude, longitude")
                
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                
                # Basic validation for South African coordinates
                if not (-35 <= lat <= -22):
                    raise ValidationError("Latitude must be between -35 and -22 for South Africa")
                if not (16 <= lon <= 33):
                    raise ValidationError("Longitude must be between 16 and 33 for South Africa")
                    
            except (ValueError, IndexError):
                raise ValidationError("Invalid coordinate format. Use: -26.1234, 28.5678")
        
        return coordinates
    
    def clean(self):
        cleaned_data = super().clean()
        installation_date = cleaned_data.get('installation_date')
        warranty_expiry = cleaned_data.get('warranty_expiry')
        
        if installation_date and installation_date > timezone.now().date():
            raise ValidationError("Installation date cannot be in the future")
        
        if installation_date and warranty_expiry and warranty_expiry < installation_date:
            raise ValidationError("Warranty expiry cannot be before installation date")
        
        return cleaned_data


class WaterSourceForm(InfrastructureAssetForm):
    """Form for water sources"""
    
    class Meta:
        model = WaterSource
        fields = InfrastructureAssetForm.Meta.fields + [
            'source_type', 'water_quality', 'daily_capacity_litres',
            'depth_meters', 'yield_litres_per_hour', 'last_water_test_date',
            'water_test_results', 'pump_type', 'power_source'
        ]
        widgets = dict(InfrastructureAssetForm.Meta.widgets, **{
            'source_type': forms.Select(attrs={'class': 'form-control'}),
            'water_quality': forms.Select(attrs={'class': 'form-control'}),
            'daily_capacity_litres': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Litres per day'
            }),
            'depth_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Meters'
            }),
            'yield_litres_per_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Litres per hour'
            }),
            'last_water_test_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'water_test_results': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pump_type': forms.TextInput(attrs={'class': 'form-control'}),
            'power_source': forms.Select(attrs={'class': 'form-control'}),
        })
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set category to water
        self.fields['category'].initial = 'water'
        self.fields['category'].widget.attrs['readonly'] = True
        
        # Make water-specific fields optional where appropriate
        self.fields['daily_capacity_litres'].required = False
        self.fields['depth_meters'].required = False
        self.fields['yield_litres_per_hour'].required = False
        self.fields['last_water_test_date'].required = False
        self.fields['water_test_results'].required = False
        self.fields['pump_type'].required = False
        self.fields['power_source'].required = False


class WaterDistributionPointForm(InfrastructureAssetForm):
    """Form for water distribution points"""
    
    class Meta:
        model = WaterDistributionPoint
        fields = InfrastructureAssetForm.Meta.fields + [
            'distribution_type', 'water_source', 'households_served',
            'estimated_users', 'distance_from_source_meters',
            'storage_capacity_litres', 'has_meter', 'meter_reading_date',
            'last_meter_reading', 'operates_24_7', 'operating_hours'
        ]
        widgets = dict(InfrastructureAssetForm.Meta.widgets, **{
            'distribution_type': forms.Select(attrs={'class': 'form-control'}),
            'water_source': forms.Select(attrs={'class': 'form-control'}),
            'households_served': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '8'
            }),
            'estimated_users': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of users'
            }),
            'distance_from_source_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Meters'
            }),
            'storage_capacity_litres': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Litres'
            }),
            'has_meter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
           'meter_reading_date': forms.DateInput(attrs={
               'class': 'form-control',
               'type': 'date'
           }),
           'last_meter_reading': forms.NumberInput(attrs={
               'class': 'form-control',
               'step': '0.01',
               'placeholder': 'Meter reading'
           }),
           'operates_24_7': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
           'operating_hours': forms.TextInput(attrs={
               'class': 'form-control',
               'placeholder': 'e.g., 06:00 - 18:00'
           }),
       })
   
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Set category to water
            self.fields['category'].initial = 'water'
            self.fields['category'].widget.attrs['readonly'] = True
            
            # Filter water sources to operational ones
            self.fields['water_source'].queryset = WaterSource.objects.filter(
                operational_status=True
            ).order_by('name')
            
            # Filter households to active ones
            self.fields['households_served'].queryset = Household.objects.filter(
                is_active=True
            ).order_by('head_of_household__last_name')
            
            # Make optional fields
            self.fields['households_served'].required = False
            self.fields['distance_from_source_meters'].required = False
            self.fields['storage_capacity_litres'].required = False
            self.fields['meter_reading_date'].required = False
            self.fields['last_meter_reading'].required = False
            self.fields['operating_hours'].required = False
        
        def clean(self):
            cleaned_data = super().clean()
            has_meter = cleaned_data.get('has_meter')
            meter_reading_date = cleaned_data.get('meter_reading_date')
            last_meter_reading = cleaned_data.get('last_meter_reading')
            operates_24_7 = cleaned_data.get('operates_24_7')
            operating_hours = cleaned_data.get('operating_hours')
            
            if has_meter and not last_meter_reading:
                raise ValidationError("Meter reading is required if the point has a meter")
            
            if not operates_24_7 and not operating_hours:
                raise ValidationError("Operating hours are required if not operating 24/7")
            
            return cleaned_data


class MaintenanceRecordForm(forms.ModelForm):
   """Form for maintenance records"""
   
   class Meta:
       model = MaintenanceRecord
       fields = [
           'asset', 'maintenance_type', 'status', 'scheduled_date',
           'completed_date', 'estimated_duration_hours', 'actual_duration_hours',
           'technician', 'contractor', 'description', 'work_performed',
           'parts_used', 'estimated_cost', 'actual_cost', 'next_maintenance_due',
           'recommendations', 'condition_before', 'condition_after'
       ]
       widgets = {
           'asset': forms.Select(attrs={'class': 'form-control'}),
           'maintenance_type': forms.Select(attrs={'class': 'form-control'}),
           'status': forms.Select(attrs={'class': 'form-control'}),
           'scheduled_date': forms.DateInput(attrs={
               'class': 'form-control',
               'type': 'date'
           }),
           'completed_date': forms.DateInput(attrs={
               'class': 'form-control',
               'type': 'date'
           }),
           'estimated_duration_hours': forms.NumberInput(attrs={
               'class': 'form-control',
               'step': '0.25',
               'placeholder': 'Hours'
           }),
           'actual_duration_hours': forms.NumberInput(attrs={
               'class': 'form-control',
               'step': '0.25',
               'placeholder': 'Hours'
           }),
           'technician': forms.Select(attrs={'class': 'form-control'}),
           'contractor': forms.TextInput(attrs={'class': 'form-control'}),
           'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'work_performed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'parts_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
           'estimated_cost': forms.NumberInput(attrs={
               'class': 'form-control',
               'step': '0.01',
               'placeholder': '0.00'
           }),
           'actual_cost': forms.NumberInput(attrs={
               'class': 'form-control',
               'step': '0.01',
               'placeholder': '0.00'
           }),
           'next_maintenance_due': forms.DateInput(attrs={
               'class': 'form-control',
               'type': 'date'
           }),
           'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
           'condition_before': forms.Select(attrs={'class': 'form-control'}),
           'condition_after': forms.Select(attrs={'class': 'form-control'}),
       }
   
   def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self.fields['asset'].queryset = InfrastructureAsset.objects.select_related('village').order_by('name')
       self.fields['technician'].queryset = CustomUser.objects.filter(is_active=True).order_by('first_name')
       self.fields['technician'].empty_label = "Select technician..."
       
       # Make optional fields
       self.fields['completed_date'].required = False
       self.fields['actual_duration_hours'].required = False
       self.fields['technician'].required = False
       self.fields['contractor'].required = False
       self.fields['work_performed'].required = False
       self.fields['parts_used'].required = False
       self.fields['estimated_cost'].required = False
       self.fields['actual_cost'].required = False
       self.fields['next_maintenance_due'].required = False
       self.fields['recommendations'].required = False
       self.fields['condition_before'].required = False
       self.fields['condition_after'].required = False
   
   def clean(self):
       cleaned_data = super().clean()
       scheduled_date = cleaned_data.get('scheduled_date')
       completed_date = cleaned_data.get('completed_date')
       status = cleaned_data.get('status')
       estimated_duration = cleaned_data.get('estimated_duration_hours')
       actual_duration = cleaned_data.get('actual_duration_hours')
       
       if completed_date and scheduled_date and completed_date < scheduled_date:
           raise ValidationError("Completion date cannot be before scheduled date")
       
       if status == 'completed' and not completed_date:
           raise ValidationError("Completion date is required for completed maintenance")
       
       if actual_duration and estimated_duration and actual_duration > estimated_duration * 3:
           self.add_error('actual_duration_hours', 
                        "Actual duration is significantly higher than estimated. Please verify.")
       
       return cleaned_data


class ServiceInterruptionForm(forms.ModelForm):
   """Form for service interruptions"""
   
   class Meta:
       model = ServiceInterruption
       fields = [
           'asset', 'interruption_type', 'severity', 'start_time',
           'end_time', 'estimated_restoration', 'affected_households',
           'estimated_affected_people', 'cause', 'description',
           'resolution_actions', 'communities_notified', 'notification_method',
           'is_resolved', 'resolution_date', 'lessons_learned'
       ]
       widgets = {
           'asset': forms.Select(attrs={'class': 'form-control'}),
           'interruption_type': forms.Select(attrs={'class': 'form-control'}),
           'severity': forms.Select(attrs={'class': 'form-control'}),
           'start_time': forms.DateTimeInput(attrs={
               'class': 'form-control',
               'type': 'datetime-local'
           }),
           'end_time': forms.DateTimeInput(attrs={
               'class': 'form-control',
               'type': 'datetime-local'
           }),
           'estimated_restoration': forms.DateTimeInput(attrs={
               'class': 'form-control',
               'type': 'datetime-local'
           }),
           'affected_households': forms.SelectMultiple(attrs={
               'class': 'form-control',
               'size': '8'
           }),
           'estimated_affected_people': forms.NumberInput(attrs={
               'class': 'form-control',
               'placeholder': 'Number of people affected'
           }),
           'cause': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'resolution_actions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'communities_notified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
           'notification_method': forms.TextInput(attrs={'class': 'form-control'}),
           'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
           'resolution_date': forms.DateTimeInput(attrs={
               'class': 'form-control',
               'type': 'datetime-local'
           }),
           'lessons_learned': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
       }
   
   def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self.fields['asset'].queryset = InfrastructureAsset.objects.select_related('village').order_by('name')
       self.fields['affected_households'].queryset = Household.objects.filter(
           is_active=True
       ).order_by('head_of_household__last_name')
       
       # Make optional fields
       self.fields['end_time'].required = False
       self.fields['estimated_restoration'].required = False
       self.fields['affected_households'].required = False
       self.fields['resolution_actions'].required = False
       self.fields['notification_method'].required = False
       self.fields['resolution_date'].required = False
       self.fields['lessons_learned'].required = False
   
   def clean(self):
       cleaned_data = super().clean()
       start_time = cleaned_data.get('start_time')
       end_time = cleaned_data.get('end_time')
       estimated_restoration = cleaned_data.get('estimated_restoration')
       is_resolved = cleaned_data.get('is_resolved')
       resolution_date = cleaned_data.get('resolution_date')
       
       if end_time and start_time and end_time <= start_time:
           raise ValidationError("End time must be after start time")
       
       if estimated_restoration and start_time and estimated_restoration <= start_time:
           raise ValidationError("Estimated restoration must be after start time")
       
       if is_resolved and not resolution_date:
           raise ValidationError("Resolution date is required when marking as resolved")
       
       if resolution_date and start_time and resolution_date < start_time:
           raise ValidationError("Resolution date cannot be before start time")
       
       return cleaned_data


class AssetInspectionForm(forms.ModelForm):
   """Form for asset inspections"""
   
   class Meta:
       model = AssetInspection
       fields = [
           'asset', 'inspection_type', 'inspection_date', 'inspector',
           'overall_condition', 'operational_status', 'safety_concerns',
           'structural_condition', 'electrical_condition', 'mechanical_condition',
           'immediate_actions_required', 'maintenance_recommendations',
           'upgrade_recommendations', 'next_inspection_date', 'priority_level',
           'inspection_photos', 'inspection_report'
       ]
       widgets = {
           'asset': forms.Select(attrs={'class': 'form-control'}),
           'inspection_type': forms.Select(attrs={'class': 'form-control'}),
           'inspection_date': forms.DateInput(attrs={
               'class': 'form-control',
               'type': 'date'
           }),
           'inspector': forms.Select(attrs={'class': 'form-control'}),
           'overall_condition': forms.Select(attrs={'class': 'form-control'}),
           'operational_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
           'safety_concerns': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'structural_condition': forms.Select(attrs={'class': 'form-control'}),
           'electrical_condition': forms.Select(attrs={'class': 'form-control'}),
           'mechanical_condition': forms.Select(attrs={'class': 'form-control'}),
           'immediate_actions_required': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'maintenance_recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'upgrade_recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           'next_inspection_date': forms.DateInput(attrs={
               'class': 'form-control',
               'type': 'date'
           }),
           'priority_level': forms.Select(attrs={'class': 'form-control'}),
           'inspection_photos': forms.FileInput(attrs={'class': 'form-control'}),
           'inspection_report': forms.FileInput(attrs={'class': 'form-control'}),
       }
   
   def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self.fields['asset'].queryset = InfrastructureAsset.objects.select_related('village').order_by('name')
       self.fields['inspector'].queryset = CustomUser.objects.filter(is_active=True).order_by('first_name')
       
       # Make optional fields
       self.fields['safety_concerns'].required = False
       self.fields['structural_condition'].required = False
       self.fields['electrical_condition'].required = False
       self.fields['mechanical_condition'].required = False
       self.fields['immediate_actions_required'].required = False
       self.fields['maintenance_recommendations'].required = False
       self.fields['upgrade_recommendations'].required = False
       self.fields['next_inspection_date'].required = False
       self.fields['inspection_photos'].required = False
       self.fields['inspection_report'].required = False
   
   def clean(self):
       cleaned_data = super().clean()
       inspection_date = cleaned_data.get('inspection_date')
       next_inspection_date = cleaned_data.get('next_inspection_date')
       
       if inspection_date and inspection_date > timezone.now().date():
           raise ValidationError("Inspection date cannot be in the future")
       
       if next_inspection_date and inspection_date and next_inspection_date <= inspection_date:
           raise ValidationError("Next inspection date must be after current inspection date")
       
       return cleaned_data


class QuickMaintenanceForm(forms.Form):
   """Quick form for scheduling maintenance"""
   
   MAINTENANCE_TYPES = [
       ('preventive', 'Preventive Maintenance'),
       ('corrective', 'Corrective Maintenance'),
       ('emergency', 'Emergency Repair'),
       ('inspection', 'Inspection'),
   ]
   
   maintenance_type = forms.ChoiceField(
       choices=MAINTENANCE_TYPES,
       widget=forms.Select(attrs={'class': 'form-control'})
   )
   scheduled_date = forms.DateField(
       widget=forms.DateInput(attrs={
           'class': 'form-control',
           'type': 'date'
       })
   )
   description = forms.CharField(
       widget=forms.Textarea(attrs={
           'class': 'form-control',
           'rows': 3,
           'placeholder': 'Describe the maintenance work required...'
       })
   )
   technician = forms.ModelChoiceField(
       queryset=CustomUser.objects.filter(is_active=True),
       empty_label="Select technician...",
       required=False,
       widget=forms.Select(attrs={'class': 'form-control'})
   )
   estimated_cost = forms.DecimalField(
       max_digits=10,
       decimal_places=2,
       required=False,
       widget=forms.NumberInput(attrs={
           'class': 'form-control',
           'step': '0.01',
           'placeholder': '0.00'
       })
   )
   
   def clean_scheduled_date(self):
       scheduled_date = self.cleaned_data.get('scheduled_date')
       if scheduled_date and scheduled_date < timezone.now().date():
           raise ValidationError("Scheduled date cannot be in the past")
       return scheduled_date


class BulkMaintenanceForm(forms.Form):
   """Form for bulk maintenance scheduling"""
   
   assets = forms.ModelMultipleChoiceField(
       queryset=InfrastructureAsset.objects.all(),
       widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
   )
   maintenance_type = forms.ChoiceField(
       choices=MaintenanceRecord.MAINTENANCE_TYPES,
       widget=forms.Select(attrs={'class': 'form-control'})
   )
   scheduled_date = forms.DateField(
       widget=forms.DateInput(attrs={
           'class': 'form-control',
           'type': 'date'
       })
   )
   description = forms.CharField(
       widget=forms.Textarea(attrs={
           'class': 'form-control',
           'rows': 3
       })
   )
   technician = forms.ModelChoiceField(
       queryset=CustomUser.objects.filter(is_active=True),
       empty_label="Select technician...",
       required=False,
       widget=forms.Select(attrs={'class': 'form-control'})
   )
   
   def __init__(self, *args, **kwargs):
       category = kwargs.pop('category', None)
       village = kwargs.pop('village', None)
       super().__init__(*args, **kwargs)
       
       queryset = InfrastructureAsset.objects.filter(operational_status=True)
       if category:
           queryset = queryset.filter(category=category)
       if village:
           queryset = queryset.filter(village=village)
       
       self.fields['assets'].queryset = queryset.order_by('name')
   
   def clean_scheduled_date(self):
       scheduled_date = self.cleaned_data.get('scheduled_date')
       if scheduled_date and scheduled_date < timezone.now().date():
           raise ValidationError("Scheduled date cannot be in the past")
       return scheduled_date
                