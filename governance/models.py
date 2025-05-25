# governance/models.py
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from _core.models import TimeStampedModel


from django.urls import reverse
from django.core.validators import RegexValidator

class Province(TimeStampedModel):
    """Model for provinces"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class District(TimeStampedModel):
    """Model for district municipalities"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name='districts')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# Enhance your existing Municipality model - replace the current one
class Municipality(TimeStampedModel):
    """Model for local municipalities"""
    MUNICIPALITY_TYPES = [
        ('A', 'Category A (Metropolitan)'),
        ('B', 'Category B (Local)'),
        ('C', 'Category C (District)'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^[A-Z]{2,3}\d{3}$',
            message='Code must be in format: ABC123 (2-3 letters followed by 3 digits)'
        )]
    )
    municipality_type = models.CharField(max_length=1, choices=MUNICIPALITY_TYPES, default='B')
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name='municipalities')
    contact_info = models.TextField()
    website = models.URLField(blank=True)
    mayor_name = models.CharField(max_length=100, blank=True)
    municipal_manager = models.CharField(max_length=100, blank=True)
    population = models.PositiveIntegerField(null=True, blank=True)
    area_km2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Municipalities"
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_absolute_url(self):
        return reverse('governance:municipality_detail', kwargs={'pk': self.pk})
    
    @property
    def total_traditional_councils(self):
        return self.traditional_councils.filter(is_active=True).count()
    
    @property
    def total_villages(self):
        return sum(council.villages.filter(is_active=True).count() 
                  for council in self.traditional_councils.filter(is_active=True))
        
    @property
    def total_ward_committees(self):
        return self.ward_committees.filter(is_active=True).count()
    
    @property
    def total_traditional_councils(self):
        return self.traditional_councils.filter(is_active=True).count()
    
    @property
    def total_villages(self):
        return sum(council.villages.filter(is_active=True).count() 
                  for council in self.traditional_councils.filter(is_active=True))



class WardCommittee(TimeStampedModel):
    """Model for ward committees that interface between municipalities and traditional councils"""
    COMMITTEE_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('dissolved', 'Dissolved'),
        ('forming', 'Forming'),
    ]
    
    name = models.CharField(max_length=100)
    ward_number = models.CharField(max_length=20)
    ward_code = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^WRD\d{3,4}$',
            message='Ward code must be in format: WRD123 or WRD1234'
        )]
    )
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name='ward_committees')
    ward_councillor = models.CharField(max_length=100, blank=True)
    councillor_contact = models.TextField(blank=True)
    geographic_boundaries = models.TextField()
    population = models.PositiveIntegerField(null=True, blank=True)
    committee_secretary = models.CharField(max_length=100, blank=True)
    meeting_venue = models.CharField(max_length=255, blank=True)
    established_date = models.DateField()
    status = models.CharField(max_length=20, choices=COMMITTEE_STATUS, default='active')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['ward_number', 'name']
        verbose_name_plural = "Ward Committees"
        unique_together = ['municipality', 'ward_number']
    
    def __str__(self):
        return f"Ward {self.ward_number} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('governance:ward_committee_detail', kwargs={'pk': self.pk})
    
    @property
    def total_traditional_councils(self):
        return self.traditional_councils.filter(is_active=True).count()
    
    @property
    def total_villages(self):
        return sum(council.villages.filter(is_active=True).count() 
                  for council in self.traditional_councils.filter(is_active=True))


    @property
    def current_performance_score(self):
        """Get the latest performance score"""
        latest_metric = self.performance_metrics.order_by('-reporting_period_end').first()
        return latest_metric.bridge_effectiveness_score if latest_metric else None
    
    @property
    def active_issues_count(self):
        """Count of unresolved community issues"""
        return self.community_issues.exclude(status__in=['resolved', 'closed']).count()
    
    @property
    def recent_community_engagement(self):
        """Recent community engagement activities"""
        from django.utils import timezone
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return self.engagements.filter(date_scheduled__gte=thirty_days_ago).count()


