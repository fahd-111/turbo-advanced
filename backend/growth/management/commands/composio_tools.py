"""Print the real input schema of Composio tools.

Used to confirm the slugs and argument names in growth/services/tools.py
against a live Composio project:

    python manage.py composio_tools INSTAGRAM_POST_IG_USER_MEDIA
    python manage.py composio_tools --toolkit instagram
"""

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from growth.services.composio_client import ComposioNotConfigured, get_client


class Command(BaseCommand):
    help = "Inspect Composio tool slugs and their input schemas."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("slugs", nargs="*", help="Tool slugs to describe.")
        parser.add_argument(
            "--toolkit",
            help="List every tool slug in a toolkit (e.g. instagram, facebook).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            client = get_client()
        except ComposioNotConfigured as exc:
            raise CommandError(str(exc)) from exc

        toolkit = options.get("toolkit")
        slugs = options.get("slugs") or []
        if not toolkit and not slugs:
            raise CommandError("Give one or more slugs, or --toolkit NAME.")

        if toolkit:
            # The SDK defaults to a page of 20 and silently truncates, which
            # hides exactly the tools you are usually looking for.
            tools = client.tools.get_raw_composio_tools(toolkits=[toolkit], limit=500)
            self.stdout.write(
                self.style.MIGRATE_HEADING(f"{toolkit}: {len(tools)} tools")
            )
            for tool in sorted(tools, key=lambda t: t.slug):
                marker = " (deprecated)" if tool.is_deprecated else ""
                self.stdout.write(f"  {tool.slug}{marker}")

        for slug in slugs:
            tool = client.tools.get_raw_composio_tool_by_slug(slug)
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{tool.slug}"))
            if tool.is_deprecated:
                self.stdout.write(self.style.WARNING("  DEPRECATED"))
            self.stdout.write(f"  {tool.description}")
            self.stdout.write("  input_parameters:")
            self.stdout.write(json.dumps(tool.input_parameters, indent=2))
