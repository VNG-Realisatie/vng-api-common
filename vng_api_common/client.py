"""
Interface to get a client object for a given URL.
"""

import logging
from typing import Any, Optional

from django.conf import settings
from django.utils.module_loading import import_string

from ape_pie import APIClient
from requests import JSONDecodeError, RequestException, Response

logger = logging.getLogger(__name__)


class ClientError(RuntimeError):
    pass


# TODO: use more approriate method name
def to_internal_data(response: Response) -> dict | list | None:
    try:
        response_json = response.json()
    except JSONDecodeError:
        logger.exception("Unable to parse json from response")
        response_json = None

    try:
        response.raise_for_status()
    except RequestException as exc:
        if response.status_code >= 500:
            raise
        raise ClientError(response_json if response_json is not None else {}) from exc

    assert response_json
    return response_json


class Client(APIClient):
    def request(
        self, method: str | bytes, url: str | bytes, *args, **kwargs
    ) -> Response:

        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")
        headers.setdefault("Content-Type", "application/json")

        kwargs["headers"] = headers

        data = kwargs.get("data", {})

        if data:
            kwargs["json"] = data

        return super().request(method, url, *args, **kwargs)


def get_client(url: str) -> Client | None:
    """
    Get a client instance for the given URL.
    If no suitable client is found, ``None`` is returned.
    """
    from zgw_consumers.client import build_client
    from zgw_consumers.models import Service

    service: Optional[Service] = Service.get_service(url)

    if not service:
        logger.warning(f"No service configured for {url}")
        return None

    return build_client(service, client_factory=Client)
