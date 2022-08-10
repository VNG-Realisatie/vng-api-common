import logging
import os

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import render_to_string

from notifications_api_common.kanalen import KANAAL_REGISTRY


class Command(BaseCommand):
    """
    Generate a markdown file documenting the notification channels of the component
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
        kanalen = sorted(KANAAL_REGISTRY, key=lambda s: s.label)

        template = "vng_api_common/notificaties.md"
        markdown = render_to_string(
            template,
            context={
                "kanalen": kanalen,
                "project_name": settings.PROJECT_NAME,
                "site_title": settings.SITE_TITLE,
            },
        )

        with open(output_file, "w") as f:
            f.write(markdown)
