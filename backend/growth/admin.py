from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display

from growth.models import AuditLog, Business, ConnectionStatus, SocialConnection

CONNECTION_SUMMARY_FIELDS = (
    "platform",
    "status",
    "external_account_id",
    "last_checked_at",
)


class SocialConnectionInline(admin.TabularInline):
    model = SocialConnection
    extra = 0
    fields = CONNECTION_SUMMARY_FIELDS
    readonly_fields = CONNECTION_SUMMARY_FIELDS
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Business)
class BusinessAdmin(ModelAdmin):
    list_display = ["name", "industry", "timezone", "display_pauses", "created_at"]
    list_filter = ["industry", "publishing_paused", "replies_paused"]
    search_fields = ["name", "description", "website_url"]
    autocomplete_fields = ["owner"]
    inlines = [SocialConnectionInline]

    fieldsets = (
        (None, {"fields": ("owner", "name", "description", "industry")}),
        (
            _("Audience & reach"),
            {"fields": ("website_url", "target_audience", "location", "timezone")},
        ),
        (
            _("Agent controls"),
            {
                "fields": (
                    "publishing_paused",
                    "replies_paused",
                    "review_buffer_hours",
                    "monthly_budget_usd",
                    "settings",
                )
            },
        ),
    )

    @display(description=_("Agent"), label=True)
    def display_pauses(self, instance):
        paused = [
            label
            for flag, label in (
                (instance.publishing_paused, "publishing paused"),
                (instance.replies_paused, "replies paused"),
            )
            if flag
        ]
        return ", ".join(paused) or "running"


@admin.register(SocialConnection)
class SocialConnectionAdmin(ModelAdmin):
    list_display = [
        "business",
        "platform",
        "display_status",
        "external_account_name",
        "last_checked_at",
    ]
    list_filter = ["platform", "status"]
    search_fields = ["business__name", "external_account_id", "external_account_name"]
    readonly_fields = ["created_at", "modified_at", "last_checked_at", "last_error"]

    @display(
        description=_("Status"),
        label={
            ConnectionStatus.HEALTHY: "success",
            ConnectionStatus.PENDING: "info",
            ConnectionStatus.NEEDS_REAUTH: "warning",
            ConnectionStatus.DISCONNECTED: "danger",
        },
    )
    def display_status(self, instance):
        return instance.status


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ["created_at", "business", "actor", "action"]
    list_filter = ["actor", "action"]
    search_fields = ["business__name", "action"]
    readonly_fields = ["business", "actor", "action", "payload", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
