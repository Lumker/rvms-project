from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to be an admin"""
    
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or 
            self.request.user.is_staff
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('dashboard')

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to be staff"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class ActiveUserRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to be active"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_active

class MessageMixin:
    """Mixin to add success messages to class-based views"""
    
    success_message = ""
    
    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        return response
    
    def get_success_message(self, cleaned_data):
        return self.success_message % cleaned_data if self.success_message else ""