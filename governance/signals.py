from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import TraditionalCouncil, Village, CouncilMeeting, Resolution

@receiver(post_save, sender=TraditionalCouncil)
def log_council_activity(sender, instance, created, **kwargs):
    if created:
        # Log activity - you can integrate with your activity logging system
        print(f"New Traditional Council created: {instance.name}")

@receiver(post_save, sender=CouncilMeeting)
def log_meeting_activity(sender, instance, created, **kwargs):
    if created:
        print(f"New meeting scheduled: {instance.title} for {instance.council.name}")

@receiver(post_save, sender=Resolution)
def log_resolution_activity(sender, instance, created, **kwargs):
    if not created and instance.status == 'approved':
        print(f"Resolution approved: {instance.title}")