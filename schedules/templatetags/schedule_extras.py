from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """딕셔너리에서 키로 값을 조회하는 템플릿 필터"""
    if isinstance(dictionary, dict):
        return dictionary.get(int(key), 0)
    return 0