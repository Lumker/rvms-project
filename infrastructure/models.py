# infrastructure/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from _core.models import TimeStampedModel, SoftDeleteModel
from governance.models import Village, Municipality, WardCommittee, TraditionalCouncil
from households.models import Household
import uuid

User = get_user_model()

class InfrastructureAsset(SoftDeleteModel):
    """Base model for all infrastructure assets"""
    ASSET_CATEGORIES = [
        ('water', 'Water Infrastructure'),
        ('electricity', 'Electricity Infrastructure'),
        ('roads', 'Roads & Transport'),
        ('health', 'Health Facilities'),
        ('education', 'Education Facilities'),
        ('communication', 'Communication Infrastructure'),
        ('sanitation', 'Sanitation Infrastructure'),
        ('community', 'Community Facilities'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('critical', 'Critical'),
        ('non_functional', 'Non-Functional'),
    ]
    
    OWNERSHIP_TYPES = [
        ('government', 'Government'),
        ('municipality', 'Municipality'),
        ('community', 'Community'),
        ('private', 'Private'),
        ('ngo', 'NGO/Non-Profit'),
        ('traditional', 'Traditional Authority'),
    ]
    
    # Basic Information
    asset_id = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=ASSET_CATEGORIES)
    description = models.TextField(blank=True)
    
    # Location
    village = models.ForeignKey(Village, on_delete=models.PROTECT, related_name='infrastructure_assets')
    ward_committee = models.ForeignKey(WardCommittee, on_delete=models.PROTECT, null=True, blank=True)
    gps_coordinates = models.CharField(max_length=50, blank=True, help_text="Format: -26.1234, 28.5678")
    physical_address = models.TextField()
    
    # Status & Condition
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    operational_status = models.BooleanField(default=True, help_text="Is the asset currently operational?")
    last_inspection_date = models.DateField(null=True, blank=True)
    next_inspection_due = models.DateField(null=True, blank=True)
    
    # Ownership & Management
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_TYPES, default='government')
    owner_details = models.TextField(blank=True)
    custodian = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='custodian_assets',
        help_text="Person responsible for asset maintenance"
    )
    
    # Financial
    estimated_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Estimated replacement value in ZAR"
    )
    annual_maintenance_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Annual maintenance budget in ZAR"
    )
    
    # Construction/Installation
    installation_date = models.DateField(null=True, blank=True)
    expected_lifespan_years = models.PositiveIntegerField(null=True, blank=True)
    contractor = models.CharField(max_length=200, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    
    # Documentation
    asset_photo = models.ImageField(upload_to='infrastructure/assets/', blank=True, null=True)
    technical_documents = models.FileField(upload_to='infrastructure/documents/', blank=True, null=True)
    
    class Meta:
        ordering = ['village__name', 'category', 'name']
        verbose_name = "Infrastructure Asset"
        verbose_name_plural = "Infrastructure Assets"
    
    def __str__(self):
        return f"{self.name} ({self.village.name})"
    
    def save(self, *args, **kwargs):
        if not self.asset_id:
            # Generate asset ID: INF-<CATEGORY>-<YEAR>-<SEQUENCE>
            year = timezone.now().year
            category_code = self.category.upper()[:3]
            latest = InfrastructureAsset.objects.filter(
                category=self.category,
                created_at__year=year
            ).order_by('-id').first()
            
            if latest and latest.asset_id:
                try:
                    last_num = int(latest.asset_id.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.asset_id = f"INF-{category_code}-{year}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('infrastructure:asset_detail', kwargs={'pk': self.pk})
    
    @property
    def age_years(self):
        """Calculate asset age in years"""
        if self.installation_date:
            return (timezone.now().date() - self.installation_date).days // 365
        return None
    
    @property
    def remaining_lifespan_years(self):
        """Calculate remaining lifespan"""
        if self.expected_lifespan_years and self.age_years:
            return max(0, self.expected_lifespan_years - self.age_years)
        return None
    
    @property
    def condition_score(self):
        """Numeric condition score for analytics"""
        scores = {
            'excellent': 5,
            'good': 4,
            'fair': 3,
            'poor': 2,
            'critical': 1,
            'non_functional': 0
        }
        return scores.get(self.condition, 0)
    
    @property
    def is_overdue_inspection(self):
        """Check if inspection is overdue"""
        return self.next_inspection_due and self.next_inspection_due < timezone.now().date()


# Water Infrastructure Models
class WaterSource(InfrastructureAsset):
    """Water sources like boreholes, springs, rivers"""
    SOURCE_TYPES = [
        ('borehole', 'Borehole'),
        ('spring', 'Natural Spring'),
        ('river', 'River/Stream'),
        ('dam', 'Dam/Reservoir'),
        ('rainwater', 'Rainwater Harvesting'),
        ('municipal', 'Municipal Supply'),
        ('other', 'Other'),
    ]
    
    WATER_QUALITY = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('acceptable', 'Acceptable'),
        ('poor', 'Poor'),
        ('contaminated', 'Contaminated'),
    ]
    
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    water_quality = models.CharField(max_length=20, choices=WATER_QUALITY, default='good')
    daily_capacity_litres = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Daily water production capacity in litres"
    )
    depth_meters = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Depth in meters (for boreholes)"
    )
    yield_litres_per_hour = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Water yield per hour"
    )
    last_water_test_date = models.DateField(null=True, blank=True)
    water_test_results = models.TextField(blank=True, help_text="Latest water quality test results")
    pump_type = models.CharField(max_length=100, blank=True)
    power_source = models.CharField(
        max_length=50, 
        blank=True,
        choices=[
            ('electric', 'Electric Grid'),
            ('solar', 'Solar Power'),
            ('generator', 'Generator'),
            ('hand_pump', 'Hand Pump'),
            ('wind', 'Wind Power'),
            ('gravity', 'Gravity Fed'),
        ]
    )
    
    class Meta:
        verbose_name = "Water Source"
        verbose_name_plural = "Water Sources"
    
    def save(self, *args, **kwargs):
        self.category = 'water'
        super().save(*args, **kwargs)


