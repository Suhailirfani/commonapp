from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to look up a key in a dictionary.
    Supports string or integer key matching.
    """
    if isinstance(dictionary, dict):
        val = dictionary.get(str(key))
        if val is None:
            val = dictionary.get(key)
        return val
    return None
