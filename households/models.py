# households/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from _core.models import TimeStampedModel
from _core.validators import validate_sa_id_number, sa_phone_validator
from governance.models import Village, Municipality, TraditionalCouncil, WardCommittee
import uuid
from datetime import date

class Household(TimeStampedModel):
    """Household as the core unit of rural development"""
    HOUSING_TYPE_CHOICES = [
        ('traditional', 'Traditional Dwelling'),
        ('formal', 'Formal House'),
        ('informal', 'Informal Dwelling'),
        ('rondavel', 'Rondavel'),
        ('apartment', 'Apartment/Flat'),
        ('backyard_dwelling', 'Backyard Dwelling'),
        ('hostel', 'Hostel'),
        ('other', 'Other'),
    ]
    
    LAND_TENURE_CHOICES = [
        ('traditional', 'Traditional/Communal'),
        ('freehold', 'Freehold'),
        ('leasehold', 'Leasehold'),
        ('rental', 'Rental'),
        ('informal', 'Informal Settlement'),
        ('government', 'Government Housing'),
        ('other', 'Other'),
    ]
    
    WATER_SOURCE_CHOICES = [
        ('piped_indoor', 'Piped Water Inside Dwelling'),
        ('piped_yard', 'Piped Water in Yard'),
        ('communal_tap', 'Communal Tap'),
        ('borehole', 'Borehole'),
        ('well', 'Well'),
        ('spring', 'Natural Spring'),
        ('river_dam', 'River/Dam'),
        ('rainwater', 'Rainwater Harvesting'),
        ('water_vendor', 'Water Vendor/Tanker'),
        ('other', 'Other'),
    ]
    
    ELECTRICITY_SOURCE_CHOICES = [
        ('grid', 'Eskom Grid'),
        ('solar', 'Solar Power'),
        ('generator', 'Generator'),
        ('candles', 'Candles'),
        ('paraffin', 'Paraffin'),
        ('gas', 'Gas'),
        ('battery', 'Battery'),
        ('none', 'No Electricity'),
        ('other', 'Other'),
    ]
    
    household_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Geographic relationships
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name='households')
    ward_committee = models.ForeignKey(
        WardCommittee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='households',
        help_text="Ward committee responsible for this household"
    )
    
    # Address and location
    physical_address = models.TextField(help_text="Physical address or description")
    postal_address = models.TextField(blank=True, help_text="Postal address if different")
    gps_coordinates = models.CharField(
        max_length=50, 
        blank=True,
        help_text="GPS coordinates (latitude, longitude)"
    )
    
    # Housing details
    housing_type = models.CharField(max_length=20, choices=HOUSING_TYPE_CHOICES)
    land_tenure = models.CharField(max_length=20, choices=LAND_TENURE_CHOICES)
    rooms_count = models.PositiveIntegerField(default=1, help_text="Number of rooms")
    plot_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Plot size in square meters"
    )
    
    # Services and infrastructure
    water_source = models.CharField(max_length=20, choices=WATER_SOURCE_CHOICES)
    electricity_source = models.CharField(max_length=20, choices=ELECTRICITY_SOURCE_CHOICES)
    has_toilet = models.BooleanField(default=False)
    toilet_type = models.CharField(max_length=100, blank=True)
    waste_disposal = models.CharField(max_length=100, blank=True)
    
    # Economic information
    estimated_monthly_income = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Estimated total household monthly income"
    )
    main_income_source = models.CharField(max_length=100, blank=True)
    
    # Registration details
    established_date = models.DateField(
        null=True, 
        blank=True,
        help_text="When the household was established"
    )
    registration_date = models.DateField(
        auto_now_add=True,
        help_text="When this record was created"
    )
    verified = models.BooleanField(
        default=False,
        help_text="Whether household data has been verified"
    )
    verified_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_households'
    )
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    special_circumstances = models.TextField(
        blank=True,
        help_text="Any special circumstances (disability, elderly, child-headed, etc.)"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['household_id']
        indexes = [
            models.Index(fields=['village', 'is_active']),
            models.Index(fields=['ward_committee', 'is_active']),
            models.Index(fields=['housing_type']),
        ]
    
    def __str__(self):
        return f"Household {self.household_id} - {self.village.name}"
    
    def generate_household_id(self):
        """Generate a unique household ID: VIL001-HH-001234"""
        village_code = self.village.code if self.village.code else self.village.name[:3].upper()
        
        # Get the count of households in this village for sequential numbering
        existing_count = Household.objects.filter(village=self.village).count()
        sequential_number = existing_count + 1
        
        return f"{village_code}-HH-{sequential_number:06d}"
    
    def save(self, *args, **kwargs):
        # Generate household ID if not exists
        if not self.household_id:
            self.household_id = self.generate_household_id()
        
        # Auto-assign ward committee based on village
        if not self.ward_committee and self.village:
            # Try to find ward committee that includes this village
            try:
                traditional_council = self.village.traditional_council
                if traditional_council and traditional_council.ward_committee:
                    self.ward_committee = traditional_council.ward_committee
            except:
                pass
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate household data"""
        if self.gps_coordinates:
            # Basic GPS validation (you could make this more sophisticated)
            try:
                coords = self.gps_coordinates.split(',')
                if len(coords) != 2:
                    raise ValidationError("GPS coordinates must be in format: latitude,longitude")
                lat, lon = float(coords[0].strip()), float(coords[1].strip())
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise ValidationError("Invalid GPS coordinates")
            except (ValueError, IndexError):
                raise ValidationError("Invalid GPS coordinates format")
    
    @property
    def resident_count(self):
        """Total number of residents in household"""
        return self.residents.filter(is_active=True).count()
    
    @property
    def adult_count(self):
        """Number of adults (18+) in household"""
        return self.residents.filter(
            is_active=True,
            date_of_birth__lt=date.today().replace(year=date.today().year - 18)
        ).count()
    
    @property
    def child_count(self):
        """Number of children (<18) in household"""
        return self.residents.filter(
            is_active=True,
            date_of_birth__gte=date.today().replace(year=date.today().year - 18)
        ).count()
    
    @property
    def head_of_household(self):
        """Get the household head"""
        try:
            return self.residents.get(is_head_of_household=True, is_active=True)
        except Resident.DoesNotExist:
            return None
        except Resident.MultipleObjectsReturned:
            # Fix multiple heads issue
            heads = self.residents.filter(is_head_of_household=True, is_active=True)
            first_head = heads.first()
            heads.exclude(pk=first_head.pk).update(is_head_of_household=False)
            return first_head
    
    @property
    def municipality(self):
        """Get municipality through village"""
        return self.village.traditional_council.municipality if self.village.traditional_council else None
    
    @property
    def total_household_income(self):
        """Calculate total household income from all residents"""
        total = self.residents.filter(
            is_active=True,
            monthly_income__isnull=False
        ).aggregate(
            total=models.Sum('monthly_income')
        )['total']
        return total or 0

class Resident(TimeStampedModel):
    """Individual resident model linked to household"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
        ('cohabiting', 'Cohabiting'),
    ]
    
    EDUCATION_CHOICES = [
        ('none', 'No Formal Education'),
        ('primary_incomplete', 'Primary Incomplete'),
        ('primary_complete', 'Primary Complete'),
        ('secondary_incomplete', 'Secondary Incomplete'),
        ('matric', 'Matric/Grade 12'),
        ('tertiary_diploma', 'Diploma/Certificate'),
        ('degree', 'University Degree'),
        ('postgraduate', 'Postgraduate'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('employed_formal', 'Employed (Formal)'),
        ('employed_informal', 'Employed (Informal)'),
        ('self_employed', 'Self Employed'),
        ('unemployed', 'Unemployed'),
        ('student', 'Student'),
        ('pensioner', 'Pensioner'),
        ('homemaker', 'Homemaker'),
        ('disabled', 'Unable to Work (Disability)'),
        ('other', 'Other'),
    ]
    
    # Personal identification
    id_number = models.CharField(
        max_length=13, 
        unique=True,
        validators=[validate_sa_id_number],
        help_text="South African ID Number (13 digits)"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Household relationship
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='residents')
    is_head_of_household = models.BooleanField(default=False)
    relationship_to_head = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Relationship to household head (spouse, child, parent, etc.)"
    )
    
    # Contact information
    phone_number = models.CharField(
        max_length=15, 
        blank=True,
        validators=[sa_phone_validator]
    )
    email = models.EmailField(blank=True)
    alternative_contact = models.CharField(max_length=255, blank=True)
    
    # Demographics
    marital_status = models.CharField(
        max_length=20, 
        choices=MARITAL_STATUS_CHOICES, 
        blank=True
    )
    education_level = models.CharField(
        max_length=30, 
        choices=EDUCATION_CHOICES, 
        blank=True
    )
    employment_status = models.CharField(
        max_length=30, 
        choices=EMPLOYMENT_STATUS_CHOICES, 
        blank=True
    )
    occupation = models.CharField(max_length=100, blank=True)
    employer = models.CharField(max_length=100, blank=True)
    monthly_income = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Government support
    receives_grants = models.BooleanField(default=False)
    grant_types = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Types of grants received (comma-separated)"
    )
    grant_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total monthly grant amount"
    )
    
    # Health and special needs
    has_disability = models.BooleanField(default=False)
    disability_type = models.CharField(max_length=100, blank=True)
    chronic_illnesses = models.TextField(blank=True)
    special_needs = models.TextField(blank=True)
    
    # System integration
    user_account = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resident_profile',
        help_text="Linked system user account if resident has access"
    )
    
    # Documentation
    photo = models.ImageField(upload_to='resident_photos/', null=True, blank=True)
    id_document = models.FileField(upload_to='resident_documents/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether resident still lives in this household"
    )
    date_moved_in = models.DateField(null=True, blank=True)
    date_moved_out = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['household', 'is_active']),
            models.Index(fields=['id_number']),
            models.Index(fields=['is_head_of_household']),
            models.Index(fields=['employment_status']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id_number})"
    
    def save(self, *args, **kwargs):
        # Extract date of birth from ID number if not provided
        if self.id_number and not self.date_of_birth:
            self.date_of_birth = self.extract_dob_from_id()
        
        # Extract gender from ID number if not provided
        if self.id_number and not self.gender:
            self.gender = self.extract_gender_from_id()
        
        # Ensure only one head of household per household
        if self.is_head_of_household:
            Resident.objects.filter(
                household=self.household,
                is_head_of_household=True,
                is_active=True
            ).exclude(pk=self.pk if self.pk else -1).update(is_head_of_household=False)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate resident data"""
        # Validate ID number date of birth matches
        if self.id_number and self.date_of_birth:
            extracted_dob = self.extract_dob_from_id()
            if extracted_dob and extracted_dob != self.date_of_birth:
                raise ValidationError("Date of birth doesn't match ID number")
        
        # Validate move out date
        if self.date_moved_out and self.date_moved_in:
            if self.date_moved_out <= self.date_moved_in:
                raise ValidationError("Move out date must be after move in date")
    
    def extract_dob_from_id(self):
        """Extract date of birth from SA ID number"""
        if len(self.id_number) != 13:
            return None
        
        try:
            year_part = int(self.id_number[:2])
            month = int(self.id_number[2:4])
            day = int(self.id_number[4:6])
            
            # Determine century (assuming current system)
            current_year = date.today().year
            if year_part <= (current_year % 100):
                year = 2000 + year_part
            else:
                year = 1900 + year_part
            
            return date(year, month, day)
        except (ValueError, TypeError):
            return None
    
    def extract_gender_from_id(self):
        """Extract gender from SA ID number"""
        if len(self.id_number) != 13:
            return None
        
        try:
            gender_digit = int(self.id_number[6])
            return 'M' if gender_digit >= 5 else 'F'
        except (ValueError, IndexError):
            return None
    
    @property
    def age(self):
        """Calculate current age"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def full_name(self):
        """Full name of resident"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_adult(self):
        """Check if resident is adult (18+)"""
        return self.age >= 18
    
    @property
    def is_senior(self):
        """Check if resident is senior citizen (60+)"""
        return self.age >= 60
    
    @property
    def total_monthly_income(self):
        """Calculate total monthly income including grants"""
        total = self.monthly_income or 0
        if self.grant_amount:
            total += self.grant_amount
        return total

class HouseholdService(TimeStampedModel):
    """Track services available to households"""
    SERVICE_TYPES = [
        ('water', 'Water Supply'),
        ('electricity', 'Electricity'),
        ('sanitation', 'Sanitation'),
        ('waste', 'Waste Collection'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('transport', 'Public Transport'),
        ('communication', 'Communication/Internet'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('partial', 'Partially Available'),
        ('unavailable', 'Not Available'),
        ('planned', 'Planned'),
        ('under_construction', 'Under Construction'),
    ]
    
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    quality_rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Quality rating 1-5 (5 being excellent)"
    )
    distance_to_service = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Distance to service in kilometers"
    )
    monthly_cost = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Monthly cost for this service"
    )
    notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['household', 'service_type']
        ordering = ['household', 'service_type']
    
    def __str__(self):
        return f"{self.household.household_id} - {self.get_service_type_display()}"