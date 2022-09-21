import importlib
import re

from drf_spectacular.drainage import reset_generator_stats
from drf_spectacular.generators import (
    EndpointEnumerator as _EndpointEnumerator,
    SchemaGenerator as _OpenAPISchemaGenerator,
)
from drf_spectacular.plumbing import (
    build_root_object,
    normalize_result_object,
    sanitize_result_object,
)
from drf_spectacular.settings import spectacular_settings


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
        """Generate a OpenAPI schema."""
        reset_generator_stats()
        result = build_root_object(
            paths=self.parse(request, public),
            components=self.registry.build(spectacular_settings.APPEND_COMPONENTS),
            version=self.api_version or getattr(request, "version", None),
        )
        result = self.restructure_root_object(result)
        for hook in spectacular_settings.POSTPROCESSING_HOOKS:
            result = hook(result=result, generator=self, request=request, public=public)

        return sanitize_result_object(normalize_result_object(result))

    def create_view(self, callback, method, request=None):
        view = super(_OpenAPISchemaGenerator, self).create_view(
            callback, method, request=request
        )

        if method == "HEAD":
            return view

        return super().create_view(callback, method, request=request)

    def restructure_root_object(self, root):
        settings = spectacular_settings
        if settings.DESCRIPTION:
            schema_module = importlib.import_module(settings.DESCRIPTION)
            root["info"]["title"] = schema_module.TITLE
            root["info"]["version"] = schema_module.VERSION
            root["info"]["description"] = (
                schema_module.DESCRIPTION if schema_module.DESCRIPTION else ""
            )
            root["info"]["contact"] = schema_module.CONTACT
            root["info"]["license"] = schema_module.LICENSE

        if settings.TAGS:
            TAGS = []
            for tag in settings.TAGS:
                schema_module = importlib.import_module(tag["path"])
                doc_string = schema_module.__dict__[tag["view"]].__doc__
                doc_string = re.sub(r" +", " ", doc_string)

                TAGS.append({"name": tag["name"], "description": doc_string})
            root["tags"] = TAGS
        return root