class WaterDistributionPoint(InfrastructureAsset):
    """Water distribution points like taps, tanks, kiosks"""
    DISTRIBUTION_TYPES = [
        ('communal_tap', 'Communal Tap'),
        ('household_tap', 'Household Tap'),
        ('water_tank', 'Water Tank'),
        ('water_kiosk', 'Water Kiosk'),
        ('standpipe', 'Standpipe'),
        ('tanker_point', 'Water Tanker Point'),
    ]
    
    distribution_type = models.CharField(max_length=20, choices=DISTRIBUTION_TYPES)
    water_source = models.ForeignKey(
        WaterSource, 
        on_delete=models.PROTECT, 
        related_name='distribution_points'
    )
    households_served = models.ManyToManyField(
        Household, 
        blank=True,
        related_name='water_distribution_points'
    )
    estimated_users = models.PositiveIntegerField(
        default=0,
        help_text="Estimated number of people using this point"
    )
    distance_from_source_meters = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Distance from water source in meters"
    )
    storage_capacity_litres = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Storage capacity for tanks"
    )
    has_meter = models.BooleanField(default=False)
    meter_reading_date = models.DateField(null=True, blank=True)
    last_meter_reading = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Service hours
    operates_24_7 = models.BooleanField(default=True)
    operating_hours = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Operating hours if not 24/7"
    )
    
    class Meta:
        verbose_name = "Water Distribution Point"
        verbose_name_plural = "Water Distribution Points"
    
    def save(self, *args, **kwargs):
        self.category = 'water'
        super().save(*args, **kwargs)
    
    @property
    def users_per_point_ratio(self):
        """Calculate users per distribution point for planning"""
        return self.estimated_users


class MaintenanceRecord(TimeStampedModel):
    """Maintenance records for infrastructure assets"""
    MAINTENANCE_TYPES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('emergency', 'Emergency Repair'),
        ('upgrade', 'Upgrade/Improvement'),
        ('inspection', 'Inspection'),
        ('cleaning', 'Cleaning'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('deferred', 'Deferred'),
    ]
    
    asset = models.ForeignKey(
        InfrastructureAsset, 
        on_delete=models.CASCADE, 
        related_name='maintenance_records'
    )
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Scheduling
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    estimated_duration_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    actual_duration_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Personnel
    technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='maintenance_performed'
    )
    contractor = models.CharField(max_length=200, blank=True)
    
    # Work Details
    description = models.TextField(help_text="Description of maintenance work")
    work_performed = models.TextField(blank=True, help_text="Actual work performed")
    parts_used = models.TextField(blank=True, help_text="Parts and materials used")
    
    # Costs
    estimated_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    actual_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Follow-up
    next_maintenance_due = models.DateField(null=True, blank=True)
    recommendations = models.TextField(blank=True)
    
    # Asset condition after maintenance
    condition_before = models.CharField(
        max_length=20, 
        choices=InfrastructureAsset.CONDITION_CHOICES,
        blank=True
    )
    condition_after = models.CharField(
        max_length=20, 
        choices=InfrastructureAsset.CONDITION_CHOICES,
        blank=True
    )
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = "Maintenance Record"
        verbose_name_plural = "Maintenance Records"
    
    def __str__(self):
        return f"{self.get_maintenance_type_display()} - {self.asset.name}"
    
    def save(self, *args, **kwargs):
        # Auto-update asset's next inspection due date
        if self.status == 'completed' and self.next_maintenance_due:
            self.asset.next_inspection_due = self.next_maintenance_due
            self.asset.last_inspection_date = self.completed_date or timezone.now().date()
            if self.condition_after:
                self.asset.condition = self.condition_after
            self.asset.save()
        
        super().save(*args, **kwargs)


