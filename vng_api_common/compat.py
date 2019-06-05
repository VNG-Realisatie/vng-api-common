from typing import Union

from django.http import HttpRequest


def get_header(request: HttpRequest, header: str) -> Union[None, str]:
    """
    Extract the value of the header from the request.

    Django 2.2 exposes request.headers, while older versions require you to
    access it from request.META with the ``HTTP_`` prefix.
    """
    # django 2.2
    if hasattr(request, 'headers'):
        return request.headers.get(header)

    # older versions
    header_key = f"HTTP_{header}".replace('-', '_').upper()
    return request.META.get(header_key)
