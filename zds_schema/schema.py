import logging

from drf_yasg import openapi
from drf_yasg.generators import (
    OpenAPISchemaGenerator as _OpenAPISchemaGenerator
)

logger = logging.getLogger(__name__)


class OpenAPISchemaGenerator(_OpenAPISchemaGenerator):

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
            if not parameter.name.endswith('_uuid'):
                continue
            parameter.format = openapi.FORMAT_UUID
            parameter.description = "Unieke resource identifier (UUID4)"
        return parameters
