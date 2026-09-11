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
