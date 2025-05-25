from django.contrib import admin
from .models import (
    Province, District, Municipality, TraditionalCouncil, 
    Village, CouncilMember, CouncilMeeting, Resolution
)

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'province', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['province', 'created_at']
    raw_id_fields = ['province']

@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'municipality_type', 'district', 'mayor_name', 'population', 'is_active']
    list_filter = ['municipality_type', 'district__province', 'district', 'is_active']
    search_fields = ['name', 'code', 'mayor_name', 'municipal_manager']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'municipality_type', 'district')
        }),
        ('Leadership', {
            'fields': ('mayor_name', 'municipal_manager')
        }),
        ('Demographics', {
            'fields': ('population', 'area_km2')
        }),
        ('Contact', {
            'fields': ('contact_info', 'website')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(TraditionalCouncil)
class TraditionalCouncilAdmin(admin.ModelAdmin):
    list_display = ['name', 'leader_name', 'municipality', 'establishment_date', 'status', 'is_active']
    list_filter = ['status', 'municipality__district__province', 'municipality', 'is_active']
    search_fields = ['name', 'leader_name', 'municipality__name']
    list_editable = ['status', 'is_active']
    ordering = ['name']
    date_hierarchy = 'establishment_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'municipality')
        }),
        ('Leadership', {
            'fields': ('leader_name', 'leader_title')
        }),
        ('Dates', {
            'fields': ('establishment_date', 'term_end_date')
        }),
        ('Contact & Jurisdiction', {
            'fields': ('contact_info', 'geographic_jurisdiction')
        }),
        ('Official Details', {
            'fields': ('recognition_certificate', 'status', 'is_active')
        }),
    )

@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'traditional_council', 'location', 'population']
    search_fields = ['name', 'code', 'location']
    list_filter = [
        'traditional_council__municipality__district__province',
        'traditional_council__municipality__district',
        'traditional_council__municipality',
        'traditional_council'
    ]
    raw_id_fields = ['traditional_council']

class CouncilMemberInline(admin.TabularInline):
    model = CouncilMember
    extra = 1
    raw_id_fields = ['user']

@admin.register(CouncilMember)
class CouncilMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'council', 'role', 'appointed_date', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'council__name']
    list_filter = ['role', 'is_active', 'council', 'appointed_date']
    raw_id_fields = ['council', 'user']
    date_hierarchy = 'appointed_date'

class ResolutionInline(admin.TabularInline):
    model = Resolution
    extra = 1
    raw_id_fields = ['proposed_by']

@admin.register(CouncilMeeting)
class CouncilMeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'council', 'date', 'time', 'status', 'location']
    search_fields = ['title', 'council__name', 'location']
    list_filter = ['status', 'council', 'date']
    raw_id_fields = ['council']
    filter_horizontal = ['attendees']
    date_hierarchy = 'date'
    inlines = [ResolutionInline]

@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting', 'status', 'proposed_by', 'created_at', 'date_implemented']
    search_fields = ['title', 'description', 'meeting__title']
    list_filter = ['status', 'meeting__council', 'created_at']
    raw_id_fields = ['meeting', 'proposed_by']
    date_hierarchy = 'created_at'