# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Turbo is a Django & Next.js monorepo boilerplate with JWT authentication, combining a REST API backend with a modern frontend using pnpm workspaces.

## Commands

### Development
```bash
# Start all services
docker compose up

# Backend commands (run inside container)
docker compose exec api uv run -- python manage.py migrate
docker compose exec api uv run -- python manage.py createsuperuser
docker compose exec api uv add <package>  # Add dependency

# Frontend commands (run inside container)
docker compose exec web pnpm --filter web dev
docker compose exec web pnpm --filter web build
docker compose exec web pnpm add <package> -w  # Global dependency
docker compose exec web pnpm --filter web add <package>  # App-specific
```

### Testing
```bash
# Run all backend tests
docker compose exec api uv run -- pytest .

# Run specific test file
docker compose exec api uv run -- pytest api/tests/test_api.py

# Run specific test
docker compose exec api uv run -- pytest api/tests/test_api.py -k "test_name"
```

### Code Quality
```bash
# Run pre-commit hooks manually
pre-commit run --all-files

# Type check the growth app
docker compose exec api uv run -- mypy
```

### API Types
```bash
# Regenerate TypeScript types from OpenAPI schema after backend changes
docker compose exec web pnpm openapi:generate
```

## Architecture

### Monorepo Structure
- `backend/` - Django REST API (uv package manager)
  - `backend/api/` - Core API app (User model, auth endpoints)
  - `backend/settings_config/` - System settings (Stripe, Resend, TinyMCE, Cloudinary)
  - `backend/blog/` - Blog & Newsletter app
  - `backend/growth/` - Growth Agent: tenants, social connections, publishing
- `frontend/` - pnpm workspace containing:
  - `apps/web/` - Main Next.js application
  - `packages/types/` - OpenAPI-generated TypeScript types
  - `packages/ui/` - Shared UI components

### Authentication Flow
1. Backend uses `djangorestframework-simplejwt` for JWT tokens at `/api/token/` and `/api/token/refresh/`
2. Frontend uses `next-auth` credentials provider storing tokens in session
3. Protected pages check authentication via `getServerSession(authOptions)` from `@/lib/auth`

### API Communication Pattern
- Backend exposes OpenAPI schema at `/api/schema/`
- `openapi-typescript-codegen` generates TypeScript client in `frontend/packages/types/api/`
- Server Actions in `frontend/apps/web/actions/` handle API calls using `getApiClient()` from `@/lib/api.ts`

### Key Backend Files
- `backend/api/models.py` - Custom User model
- `backend/api/api.py` - DRF ViewSets
- `backend/api/serializers.py` - API serializers
- `backend/api/tests/` - pytest test suite with factories and fixtures

### Key Frontend Files
- `frontend/apps/web/lib/auth.ts` - NextAuth configuration and JWT refresh logic
- `frontend/apps/web/lib/api.ts` - API client wrapper with authentication
- `frontend/apps/web/actions/` - Server Actions for form submissions

## Code Style

- **Python**: Ruff for linting and formatting (configured in `pyproject.toml`)
- **TypeScript/JavaScript**: Biome for linting and formatting (configured in `frontend/biome.json`)
- **Commits**: Conventional commits enforced via pre-commit hook

## URLs

- Frontend: http://localhost:3000
- API: http://localhost:8000 (redirects to /admin/)
- Health Check: http://localhost:8000/health/
- Swagger UI: http://localhost:8000/api/schema/swagger-ui/
- Admin: http://localhost:8000/admin/
- GlitchTip: http://localhost:8001 (error tracking, performance & uptime monitoring)

## Error & Uptime Monitoring (GlitchTip)

Self-hosted error tracking, performance monitoring, and uptime monitoring using GlitchTip with Sentry SDK compatibility.

### Features
- **Error Tracking**: Full stack traces with local variables (Sentry-compatible)
- **Performance Monitoring**: Transaction tracing and performance metrics
- **Uptime Monitoring**: HTTP/TCP ping, heartbeat, and alerts when services go down

