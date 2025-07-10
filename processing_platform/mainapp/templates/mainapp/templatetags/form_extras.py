import os
from django import template

register = template.Library()

@register.filter
def basename(path):
    """
    Return the final component of a filesystem path.
    Example: '/a/b/c.txt' → 'c.txt'
    """
    return os.path.basename(path)
