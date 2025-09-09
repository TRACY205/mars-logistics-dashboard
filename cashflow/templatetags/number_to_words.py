from django import template
import math

register = template.Library()

# Words for digits
ones = ("", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine")
tens = ("", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety")
teens = ("Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
         "Seventeen", "Eighteen", "Nineteen")

# Helper function to convert numbers to words
def _num_to_words(n):
    if n == 0:
        return "Zero"
    words = ""
    if n >= 1000:
        words += _num_to_words(n // 1000) + " Thousand "
        n %= 1000
    if n >= 100:
        words += ones[n // 100] + " Hundred "
        n %= 100
    if n >= 20:
        words += tens[n // 10] + " "
        n %= 10
    elif n >= 10:
        words += teens[n - 10] + " "
        n = 0
    if n > 0:
        words += ones[n] + " "
    return words.strip()

# Template filter
@register.filter
def number_to_words(value):
    try:
        value = float(value)
        shs = int(math.floor(value))
        cts = int(round((value - shs) * 100))
        if cts > 0:
            return f"{_num_to_words(shs)} Shillings and {cts} Cents Only"
        else:
            return f"{_num_to_words(shs)} Shillings Only"
    except:
        return value
