# infrastructure/templatetags/infrastructure_tags.py (update)

from django import template
from django.db.models import Count, Q

register = template.Library()

@register.filter
def condition_color(condition):
    """Return Bootstrap color class based on condition"""
    color_map = {
        'excellent': 'success',
        'good': 'info', 
        'fair': 'warning',
        'poor': 'danger',
        'critical': 'danger',
        'non_functional': 'secondary',
        # Maintenance status colors
        'scheduled': 'warning',
        'in_progress': 'info',
        'completed': 'success',
        'cancelled': 'danger',
        'deferred': 'secondary',
        # Default
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        # Priority levels
        'low': 'secondary',
        'medium': 'info',
        'high': 'warning',
        'urgent': 'danger',
    }
    return color_map.get(condition, 'secondary')

@register.filter
def status_icon(status):
    """Return FontAwesome icon based on status"""
    icon_map = {
        'excellent': 'fa-check-circle',
        'good': 'fa-thumbs-up',
        'fair': 'fa-exclamation-triangle',
        'poor': 'fa-times-circle',
        'critical': 'fa-exclamation-circle',
        'non_functional': 'fa-ban',
        # Maintenance status icons
        'scheduled': 'fa-calendar',
        'in_progress': 'fa-cog fa-spin',
        'completed': 'fa-check',
        'cancelled': 'fa-times',
        'deferred': 'fa-pause',
        # Service interruption icons
        'ongoing': 'fa-exclamation-triangle',
        'resolved': 'fa-check-circle',
    }
    return icon_map.get(status, 'fa-question-circle')

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    if not total or total == 0:
        return 0
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0

@register.filter
def duration_hours(start_time, end_time):
    """Calculate duration in hours between two datetime objects"""
    if not start_time or not end_time:
        return 0
    try:
        return round((end_time - start_time).total_seconds() / 3600, 2)
    except:
        return 0

@register.simple_tag
def get_asset_count_by_condition(queryset, condition):
    """Get count of assets by condition - Fixed version"""
    try:
        # If queryset is already evaluated (like from pagination), 
        # we need to count manually
        if hasattr(queryset, '_result_cache') and queryset._result_cache is not None:
            # Queryset is already evaluated, count manually
            return sum(1 for item in queryset if getattr(item, 'overall_condition', None) == condition)
        else:
            # Queryset not evaluated yet, can use filter
            return queryset.filter(overall_condition=condition).count()
    except:
        return 0

@register.simple_tag
def get_maintenance_cost_by_month(year, month):
    """Get maintenance cost for a specific month"""
    try:
        from infrastructure.models import MaintenanceRecord
        from django.db.models import Sum
        
        cost = MaintenanceRecord.objects.filter(
            completed_date__year=year,
            completed_date__month=month,
            status='completed'
        ).aggregate(total=Sum('actual_cost'))['total']
        
        return cost or 0
    except:
        return 0

@register.inclusion_tag('infrastructure/includes/condition_badge.html')
def condition_badge(condition, size='sm'):
    """Render a condition badge"""
    return {
        'condition': condition,
        'size': size,
        'color': condition_color(condition),
        'icon': status_icon(condition)
    }

@register.inclusion_tag('infrastructure/includes/asset_card.html')
def asset_card(asset):
    """Render an asset card"""
    return {'asset': asset}

@register.simple_tag
def count_by_condition(inspections_list, condition):
    """Count inspections by condition from a list"""
    try:
        return sum(1 for inspection in inspections_list if inspection.overall_condition == condition)
    except:
        return 0