from collections import OrderedDict
from typing import List

from drf_yasg import openapi
from drf_yasg.generators import (
    EndpointEnumerator as _EndpointEnumerator,
    OpenAPISchemaGenerator as _OpenAPISchemaGenerator,
)
from drf_yasg.utils import get_consumes, get_produces
from rest_framework.schemas.utils import is_list_view
from rest_framework.settings import api_settings

from vng_api_common.utils import get_view_summary


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
    endpoint_enumerator_class = EndpointEnumerator

    def get_tags(self, request=None, public=False):
        """Retrieve the tags for the root schema.

        :param request: the request used for filtering accessible endpoints and finding the spec URI
        :param bool public: if True, all endpoints are included regardless of access through `request`

        :return: List of tags containing the tag name and a description.
        """
        tags = {}

        endpoints = self.get_endpoints(request)
        for path, (view_cls, methods) in sorted(endpoints.items()):
            if "{" in path:
                continue

            tag = path.rsplit("/", 1)[-1]
            if tag in tags:
                continue

            # exclude special non-rest actions
            if tag.startswith("_"):
                continue
            tags[tag] = get_view_summary(view_cls)

        return [
            OrderedDict([("name", operation), ("description", desc)])
            for operation, desc in sorted(tags.items())
        ]

    def get_schema(self, request=None, public=False):
        """
        Rewrite parent class to add 'responses' in components
        """
        endpoints = self.get_endpoints(request)
        components = self.reference_resolver_class(
            openapi.SCHEMA_DEFINITIONS, "responses", force_init=True
        )
        self.consumes = get_consumes(api_settings.DEFAULT_PARSER_CLASSES)
        self.produces = get_produces(api_settings.DEFAULT_RENDERER_CLASSES)
        paths, prefix = self.get_paths(endpoints, components, request, public)

        security_definitions = self.get_security_definitions()
        if security_definitions:
            security_requirements = self.get_security_requirements(security_definitions)
        else:
            security_requirements = None

        url = self.url
        if url is None and request is not None:
            url = request.build_absolute_uri()

        return openapi.Swagger(
            info=self.info,
            paths=paths,
            consumes=self.consumes or None,
            produces=self.produces or None,
            tags=self.get_tags(request, public),
            security_definitions=security_definitions,
            security=security_requirements,
            _url=url,
            _prefix=prefix,
            _version=self.version,
            **dict(components),
        )

    def get_path_parameters(self, path, view_cls):
        """Return a list of Parameter instances corresponding to any templated path variables.

        :param str path: templated request path
        :param type view_cls: the view class associated with the path
        :return: path parameters
        :rtype: list[openapi.Parameter]
        """
        parameters = super().get_path_parameters(path, view_cls)

        # see if we can specify UUID a bit more
        for parameter in parameters:
            # the most pragmatic of checks
            if not parameter.name.endswith("_uuid"):
                continue
            parameter.format = openapi.FORMAT_UUID
            parameter.description = "Unieke resource identifier (UUID4)"
        return parameters

    def get_operation_keys(self, subpath, method, view) -> List[str]:
        if method != "HEAD":
            return super().get_operation_keys(subpath, method, view)

        assert not is_list_view(
            subpath, method, view
        ), "HEAD requests are only supported on detail endpoints"

        # taken from DRF schema generation
        named_path_components = [
            component
            for component in subpath.strip("/").split("/")
            if "{" not in component
        ]

        return named_path_components + ["headers"]

    def get_overrides(self, view, method) -> dict:
        if method == "HEAD":
            return {}
        return super().get_overrides(view, method)
