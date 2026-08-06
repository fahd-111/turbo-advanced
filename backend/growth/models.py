from decimal import Decimal
from zoneinfo import available_timezones

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


def validate_timezone(value: str) -> None:
    if value not in available_timezones():
        raise ValidationError(
            _("%(value)s is not a valid IANA timezone."), params={"value": value}
        )


class Platform(models.TextChoices):
    INSTAGRAM = "instagram", _("Instagram")
    FACEBOOK = "facebook", _("Facebook")


class Business(models.Model):
    """A tenant. Every other row in this app is scoped to exactly one Business."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="businesses",
        verbose_name=_("owner"),
    )
    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    industry = models.CharField(_("industry"), max_length=120, blank=True)
    website_url = models.URLField(_("website URL"), blank=True)
    target_audience = models.TextField(_("target audience"), blank=True)
    location = models.CharField(_("location"), max_length=200, blank=True)
    timezone = models.CharField(
        _("timezone"),
        max_length=64,
        default="UTC",
        validators=[validate_timezone],
        help_text=_("IANA timezone; all scheduling is rendered in this zone."),
    )
    settings = models.JSONField(_("settings"), default=dict, blank=True)

    # Kill switches. Workers re-read these immediately before publishing/replying.
    publishing_paused = models.BooleanField(_("publishing paused"), default=False)
    replies_paused = models.BooleanField(_("auto-replies paused"), default=False)

    review_buffer_hours = models.PositiveIntegerField(
        _("review buffer (hours)"),
        default=0,
        help_text=_("Hours a generated post waits in the calendar before publishing."),
    )
    monthly_budget_usd = models.DecimalField(
        _("monthly budget (USD)"),
        max_digits=8,
        decimal_places=2,
        default=Decimal("50.00"),
        help_text=_("Hard cap on LLM/image spend per month."),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    class Meta:
        verbose_name = _("business")
        verbose_name_plural = _("businesses")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def composio_user_id(self) -> str:
        """Stable Composio entity id for this tenant."""
        return f"business_{self.pk}"


class ConnectionStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    HEALTHY = "healthy", _("Healthy")
    NEEDS_REAUTH = "needs_reauth", _("Needs reauth")
    DISCONNECTED = "disconnected", _("Disconnected")


class SocialConnection(models.Model):
    """One connected Instagram Business/Creator account or Facebook Page."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="connections",
        verbose_name=_("business"),
    )
    platform = models.CharField(_("platform"), max_length=20, choices=Platform.choices)
    composio_connected_account_id = models.CharField(
        _("Composio connected account id"), max_length=128, blank=True
    )
    external_account_id = models.CharField(
        _("external account id"),
        max_length=128,
        blank=True,
        help_text=_("Instagram user id or Facebook Page id."),
    )
    external_account_name = models.CharField(
        _("external account name"), max_length=200, blank=True
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.PENDING,
    )
    last_checked_at = models.DateTimeField(_("last checked at"), null=True, blank=True)
    last_error = models.TextField(_("last error"), blank=True)

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    class Meta:
        verbose_name = _("social connection")
        verbose_name_plural = _("social connections")
        constraints = [
            models.UniqueConstraint(
                fields=["business", "platform"], name="unique_business_platform"
            )
        ]

    def __str__(self) -> str:
        return f"{self.business.name} · {self.get_platform_display()}"

    @property
    def is_usable(self) -> bool:
        return (
            self.status == ConnectionStatus.HEALTHY
            and bool(self.composio_connected_account_id)
            and bool(self.external_account_id)
        )


class AuditLog(models.Model):
    """Append-only record of every autonomous action the agent takes."""

    class Actor(models.TextChoices):
        AGENT = "agent", _("Agent")
        USER = "user", _("User")
        SYSTEM = "system", _("System")

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        verbose_name=_("business"),
    )
    actor = models.CharField(_("actor"), max_length=20, choices=Actor.choices)
    action = models.CharField(_("action"), max_length=100)
    payload = models.JSONField(_("payload"), default=dict, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("audit log entry")
        verbose_name_plural = _("audit log")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["business", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.actor}:{self.action}"

    @classmethod
    def record(
        cls,
        business: Business,
        action: str,
        actor: str = Actor.AGENT,
        **payload: object,
    ) -> "AuditLog":
        return cls.objects.create(
            business=business, actor=actor, action=action, payload=payload
        )
