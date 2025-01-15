from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")

@register.filter
def call_get_progress_for_user(obj, user):
    """
    Call get_progress_for_user method with user argument
    """
    return obj.get_progress_for_user(user)


@register.filter
def call_get_course_progress(obj, user):
    """Get course progress for a user"""
    return obj.get_course_progress_for_user(user)
