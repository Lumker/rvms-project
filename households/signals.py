from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Household, Resident
from users.models import CustomUser

@receiver(post_save, sender=Household)
def update_ward_committee_assignment(sender, instance, created, **kwargs):
    """Auto-assign ward committee based on village"""
    if created and not instance.ward_committee:
        try:
            if instance.village.traditional_council:
                tc = instance.village.traditional_council
                if tc.ward_committee:
                    instance.ward_committee = tc.ward_committee
                    instance.save(update_fields=['ward_committee'])
        except:
            pass

@receiver(pre_save, sender=Resident)
def extract_data_from_id(sender, instance, **kwargs):
    """Extract date of birth and gender from ID number"""
    if instance.id_number and len(instance.id_number) == 13:
        # Extract date of birth if not provided
        if not instance.date_of_birth:
            instance.date_of_birth = instance.extract_dob_from_id()
        
        # Extract gender if not provided
        if not instance.gender:
            instance.gender = instance.extract_gender_from_id()

@receiver(post_save, sender=Resident)
def ensure_single_household_head(sender, instance, created, **kwargs):
    """Ensure only one head of household per household"""
    if instance.is_head_of_household:
        # Remove head status from other residents in same household
        Resident.objects.filter(
            household=instance.household,
            is_head_of_household=True,
            is_active=True
        ).exclude(pk=instance.pk).update(is_head_of_household=False)