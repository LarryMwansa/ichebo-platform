from django import template

register = template.Library()


@register.filter
def dict_key(d, key):
    """Return d[key] or empty list if missing."""
    return d.get(key, [])


@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter."""
    return value.split(delimiter)
