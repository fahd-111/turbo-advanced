from os import environ
from pathlib import Path
from urllib.parse import urlparse

import sentry_sdk
from django.core.management.utils import get_random_secret_key
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

######################################################################
# Sentry / BugSink
######################################################################
SENTRY_DSN = environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        send_default_pii=True,
    )

######################################################################
# Composio
######################################################################
COMPOSIO_API_KEY = environ.get("COMPOSIO_API_KEY", "")
COMPOSIO_WEBHOOK_SECRET = environ.get("COMPOSIO_WEBHOOK_SECRET", "")
COMPOSIO_TIMEOUT_SECONDS = int(environ.get("COMPOSIO_TIMEOUT_SECONDS", "30"))
COMPOSIO_MAX_RETRIES = int(environ.get("COMPOSIO_MAX_RETRIES", "2"))

# One auth config per toolkit. Swapping Composio's managed Meta app for our own
# reviewed Meta app is a change of these ids only, never a code change.
COMPOSIO_AUTH_CONFIG_IDS = {
    "instagram": environ.get("COMPOSIO_INSTAGRAM_AUTH_CONFIG_ID", ""),
    "facebook": environ.get("COMPOSIO_FACEBOOK_AUTH_CONFIG_ID", ""),
}

# Composio requires an explicit toolkit version for manual tool execution
# ("latest" is rejected). Pin them: tool argument schemas change between
# versions, and growth/services/tools.py is written against these.
COMPOSIO_TOOLKIT_VERSIONS = {
    "instagram": environ.get("COMPOSIO_INSTAGRAM_TOOLKIT_VERSION", "20260730_00"),
    "facebook": environ.get("COMPOSIO_FACEBOOK_TOOLKIT_VERSION", "20260721_00"),
}

# Where Composio sends the user back after the OAuth consent screen.
PUBLIC_API_URL = environ.get("PUBLIC_API_URL", "http://localhost:8000")

######################################################################
# General
######################################################################
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = environ.get("SECRET_KEY", get_random_secret_key())

DEBUG = environ.get("DEBUG", "") == "1"

# PUBLIC_API_URL is by definition the host the outside world reaches us on, so
# it doubles as the allowed host / trusted origin rather than needing its own
# env var that can drift out of sync when the dev tunnel URL changes.
_public_host = urlparse(PUBLIC_API_URL).hostname

ALLOWED_HOSTS = ["localhost", "api"]
if _public_host and _public_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_public_host)

CSRF_TRUSTED_ORIGINS = [PUBLIC_API_URL] if _public_host else []

WSGI_APPLICATION = "api.wsgi.application"

ROOT_URLCONF = "api.urls"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

######################################################################
# Apps
######################################################################
INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "api",
    "settings_config",
    "blog",
    "growth",
]

######################################################################
# Middleware
######################################################################
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

######################################################################
# Templates
######################################################################
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

######################################################################
# Database
######################################################################
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "USER": environ.get("DATABASE_USER", "postgres"),
        "PASSWORD": environ.get("DATABASE_PASSWORD", "change-password"),
        "NAME": environ.get("DATABASE_NAME", "db"),
        "HOST": environ.get("DATABASE_HOST", "db"),
        "PORT": "5432",
        "TEST": {
            "NAME": "test",
        },
    }
}

######################################################################
# Authentication
######################################################################
AUTH_USER_MODEL = "api.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

######################################################################
# Internationalization
######################################################################
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

######################################################################
# Staticfiles
######################################################################
STATIC_URL = "static/"

######################################################################
# Rest Framework
######################################################################
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

######################################################################
# Unfold
######################################################################
UNFOLD = {
    "SITE_HEADER": _("Turbo Admin"),
    "SITE_TITLE": _("Turbo Admin"),
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Navigation"),
                "separator": False,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:api_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "label",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Growth Agent"),
                "separator": True,
                "items": [
                    {
                        "title": _("Businesses"),
                        "icon": "storefront",
                        "link": reverse_lazy("admin:growth_business_changelist"),
                    },
                    {
                        "title": _("Social Connections"),
                        "icon": "link",
                        "link": reverse_lazy(
                            "admin:growth_socialconnection_changelist"
                        ),
                    },
                    {
                        "title": _("Audit Log"),
                        "icon": "history",
                        "link": reverse_lazy("admin:growth_auditlog_changelist"),
                    },
                ],
            },
            {
                "title": _("Blog & Newsletter"),
                "separator": True,
                "items": [
                    {
                        "title": _("Posts"),
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                    },
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": _("Tags"),
                        "icon": "label",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                    },
                    {
                        "title": _("Subscribers"),
                        "icon": "group",
                        "link": reverse_lazy(
                            "admin:blog_newslettersubscriber_changelist"
                        ),
                    },
                    {
                        "title": _("Newsletters"),
                        "icon": "mail",
                        "link": reverse_lazy("admin:blog_newsletter_changelist"),
                    },
                ],
            },
            {
                "title": _("System Settings"),
                "separator": True,
                "items": [
                    {
                        "title": _("Stripe"),
                        "icon": "credit_card",
                        "link": reverse_lazy(
                            "admin:settings_config_stripeconfiguration_changelist"
                        ),
                    },
                    {
                        "title": _("Resend (Email)"),
                        "icon": "mail",
                        "link": reverse_lazy(
                            "admin:settings_config_resendconfiguration_changelist"
                        ),
                    },
                    {
                        "title": _("TinyMCE (Editor)"),
                        "icon": "edit_note",
                        "link": reverse_lazy(
                            "admin:settings_config_tinymceconfiguration_changelist"
                        ),
                    },
                    {
                        "title": _("Cloudinary (Media)"),
                        "icon": "cloud_upload",
                        "link": reverse_lazy(
                            "admin:settings_config_cloudinaryconfiguration_changelist"
                        ),
                    },
                ],
            },
        ],
    },
}