class ServiceInterruption(TimeStampedModel):
    """Track service interruptions and outages"""
    INTERRUPTION_TYPES = [
        ('planned', 'Planned Maintenance'),
        ('unplanned', 'Unplanned Outage'),
        ('emergency', 'Emergency Shutdown'),
        ('shortage', 'Resource Shortage'),
        ('equipment_failure', 'Equipment Failure'),
        ('power_outage', 'Power Outage'),
        ('weather', 'Weather Related'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low Impact'),
        ('medium', 'Medium Impact'),
        ('high', 'High Impact'),
        ('critical', 'Critical'),
    ]
    
    asset = models.ForeignKey(
        InfrastructureAsset, 
        on_delete=models.CASCADE, 
        related_name='service_interruptions'
    )
    interruption_type = models.CharField(max_length=20, choices=INTERRUPTION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # Timeline
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    estimated_restoration = models.DateTimeField(null=True, blank=True)
    
    # Impact
    affected_households = models.ManyToManyField(
        Household, 
        blank=True,
        related_name='service_interruptions'
    )
    estimated_affected_people = models.PositiveIntegerField(default=0)
    
    # Details
    cause = models.TextField(help_text="Cause of interruption")
    description = models.TextField(help_text="Detailed description")
    resolution_actions = models.TextField(blank=True)
    
    # Communication
    communities_notified = models.BooleanField(default=False)
    notification_method = models.CharField(
        max_length=100, 
        blank=True,
        help_text="How communities were notified"
    )
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_date = models.DateTimeField(null=True, blank=True)
    lessons_learned = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = "Service Interruption"
        verbose_name_plural = "Service Interruptions"
    
    def __str__(self):
        status = "Resolved" if self.is_resolved else "Ongoing"
        return f"{self.asset.name} - {self.get_interruption_type_display()} ({status})"
    
    @property
    def duration_hours(self):
        """Calculate duration of interruption"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return None
    
    @property
    def is_ongoing(self):
        """Check if interruption is still ongoing"""
        return not self.is_resolved and (not self.end_time or self.end_time > timezone.now())


class AssetInspection(TimeStampedModel):
    """Regular inspections of infrastructure assets"""
    INSPECTION_TYPES = [
        ('routine', 'Routine Inspection'),
        ('safety', 'Safety Inspection'),
        ('compliance', 'Compliance Check'),
        ('damage_assessment', 'Damage Assessment'),
        ('pre_maintenance', 'Pre-Maintenance'),
        ('post_maintenance', 'Post-Maintenance'),
    ]
    
    asset = models.ForeignKey(
        InfrastructureAsset, 
        on_delete=models.CASCADE, 
        related_name='inspections'
    )
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPES)
    inspection_date = models.DateField()
    inspector = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='inspections_performed'
    )
    
    # Inspection Results
    overall_condition = models.CharField(
        max_length=20, 
        choices=InfrastructureAsset.CONDITION_CHOICES
    )
    operational_status = models.BooleanField()
    safety_concerns = models.TextField(blank=True)
    
    # Detailed Findings
    structural_condition = models.CharField(
        max_length=20, 
        choices=InfrastructureAsset.CONDITION_CHOICES,
        blank=True
    )
    electrical_condition = models.CharField(
        max_length=20, 
        choices=InfrastructureAsset.CONDITION_CHOICES,
        blank=True
    )
    mechanical_condition = models.CharField(
        max_length=20, 
        choices=InfrastructureAsset.CONDITION_CHOICES,
        blank=True
    )
    
    # Recommendations
    immediate_actions_required = models.TextField(blank=True)
    maintenance_recommendations = models.TextField(blank=True)
    upgrade_recommendations = models.TextField(blank=True)
    
    # Follow-up
    next_inspection_date = models.DateField(null=True, blank=True)
    priority_level = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    
    # Documentation
    inspection_photos = models.ImageField(
        upload_to='infrastructure/inspections/', 
        blank=True, 
        null=True
    )
    inspection_report = models.FileField(
        upload_to='infrastructure/reports/', 
        blank=True, 
        null=True
    )
    
    class Meta:
        ordering = ['-inspection_date']
        verbose_name = "Asset Inspection"
        verbose_name_plural = "Asset Inspections"
    
    def __str__(self):
        return f"{self.asset.name} - {self.get_inspection_type_display()} ({self.inspection_date})"
    
    def save(self, *args, **kwargs):
        # Update asset condition and next inspection date
        self.asset.condition = self.overall_condition
        self.asset.operational_status = self.operational_status
        self.asset.last_inspection_date = self.inspection_date
        if self.next_inspection_date:
            self.asset.next_inspection_due = self.next_inspection_date
        self.asset.save()
        
        super().save(*args, **kwargs)