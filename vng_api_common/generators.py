from importlib import import_module

from django.conf import settings

from drf_spectacular.generators import (
    EndpointEnumerator as _EndpointEnumerator,
    SchemaGenerator as _OpenAPISchemaGenerator,
)


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

    def create_view(self, callback, method, request=None):
        if (
            method != "HEAD"
            and hasattr(callback.cls, "_conditional_retrieves")
            and "head" not in callback.actions
        ):
            # hack to get test_schema_root_tags pass when run in isolation
            callback.actions["head"] = callback.cls._conditional_retrieves[0]

        return super().create_view(callback, method, request=request)
