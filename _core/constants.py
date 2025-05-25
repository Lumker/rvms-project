# Common constants used across the application

# Date formats
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_DATE_FORMAT = '%d %B %Y'
DISPLAY_DATETIME_FORMAT = '%d %B %Y at %H:%M'

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File upload limits (in bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB

# South African specific
SA_PROVINCES = [
    ('EC', 'Eastern Cape'),
    ('FS', 'Free State'),
    ('GP', 'Gauteng'),
    ('KZN', 'KwaZulu-Natal'),
    ('LP', 'Limpopo'),
    ('MP', 'Mpumalanga'),
    ('NC', 'Northern Cape'),
    ('NW', 'North West'),
    ('WC', 'Western Cape'),
]

# Common regex patterns
PATTERNS = {
    'sa_id': r'^\d{13}$',
    'phone': r'^\+?1?\d{9,15}$',
    'postal_code': r'^\d{4}$',
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
}

# Status colors for templates
STATUS_COLORS = {
    'active': 'success',
    'inactive': 'secondary',
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'completed': 'info',
    'cancelled': 'dark',
}