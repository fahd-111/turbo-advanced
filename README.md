# Turbo - Django & Next.js boilerplate <!-- omit from toc -->

Turbo is a simple bootstrap template for Django and Next.js, combining both frameworks under one monorepository, including best practices.

## Features <!-- omit from toc -->

- **Microsites**: supports several front ends connected to API backend
- **API typesafety**: exported types from backend stored in shared front end package
- **Server actions**: handling form submissions in server part of Next project
- **Tailwind CSS**: built-in support for all front end packages and sites
- **Docker Compose**: start both front end and backend by running `docker compose up`
- **Auth system**: Django session authentication shared by the API and web app
- **Profile management**: update profile information from the front end
- **Registrations**: new accounts can sign in immediately after signup
- **Admin theme**: Unfold admin theme with user & group management
- **Custom user model**: extended default Django user model
- **Visual Studio Code**: project already constains VS Code containers and tasks

## Table of contents <!-- omit from toc -->

- [Quickstart](#quickstart)
  - [Environment files configuration](#environment-files-configuration)
  - [Running docker compose](#running-docker-compose)
- [Included dependencies](#included-dependencies)
  - [Backend dependencies](#backend-dependencies)
  - [Front end dependencies](#front-end-dependencies)
- [Front end project structure](#front-end-project-structure)
  - [Adding microsite to docker-compose.yaml](#adding-microsite-to-docker-composeyaml)
- [Authentication](#authentication)
  - [Configuring env variables](#configuring-env-variables)
  - [User accounts on the backend](#user-accounts-on-the-backend)
  - [Authenticated paths on frontend](#authenticated-paths-on-frontend)
- [API calls to backend](#api-calls-to-backend)
  - [API Client](#api-client)
  - [Updating OpenAPI schema](#updating-openapi-schema)
  - [Swagger](#swagger)
  - [Client side requests](#client-side-requests)
- [Test suite](#test-suite)
- [Developing in VS Code](#developing-in-vs-code)

## Quickstart

To start using Turbo, it is needed to clone the repository to your local machine and then run `docker compose`, which will take care about the installation process. The only prerequisite for starting Turbo template is to have `docker compose` installed and preconfiguring files with environment variables.

```bash
git clone https://github.com/unfoldadmin/turbo.git
cd turbo
```

### Environment files configuration

Before you can run `docker compose up`, you have to set up two files with environment variables. Both files are loaded via `docker compose` and variables are available within docker containers.

```bash
cp .env.backend.template .env.backend # set SECRET_KEY and DEBUG=1 for debug mode on
cp .env.frontend.template .env.frontend
```

For more advanced environment variables configuration for the front end, it is recommended to read official [Next.js documentation](https://nextjs.org/docs/pages/building-your-application/configuring/environment-variables) about environment variables where it is possible to configure specific variables for each microsite.

On the backend it is possible to use third party libraries for loading environment variables. In case that loading variables through `os.environ` is not fulfilling the requriements, we recommend using [django-environ](https://github.com/joke2k/django-environ) application.

### Running docker compose

```bash
docker compose up
```

After successful installation, it will be possible to access both front end (http://localhost:3000) and backend (http://localhost:8000) part of the system from the browsers.

**NOTE**: Don't forget to change database credentials in docker-compose.yaml and in .env.backend by configuring `DATABASE_PASSWORD`.

## Included dependencies

### Local commit checks and CI

Install Docker and start its daemon, then enable both Git hooks once per checkout:

```bash
uv tool install pre-commit
pre-commit install
```

Every commit runs the existing file checks plus production API/web builds,
container readiness, Django migration checks, backend tests, TypeScript checks,
Ruff/Biome lint and formatting checks, and Python/JavaScript dependency audits.
Commit messages must follow Conventional Commits, for example `fix: correct health check`.
Full checks take several minutes and require network access for security advisories.
Frontend checks include a Node test for registration/password validation,
the production build, TypeScript, lint/format checks and HTTP readiness.

Run all checks manually with `pre-commit run --all-files`, or just the Docker
pipeline with `bash scripts/check.sh`. Checks use disposable databases without
host ports or deployment secrets and clean their containers/volumes on exit.

The runner prints a short PASS/FAIL summary and up to six diagnostic lines per
check. Full output is saved in the temporary log directory printed at the end;
`index.txt` maps check names to log files.
Python advisories and high/critical JavaScript advisories block commits.
Outdated Python/frontend packages and failed version lookups also block commits.
The approved exceptions are Redis Python client 6.4.0 (Kombu requires `<6.5`)
and frontend releases younger than 24 hours. The version report requires the
newest eligible release; security audits still check every installed package.
pnpm 12.4.1 and the 24-hour release policy are shared by local and Docker builds.
Code/file counts report tracked source lines and files by extension, plus TSX
files in component directories; generated clients and declarations are excluded.
Version reports and counts appear in the GitHub job summary, with full logs
available as per-job `check-logs-*` artifacts. All required checks must pass.
GitHub Actions runs on pull requests and pushes to `main`. After file checks,
separate jobs run API/web builds, health checks, migrations, tests, lint,
formatting, types, security audits, outdated-package checks, and code metrics.
The final `ci-success` job requires every job to succeed; configure it as the
required branch-protection check to enforce this before merging.
Run an individual group locally with, for example, `bash scripts/check.sh security`.

### Testing the production stack locally

Create `.env` from `.env.example.production` and replace the placeholder secrets.
For local testing, use `http://localhost:4000` for `NEXT_PUBLIC_BACKEND_URL`,
`http://localhost:8001` for `GLITCHTIP_DOMAIN`, `consolemail://` for
`GLITCHTIP_EMAIL_URL`, and leave `SENTRY_DSN` empty until a GlitchTip project exists.
Stop the development stack first because both frontends use port 3000.

```bash
docker compose -p turbo-production -f docker-compose.prod.yaml up -d --build --wait --wait-timeout 180
docker compose -p turbo-production -f docker-compose.prod.yaml ps
docker compose -p turbo-production -f docker-compose.prod.yaml logs --tail 50
```

The nine services must report `healthy`. The API runs checks and migrations before
serving requests; GlitchTip runs its migrations before web and worker startup.
API readiness checks PostgreSQL and Redis. Celery workers answer targeted pings;
Celery beat and GlitchTip workers must keep their heartbeat files fresh.
Static-file collection must succeed during the API image build.

Local URLs: frontend `http://localhost:3000`, API `http://localhost:4000/health/`,
and GlitchTip `http://localhost:8001`. Production authentication uses secure cookies;
test authenticated flows behind HTTPS. Set the real domains in `.env` before deployment.

To stop this stack while keeping its database volumes:

```bash
docker compose -p turbo-production -f docker-compose.prod.yaml down
```

The general rule when it comes to dependencies is to have minimum of third party applications or plugins to avoid future problems updating the project and keep the maintenance of applications is minimal.

### Backend dependencies

For dependency management in Django application we are using `uv`. When starting the project through the `docker compose` command, it is checked for new dependencies as well. In the case they are not installed, docker will install them before running development server.

- **[djangorestframework](https://github.com/encode/django-rest-framework)** - REST API support
- **[drf-spectacular](https://github.com/tfranzel/drf-spectacular)** - OpenAPI schema generator
- **[django-unfold](https://github.com/unfoldadmin/django-unfold)** - Admin theme for Django admin panel

Below, you can find a command to install new dependency into backend project.

```bash
docker compose exec api uv add djangorestframework
```

### Front end dependencies

For the frontend project, it is bit more complicated to maintain front end dependencies than in backend part. Dependencies, can be split into two parts. First part are general dependencies available for all projects under packages and apps folders. The second part are dependencies, which are project specific.

- **[react-hook-form](https://github.com/react-hook-form/react-hook-form)** - Handling of React forms
- **[tailwind-merge](https://github.com/dcastil/tailwind-merge)** - Tailwind CSS class names helper
- **[zod](https://github.com/colinhacks/zod)** - Schema validation

To install a global dependency for all packages and apps, use `-w` parameter. In case of development package, add `-D` argument to install it into development dependencies.

```bash
docker compose exec web pnpm add react-hook-form -w
```

To install a dependency for specific app or package, use `--filter` to specify particular package.

```bash
docker compose exec web pnpm --filter web add react-hook-form
```

## Front end project structure

Project structure on the front end, it is quite different from the directory hierarchy in the backend. Turbo counts with an option that front end have multiple front ends available on various domains or ports.

```text
frontend
| - apps       // available sites
|   - web      // available next.js project
| - packages   // shared packages between sites
|   - types    // exported types from backend - api
|   - ui       // general ui components
```

The general rule here is, if you want to have some shared code, create new package under packages/ folder. After adding new package and making it available for your website, it is needed to install the new package into website project by running a command below.

```bash
docker compose exec web pnpm --filter web add @frontend/ui
```

### Adding microsite to docker-compose.yaml

If you want to have new website facing customers, create new project under apps/ directory. Keep in mind that `docker-compose.yaml` file must be adjusted to start a new project with appropriate new port.

```yaml
new_microsite:
  command: bash -c "pnpm install -r && pnpm --filter new_microsite dev"
  build:
    context: frontend # Dockerfile can be same
  volumes:
    - ./frontend:/app
  expose:
    - "3001" # different port
  ports:
    - "3001:3001" # different port
  env_file:
    - .env.frontend
  depends_on:
    - api
```

## Authentication

Django is the only authentication authority. Login uses Django's database sessions;
the browser holds the Django `sessionid` HttpOnly cookie, with no separate web JWT.

- `GET /api/auth/csrf` on the web obtains Django's CSRF token.
- `POST /api/auth/login` and `/api/auth/logout` forward to Django through the web's same-origin proxy.
- Server-rendered pages and server actions forward the Django session and CSRF cookies to the API.
- Logout invalidates the server session. Password changes require signing in again; old sessions become invalid.
- Registration creates active accounts that can sign in immediately.

### Configuring env variables

Set `API_URL` on the web to the internal Django URL (`http://api:8000` locally,
`http://api:4000` in staging/production). Set a stable Django `SECRET_KEY` and set
`CSRF_TRUSTED_ORIGINS` on the backend to the web origin, including the scheme
(e.g. `https://yourdomain.com`; comma-separated for multiple origins).
The development default is `http://localhost:3000`. Django sets secure cookies
when `DEBUG=0`, so staging and production require HTTPS.

Existing NextAuth/JWT logins do not carry over; users must sign in again after deployment.
Both web and API must be deployed together. No database schema change is required.

### User accounts on the backend

There are two ways how to create new user account in the backend. First option is to run managed command responsible for creating superuser. It is more or less required, if you want to have an access to the Django admin. After running the command below, it will be possible to log in on the front end part of the application.

```bash
docker compose exec api uv run -- python manage.py createsuperuser
```

The second option is to register through the frontend. New accounts are active by default and can sign in immediately. Administrators can still deactivate accounts through Django admin to prevent login.

### Authenticated paths on frontend

Protected pages use `getCurrentUser()` from `frontend/apps/web/lib/auth.ts`, which
asks Django's `/api/users/me/` endpoint to validate the session. The account layout
redirects anonymous users to `/login`; account actions also check authentication.
Django enforces authorization and CSRF protection on API mutations.

```tsx
import { getCurrentUser } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function PrivatePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return <p>Hello, {user.username}</p>;
}
```

## API calls to backend

Currently Turbo implements Next.js server actions in folder `frontend/apps/web/actions/` responsible for communication with the backend. When the server action is hit from the client, it fetches required data from Django API backend.

### API Client

The query between server action and Django backend is handled by using an API client generated by `openapi-typescript-codegen` package. In Turbo, there is a function `getApiClient` available in `frontend/apps/web/lib/api.ts` which already implements default options and Django session cookies.

### Updating OpenAPI schema

After changes on the backend, for example adding new fields into serializers, it is required to update typescript schema on the frontend. The schema can be updated by running command below. In VS Code, there is prepared task which will update definition.

```bash
docker compose exec web pnpm openapi:generate
```

### Swagger

By default, Turbo includes Swagger for API schema which is available here `http://localhost:8000/api/schema/swagger-ui/`. Swagger can be disabled by editing `urls.py` and removing `SpectacularSwaggerView`.

### Client side requests

At the moment, Turbo does not contain any examples of client side requests towards the backend. All the requests are handled by server actions. For client side requests, it is recommended to use [react-query](https://github.com/TanStack/query).

## Test suite

Project contains test suite for backend part. For testing it was used library called [pytest](https://docs.pytest.org/en/latest/) along with some additinal libraries extending functionality of pytest:

- [pytest-django](https://pytest-django.readthedocs.io/en/latest/) - for testing django applications
- [pytest-factoryboy](https://pytest-factoryboy.readthedocs.io/en/latest/) - for creating test data

All these libraries mentioned above are already preconfigured in `backend/api/tests` directory.

- `conftest.py` - for configuring pytest
- `factories.py` - for generating reusable test objects using factory_boy, which creates model instances with default values that can be customized as needed
- `fixtures.py` - for creating pytest fixtures that provide test data or resources that can be shared and reused across multiple tests

To run tests, use the command below which will collect all the tests available in backend/api/tests folder:

```bash
docker compose exec api uv run -- pytest .
```

Tu run tests available only in one specific file run:

```bash
docker compose exec api uv run -- pytest api/tests/test_api.py
```

To run one specific test, use the command below:

```bash
docker compose exec api uv run -- pytest api/tests/test_api.py -k "test_api_users_me_authorized"
```

## Developing in VS Code

The project contains configuration files for devcontainers so it is possible to directly work inside the container within VS Code. When the project opens in the VS Code the popup will appear to reopen the project in container. An action **Dev Containers: Reopen in Container** is available as well. Click on the reopen button and select the container which you want to work on. When you want to switch from the frontend to the backend project run **Dev Containers: Switch container** action. In case you are done and you want to work in the parent folder run **Dev Containers: Reopen Folder Locally** action
