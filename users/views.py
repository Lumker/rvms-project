from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import CustomUser, UserProfile
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm, UserProfileForm

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'users/edit_profile.html', context)

@login_required
def user_list(request):
    """List all users (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    users = CustomUser.objects.select_related('profile').order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'role_choices': UserProfile.ROLE_CHOICES,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'users/user_list.html', context)

@login_required
def user_detail(request, pk):
    """User detail view"""
    user = get_object_or_404(CustomUser.objects.select_related('profile'), pk=pk)
    
    # Only allow access to own profile or if user is staff
    if request.user != user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this profile.")
        return redirect('users:profile')
    
    context = {'user_obj': user}
    return render(request, 'users/user_detail.html', context)

@login_required
def user_update(request, pk):
    """Update user (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to update users.")
        return redirect('users:user_list')
    
    user = get_object_or_404(CustomUser, pk=pk)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'User {user.username} has been updated successfully!')
            return redirect('users:user_detail', pk=user.pk)
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_obj': user,
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'users/user_update.html', context)

# users/views.py
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PublicRegistrationForm, AdminUserCreationForm

def public_registration(request):
    """Public registration for potential committee members"""
    if request.method == 'POST':
        form = PublicRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require approval
            user.save()
            
            # Create profile with registration details
            profile = user.profile
            profile.registration_reason = form.cleaned_data['registration_reason']
            profile.intended_ward = form.cleaned_data['intended_ward']
            profile.current_address = form.cleaned_data['current_address']
            profile.save()
            
            messages.success(request, 
                'Registration submitted! You will receive an email once approved.')
            return redirect('users:registration_success')
    else:
        form = PublicRegistrationForm()
    
    return render(request, 'users/public_registration.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.profile.is_governance_admin)
def pending_registrations(request):
    """View for admins to approve/reject registrations"""
    pending_users = CustomUser.objects.filter(
        profile__registration_status='pending'
    ).select_related('profile')
    
    return render(request, 'users/pending_registrations.html', {
        'pending_users': pending_users
    })

@login_required
@user_passes_test(lambda u: u.profile.is_governance_admin)
def approve_registration(request, user_id):
    """Approve a pending registration"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.is_active = True
        user.save()
        
        user.profile.approve_registration(request.user)
        
        messages.success(request, f'User {user.get_full_name()} approved successfully!')
        return redirect('users:pending_registrations')
    
    return render(request, 'users/confirm_approval.html', {'user': user})

@login_required
@user_passes_test(lambda u: u.profile.is_governance_admin)
def bulk_user_creation(request):
    """Bulk create users from CSV/Excel for large committee appointments"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        # Process CSV file
        csv_file = request.FILES['csv_file']
        # Implementation for CSV processing
        pass
    
    return render(request, 'users/bulk_user_creation.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import CustomUser, UserProfile, UserNotification, UserMessage
import json

@login_required
def profile_view(request):
    """View user profile"""
    profile = request.user.profile
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_edit(request):
    """Edit user profile"""
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update user fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.phone_number = request.POST.get('phone_number', '')
        request.user.save()
        
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        profile.department = request.POST.get('department', '')
        profile.address = request.POST.get('address', '')
        
        if 'date_of_birth' in request.POST and request.POST['date_of_birth']:
            from datetime import datetime
            try:
                profile.user.date_of_birth = datetime.strptime(request.POST['date_of_birth'], '%Y-%m-%d').date()
                profile.user.save()
            except ValueError:
                pass
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')
    
    return render(request, 'users/profile_edit.html', {'profile': profile})

@login_required
@csrf_exempt
def update_profile_picture(request):
    """Update user profile picture via AJAX"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        try:
            profile = request.user.profile
            
            # Delete old profile picture if exists
            if profile.profile_picture:
                try:
                    profile.profile_picture.delete()
                except:
                    pass
            
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            
            return JsonResponse({
                'success': True,
                'image_url': profile.get_avatar_url(),
                'message': 'Profile picture updated successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'No image file provided'
    })

@login_required
def notifications_list(request):
    """List all notifications for user"""
    notifications = request.user.notifications.all()
    
    # Mark all as read when viewing
    notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'notifications': page_obj,
    }
    return render(request, 'users/notifications.html', context)

@login_required
def api_notifications(request):
    """API endpoint for notifications"""
    try:
        # Get unread notifications first, then some read ones
        unread_notifications = request.user.notifications.filter(is_read=False)[:5]
        read_notifications = request.user.notifications.filter(is_read=True)[:3]
        
        # Combine them
        notifications = list(unread_notifications) + list(read_notifications)
        
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'icon': notification.icon,
                'time_ago': notification.time_ago,
                'is_read': notification.is_read,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat(),
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        # Return error for debugging
        return JsonResponse({
            'error': str(e),
            'message': 'Error loading notifications'
        }, status=500)

@login_required
@csrf_exempt
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if request.method == 'POST':
        try:
            notification = get_object_or_404(UserNotification, id=notification_id, user=request.user)
            notification.mark_as_read()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def clear_all_notifications(request):
    """Clear all notifications for user"""
    if request.method == 'POST':
        try:
            request.user.notifications.filter(is_read=False).update(
                is_read=True, 
                read_at=timezone.now()
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def inbox(request):
    """User inbox for messages"""
    messages_list = request.user.received_messages.all()
    
    # Mark all as read when viewing
    messages_list.filter(is_read=False).update(is_read=True, read_at=timezone.now())
    
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'messages': page_obj,
    }
    return render(request, 'users/inbox.html', context)

@login_required
def api_messages(request):
    """API endpoint for messages"""
    try:
        # Get unread messages
        messages_list = request.user.received_messages.filter(is_read=False)[:10]
        
        data = []
        for message in messages_list:
            data.append({
                'id': message.id,
                'subject': message.subject,
                'sender_name': message.sender_name,
                'sender_avatar': message.sender_avatar,
                'time_ago': message.time_ago,
                'is_read': message.is_read,
                'priority': message.priority,
                'created_at': message.created_at.isoformat(),
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'message': 'Error loading messages'
        }, status=500)

@login_required
def compose_message(request):
    """Compose new message"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        priority = request.POST.get('priority', 'normal')
        
        try:
            recipient = get_object_or_404(CustomUser, id=recipient_id)
            
            message = UserMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                body=body,
                priority=priority
            )
            
            # Create notification for recipient
            UserNotification.objects.create(
                user=recipient,
                notification_type='user_message',
                title='New Message',
                message=f'You have a new message from {request.user.get_full_name() or request.user.username}',
                related_object_id=message.id,
                related_object_type='UserMessage'
            )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('users:inbox')
            
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
    
    # Get all users except current user
    users = CustomUser.objects.exclude(id=request.user.id).filter(is_active=True)
    
    context = {
        'users': users,
    }
    return render(request, 'users/compose_message.html', context)

@login_required
def message_detail(request, message_id):
    """View message detail"""
    message = get_object_or_404(UserMessage, id=message_id)
    
    # Check if user is sender or recipient
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('users:inbox')
    
    # Mark as read if recipient is viewing
    if message.recipient == request.user and not message.is_read:
        message.mark_as_read()
    
    context = {
        'message': message,
    }
    return render(request, 'users/message_detail.html', context)

@login_required
@csrf_exempt
def update_settings(request):
    """Update user settings"""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            
            # Update preferences
            old_theme = profile.theme_preference
            profile.theme_preference = request.POST.get('theme_preference', 'light')
            profile.language_preference = request.POST.get('language_preference', 'en')
            
            # Update notification preferences
            notification_prefs = {
                'email_notifications': 'email_notifications' in request.POST,
                'document_updates': 'document_updates' in request.POST,
                'meeting_reminders': 'meeting_reminders' in request.POST,
                'system_updates': 'system_updates' in request.POST,
                'weekly_digest': 'weekly_digest' in request.POST,
            }
            profile.notification_preferences = notification_prefs
            profile.save()
            
            theme_changed = old_theme != profile.theme_preference
            
            return JsonResponse({
                'success': True,
                'theme_changed': theme_changed,
                'new_theme': profile.theme_preference
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def update_online_status(request):
    """Update user's online status"""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            profile.last_login_ip = request.META.get('REMOTE_ADDR')
            profile.save(update_fields=['last_login_ip', 'updated_at'])
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

from django.contrib.auth import logout
from django.shortcuts import redirect

@login_required
def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')  # Adjust this to your login URL name