# USERS/MODELS.PY

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from _core.models import TimeStampedModel
from _core.validators import sa_phone_validator, validate_sa_id_number
from django.utils import timezone
import os

def user_profile_picture_path(instance, filename):
    """Generate file path for user profile pictures"""
    ext = filename.split('.')[-1]
    filename = f'profile_{instance.user.id}.{ext}'
    return os.path.join('profile_pictures/', filename)

class CustomUser(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    
    # Additional fields beyond the default User model
    email = models.EmailField(unique=True)  # Make email unique
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        validators=[sa_phone_validator],
        help_text="Phone number in format: +27XXXXXXXXX or 0XXXXXXXXX"
    )
    id_number = models.CharField(
        max_length=13, 
        blank=True, 
        validators=[validate_sa_id_number],
        help_text="South African ID Number (13 digits)",
        unique=True,
        null=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def full_name(self):
        return self.get_full_name() or self.username
    
    @property
    def unread_notifications_count(self):
        """Get count of unread notifications"""
        return self.notifications.filter(is_read=False).count()
    
    @property
    def unread_messages_count(self):
        """Get count of unread messages"""
        return self.received_messages.filter(is_read=False).count()

class UserProfile(TimeStampedModel):
    """Extended user profile model"""
    
    ROLE_CHOICES = [
        ('admin', 'System Administrator'),
        ('governance_admin', 'Governance Administrator'),
        ('council_member', 'Council Member'),
        ('village_admin', 'Village Administrator'),
        ('villager', 'Villager'),
        ('staff', 'Staff Member'),
    ]
    
    REGISTRATION_STATUS = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    REGISTRATION_METHOD = [
        ('self', 'Self Registration'),
        ('admin', 'Admin Created'),
        ('bulk', 'Bulk Import'),
        ('invitation', 'Invited'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    
    # Profile Picture and Personal Info
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path, 
        blank=True, 
        null=True,
        help_text="Profile picture (JPG, PNG, GIF - Max 2MB)"
    )
    bio = models.TextField(blank=True, help_text="Brief description about yourself")
    department = models.CharField(max_length=100, blank=True, help_text="Department or division")
    
    # Role and Permissions
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='villager')
    practice_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Address Information
    address = models.TextField(blank=True)
    current_address = models.TextField(blank=True, help_text="Current residential address")
    
    # Profile status
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Registration workflow
    registration_status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='pending')
    registration_method = models.CharField(max_length=20, choices=REGISTRATION_METHOD, default='self')
    registration_reason = models.TextField(blank=True)
    
    # Approval workflow
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_users'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Geographic context
    intended_ward = models.ForeignKey('governance.WardCommittee', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact verification
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    
    # Preferences
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User notification preferences"
    )
    theme_preference = models.CharField(
        max_length=20, 
        choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')], 
        default='light'
    )
    language_preference = models.CharField(
        max_length=10, 
        choices=[('en', 'English'), ('af', 'Afrikaans'), ('zu', 'Zulu'), ('xh', 'Xhosa')], 
        default='en'
    )
    
    # Activity tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"
    
    def get_avatar_url(self):
        """Get profile picture URL or default avatar"""
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/assets/img/profiles/default-avatar.png'
    
    def get_display_name(self):
        """Get the best display name for the user"""
        if self.user.get_full_name():
            return self.user.get_full_name()
        return self.user.username
    
    @property
    def is_council_member(self):
        return hasattr(self.user, 'council_roles') and self.user.council_roles.filter(is_active=True).exists()
    
    @property
    def is_governance_admin(self):
        return self.role in ['admin', 'governance_admin'] or self.user.is_superuser
    
    @property
    def can_approve_users(self):
        """Check if user can approve other users"""
        return self.role in ['admin', 'governance_admin'] or self.user.is_superuser
    
    @property
    def notification_settings(self):
        """Get notification settings with defaults"""
        default_settings = {
            'email_notifications': True,
            'document_updates': True,
            'meeting_reminders': True,
            'system_updates': False,
            'weekly_digest': True
        }
        return {**default_settings, **self.notification_preferences}
    
    def approve_registration(self, approved_by_user):
        """Approve user registration"""
        self.registration_status = 'approved'
        self.approved_by = approved_by_user
        self.approval_date = timezone.now()
        self.save()
        
        # Create notification
        self.create_notification(
            'registration_approved',
            'Registration Approved',
            'Your registration has been approved. Welcome to the Rural Village Management System!'
        )
    
    def reject_registration(self, rejected_by_user, reason=""):
        """Reject user registration"""
        self.registration_status = 'rejected'
        self.approved_by = rejected_by_user
        self.rejection_reason = reason
        self.save()
        
        # Create notification
        self.create_notification(
            'registration_rejected',
            'Registration Rejected',
            f'Your registration has been rejected. Reason: {reason}'
        )
    
    def create_notification(self, notification_type, title, message, related_object=None):
        """Helper method to create notifications"""
        UserNotification.objects.create(
            user=self.user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_id=related_object.id if related_object else None,
            related_object_type=related_object.__class__.__name__ if related_object else None
        )
    
    def update_login_info(self, ip_address):
        """Update login information"""
        self.last_login_ip = ip_address
        self.login_count += 1
        self.save(update_fields=['last_login_ip', 'login_count'])


