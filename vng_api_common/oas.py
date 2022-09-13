"""
Utility module for Open API Specification 3.0.x.

This should get merged into gemma-zds-client, but some heavy refactoring is
needed for that.
"""
from typing import Union

import requests
import yaml

TYPE_OBJECT = "object"
TYPE_STRING = "string"
TYPE_NUMBER = "number"
TYPE_INTEGER = "integer"
TYPE_BOOLEAN = "boolean"
TYPE_ARRAY = "array"
TYPE_FILE = "file"

TYPE_MAP = {
    TYPE_OBJECT: dict,
    TYPE_STRING: str,
    TYPE_NUMBER: (float, int),
    TYPE_INTEGER: int,
    TYPE_BOOLEAN: bool,
    TYPE_ARRAY: list,
}


class SchemaFetcher:
    def __init__(self):
        self.cache = {}

    def fetch(self, url: str):
        """
        Fetch a YAML-based OAS 3.0.x schema.
        """
        if url in self.cache:
            return self.cache[url]

        response = requests.get(url)
        response.raise_for_status()

        spec = yaml.safe_load(response.content)
        spec_version = response.headers.get(
            "X-OAS-Version", spec.get("openapi", spec.get("swagger", ""))
        )
        if not spec_version.startswith("3.0"):
            raise ValueError("Unsupported spec version: {}".format(spec_version))

        self.cache[url] = spec
        return spec


def obj_has_shape(obj: Union[list, dict], schema: dict, resource: str) -> bool:
    """
    Compare an instance of an object with the expected shape from an OAS 3 schema.

    ..todo:: doesn't handle references and nested schema's yet.

    :param obj: the value retrieved from the endpoint, json-decoded to a dict or list
    :param schema: the OAS 3.0.x schema to test against, yaml-decoded to dict
    :param resource: the name of the resource to test the schape against
    """
    obj_schema = schema["components"]["schemas"][resource]

    required = obj_schema.get("required", [])

    for prop, prop_schema in obj_schema["properties"].items():
        if prop in required and prop not in obj:
            # missing required prop -> can't match the schema
            return False

        # can't compare something that isn't there...
        if prop not in obj:
            continue

        value = obj[prop]

        # TODO Handling references not yet implemented
        if "$ref" in prop_schema:
            continue

        # Allow None if property is nullable
        if value is None:
            if prop_schema.get("nullable", False):
                continue
            else:
                return False

        expected_type = TYPE_MAP[prop_schema["type"]]

        # type mismatch -> not what we're looking for
        if not isinstance(value, expected_type):
            return False

    return True


fetcher = SchemaFetcher()
