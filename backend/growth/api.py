from django.core.signing import BadSignature
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from growth.models import Business, SocialConnection
from growth.serializers import (
    BusinessSerializer,
    ConnectRequestSerializer,
    ConnectResponseSerializer,
    SocialConnectionSerializer,
)
from growth.services import connections as connection_service
from growth.services.composio_client import COMPOSIO_FAILURES, ComposioNotConfigured


class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    # Empty by design: only used for schema introspection, so losing
    # get_queryset() below would expose nothing rather than every tenant.
    queryset = Business.objects.none()

    def get_queryset(self):
        return (
            Business.objects.filter(owner=self.request.user)
            .prefetch_related("connections")
            .order_by("name")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "connect":
            return ConnectRequestSerializer
        return super().get_serializer_class()

    @extend_schema(
        request=ConnectRequestSerializer, responses={200: ConnectResponseSerializer}
    )
    @action(["post"], detail=True)
    def connect(self, request: Request, pk: str | None = None) -> Response:
        """Start the Composio OAuth flow; returns the URL to send the user to."""
        business = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            connection, redirect_url = connection_service.initiate_connection(
                business, serializer.validated_data["platform"]
            )
        except ComposioNotConfigured as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except COMPOSIO_FAILURES as exc:
            return Response(
                {"detail": f"Composio rejected the request: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "redirect_url": redirect_url,
                "connection": SocialConnectionSerializer(connection).data,
            }
        )


class SocialConnectionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SocialConnectionSerializer
    queryset = SocialConnection.objects.none()

    def get_queryset(self):
        return SocialConnection.objects.filter(
            business__owner=self.request.user
        ).select_related("business")

    def perform_destroy(self, instance: SocialConnection) -> None:
        connection_service.disconnect(instance)

    @extend_schema(request=None, responses={200: SocialConnectionSerializer})
    @action(["post"], detail=True, url_path="check")
    def check_health(self, request: Request, pk: str | None = None) -> Response:
        """Re-read the connection's status from Composio."""
        connection = self.get_object()
        try:
            connection = connection_service.sync_connection(connection)
        except ComposioNotConfigured as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except COMPOSIO_FAILURES as exc:
            return Response(
                {"detail": f"Composio rejected the request: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(self.get_serializer(connection).data)


def connection_callback(request):
    """Where Composio returns the user after the OAuth consent screen.

    Unauthenticated by necessity, so the connection is identified by a signed
    token and the response never echoes tenant data back.
    """
    token = request.GET.get("token", "")
    try:
        connection = connection_service.connection_from_token(token)
    except (BadSignature, SocialConnection.DoesNotExist):
        return JsonResponse({"detail": "Invalid or expired callback."}, status=400)

    try:
        connection = connection_service.sync_connection(connection)
    except ComposioNotConfigured as exc:
        return JsonResponse({"detail": str(exc)}, status=503)
    except COMPOSIO_FAILURES as exc:
        return JsonResponse(
            {"detail": f"Composio rejected the request: {exc}"}, status=502
        )

    return JsonResponse({"platform": connection.platform, "status": connection.status})
