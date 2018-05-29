from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@stringfilter
def my_split(value, arg):
    """Removes all values of arg from the given string"""
    return value.lower().split(arg)


register.filter('my_split', my_split)
