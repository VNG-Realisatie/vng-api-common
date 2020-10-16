"""
Interface to get a zds_client object for a given URL.
"""
from typing import Optional

from django.conf import settings
from django.utils.module_loading import import_string

from zds_client import Client

from .models import APICredential


def get_client(api_root_url: str) -> Optional[Client]:
    """
    Get a client instance for the given URL.

    If the setting CUSTOM_CLIENT_FETCHER is defined, then this callable is invoked.
    Otherwise we fall back on the default implementation.

    If no suitable client is found, ``None`` is returned.
    """
    custom_client_fetcher = getattr(settings, "CUSTOM_CLIENT_FETCHER", None)
    if custom_client_fetcher:
        client_getter = import_string(custom_client_fetcher)
        return client_getter(api_root_url)

    # default implementation
    Client = import_string(settings.ZDS_CLIENT_CLASS)

    if not api_root_url.endswith("/"):
        api_root_url = f"{api_root_url}/"

    client = Client.from_url(api_root_url)
    if client is None:
        return None

    client.base_url = api_root_url
    client.auth = APICredential.get_auth(api_root_url)
    return client
