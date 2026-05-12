from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='replace')
def replace(value, arg):
    """Replaces all values of arg with a space or other char"""
    parts = arg.split(',')
    if len(parts) == 2:
        return value.replace(parts[0], parts[1])
    return value.replace(arg, ' ')

@register.filter(name='risk_color')
def risk_color(risk_value):
    """Returns aesthetic color tokens based on institutional risk levels."""
    risk = str(risk_value).upper()
    if risk in ['HIGH', 'CRITICAL']:
        return 'red'
    return 'orange'