# Notification Model (within users app)
class UserNotification(TimeStampedModel):
    """User notifications model"""
    
    NOTIFICATION_TYPES = [
        ('document_approved', 'Document Approved'),
        ('document_generated', 'Document Generated'),
        ('document_delivered', 'Document Delivered'),
        ('document_rejected', 'Document Rejected'),
        ('meeting_scheduled', 'Meeting Scheduled'),
        ('meeting_reminder', 'Meeting Reminder'),
        ('registration_approved', 'Registration Approved'),
        ('registration_rejected', 'Registration Rejected'),
        ('system_update', 'System Update'),
        ('user_message', 'New Message'),
        ('batch_completed', 'Batch Process Completed'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Link to related object
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    # Priority and action
    priority = models.CharField(
        max_length=10, 
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')],
        default='normal'
    )
    action_url = models.URLField(blank=True, help_text="URL to take action on this notification")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Notification"
        verbose_name_plural = "User Notifications"
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    @property
    def icon(self):
        """Get FontAwesome icon for notification type"""
        icons = {
            'document_approved': 'fa-check-circle',
            'document_generated': 'fa-file-pdf',
            'document_delivered': 'fa-truck',
            'document_rejected': 'fa-times-circle',
            'meeting_scheduled': 'fa-calendar-plus',
            'meeting_reminder': 'fa-bell',
            'registration_approved': 'fa-user-check',
            'registration_rejected': 'fa-user-times',
            'system_update': 'fa-cog',
            'user_message': 'fa-envelope',
            'batch_completed': 'fa-tasks',
        }
        return icons.get(self.notification_type, 'fa-bell')
    
    @property
    def time_ago(self):
        """Get human-readable time since creation"""
        from django.utils.timesince import timesince
        return timesince(self.created_at) + ' ago'
    
    @property
    def color_class(self):
        """Get Bootstrap color class based on priority"""
        colors = {
            'low': 'text-muted',
            'normal': 'text-info',
            'high': 'text-warning',
            'urgent': 'text-danger'
        }
        return colors.get(self.priority, 'text-info')
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# Message Model (within users app)
class UserMessage(TimeStampedModel):
    """Internal messaging system"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Threading support
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Attachments (optional)
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Message"
        verbose_name_plural = "User Messages"
    
    def __str__(self):
        return f"{self.subject} - From {self.sender.username} to {self.recipient.username}"
    
    @property
    def time_ago(self):
        """Get human-readable time since creation"""
        from django.utils.timesince import timesince
        return timesince(self.created_at) + ' ago'
    
    @property
    def sender_avatar(self):
        """Get sender's avatar URL"""
        return self.sender.profile.get_avatar_url()
    
    @property
    def sender_name(self):
        """Get sender's display name"""
        return self.sender.profile.get_display_name()
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# Enhanced signal to create/update user profile
@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
        # Create welcome notification for new users
        if instance.is_active:
            UserNotification.objects.create(
                user=instance,
                notification_type='system_update',
                title='Welcome to RVMS',
                message='Welcome to the Rural Village Management System! Please complete your profile to get started.',
                priority='normal'
            )
    else:
        # Update existing profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()

# Signal to create notification when user logs in
from django.contrib.auth.signals import user_logged_in

@receiver(user_logged_in)
def user_login_handler(sender, request, user, **kwargs):
    """Handle user login"""
    if hasattr(user, 'profile'):
        # Get client IP
        ip_address = request.META.get('REMOTE_ADDR')
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR').split(',')[0]
        
        # Update login info
        user.profile.update_login_info(ip_address)
        
        
# _core/models.py

  
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from .._core.validators import phone_validator, sa_id_validator, postal_code_validator

class TimeStampedModel(models.Model):
    """
    Abstract base class that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SoftDeleteQuerySet(models.QuerySet):
    """Custom QuerySet for soft delete functionality"""
    
    def delete(self):
        """Soft delete all objects in the queryset"""
        return self.update(deleted_at=timezone.now())
    
    def hard_delete(self):
        """Permanently delete all objects in the queryset"""
        return super().delete()
    
    def alive(self):
        """Return only non-deleted objects"""
        return self.filter(deleted_at__isnull=True)
    
    def deleted(self):
        """Return only deleted objects"""
        return self.filter(deleted_at__isnull=False)

class SoftDeleteManager(models.Manager):
    """Custom manager for soft delete functionality"""
    
    def get_queryset(self):
        """Return only non-deleted objects by default"""
        return SoftDeleteQuerySet(self.model, using=self._db).alive()
    
    def all_with_deleted(self):
        """Return all objects including deleted ones"""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def deleted_only(self):
        """Return only deleted objects"""
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()

class SoftDeleteModel(TimeStampedModel):
    """
    Abstract base class that provides soft delete functionality
    along with timestamps.
    """
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Access to all objects including deleted
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete the object"""
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object"""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore a soft-deleted object"""
        self.deleted_at = None
        self.save()
    
    @property
    def is_deleted(self):
        """Check if the object is soft-deleted"""
        return self.deleted_at is not None

class BaseModel(SoftDeleteModel):
    """
    Base model that combines TimeStampedModel and SoftDeleteModel
    with additional common fields.
    """
    is_active = models.BooleanField(default=True, help_text="Designates whether this item should be treated as active.")
    
    class Meta:
        abstract = True 
      
       
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
        

# documents/models.py
from django.db import models
from django.contrib.auth import get_user_model
from governance.models import Village, Municipality, TraditionalCouncil
from households.models import Household, Resident
import uuid
import os

User = get_user_model()

def document_file_path(instance, filename):
    """Generate file path for new document"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('documents/', filename)

class DocumentTemplate(models.Model):
    """Template for generated documents"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    template_file = models.CharField(max_length=255, help_text="Path to the HTML template file")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Document Template"
        verbose_name_plural = "Document Templates"

class ProofOfResidence(models.Model):
    """Proof of residence document record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('generated', 'Generated'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic information
    document_number = models.CharField(max_length=20, unique=True, editable=False)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='proof_documents')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='proof_documents')
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name='proof_documents')
    
    # Document details
    purpose = models.CharField(max_length=255, help_text="Purpose for which the document is needed")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, related_name='proof_documents')
    document_file = models.FileField(upload_to=document_file_path, null=True, blank=True)
    
    # Administrative
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_documents')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_documents')
    approved_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Validity
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Proof of Residence: {self.resident.full_name} - {self.document_number}"
    
    class Meta:
        verbose_name = "Proof of Residence"
        verbose_name_plural = "Proofs of Residence"
        ordering = ['-requested_at']
    
    def save(self, *args, **kwargs):
        """Override save to generate document number on creation"""
        if not self.document_number:
            # Format: PR-<YearMonth>-<RandomDigits>
            import datetime
            now = datetime.datetime.now()
            prefix = f"PR-{now.strftime('%Y%m')}-"
            random_suffix = uuid.uuid4().hex[:6].upper()
            self.document_number = f"{prefix}{random_suffix}"
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if document is currently valid"""
        import datetime
        today = datetime.date.today()
        return (
            self.status == 'generated' or self.status == 'delivered'
        ) and (
            (self.valid_from is None or self.valid_from <= today) and 
            (self.valid_until is None or self.valid_until >= today)
        )
    
    @property
    def can_be_approved(self):
        """Check if document can be approved"""
        return self.status == 'pending'
    
    @property
    def can_be_generated(self):
        """Check if document can be generated"""
        return self.status == 'approved'
    
    @property
    def can_be_delivered(self):
        """Check if document can be delivered"""
        return self.status == 'generated'

class DocumentLog(models.Model):
    """Log of actions taken on a document"""
    document = models.ForeignKey(ProofOfResidence, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.action} on {self.document.document_number} by {self.action_by}"
    
    class Meta:
        verbose_name = "Document Log"
        verbose_name_plural = "Document Logs"
        ordering = ['-action_at']

class BatchProcess(models.Model):
    """Batch processing of documents"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_documents = models.PositiveIntegerField(default=0)
    processed_documents = models.PositiveIntegerField(default=0)
    failed_documents = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Batch: {self.name}"
    
    class Meta:
        verbose_name = "Batch Process"
        verbose_name_plural = "Batch Processes"
        ordering = ['-created_at']
    
    @property
    def progress_percentage(self):
        """Calculate the progress percentage"""
        if self.total_documents == 0:
            return 0
        return int((self.processed_documents / self.total_documents) * 100)

class BatchItem(models.Model):
    """Individual item in a batch process"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    batch = models.ForeignKey(BatchProcess, on_delete=models.CASCADE, related_name='items')
    document = models.ForeignKey(ProofOfResidence, on_delete=models.CASCADE, related_name='batch_items')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Batch Item: {self.document.document_number} in {self.batch.name}"
    
    class Meta:
        verbose_name = "Batch Item"
        verbose_name_plural = "Batch Items"
        ordering = ['batch', 'status']
        