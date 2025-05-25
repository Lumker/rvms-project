from django.contrib import admin
from django.utils.html import format_html

class BaseModelAdmin(admin.ModelAdmin):
    """Base admin class with common functionality"""
    
    list_per_page = 25
    save_on_top = True
    
    def get_readonly_fields(self, request, obj=None):
        """Make timestamp fields readonly"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        readonly_fields.extend(['created_at', 'updated_at'])
        return readonly_fields

class SoftDeleteModelAdmin(BaseModelAdmin):
    """Admin class for models with soft delete"""
    
    def get_queryset(self, request):
        """Show all objects including soft-deleted ones in admin"""
        return self.model.all_objects.get_queryset()
    
    def delete_queryset(self, request, queryset):
        """Soft delete selected objects"""
        queryset.delete()
    
    def deleted_status(self, obj):
        """Show deleted status in list display"""
        if obj.is_deleted:
            return format_html('<span class="text-danger">Deleted</span>')
        return format_html('<span class="text-success">Active</span>')
    
    deleted_status.short_description = 'Status'
    deleted_status.admin_order_field = 'deleted_at'

    actions = ['soft_delete', 'restore_objects']
    
    def soft_delete(self, request, queryset):
        """Admin action to soft delete objects"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} objects were soft deleted.')
    soft_delete.short_description = "Soft delete selected objects"
    
    def restore_objects(self, request, queryset):
        """Admin action to restore soft deleted objects"""
        count = 0
        for obj in queryset:
            if obj.is_deleted:
                obj.restore()
                count += 1
        self.message_user(request, f'{count} objects were restored.')
    restore_objects.short_description = "Restore selected objects"