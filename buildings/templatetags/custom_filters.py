from django import template
from buildings.models import Log

register = template.Library()


@register.filter(name="action_label")
def action_label(action_code):
    action_dict = dict(Log.ACTION_CHOICES)
    return action_dict.get(action_code, action_code)
