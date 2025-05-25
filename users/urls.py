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