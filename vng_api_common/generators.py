import importlib

from drf_spectacular.drainage import reset_generator_stats
from drf_spectacular.plumbing import sanitize_result_object, normalize_result_object, \
    sanitize_specification_extensions
from drf_spectacular.settings import spectacular_settings

from drf_spectacular.generators import (
    SchemaGenerator as _OpenAPISchemaGenerator,
)

class OpenAPISchemaGenerator(_OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        """ Generate a OpenAPI schema. """
        reset_generator_stats()
        result = self.build_root_object(
            paths=self.parse(request, public),
            components=self.registry.build(spectacular_settings.APPEND_COMPONENTS),
            version=self.api_version or getattr(request, 'version', None),
        )
        for hook in spectacular_settings.POSTPROCESSING_HOOKS:
            result = hook(result=result, generator=self, request=request, public=public)

        return sanitize_result_object(normalize_result_object(result))

    def build_root_object(self,paths, components, version):
        settings = spectacular_settings
        schema_module = importlib.import_module(settings.DESCRIPTION)

        if settings.VERSION and version:
            version = schema_module.VERSION
        else:
            version = settings.VERSION or version or ''
        root = {
            'openapi': '3.0.3',
            'info': {
                'title': schema_module.TITLE,
                'version': version,
                **sanitize_specification_extensions(settings.EXTENSIONS_INFO),
            },
            'paths': {**paths, **settings.APPEND_PATHS},
            'components': components,
            **sanitize_specification_extensions(settings.EXTENSIONS_ROOT),
        }
        if settings.DESCRIPTION:
            root['info']['description'] = schema_module.DESCRIPTION if schema_module.DESCRIPTION else ""
        if settings.TOS:
            root['info']['termsOfService'] = settings.TOS
        if settings.CONTACT:
            root['info']['contact'] = schema_module.CONTACT
        if settings.LICENSE:
            root['info']['license'] = schema_module.LICENSE
        if settings.SERVERS:
            root['servers'] = settings.SERVERS
        if settings.TAGS:
            root['tags'] = settings.TAGS
        if settings.EXTERNAL_DOCS:
            root['externalDocs'] = settings.EXTERNAL_DOCS
        return root
