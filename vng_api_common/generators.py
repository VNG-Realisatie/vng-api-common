from importlib import import_module
from unittest import mock

from django.conf import settings

import drf_spectacular.plumbing
from drf_spectacular.generators import (
    EndpointEnumerator as _EndpointEnumerator,
    SchemaGenerator as _OpenAPISchemaGenerator,
)


def build_mock_request(*args, **kwargs):
    """Build a mock request for drf_spectacular schema generation.

    Wraps the default drf_spectacular GET_MOCK_REQUEST and attaches a mock jwt_auth on it.
    """
    request = drf_spectacular.plumbing.build_mock_request(*args, **kwargs)
    request._request.jwt_auth = mock.Mock()
    return request


class EndpointEnumerator(_EndpointEnumerator):
    def get_allowed_methods(self, callback) -> list:
        methods = super().get_allowed_methods(callback)

        # head requests are explicitly supported for endpoint that provide caching
        conditional_retrieves = getattr(callback.cls, "_conditional_retrieves", [])
        if not conditional_retrieves:
            return methods

        if set(conditional_retrieves).intersection(callback.actions.values()):
            methods.append("HEAD")

        return methods


class OpenAPISchemaGenerator(_OpenAPISchemaGenerator):
    endpoint_inspector_cls = EndpointEnumerator

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request=request, public=public)

        assert isinstance(schema, dict)
        assert isinstance(schema["tags"], list)
        schema["tags"] += self.get_tags()

        try:
            info_module = import_module(settings.DOCUMENTATION_INFO_MODULE)
        except (ImportError, AttributeError):
            return schema

        info_kwargs = {
            variable.lower(): getattr(info_module, variable)
            for variable in info_module.__all__
        }

        schema["info"].update(info_kwargs)
        return schema

    def get_tags(self):
        tags = []

        endpoints = self._get_paths_and_endpoints()
        for path, path_regex, method, view in endpoints:
            path_fragments = path.split("/api/v{version")
            endpoint_path = path_fragments[-1]

            if "{" in endpoint_path:
                continue

            tag = endpoint_path.rsplit("/", 1)[-1]

            # exclude special non-rest actions
            if tag.startswith("_") or not tag or tag in [tag["name"] for tag in tags]:
                continue

            tags.append(
                {
                    "name": tag,
                    "description": getattr(view, "global_description", ""),
                }
            )

        return tags

    def create_view(self, callback, method, request=None):
        if (
            method != "HEAD"
            and hasattr(callback.cls, "_conditional_retrieves")
            and "head" not in callback.actions
        ):
            # hack to get test_schema_root_tags pass when run in isolation
            callback.actions["head"] = callback.cls._conditional_retrieves[0]

        return super().create_view(callback, method, request=request)
