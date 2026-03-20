from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None
    
@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def to_range(value):
    try:
        upper = int(value)
        if upper < 1:
            return [1]
        return range(1, upper + 1)
    except (ValueError, TypeError):
        return [1]