# Add ward committee member model
class WardCommitteeMember(TimeStampedModel):
    MEMBER_ROLES = [
        ('chairperson', 'Chairperson'),
        ('deputy_chairperson', 'Deputy Chairperson'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
        ('youth_rep', 'Youth Representative'),
        ('women_rep', 'Women Representative'),
        ('disability_rep', 'Disability Representative'),
    ]
    
    ward_committee = models.ForeignKey(WardCommittee, on_delete=models.CASCADE, related_name='committee_members')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='ward_committee_roles')
    role = models.CharField(max_length=50, choices=MEMBER_ROLES)
    appointed_date = models.DateField()
    term_end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['ward_committee', 'user', 'role']
        ordering = ['ward_committee__ward_number', 'role']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} (Ward {self.ward_committee.ward_number})"


# governance/models.py - Add these models

class CommunityEngagement(TimeStampedModel):
    """Track community engagement activities"""
    ENGAGEMENT_TYPES = [
        ('meeting', 'Community Meeting'),
        ('consultation', 'Public Consultation'),
        ('survey', 'Community Survey'),
        ('petition', 'Community Petition'),
        ('complaint', 'Community Complaint'),
        ('project_visit', 'Project Site Visit'),
        ('awareness', 'Awareness Campaign'),
        ('feedback', 'Municipal Feedback Session'),
    ]
    
    ENGAGEMENT_STATUS = [
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('follow_up_needed', 'Follow-up Needed'),
    ]
    
    ward_committee = models.ForeignKey(WardCommittee, on_delete=models.CASCADE, related_name='engagements')
    engagement_type = models.CharField(max_length=20, choices=ENGAGEMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_scheduled = models.DateTimeField()
    date_completed = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255)
    
    # Participation tracking
    expected_attendance = models.PositiveIntegerField(default=0)
    actual_attendance = models.PositiveIntegerField(default=0)
    
    # Municipal involvement
    municipal_officials_present = models.ManyToManyField(
        'users.CustomUser', 
        related_name='attended_engagements',
        blank=True
    )
    
    status = models.CharField(max_length=20, choices=ENGAGEMENT_STATUS, default='planned')
    outcomes = models.TextField(blank=True, help_text="Key outcomes and decisions")
    follow_up_actions = models.TextField(blank=True)
    
    # Impact measurement
    satisfaction_rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        help_text="Average satisfaction rating (1-5)"
    )
    
    class Meta:
        ordering = ['-date_scheduled']
    
    def __str__(self):
        return f"{self.get_engagement_type_display()} - {self.title}"
    
    @property
    def attendance_rate(self):
        if self.expected_attendance > 0:
            return (self.actual_attendance / self.expected_attendance) * 100
        return 0

