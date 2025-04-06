from django import template
from django.shortcuts import get_object_or_404
from ..models import impact, rating

register = template.Library()

# Filter for the left side of the matrix
@register.filter(name='is_marked')
def is_marked(operation, subresource):
    return impact.objects.filter(
        id_operation=operation,
        id_subresource=subresource,
        is_marked=True
    ).exists()

# Filter for the left side of the matrix (get rating)
@register.filter(name='get_rating')
def get_rating(phase, subresource):
    try:
        return rating.objects.get(id_phase=phase, id_subresource=subresource)
    except rating.DoesNotExist:
        return None  # Return None so you can check in the template