### Setup
1. Start services: `docker compose up`
2. Access GlitchTip at http://localhost:8001
3. **Register** a new account (open registration enabled in dev)
4. Create an **Organization** (e.g., "Turbo")
5. Create a **Project** inside the organization (e.g., "Backend API")
6. Go to Project → **Settings** → **SDK Setup** and copy the DSN
7. The DSN will look like: `http://abc123@localhost:8001/1`
8. **Important**: Change `localhost:8001` to `glitchtip-web:8000` for Docker networking:
   ```
   # Browser URL:  http://abc123@localhost:8001/1
   # Docker URL:   http://abc123@glitchtip-web:8000/1
   ```
9. Add the Docker URL to `.env.backend`:
   ```
   SENTRY_DSN=http://abc123@glitchtip-web:8000/1
   ```
10. Restart the API: `docker compose restart api`

### Docker Networking Note
- **Inside Docker** (container-to-container): Use `glitchtip-web:8000` (service name)
- **Outside Docker** (browser): Use `localhost:8001` (port mapping)

### Uptime Monitoring Setup
1. Go to **Uptime Monitors** in the sidebar
2. Click **Create Monitor**
3. Add monitors for your services:
   - **API Health**: `http://api:8000/health/` (Ping, 60s interval)
   - **Frontend**: `http://web:3000/` (Ping, 60s interval)
   - **Database**: `db:5432` (TCP Port)

### Manual Error Reporting
```python
import sentry_sdk

# Capture exception
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)

# Capture message
sentry_sdk.capture_message("Something happened")

# Add context
with sentry_sdk.push_scope() as scope:
    scope.set_tag("custom_tag", "value")
    scope.set_extra("extra_data", {"key": "value"})
    sentry_sdk.capture_message("Tagged message")
```

## System Settings (settings_config app)

Database-stored configurations for third-party services, managed via Django admin.

### Available Configurations
- **Stripe** - Payment processing (publishable key, secret key, webhook secret)
- **Resend** - Email service (API key, from email/name, test email feature)
- **TinyMCE** - Rich text editor (API key, height, plugins, toolbar)
- **Cloudinary** - Media storage (cloud name, API key/secret, default folder)

### Retrieving Configurations
```python
from settings_config.services import (
    get_stripe_config,
    get_resend_config,
    get_tinymce_config,
    get_cloudinary_config,
    send_email,
    upload_to_cloudinary,
    delete_from_cloudinary,
)

# Stripe
stripe_config = get_stripe_config()
if stripe_config:
    stripe.api_key = stripe_config.secret_key

# Send email using Resend
success, message = send_email("user@example.com", "Subject", "<h1>HTML</h1>")

# TinyMCE config for templates
tinymce = get_tinymce_config()
if tinymce:
    config_dict = tinymce.get_config_dict()
    js_url = tinymce.get_js_url()

# Cloudinary upload
url = upload_to_cloudinary(image_file, folder="blog/images")
delete_from_cloudinary(old_url)
```

### Singleton Pattern
All configuration models use a singleton pattern - only one instance exists per model. Access via `Model.load()` for cached retrieval.

### Adding New Configuration Models
1. Create model extending `SingletonModel` in `settings_config/models.py`
2. Create admin class extending `SingletonModelAdmin` in `settings_config/admin.py`
3. Add sidebar navigation in `api/settings.py` UNFOLD config
4. Create helper function in `settings_config/services.py`

## Blog & Newsletter (blog app)

Content management system for blog posts and newsletter campaigns.

### Models
- **Post** - Blog posts with TinyMCE editor, Cloudinary images, SEO fields
- **Category** - Post categories with slug
- **Tag** - Post tags with slug
- **NewsletterSubscriber** - Email subscribers with confirmation workflow
- **Newsletter** - Newsletter campaigns with scheduling

### Features
- TinyMCE rich text editor (configured via System Settings)
- Cloudinary image uploads for featured images
- SEO meta fields (title, description)
- Post status workflow (draft → published → archived)
- Newsletter subscriber management with status tracking

## Growth Agent (growth app)

