from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when user is created or updated"""
    if created:
        # Only create if profile doesn't exist
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'role': 'admin' if instance.is_superuser else 'villager'}
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Create profile if it doesn't exist
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'role': 'admin' if instance.is_superuser else 'villager'}
        )