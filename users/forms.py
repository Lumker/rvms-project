from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile
from _core.validators import sa_phone_validator, validate_sa_id_number
from governance.models import WardCommittee

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'role', 'practice_number', 'address', 'is_verified',
            'registration_status', 'registration_method', 'registration_reason',
            'current_address', 'intended_ward', 'phone_verified', 'email_verified'
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'practice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter practice number (if applicable)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Enter full address'
            }),
            'is_verified': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'registration_status': forms.Select(attrs={'class': 'form-control'}),
            'registration_method': forms.Select(attrs={'class': 'form-control'}),
            'registration_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for registration'
            }),
            'current_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Current residential address'
            }),
            'intended_ward': forms.Select(attrs={'class': 'form-control'}),
            'phone_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text
        self.fields['practice_number'].help_text = "Professional practice number (for staff/admin roles)"
        self.fields['address'].help_text = "Full residential or business address"
        self.fields['is_verified'].help_text = "Check if this user profile has been verified"
        self.fields['current_address'].help_text = "Current residential address"
        self.fields['phone_verified'].help_text = "Check if phone number has been verified"
        self.fields['email_verified'].help_text = "Check if email address has been verified"

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    # Fields from CustomUser model
    phone_number = forms.CharField(
        required=False,
        validators=[sa_phone_validator],
        help_text="Phone number in format: +27XXXXXXXXX or 0XXXXXXXXX"
    )
    id_number = forms.CharField(
        required=False,
        validators=[validate_sa_id_number],
        help_text="South African ID Number (13 digits)"
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    # Additional profile fields
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES, 
        required=False,
        initial='villager'
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )
    practice_number = forms.CharField(required=False)
    
    # New registration fields
    registration_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Reason for registration'})
    )
    current_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Current residential address'})
    )
    intended_ward = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="Select ward (if applicable)"
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'id_number', 'date_of_birth',
            'password1', 'password2'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set queryset for intended_ward
        try:
            from governance.models import WardCommittee
            self.fields['intended_ward'].queryset = WardCommittee.objects.all()
        except ImportError:
            # Remove field if governance app not available
            del self.fields['intended_ward']
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name == 'is_verified':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a unique username'
        self.fields['email'].widget.attrs['placeholder'] = 'your.email@example.com'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['phone_number'].widget.attrs['placeholder'] = '+27XXXXXXXXX'
        self.fields['id_number'].widget.attrs['placeholder'] = '13-digit ID number'
        self.fields['address'].widget.attrs['placeholder'] = 'Full address'
        self.fields['practice_number'].widget.attrs['placeholder'] = 'Practice number (if applicable)'
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.id_number = self.cleaned_data.get('id_number', '')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        
        if commit:
            user.save()
            # Create or update the user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data.get('role', 'villager')
            profile.address = self.cleaned_data.get('address', '')
            profile.practice_number = self.cleaned_data.get('practice_number', '')
            profile.registration_reason = self.cleaned_data.get('registration_reason', '')
            profile.current_address = self.cleaned_data.get('current_address', '')
            profile.intended_ward = self.cleaned_data.get('intended_ward')
            profile.registration_method = 'self'  # Default for self-registration
            profile.save()
        
        return user

class UserUpdateForm(forms.ModelForm):
    """Form for updating user basic information"""
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'id_number', 'date_of_birth']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+27XXXXXXXXX or 0XXXXXXXXX'
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '13-digit ID number'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
        }

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    class Meta:
        model = UserProfile
        fields = ['role', 'address', 'practice_number', 'current_address', 'intended_ward']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Enter full address'
            }),
            'practice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Practice number (if applicable)'
            }),
            'current_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Current residential address'
            }),
            'intended_ward': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['practice_number'].help_text = "Professional practice number (for staff/admin roles)"
        self.fields['address'].help_text = "Full residential or business address"
        self.fields['current_address'].help_text = "Current residential address"
        
        # Set queryset for intended_ward
        try:
            from governance.models import WardCommittee
            self.fields['intended_ward'].queryset = WardCommittee.objects.all()
        except ImportError:
            # Remove field if governance app not available
            del self.fields['intended_ward']


class PublicRegistrationForm(UserCreationForm):
    registration_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Please explain why you want to register (e.g., to serve as a committee member)"
    )
    intended_ward = forms.ModelChoiceField(
        queryset=WardCommittee.objects.filter(is_active=True),
        required=False,
        help_text="Which ward committee are you interested in joining?"
    )
    current_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        help_text="Your current residential address"
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'id_number', 'date_of_birth', 'password1', 'password2'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required for committee members
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone_number'].required = True
        self.fields['id_number'].required = True


class AdminUserCreationForm(UserCreationForm):
    """Form for admins to quickly create users"""
    send_credentials = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Send login credentials to user via email"
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'id_number']


class AdminUserProfileForm(forms.ModelForm):
    """Form for admin to update user profiles (includes verification and approval)"""
    
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for rejection (if applicable)'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'role', 'practice_number', 'address', 'is_verified', 'verification_date',
            'registration_status', 'registration_method', 'registration_reason',
            'current_address', 'intended_ward', 'phone_verified', 'email_verified'
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'practice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Practice number (if applicable)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Enter full address'
            }),
            'is_verified': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'verification_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'registration_status': forms.Select(attrs={'class': 'form-control'}),
            'registration_method': forms.Select(attrs={'class': 'form-control'}),
            'registration_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'readonly': True
            }),
            'current_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Current residential address'
            }),
            'intended_ward': forms.Select(attrs={'class': 'form-control'}),
            'phone_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['verification_date'].help_text = "Date and time when profile was verified"
        self.fields['is_verified'].help_text = "Check if this user profile has been verified"
        self.fields['phone_verified'].help_text = "Check if phone number has been verified"
        self.fields['email_verified'].help_text = "Check if email address has been verified"
        
        # Set queryset for intended_ward
        try:
            from governance.models import WardCommittee
            self.fields['intended_ward'].queryset = WardCommittee.objects.all()
        except ImportError:
            # Remove field if governance app not available
            del self.fields['intended_ward']

class UserSearchForm(forms.Form):
    """Form for searching users"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, username, or email...'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + UserProfile.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_verified = forms.ChoiceField(
        choices=[
            ('', 'All Users'),
            ('verified', 'Verified Only'),
            ('unverified', 'Unverified Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'All Users'),
            ('active', 'Active Only'),
            ('inactive', 'Inactive Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    registration_status = forms.ChoiceField(
        choices=[('', 'All Status')] + UserProfile.REGISTRATION_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    registration_method = forms.ChoiceField(
        choices=[('', 'All Methods')] + UserProfile.REGISTRATION_METHOD,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class UserApprovalForm(forms.ModelForm):
    """Form for approving/rejecting user registrations"""
    
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for rejection (required if rejecting)'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = []
        
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if action == 'reject' and not rejection_reason:
            raise forms.ValidationError("Rejection reason is required when rejecting a user.")
        
        return cleaned_data