Multi-tenant autonomous social media marketing. See `GROWTH_AGENT_SPEC.md` for
the full product spec and phase plan. **Phase 1 (skeleton & connect flow) is
complete**; phases 2-6 are not started.

### Models (Phase 1)
- **Business** - the tenant. Everything is scoped by `business_id`. Owns the
  kill switches (`publishing_paused`, `replies_paused`), `review_buffer_hours`,
  `monthly_budget_usd`, and an IANA `timezone` (validated).
- **SocialConnection** - one Instagram Business/Creator account or Facebook Page
  per business per platform. Status: `pending | healthy | needs_reauth | disconnected`.
- **AuditLog** - append-only record of every autonomous action (`AuditLog.record()`).

Models for strategy, posts, engagement, insights and usage arrive in their own
phases rather than up front.

### Service layer (`growth/services/`)
- `composio_client.py` - the only place that talks to the Composio SDK. Timeout
  and HTTP retries are configured on the client; the wrapper adds the
  "tool ran but reported failure" case. **`ToolExecutionResponse` is a TypedDict —
  subscript it, never use attribute access.**
- `connections.py` - OAuth initiation, status sync, disconnect.
- `publishing.py` - Instagram two-step container→publish, Facebook photo post,
  IG quota check, kill-switch enforcement.
- `tools.py` - every Composio tool slug, in one place.

### Composio setup
Each business maps to Composio user id `business_{id}`. Instagram and Facebook
are separate toolkits, so each needs its own auth config id in `.env.backend`:

```
COMPOSIO_API_KEY=                    # needs WRITE on connected_accounts + triggers
COMPOSIO_INSTAGRAM_AUTH_CONFIG_ID=
COMPOSIO_FACEBOOK_AUTH_CONFIG_ID=
PUBLIC_API_URL=http://localhost:8000
```

`PUBLIC_API_URL` can stay `localhost` through Phase 4: the OAuth callback is a
browser redirect, so it only has to resolve in the developer's own browser. A
real tunnel (`cloudflared tunnel --url http://localhost:8000`) is needed from
Phase 5, when Composio's servers POST webhooks to us. It also feeds
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, so no separate host var exists.

**Editing `.env.backend` requires `docker compose up -d --force-recreate api`.**
`docker compose restart` reuses the baked-in environment and will not pick up
changes.

### Toolkit versions are pinned
Composio rejects manual tool execution without an explicit toolkit version
("latest" is not accepted). Versions are date stamps, set in `api/settings.py`
and overridable per toolkit via `COMPOSIO_<TOOLKIT>_TOOLKIT_VERSION`. Pin
deliberately: tool argument schemas change between versions, and
`growth/services/tools.py` is written against the pinned ones.

Swapping Composio's managed Meta app for our own reviewed app is a change of
these ids only, never a code change.

### Connect flow
1. `POST /api/businesses/{id}/connect/` with `{"platform": "instagram"}` →
   returns `redirect_url`; send the user there.
2. Composio redirects back to `/api/connections/callback/?token=…`. The token is
   a signed connection reference, because the callback is unauthenticated.
3. `POST /api/connections/{id}/check/` re-reads status from Composio and fills in
   the Instagram user id / Facebook Page id.

Consent links (`https://connect.composio.dev/link/lk_...`) are short lived —
re-POST to `connect/` to mint a fresh one rather than reusing an old link.

Use `connected_accounts.link()`, never `initiate()`: the latter is retired for
Composio-managed OAuth configs and returns a 400. Instagram's own account id is
read with `INSTAGRAM_GET_USER_INFO` using `ig_user_id="me"`, since we cannot
pass an id we do not yet know.

Instagram must be a Business/Creator account linked to a Facebook Page.

### Commands
```bash
# Publish one real post end-to-end (the Phase 1 smoke test)
docker compose exec api uv run -- python manage.py publish_test_post \
    --business 1 --platform instagram [--sync] [--dry-run]

# Confirm tool slugs and argument names against the live Composio project
docker compose exec api uv run -- python manage.py composio_tools --toolkit instagram
docker compose exec api uv run -- python manage.py composio_tools INSTAGRAM_POST_IG_USER_MEDIA
```
