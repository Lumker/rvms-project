from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from datetime import datetime

# Phone number validator
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
)

# South African specific phone validator
sa_phone_validator = RegexValidator(
    regex=r'^(\+27|0)[6-8][0-9]{8}$',
    message=_("Enter a valid South African phone number. Format: +27XXXXXXXXX or 0XXXXXXXXX")
)

# South African ID number validator
sa_id_validator = RegexValidator(
    regex=r'^\d{13}$',
    message=_("South African ID number must be exactly 13 digits.")
)

# Postal code validator (South African format)
postal_code_validator = RegexValidator(
    regex=r'^\d{4}$',
    message=_("Postal code must be exactly 4 digits.")
)

# Email validator (more strict than Django's default)
email_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    message=_("Enter a valid email address.")
)

# Username validator (alphanumeric and underscore only)
username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_]+$',
    message=_("Username can only contain letters, numbers, and underscores.")
)

# South African company registration number validator
company_reg_validator = RegexValidator(
    regex=r'^\d{4}\/\d{6}\/\d{2}$',
    message=_("Company registration number must be in format: YYYY/XXXXXX/XX")
)

def validate_sa_id_number(value):
    """
    Validate South African ID number using Luhn algorithm
    """
    if not value or len(value) != 13:
        raise ValidationError(_("ID number must be exactly 13 digits."))
    
    if not value.isdigit():
        raise ValidationError(_("ID number must contain only digits."))
    
    # Extract and validate date of birth
    try:
        year = int(value[:2])
        month = int(value[2:4])
        day = int(value[4:6])
        
        # Determine century (simple heuristic)
        current_year = datetime.now().year % 100
        if year <= current_year + 10:  # Assume future births within 10 years
            year += 2000
        else:
            year += 1900
        
        # Validate date
        datetime(year, month, day)
    except (ValueError, TypeError):
        raise ValidationError(_("Invalid date of birth in ID number."))
    
    # Validate gender digit (position 6)
    gender_digit = int(value[6])
    if gender_digit not in range(10):
        raise ValidationError(_("Invalid gender digit in ID number."))
    
    # Validate citizenship digit (position 10)
    citizenship_digit = int(value[10])
    if citizenship_digit not in [0, 1]:
        raise ValidationError(_("Invalid citizenship digit in ID number."))
    
    # Luhn algorithm for checksum validation
    odd_sum = sum(int(value[i]) for i in range(0, 12, 2))
    even_digits = ''.join(value[i] for i in range(1, 12, 2))
    even_sum = sum(int(digit) for digit in str(int(even_digits) * 2))
    
    total = odd_sum + even_sum
    check_digit = (10 - (total % 10)) % 10
    
    if check_digit != int(value[12]):
        raise ValidationError(_("Invalid ID number checksum."))
    
    return value

def validate_phone_number(value):
    """
    Validate and format South African phone numbers
    """
    if not value:
        return value
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', value)
    
    # Validate length and format
    if len(digits) == 10 and digits.startswith('0'):
        # Local format: 0XXXXXXXXX
        if not re.match(r'^0[6-8][0-9]{8}$', digits):
            raise ValidationError(_("Invalid South African phone number format."))
    elif len(digits) == 11 and digits.startswith('27'):
        # International format: 27XXXXXXXXX
        if not re.match(r'^27[6-8][0-9]{8}$', digits):
            raise ValidationError(_("Invalid South African phone number format."))
    else:
        raise ValidationError(_("Phone number must be 10 digits (0XXXXXXXXX) or 11 digits (27XXXXXXXXX)."))
    
    return value

def validate_postal_code(value):
    """
    Validate South African postal code
    """
    if not value:
        return value
    
    if not re.match(r'^\d{4}$', str(value)):
        raise ValidationError(_("Postal code must be exactly 4 digits."))
    
    # Check if it's a valid SA postal code range (1000-9999)
    code = int(value)
    if code < 1000 or code > 9999:
        raise ValidationError(_("Invalid South African postal code."))
    
    return value

def validate_file_size(value, max_size_mb=5):
    """
    Validate file size
    """
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            _("File size must be less than %(max_size)s MB.") % {'max_size': max_size_mb}
        )

def validate_image_file(value):
    """
    Validate image file type and size
    """
    import os
    from django.core.files.images import get_image_dimensions
    
    # Check file extension
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(_("Only image files are allowed (JPG, PNG, GIF, WebP)."))
    
    # Check file size (2MB limit for images)
    validate_file_size(value, 2)
    
    # Check image dimensions
    try:
        width, height = get_image_dimensions(value)
        if width and height:
            if width > 2000 or height > 2000:
                raise ValidationError(_("Image dimensions must be less than 2000x2000 pixels."))
            if width < 100 or height < 100:
                raise ValidationError(_("Image dimensions must be at least 100x100 pixels."))
    except Exception:
        raise ValidationError(_("Invalid image file."))

def validate_password_strength(password):
    """
    Validate password strength
    """
    if len(password) < 8:
        raise ValidationError(_("Password must be at least 8 characters long."))
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_("Password must contain at least one uppercase letter."))
    
    if not re.search(r'[a-z]', password):
        raise ValidationError(_("Password must contain at least one lowercase letter."))
    
    if not re.search(r'\d', password):
        raise ValidationError(_("Password must contain at least one digit."))
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(_("Password must contain at least one special character."))
    
    # Check for common passwords
    common_passwords = [
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'password123', 'admin', 'letmein', 'welcome', 'monkey'
    ]
    if password.lower() in common_passwords:
        raise ValidationError(_("This password is too common."))
    
    return password

def validate_age_range(birth_date, min_age=0, max_age=120):
    """
    Validate age is within acceptable range
    """
    if not birth_date:
        return birth_date
    
    from datetime import date
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    if age < min_age:
        raise ValidationError(_("Age must be at least %(min_age)s years.") % {'min_age': min_age})
    
    if age > max_age:
        raise ValidationError(_("Age cannot be more than %(max_age)s years.") % {'max_age': max_age})
    
    return birth_date

# Custom field validators for specific use cases
class MinimumAgeValidator:
    """Validator to ensure minimum age requirement"""
    
    def __init__(self, min_age):
        self.min_age = min_age
    
    def __call__(self, value):
        validate_age_range(value, min_age=self.min_age)
    
    def __eq__(self, other):
        return isinstance(other, MinimumAgeValidator) and self.min_age == other.min_age

class MaximumAgeValidator:
    """Validator to ensure maximum age requirement"""
    
    def __init__(self, max_age):
        self.max_age = max_age
    
    def __call__(self, value):
        validate_age_range(value, max_age=self.max_age)
    
    def __eq__(self, other):
        return isinstance(other, MaximumAgeValidator) and self.max_age == other.max_age