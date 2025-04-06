from django import template
from ..models import impact

register = template.Library()

@register.filter(name='is_marked')
def is_marked(operation, subresource):
    return impact.objects.filter(
        id_operation=operation,
        id_subresource=subresource,
        is_marked=True
    ).exists()