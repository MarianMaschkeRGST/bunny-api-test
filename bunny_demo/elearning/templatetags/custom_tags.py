from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")

@register.filter
def call_with_user(obj, user):
    """
    Call get_progress_for_user method with user argument
    """
    return obj.get_progress_for_user(user)
