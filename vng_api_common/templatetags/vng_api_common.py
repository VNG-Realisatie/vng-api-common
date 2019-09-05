from django.conf import settings
from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()


@register.filter
@stringfilter
def md_table_cell(value: str) -> str:
    """
    Escape pipe symbols to prevent accidental new-cell start.
    """
    return value.replace("|", "\\|")


@register.filter
def crud(row):
    attributes = ["create", "read", "update", "delete"]
    bits = []
    for attribute in attributes:
        allowed = getattr(row, attribute)
        letter = attribute[0].upper()
        if allowed:
            bits.append(letter)
        else:
            bits.append(f"~~{letter}~~")
    return "\u200b".join(bits)


@register.filter
@stringfilter
def gemmaonline_url(resource: str):
    template = settings.GEMMA_URL_TEMPLATE
    return template.format(
        informatiemodel=settings.GEMMA_URL_INFORMATIEMODEL,
        versie=settings.GEMMA_URL_INFORMATIEMODEL_VERSIE,
        componenttype=settings.GEMMA_URL_COMPONENTTYPE,
        component=resource.lower(),
    )


@register.filter
@stringfilter
def is_local(host: str):
    local_hosts = ["localhost", "127.0.0.1"]
    hostname = host.rsplit(":")[0]
    if hostname in local_hosts:
        return True
    return False
