from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def is_governance_admin(user):
    """Check if user is a governance administrator"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    if hasattr(user, 'profile'):
        return user.profile.role in ['admin', 'governance_admin']
    
    return user.groups.filter(name='Governance Admin').exists()

def is_council_member(user):
    """Check if user is an active council member"""
    if not user.is_authenticated:
        return False
    
    return user.council_roles.filter(is_active=True).exists()

def is_village_admin(user):
    """Check if user is a village administrator"""
    if not user.is_authenticated:
        return False
    
    if hasattr(user, 'profile'):
        return user.profile.role in ['admin', 'village_admin']
    
    return False

def governance_admin_required(view_func):
    """Decorator for views that require governance admin permissions"""
    def _wrapped_view(request, *args, **kwargs):
        if not is_governance_admin(request.user):
            raise PermissionDenied("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def council_member_required(view_func):
    """Decorator for views that require council member permissions"""
    def _wrapped_view(request, *args, **kwargs):
        if not (is_governance_admin(request.user) or is_council_member(request.user)):
            raise PermissionDenied("You must be a council member to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view