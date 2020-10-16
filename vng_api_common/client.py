"""
Interface to get a zds_client object for a given URL.
"""
from typing import Optional

from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string

from zds_client import Client


def get_client(url: str, url_is_api_root=False) -> Optional[Client]:
    """
    Get a client instance for the given URL.

    If the setting CUSTOM_CLIENT_FETCHER is defined, then this callable is invoked.
    Otherwise we fall back on the default implementation.

    If no suitable client is found, ``None`` is returned.
    """
    custom_client_fetcher = getattr(settings, "CUSTOM_CLIENT_FETCHER", None)
    if custom_client_fetcher:
        client_getter = import_string(custom_client_fetcher)
        return client_getter(url)

    # default implementation
    Client = import_string(settings.ZDS_CLIENT_CLASS)

    if url_is_api_root and not url.endswith("/"):
        url = f"{url}/"

    client = Client.from_url(url)
    if client is None:
        return None

    APICredential = apps.get_model("vng_api_common", "APICredential")

    if url_is_api_root:
        client.base_url = url

    client.auth = APICredential.get_auth(url)
    return client
