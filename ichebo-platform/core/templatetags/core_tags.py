from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replaces characters in a string.
    Usage: {{ value|replace:"old,new" }}
    """
    if ',' not in arg:
        return value
    old, new = arg.split(',', 1)
    return value.replace(old, new)