class CommunityIssue(TimeStampedModel):
    """Track community issues and their resolution"""
    ISSUE_CATEGORIES = [
        ('infrastructure', 'Infrastructure'),
        ('service_delivery', 'Service Delivery'),
        ('safety_security', 'Safety & Security'),
        ('health', 'Health Services'),
        ('education', 'Education'),
        ('environment', 'Environment'),
        ('economic', 'Economic Development'),
        ('social', 'Social Issues'),
        ('governance', 'Governance'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    RESOLUTION_STATUS = [
        ('reported', 'Reported'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Under Investigation'),
        ('escalated', 'Escalated to Municipality'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('requires_budget', 'Requires Budget Allocation'),
    ]
    
    ward_committee = models.ForeignKey(WardCommittee, on_delete=models.CASCADE, related_name='community_issues')
    issue_number = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=ISSUE_CATEGORIES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Reporting details
    reported_by = models.CharField(max_length=100, help_text="Name of person reporting")
    reported_date = models.DateTimeField(auto_now_add=True)
    location_description = models.CharField(max_length=255)
    
    # Resolution tracking
    status = models.CharField(max_length=20, choices=RESOLUTION_STATUS, default='reported')
    assigned_to = models.ForeignKey(
        'users.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='assigned_issues'
    )
    
    # Municipal involvement
    escalated_to_municipality = models.BooleanField(default=False)
    escalation_date = models.DateTimeField(null=True, blank=True)
    municipal_reference = models.CharField(max_length=50, blank=True)
    
    # Resolution
    resolution_date = models.DateTimeField(null=True, blank=True)
    resolution_description = models.TextField(blank=True)
    resolution_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Follow-up
    community_satisfied = models.BooleanField(null=True, blank=True)
    satisfaction_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-reported_date']
    
    def __str__(self):
        return f"{self.issue_number} - {self.title}"
    
    @property
    def days_open(self):
        from django.utils import timezone
        end_date = self.resolution_date or timezone.now()
        return (end_date.date() - self.reported_date.date()).days
    
    def save(self, *args, **kwargs):
        if not self.issue_number:
            # Generate issue number: WRD001-2025-001
            latest = CommunityIssue.objects.filter(
                ward_committee=self.ward_committee
            ).order_by('-id').first()
            
            if latest and latest.issue_number:
                try:
                    last_num = int(latest.issue_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.issue_number = f"{self.ward_committee.ward_code}-{timezone.now().year}-{new_num:03d}"
        
        super().save(*args, **kwargs)

class MunicipalInteraction(TimeStampedModel):
    """Track interactions between ward committees and municipality"""
    INTERACTION_TYPES = [
        ('meeting', 'Official Meeting'),
        ('submission', 'Document Submission'),
        ('request', 'Service Request'),
        ('complaint', 'Formal Complaint'),
        ('proposal', 'Development Proposal'),
        ('budget_input', 'Budget Input'),
        ('feedback', 'Feedback Session'),
        ('joint_project', 'Joint Project'),
    ]
    
    INTERACTION_STATUS = [
        ('initiated', 'Initiated'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('pending_response', 'Pending Municipal Response'),
        ('follow_up_needed', 'Follow-up Needed'),
        ('closed', 'Closed'),
    ]
    
    ward_committee = models.ForeignKey(WardCommittee, on_delete=models.CASCADE, related_name='municipal_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Participants
    ward_committee_representatives = models.ManyToManyField(
        WardCommitteeMember,
        related_name='municipal_interactions'
    )
    municipal_officials = models.ManyToManyField(
        'users.CustomUser',
        related_name='ward_interactions'
    )
    
    # Timing
    date_initiated = models.DateTimeField(auto_now_add=True)
    date_scheduled = models.DateTimeField(null=True, blank=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=INTERACTION_STATUS, default='initiated')
    
    # Outcomes
    outcomes = models.TextField(blank=True)
    municipal_commitments = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Documents
    related_issues = models.ManyToManyField(CommunityIssue, blank=True)
    
    class Meta:
        ordering = ['-date_initiated']
    
    def __str__(self):
        return f"{self.get_interaction_type_display()} - {self.title}"

class CommitteePerformanceMetric(TimeStampedModel):
    """Track ward committee performance metrics"""
    ward_committee = models.ForeignKey(WardCommittee, on_delete=models.CASCADE, related_name='performance_metrics')
    reporting_period_start = models.DateField()
    reporting_period_end = models.DateField()
    
    # Engagement metrics
    community_meetings_held = models.PositiveIntegerField(default=0)
    total_community_attendance = models.PositiveIntegerField(default=0)
    issues_reported = models.PositiveIntegerField(default=0)
    issues_resolved = models.PositiveIntegerField(default=0)
    
    # Municipality interaction metrics
    municipal_meetings_attended = models.PositiveIntegerField(default=0)
    submissions_to_municipality = models.PositiveIntegerField(default=0)
    municipal_responses_received = models.PositiveIntegerField(default=0)
    
    # Development metrics
    development_projects_supported = models.PositiveIntegerField(default=0)
    community_projects_initiated = models.PositiveIntegerField(default=0)
    
    # Satisfaction scores (1-5)
    community_satisfaction_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    municipal_collaboration_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Calculated automatically
    bridge_effectiveness_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['ward_committee', 'reporting_period_start', 'reporting_period_end']
        ordering = ['-reporting_period_end']
    
    def calculate_bridge_effectiveness(self):
        """Calculate how effectively the committee serves as a bridge"""
        metrics = []
        
        # Issue resolution rate
        if self.issues_reported > 0:
            resolution_rate = (self.issues_resolved / self.issues_reported) * 100
            metrics.append(min(resolution_rate / 20, 5))  # Scale to 1-5
        
        # Community engagement
        if self.community_meetings_held > 0:
            avg_attendance = self.total_community_attendance / self.community_meetings_held
            engagement_score = min(avg_attendance / 10, 5)  # Scale based on expected attendance
            metrics.append(engagement_score)
        
        # Municipal interaction
        municipal_score = min(self.municipal_meetings_attended / 2, 5)  # Expect 2+ meetings per period
        metrics.append(municipal_score)
        
        # Satisfaction scores
        if self.community_satisfaction_score:
            metrics.append(self.community_satisfaction_score)
        if self.municipal_collaboration_score:
            metrics.append(self.municipal_collaboration_score)
        
        if metrics:
            self.bridge_effectiveness_score = sum(metrics) / len(metrics)
            self.save()
        
        return self.bridge_effectiveness_score

# Enhance your existing TraditionalCouncil model - replace the current one
class TraditionalCouncil(TimeStampedModel):
    """Model for traditional councils"""
    COUNCIL_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('dissolved', 'Dissolved'),
    ]
    
    name = models.CharField(max_length=100)
    leader_name = models.CharField(max_length=100)
    leader_title = models.CharField(max_length=50, default='Chief')
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name='traditional_councils')
    ward_committee = models.ForeignKey(WardCommittee, on_delete=models.PROTECT, related_name='traditional_councils', null=True, blank=True)
    contact_info = models.TextField()
    establishment_date = models.DateField()
    term_end_date = models.DateField(null=True, blank=True)
    geographic_jurisdiction = models.TextField()
    status = models.CharField(max_length=20, choices=COUNCIL_STATUS, default='active')
    recognition_certificate = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} - {self.leader_title} {self.leader_name}"
    
    def get_absolute_url(self):
        return reverse('governance:council_detail', kwargs={'pk': self.pk})
    
    @property
    def total_villages(self):
        return self.villages.filter(is_active=True).count()
    
    @property
    def is_term_expired(self):
        from django.utils import timezone
        return self.term_end_date and self.term_end_date < timezone.now().date()
    
    # Keep your existing is_term_active for backward compatibility
    @property
    def is_term_active(self):
        return timezone.now().date() <= self.term_end_date if self.term_end_date else True
    

class Village(TimeStampedModel):
    """Model for villages under traditional authority"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    traditional_council = models.ForeignKey(TraditionalCouncil, on_delete=models.PROTECT, related_name='villages')
    location = models.CharField(max_length=255)
    population = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)  # Add this field
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):  # Add this method
        return reverse('governance:village_detail', kwargs={'pk': self.pk})
    
    class Meta:
        ordering = ['name']

class CouncilMember(TimeStampedModel):
    ROLE_CHOICES = [
        ('chairperson', 'Chairperson'),
        ('deputy', 'Deputy Chairperson'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('elder', 'Elder'),
        ('member', 'Member'),
    ]
    
    council = models.ForeignKey(TraditionalCouncil, on_delete=models.CASCADE, related_name='council_members')
    # Use your CustomUser model
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='council_roles')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    appointed_date = models.DateField()
    term_end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['council', 'user', 'role']
        ordering = ['council__name', 'role']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} ({self.council.name})"

class CouncilMeeting(TimeStampedModel):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]
    
    council = models.ForeignKey(TraditionalCouncil, on_delete=models.CASCADE, related_name='meetings')
    title = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    agenda = models.TextField()
    minutes = models.TextField(blank=True, null=True)
    attendees = models.ManyToManyField(CouncilMember, related_name='attended_meetings', blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.date}"
    
    class Meta:
        ordering = ['-date', '-time']

class Resolution(TimeStampedModel):
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('amended', 'Amended'),
        ('implemented', 'Implemented'),
    ]
    
    meeting = models.ForeignKey(CouncilMeeting, on_delete=models.CASCADE, related_name='resolutions')
    title = models.CharField(max_length=255)
    description = models.TextField()
    proposed_by = models.ForeignKey(CouncilMember, on_delete=models.SET_NULL, null=True, related_name='proposed_resolutions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    date_implemented = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-created_at']
        
