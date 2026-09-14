from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from .api import UserViewSet
from .auth_views import get_csrf_token, login_user, logout_user
from .health import health_check


router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="api-users")

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("health/", health_check, name="health_check"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/", include(router.urls)),
    path("api/auth/csrf/", get_csrf_token, name="auth-csrf"),
    path("api/auth/login/", login_user, name="auth-login"),
    path("api/auth/logout/", logout_user, name="auth-logout"),
    path("admin/", admin.site.urls),
]
