from django import template
from accounts.models import User

register = template.Library()

@register.simple_tag
def user_display_name(user, team):
    """User.get_display_name_in_team()을 템플릿에서 사용"""
    return User.get_display_name_in_team(user, team)
