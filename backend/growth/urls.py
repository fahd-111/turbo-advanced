from django.urls import include, path
from rest_framework import routers

from growth.api import BusinessViewSet, SocialConnectionViewSet, connection_callback

app_name = "growth"

router = routers.DefaultRouter()
router.register("businesses", BusinessViewSet, basename="business")
router.register("connections", SocialConnectionViewSet, basename="connection")

urlpatterns = [
    # Must precede the router: its detail route would match "callback" as a pk.
    path("connections/callback/", connection_callback, name="connection-callback"),
    path("", include(router.urls)),
]
