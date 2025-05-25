# documents/urls.py

from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Dashboard
    path('', views.DocumentDashboardView.as_view(), name='dashboard'),
    
    # Proof of Residence
    path('proof-of-residence/', views.ProofOfResidenceListView.as_view(), name='proof_list'),
    path('proof-of-residence/new/', views.ProofOfResidenceCreateView.as_view(), name='proof_create'),
    path('proof-of-residence/<int:pk>/', views.ProofOfResidenceDetailView.as_view(), name='proof_detail'),
    path('proof-of-residence/<int:pk>/edit/', views.ProofOfResidenceUpdateView.as_view(), name='proof_update'),
    path('proof-of-residence/<int:pk>/approve/', views.approve_proof_of_residence, name='proof_approve'),
    path('proof-of-residence/<int:pk>/generate/', views.generate_proof_of_residence, name='proof_generate'),
    path('proof-of-residence/<int:pk>/deliver/', views.deliver_proof_of_residence, name='proof_deliver'),
    path('proof-of-residence/<int:pk>/download/', views.download_proof_of_residence, name='proof_download'),
    
    # Document Templates
    path('templates/', views.DocumentTemplateListView.as_view(), name='template_list'),
    path('templates/new/', views.DocumentTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', views.DocumentTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:pk>/edit/', views.DocumentTemplateUpdateView.as_view(), name='template_update'),
    
    # Batch Processing
    path('batches/', views.BatchProcessListView.as_view(), name='batch_list'),
    path('batches/new/', views.BatchProcessCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchProcessDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/process/', views.process_batch, name='batch_process'),
    
    # Reports
    path('reports/batch/<int:pk>/', views.download_batch_report, name='batch_report'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    
    # API endpoints for AJAX
    path('api/residents/<int:village_id>/', views.get_residents_by_village, name='api_residents_by_village'),
    path('api/households/<int:village_id>/', views.get_households_by_village, name='api_households_by_village'),
]


# governance/urls.py

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


# households

from django.urls import path
from . import views

app_name = 'households'

urlpatterns = [
    # Dashboard
    path('', views.households_dashboard, name='dashboard'),
    
    # Households
    path('households/', views.household_list, name='household_list'),
    path('households/create/', views.household_create, name='household_create'),
    path('households/<int:pk>/', views.household_detail, name='household_detail'),
    path('households/<int:pk>/update/', views.household_update, name='household_update'),
    path('households/<int:pk>/delete/', views.household_delete, name='household_delete'),
    path('households/<int:pk>/verify/', views.household_verify, name='household_verify'),
    
    # Residents
    path('residents/', views.resident_list, name='resident_list'),
    path('residents/create/', views.resident_create, name='resident_create'),
    path('residents/<int:pk>/', views.resident_detail, name='resident_detail'),
    path('residents/<int:pk>/update/', views.resident_update, name='resident_update'),
    path('residents/<int:pk>/delete/', views.resident_delete, name='resident_delete'),
    path('residents/<int:pk>/create-user/', views.create_user_account, name='create_user_account'),
    
    # Household Services
    path('services/', views.household_service_list, name='service_list'),
    path('services/create/', views.household_service_create, name='service_create'),
    path('services/<int:pk>/update/', views.household_service_update, name='service_update'),
    path('services/<int:pk>/delete/', views.household_service_delete, name='service_delete'),
    
    # Reports
    path('reports/', views.household_reports, name='reports'),
    path('reports/demographics/', views.demographics_report, name='demographics_report'),
    path('reports/services/', views.services_report, name='services_report'),
    
    # AJAX endpoints
    path('ajax/ward-committees/', views.get_ward_committees_by_village, name='get_ward_committees_by_village'),
    path('ajax/households/', views.get_households_by_village, name='get_households_by_village'),
    path('ajax/validate-id/', views.validate_id_number, name='validate_id_number'),
]


# users/urls.py

# from django.urls import path
# from django.contrib.auth import views as auth_views
# from . import views

# app_name = 'users'

# urlpatterns = [
#     # Custom authentication views
#     path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
#     path('logout/', auth_views.LogoutView.as_view(), name='logout'),
#     path('register/', views.register, name='register'),
    
#     # Password reset URLs
#     path('password_reset/', auth_views.PasswordResetView.as_view(
#         template_name='users/password_reset.html',
#         email_template_name='users/password_reset_email.html',
#         subject_template_name='users/password_reset_subject.txt',
#         success_url='/users/password_reset/done/'
#     ), name='password_reset'),
    
#     path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
#         template_name='users/password_reset_done.html'
#     ), name='password_reset_done'),
    
#     path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
#         template_name='users/password_reset_confirm.html',
#         success_url='/users/reset/done/'
#     ), name='password_reset_confirm'),
    
#     path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
#         template_name='users/password_reset_complete.html'
#     ), name='password_reset_complete'),
    
#     # Password change URLs  
#     path('password_change/', auth_views.PasswordChangeView.as_view(
#         template_name='users/password_change.html',
#         success_url='/users/password_change/done/'
#     ), name='password_change'),
    
#     path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
#         template_name='users/password_change_done.html'
#     ), name='password_change_done'),
    
#     # Profile management
#     path('profile/', views.profile, name='profile'),
#     path('profile/edit/', views.edit_profile, name='edit_profile'),
    
#     # User management (admin only)
#     path('', views.user_list, name='user_list'),  # This handles /users/
#     path('<int:pk>/', views.user_detail, name='user_detail'),
#     path('<int:pk>/edit/', views.user_update, name='user_update'),
# ]

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
        # Custom authentication views
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt',
        success_url='/users/password_reset/done/'
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='/users/reset/done/'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Password change URLs  
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='users/password_change.html',success_url='/users/password_change/done/'
    ), name='password_change'),
    
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),
    path('', views.user_list, name='user_list'),  # This handles /users/
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/picture/', views.update_profile_picture, name='update_profile_picture'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),
    path('api/notifications/', views.api_notifications, name='api_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/clear/', views.clear_all_notifications, name='clear_all_notifications'),
    
    # Messages
    path('inbox/', views.inbox, name='inbox'),
    path('messages/compose/', views.compose_message, name='compose_message'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('api/messages/', views.api_messages, name='api_messages'),
    
    # Settings
    path('settings/', views.update_settings, name='update_settings'),
    path('online-status/', views.update_online_status, name='update_online_status'),
    
    # Auth URLs (if not using Django's built-in)
    path('logout/', views.logout_view, name='logout'),
]



