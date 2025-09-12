from django import template
from num2words import num2words  # pip install num2words

register = template.Library()

@register.filter
def number_to_words(value):
    try:
        return num2words(value, to='cardinal', lang='en').capitalize()
    except Exception:
        return value

