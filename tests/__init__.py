from vng_api_common.generators import OpenAPISchemaGenerator


def generate_schema(patterns, request=None):
    generator = OpenAPISchemaGenerator(patterns=patterns)
    return generator.get_schema(request=request)
