"""
Interface to get a client object for a given URL.
"""

import logging

from ape_pie import APIClient
from requests import JSONDecodeError, RequestException, Response

logger = logging.getLogger(__name__)


class ClientError(RuntimeError):
    pass


class NoServiceConfigured(RuntimeError):
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


def get_client(
    url: str, raise_exceptions: bool = False, **client_kwargs
) -> Client | None:
    """
    Get a client instance for the given URL.
    If no suitable client is found, ``None`` is returned.
    """
    from zgw_consumers.client import build_client
    from zgw_consumers.models import Service

    service: Service | None = Service.get_service(url)

    if not service:
        logger.warning(f"No service configured for {url}")
        if raise_exceptions:
            raise NoServiceConfigured(f"{url} API should be added to Service model")
        return

    return build_client(service, client_factory=Client, **client_kwargs)
