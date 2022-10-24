"""
Replace internal references to external for reusable components

Due to the limitations of drf_yasg we cannot handle this at the Python level
"""
from django.conf import settings
from django.core.management import BaseCommand

import oyaml as yaml
import requests


class QuotedString(str):
    pass


def quoted_scalar(dumper, data):
    # a representer to force quotations on scalars
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")


def replace_refs(source: dict, replace_dict: dict) -> None:
    for k, v in source.items():
        if isinstance(v, dict):
            replace_refs(v, replace_dict)

        if k != "$ref":
            continue

        if v in replace_dict:
            source[k] = QuotedString(replace_dict[v])


class Command(BaseCommand):
    help = "Replace internal references to external for reusable components"

    def add_arguments(self, parser):
        parser.add_argument(
            "api-spec", help="Path to the openapi spec. Will be overwritten!"
        )
        parser.add_argument(
            "output", help="Path to the yaml file with external components"
        )

    def handle(self, **options):
        source = options["api-spec"]
        output = options["output"]
        common_url = settings.COMMON_SPEC
        try:
            response = requests.get(common_url)
            response.raise_for_status()
            common_yaml = response.text
        except requests.exceptions.RequestException:
            return
        common_spec = yaml.safe_load(common_yaml)
        common_components = common_spec["components"]

        with open(source, "r", encoding="utf8") as infile:
            spec = yaml.safe_load(infile)
            components = spec["components"]
            refs = {}

            for scope, scope_items in components.items():
                if scope not in common_components:
                    continue

                for item, item_spec in scope_items.copy().items():
                    if item not in common_components[scope]:
                        continue

                    common_item_spec = common_components[scope][item]
                    if item_spec == common_item_spec:
                        # add ref to replace
                        ref = f"#/components/{scope}/{item}"
                        refs[ref] = f"{common_url}{ref}"

                        # remove item from internal components
                        del components[scope][item]

            # remove empty components
            for scope, scope_items in components.copy().items():
                if not scope_items:
                    del components[scope]

            # replace all refs
            replace_refs(spec, refs)

        with open(output, "w", encoding="utf8") as outfile:
            yaml.add_representer(QuotedString, quoted_scalar)
            yaml.dump(spec, outfile, default_flow_style=False)
