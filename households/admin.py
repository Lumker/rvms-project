from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from users.models import CustomUser, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = 'user'  # Specify which ForeignKey to use
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = [
        'role', 'practice_number', 'address', 'is_verified', 
        'verification_date', 'registration_status', 'registration_method'
    ]
    readonly_fields = ['verification_date']

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    
    # Extend the default UserAdmin fields
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'id_number', 'date_of_birth')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'id_number', 'date_of_birth')
        }),
    )
    
    list_display = [
        'username', 'email', 'first_name', 'last_name', 
        'get_role', 'is_active', 'date_joined'
    ]
    list_filter = UserAdmin.list_filter + ('profile__role', 'profile__is_verified')
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'id_number']
    
    def get_role(self, obj):
        """Get user role from profile"""
        try:
            return obj.profile.get_role_display()
        except:
            return '-'
    get_role.short_description = 'Role'

# Unregister the default User admin and register our custom one
admin.site.unregister(CustomUser)
admin.site.register(CustomUser, CustomUserAdmin)

# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = [
#         'user', 'role', 'is_verified', 'registration_status', 
#         'registration_method', 'created_at'
#     ]
#     list_filter = [
#         'role', 'is_verified', 'registration_status', 
#         'registration_method', 'created_at'
#     ]
#     search_fields = [
#         'user__username', 'user__email', 'user__first_name', 
#         'user__last_name', 'practice_number'
#     ]
#     readonly_fields = ['created_at', 'updated_at', 'verification_date']
    
#     fieldsets = (
#         ('User Information', {
#             'fields': ('user', 'role')
#         }),
#         ('Professional Details', {
#             'fields': ('practice_number', 'address')
#         }),
#         ('Registration Details', {
#             'fields': (
#                 'registration_status', 'registration_method', 
#                 'registration_reason', 'intended_ward'
#             )
#         }),
#         ('Verification', {
#             'fields': (
#                 'is_verified', 'verification_date', 'approved_by', 
#                 'approval_date', 'rejection_reason'
#             )
#         }),
#         ('Contact Verification', {
#             'fields': ('phone_verified', 'email_verified', 'current_address')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )