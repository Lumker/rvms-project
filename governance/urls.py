from django.urls import path
from . import views

app_name = 'governance'

urlpatterns = [
    # Dashboard
    path('', views.governance_dashboard, name='dashboard'),
    
    # Provinces
    path('provinces/', views.province_list, name='province_list'),
    path('provinces/create/', views.province_create, name='province_create'),
    path('provinces/<int:pk>/', views.province_detail, name='province_detail'),
    path('provinces/<int:pk>/update/', views.province_update, name='province_update'),
    # path('provinces/<int:pk>/delete/', views.province_delete, name='province_delete'),
    
    # Districts
    path('districts/', views.district_list, name='district_list'),
    path('districts/create/', views.district_create, name='district_create'),
    path('districts/<int:pk>/', views.district_detail, name='district_detail'),
    path('districts/<int:pk>/update/', views.district_update, name='district_update'),
    path('districts/<int:pk>/delete/', views.district_delete, name='district_delete'),
    
    # Municipalities
    path('municipalities/', views.municipality_list, name='municipality_list'),
    path('municipalities/create/', views.municipality_create, name='municipality_create'),
    path('municipalities/<int:pk>/', views.municipality_detail, name='municipality_detail'),
    path('municipalities/<int:pk>/update/', views.municipality_update, name='municipality_update'),
    path('municipalities/<int:pk>/delete/', views.municipality_delete, name='municipality_delete'),
    
    # Traditional Councils
    path('councils/', views.council_list, name='council_list'),
    path('councils/<int:pk>/', views.council_detail, name='council_detail'),
    path('councils/create/', views.council_create, name='council_create'),
    path('councils/<int:pk>/update/', views.council_update, name='council_update'),
    path('councils/<int:pk>/delete/', views.council_delete, name='council_delete'),
    
    # Villages
    path('villages/', views.village_list, name='village_list'),
    path('villages/create/', views.village_create, name='village_create'),
    path('villages/<int:pk>/', views.village_detail, name='village_detail'),
    path('villages/<int:pk>/update/', views.village_update, name='village_update'),
    path('villages/<int:pk>/delete/', views.village_delete, name='village_delete'),
    
    # Meetings
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('meetings/create/', views.meeting_create, name='meeting_create'),
    path('meetings/<int:pk>/update/', views.meeting_update, name='meeting_update'),
    path('meetings/<int:pk>/delete/', views.meeting_delete, name='meeting_delete'),
    
    # Add these URLs to your existing urlpatterns

    # Council Members
    path('council-members/', views.council_member_list, name='council_member_list'),
    path('council-members/create/', views.council_member_create, name='council_member_create'),
    path('council-members/<int:pk>/', views.council_member_detail, name='council_member_detail'),
    path('council-members/<int:pk>/update/', views.council_member_update, name='council_member_update'),
    path('council-members/<int:pk>/delete/', views.council_member_delete, name='council_member_delete'),

    # Resolutions
    path('resolutions/', views.resolution_list, name='resolution_list'),
    path('resolutions/create/', views.resolution_create, name='resolution_create'),
    path('resolutions/<int:pk>/', views.resolution_detail, name='resolution_detail'),
    path('resolutions/<int:pk>/update/', views.resolution_update, name='resolution_update'),
    path('resolutions/<int:pk>/delete/', views.resolution_delete, name='resolution_delete'),
    
    # Ward Committees
    path('ward-committees/', views.ward_committee_list, name='ward_committee_list'),
    path('ward-committees/create/', views.ward_committee_create, name='ward_committee_create'),
    path('ward-committees/<int:pk>/', views.ward_committee_detail, name='ward_committee_detail'),
    path('ward-committees/<int:pk>/update/', views.ward_committee_update, name='ward_committee_update'),
    path('ward-committees/<int:pk>/delete/', views.ward_committee_delete, name='ward_committee_delete'),
    
    # Ward Committee Members
    path('ward-committee-members/', views.ward_committee_member_list, name='ward_committee_member_list'),
    path('ward-committee-members/create/', views.ward_committee_member_create, name='ward_committee_member_create'),
    path('ward-committee-members/<int:pk>/', views.ward_committee_member_detail, name='ward_committee_member_detail'),
    path('ward-committee-members/<int:pk>/update/', views.ward_committee_member_update, name='ward_committee_member_update'),
    path('ward-committee-members/<int:pk>/delete/', views.ward_committee_member_delete, name='ward_committee_member_delete'),
    
    # AJAX endpoints
    path('ajax/ward-committees/', views.get_ward_committees_by_municipality, name='get_ward_committees_by_municipality'),
    path('ajax/ward-committee-members/', views.get_ward_committee_members, name='get_ward_committee_members'),

    # AJAX endpoints for status updates
    path('resolutions/<int:pk>/update-status/', views.update_resolution_status, name='update_resolution_status'),
    path('council-members/<int:pk>/activate/', views.activate_council_member, name='activate_council_member'),
    path('council-members/<int:pk>/deactivate/', views.deactivate_council_member, name='deactivate_council_member'),
    
    # AJAX endpoints
    path('ajax/districts/', views.get_districts, name='get_districts'),
    path('ajax/municipalities/', views.get_municipalities_by_district, name='get_municipalities_by_district'),
    path('ajax/councils/', views.get_councils_by_municipality, name='get_councils_by_municipality'),
    # Add this to your existing AJAX endpoints section
    path('ajax/council-members/', views.get_council_members, name='get_council_members'),
    
    # Dashboard stats (for real-time updates)
    # path('ajax/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
]