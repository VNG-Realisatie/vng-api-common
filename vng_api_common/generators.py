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

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request=request, public=public)
        schema["tags"] = self.get_tags()

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
        view = super(_OpenAPISchemaGenerator, self).create_view(
            callback, method, request=request
        )

        if method == "HEAD":
            return view

        return super().create_view(callback, method, request=request)
