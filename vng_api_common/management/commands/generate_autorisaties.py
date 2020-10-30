import logging
import os

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import render_to_string

from ...scopes import SCOPE_REGISTRY


class Command(BaseCommand):
    """
    Generate a markdown file documenting the auth scopes of the component
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--output-file",
            dest="output_file",
            default=None,
            help="Name of the output file",
        )

    def handle(self, output_file, *args, **options):
        scopes = sorted(
            (scope for scope in SCOPE_REGISTRY if not scope.children),
            key=lambda s: s.label,
        )

        template = "vng_api_common/autorisaties.md"
        markdown = render_to_string(
            template,
            context={
                "scopes": scopes,
                "project_name": settings.PROJECT_NAME,
                "site_title": settings.SITE_TITLE,
            },
        )

        with open(output_file, "w") as f:
            f.write(markdown)
