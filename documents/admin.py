from django.contrib import admin
from .models import DocumentTemplate, ProofOfResidence, DocumentLog, BatchProcess, BatchItem

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

class DocumentLogInline(admin.TabularInline):
    model = DocumentLog
    extra = 0
    readonly_fields = ['action', 'action_by', 'action_at']

@admin.register(ProofOfResidence)
class ProofOfResidenceAdmin(admin.ModelAdmin):
    list_display = ['document_number', 'resident', 'village', 'status', 'requested_at', 'approved_at']
    list_filter = ['status', 'village', 'requested_at', 'approved_at']
    search_fields = ['document_number', 'resident__first_name', 'resident__last_name', 'purpose']
    readonly_fields = ['document_number', 'requested_at', 'approved_at', 'generated_at', 'delivered_at']
    inlines = [DocumentLogInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('document_number', 'resident', 'household', 'village', 'purpose')
        }),
        ('Document Details', {
            'fields': ('status', 'template', 'document_file')
        }),
        ('Administrative', {
            'fields': ('requested_by', 'requested_at', 'approved_by', 'approved_at', 'generated_at', 'delivered_at', 'notes')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
    )

class BatchItemInline(admin.TabularInline):
    model = BatchItem
    extra = 0
    readonly_fields = ['processed_at']

@admin.register(BatchProcess)
class BatchProcessAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'total_documents', 'processed_documents', 'failed_documents', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'completed_at', 'progress_percentage']
    inlines = [BatchItemInline]