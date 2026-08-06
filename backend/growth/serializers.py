from rest_framework import serializers

from growth.models import Business, Platform, SocialConnection


class SocialConnectionSerializer(serializers.ModelSerializer):
    is_usable = serializers.BooleanField(read_only=True)

    class Meta:
        model = SocialConnection
        fields = [
            "id",
            "platform",
            "status",
            "external_account_id",
            "external_account_name",
            "is_usable",
            "last_checked_at",
            "last_error",
        ]
        read_only_fields = fields


class BusinessSerializer(serializers.ModelSerializer):
    connections = SocialConnectionSerializer(many=True, read_only=True)

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "description",
            "industry",
            "website_url",
            "target_audience",
            "location",
            "timezone",
            "publishing_paused",
            "replies_paused",
            "review_buffer_hours",
            "monthly_budget_usd",
            "connections",
            "created_at",
        ]
        read_only_fields = ["id", "connections", "created_at"]


class ConnectRequestSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=Platform.choices)


class ConnectResponseSerializer(serializers.Serializer):
    redirect_url = serializers.URLField(read_only=True)
    connection = SocialConnectionSerializer(read_only=True)
