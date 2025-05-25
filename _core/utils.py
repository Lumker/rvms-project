import re
import random
import string
from datetime import datetime, date
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def generate_unique_code(length=8, prefix="", model=None, field_name='code'):
    """
    Generate a unique code for a model field
    """
    while True:
        code = prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if model and hasattr(model, field_name):
            if not model.objects.filter(**{field_name: code}).exists():
                return code
        else:
            return code

def validate_sa_id_number(id_number):
    """
    Validate South African ID number using Luhn algorithm
    """
    if not isinstance(id_number, str) or len(id_number) != 13:
        return False
    
    if not id_number.isdigit():
        return False
    
    # Extract date of birth
    try:
        year = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])
        
        # Determine century
        current_year = datetime.now().year % 100
        if year <= current_year:
            year += 2000
        else:
            year += 1900
        
        # Validate date
        datetime(year, month, day)
    except ValueError:
        return False
    
    # Luhn algorithm for checksum
    odd_sum = sum(int(id_number[i]) for i in range(0, 12, 2))
    even_digits = ''.join(id_number[i] for i in range(1, 12, 2))
    even_sum = sum(int(digit) for digit in str(int(even_digits) * 2))
    
    total = odd_sum + even_sum
    check_digit = (10 - (total % 10)) % 10
    
    return check_digit == int(id_number[12])

def format_phone_number(phone):
    """Format phone number to standard format"""
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Add country code if missing
    if len(digits) == 10 and digits.startswith('0'):
        digits = '27' + digits[1:]
    elif len(digits) == 9:
        digits = '27' + digits
    
    # Format as +27 XX XXX XXXX
    if len(digits) == 11 and digits.startswith('27'):
        return f"+27 {digits[2:4]} {digits[4:7]} {digits[7:]}"
    
    return phone

def send_notification_email(to_email, subject, template_name, context, from_email=None):
    """
    Send notification email using template
    """
    if not from_email:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
    
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    
    return send_mail(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=[to_email],
        html_message=html_message,
        fail_silently=False,
    )

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_financial_year():
    """Get current South African financial year (April - March)"""
    today = date.today()
    if today.month >= 4:  # April to December
        return f"{today.year}/{today.year + 1}"
    else:  # January to March
        return f"{today.year - 1}/{today.year}"

class DateTimeHelper:
    """Helper class for date and time operations"""
    
    @staticmethod
    def now():
        return timezone.now()
    
    @staticmethod
    def today():
        return timezone.now().date()
    
    @staticmethod
    def start_of_day(date_obj=None):
        if date_obj is None:
            date_obj = timezone.now().date()
        return timezone.make_aware(datetime.combine(date_obj, datetime.min.time()))
    
    @staticmethod
    def end_of_day(date_obj=None):
        if date_obj is None:
            date_obj = timezone.now().date()
        return timezone.make_aware(datetime.combine(date_obj, datetime.max.time()))
    
    @staticmethod
    def start_of_month(date_obj=None):
        if date_obj is None:
            date_obj = timezone.now().date()
        return date_obj.replace(day=1)
    
    @staticmethod
    def end_of_month(date_obj=None):
        if date_obj is None:
            date_obj = timezone.now().date()
        next_month = date_obj.replace(day=28) + timezone.timedelta(days=4)
        return next_month - timezone.timedelta(days=next_month.day)