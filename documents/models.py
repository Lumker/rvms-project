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