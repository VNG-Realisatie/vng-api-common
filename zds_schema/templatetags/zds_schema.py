from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()


@register.filter
@stringfilter
def md_table_cell(value: str) -> str:
    """
    Escape pipe symbols to prevent accidental new-cell start.
    """
    return value.replace('|', '\\|')


@register.filter
def crud(row):
    attributes = ['create', 'read', 'update', 'delete']
    bits = []
    for attribute in attributes:
        allowed = getattr(row, attribute)
        letter = attribute[0].upper()
        if allowed:
            bits.append(letter)
        else:
            bits.append(f"~~{letter}~~")
    return "\u200b".join(bits)
