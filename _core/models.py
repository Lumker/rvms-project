from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from .validators import phone_validator, sa_id_validator, postal_code_validator

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