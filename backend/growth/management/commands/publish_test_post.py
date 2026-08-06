"""End-to-end smoke test: publish one real post to a connected account.

    python manage.py publish_test_post --business 1 --platform instagram

This is the Phase 1 de-risking command. It exercises the whole path: kill
switch, connection health, Composio auth, the Instagram container/publish two
step flow, and the audit log.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from growth.models import Business, Platform, SocialConnection
from growth.services import connections as connection_service
from growth.services.composio_client import ComposioNotConfigured, ToolExecutionError
from growth.services.publishing import (
    PublishingPaused,
    QuotaExhausted,
    publish_image_post,
)

# Meta fetches this URL server side and rejects redirects or HTML responses, so
# it must be a host that serves the image bytes directly (picsum 302s, and fails).
DEFAULT_IMAGE = "https://placehold.co/1080x1080/jpg"
DEFAULT_CAPTION = "Hello from Growth Agent 👋 This is an automated test post."


class Command(BaseCommand):
    help = "Publish one hardcoded test post to a connected social account."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--business", type=int, required=True, help="Business id.")
        parser.add_argument(
            "--platform", choices=[p.value for p in Platform], required=True
        )
        parser.add_argument("--image-url", default=DEFAULT_IMAGE)
        parser.add_argument("--caption", default=DEFAULT_CAPTION)
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Refresh the connection from Composio before publishing.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run every check but stop before publishing.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            business = Business.objects.get(pk=options["business"])
        except Business.DoesNotExist as exc:
            raise CommandError(f"No business with id {options['business']}") from exc

        try:
            connection = business.connections.get(platform=options["platform"])
        except SocialConnection.DoesNotExist as exc:
            raise CommandError(
                f"{business.name} has no {options['platform']} connection. "
                f"Connect one via POST /api/businesses/{business.pk}/connect/"
            ) from exc

        try:
            if options["sync"]:
                connection = connection_service.sync_connection(connection)

            self.stdout.write(
                f"{business.name} · {connection.get_platform_display()} · "
                f"status={connection.status} account={connection.external_account_id or '-'}"
            )

            if options["dry_run"]:
                if not connection.is_usable:
                    raise CommandError(f"{connection} is not usable yet.")
                self.stdout.write(
                    self.style.WARNING("Dry run: stopping before publish.")
                )
                return

            result = publish_image_post(
                connection,
                caption=options["caption"],
                image_url=options["image_url"],
            )
        except (ComposioNotConfigured, PublishingPaused, QuotaExhausted) as exc:
            raise CommandError(str(exc)) from exc
        except ToolExecutionError as exc:
            raise CommandError(f"{exc}\nResponse data: {exc.data}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Published. External post id: {result.external_post_id}"
            )
        )
