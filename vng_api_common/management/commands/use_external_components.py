"""
Replace internal references to external for reusable components

Due to the limitations of drf_yasg we cannot handle this at the Python level
"""
from django.core.management import BaseCommand

import oyaml as yaml


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
            "common-spec", help="Path to the yaml file with reusable components"
        )

    def handle(self, **options):
        source = options["api-spec"]
        common_source = options["common-spec"]

        with open(common_source, "r", encoding="utf8") as f:
            common_spec = yaml.safe_load(f)
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

                    print("item=", item)
                    common_item_spec = common_components[scope][item]
                    if item_spec == common_item_spec:
                        # add ref to replace
                        ref = f"#/components/{scope}/{item}"
                        refs[ref] = f"{common_source}{ref}"

                        # remove item from internal components
                        del components[scope][item]

            # todo remove empty components

            # replace all refs
            replace_refs(spec, refs)

        with open(source, "w", encoding="utf8") as outfile:
            yaml.add_representer(QuotedString, quoted_scalar)
            yaml.dump(spec, outfile, default_flow_style=False)
