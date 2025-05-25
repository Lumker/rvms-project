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