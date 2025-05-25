from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from ..constants import STATUS_COLORS
from ..utils import calculate_age, format_phone_number

register = template.Library()

@register.filter
def status_badge(value):
    """Convert status to Bootstrap badge"""
    if not value:
        return ''
    
    color = STATUS_COLORS.get(value.lower(), 'secondary')
    return format_html(
        '<span class="badge badge-{}">{}</span>',
        color,
        value.title()
    )

@register.filter
def format_phone(phone):
    """Format phone number"""
    return format_phone_number(phone)

@register.filter
def age_from_date(birth_date):
    """Calculate age from birth date"""
    age = calculate_age(birth_date)
    return f"{age} years old" if age else "Unknown"

@register.filter
def truncate_chars(value, length):
    """Truncate text to specified length"""
    if len(value) <= length:
        return value
    return value[:length] + '...'

@register.simple_tag
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key)

@register.inclusion_tag('_core/pagination.html')
def pagination(page_obj, request):
    """Render pagination template"""
    return {
        'page_obj': page_obj,
        'request': request,
    }

@register.simple_tag
def query_string(request, **kwargs):
    """Update query string parameters"""
    query_dict = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            query_dict[key] = value
        elif key in query_dict:
            del query_dict[key]
    return query_dict.urlencode()