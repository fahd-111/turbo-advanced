# Architecture Decisions

Why the code looks the way it does. Each entry records a decision that a future
session might otherwise re-litigate or accidentally undo. Deviations from
`GROWTH_AGENT_SPEC.md` are marked **[deviation]**.

---

## 1. Repository layout stays `backend/` + `frontend/` **[deviation]**

*Spec says:* Turborepo with `apps/web` and `apps/api`.

The repository was already a pnpm-workspace monorepo with Django 5 + DRF +
simplejwt + drf-spectacular, and OpenAPI-generated TypeScript types in
`frontend/packages/types`. Every capability the spec's layout exists to provide
was already present. Renaming directories would have been churn with no
functional gain and a broken Docker/CI setup to repair.

**Revisit if** a second backend service appears and the flat layout stops
describing reality.

---

## 2. Two Composio auth configs, not one Meta auth config **[deviation]**

*Spec says:* "One Meta auth config."

Composio models Instagram and Facebook as **separate toolkits**, each with its
own auth config and its own tool namespace. One config cannot serve both.
`COMPOSIO_AUTH_CONFIG_IDS` in `api/settings.py` maps platform → auth config id,
both from environment variables.

This preserves the spec's actual requirement — that swapping Composio's managed
Meta app for our own reviewed app after App Review is a **config change, not a
code change**.

---

## 3. Models are built in the phase that uses them **[deviation]**

*Spec says:* Phase 1 includes "models + migrations", listing all twelve.

Phase 1 created only `Business`, `SocialConnection`, and `AuditLog` — the three
the connect and publish flows actually read and write. Creating `Post`,
`Engagement`, `InsightSnapshot` and friends up front would mean shipping tables
no code touches, designed against requirements not yet exercised.

The publishing flow taught us things (composite Facebook post ids, container
ids, quota shapes) that will make the Phase 3 `Post` model better than a
guess written on day one.

**Deferred:** `ContentStrategy`, `Post`, `MediaItem` → Phase 3;
`Engagement` → Phase 5; `InsightSnapshot`, `UsageRecord` → Phase 6.
`BrandProfile` → Phase 2.

---

## 4. No Celery or Redis yet **[deviation]**

Phase 1 has no background work: every operation is synchronous and
request-scoped. Celery, celery-beat, and Redis arrive in **Phase 4** with the
publisher worker, which is the first thing that genuinely needs a queue.

The spec's Docker Compose service list (web, api, worker, beat, postgres, redis)
is a Phase 6 deliverable and still stands.

---

## 5. The OAuth callback uses a signed token, not a primary key

The callback is unauthenticated by necessity — Composio redirects a browser to
it after consent, with no session. Identifying the connection by raw primary key
would let anyone enumerate ids and force Composio API calls on other tenants'
connections.

`django.core.signing` carries the connection id, salted and with a one-hour max
age. Roughly four lines, and it closes the hole properly. See
`connections.callback_url()` / `connection_from_token()`.

---

## 6. `PUBLIC_API_URL` doubles as the allowed host

`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are derived from `PUBLIC_API_URL`
rather than being separate variables. It is by definition the hostname the
outside world reaches us on, so a second variable could only ever drift out of
sync — and would do so exactly when someone starts a dev tunnel, producing a
confusing `DisallowedHost` at the least convenient moment.

---

## 7. `localhost` is a valid `PUBLIC_API_URL` until Phase 5

The OAuth callback is a **browser redirect**, not a server-to-server call.
Composio performs the token exchange itself, then redirects the developer's own
browser — which resolves `localhost` fine. Verified working.

A real tunnel is only required from **Phase 5**, when Composio's servers POST
webhooks to us. `cloudflared` is installed on this machine for that.

---

## 8. Tool slugs and toolkit versions are pinned, in one place

All Composio tool slugs live in `growth/services/tools.py`. Toolkit versions are
pinned in `api/settings.py`, overridable per toolkit by environment variable.

Composio requires an explicit version for manual tool execution and rejects
`"latest"`. Pinning is also correct on its own merits: tool **argument schemas
change between versions**, and `tools.py` is written against specific ones.

`python manage.py composio_tools <SLUG>` prints a tool's live input schema. Run
it after any Composio update; if an argument name changed, fix `tools.py` and
nothing else needs to move.

---

## 9. External failures degrade, they do not cascade

Three deliberate choices about failure behaviour:

- **Account-id lookup failures never fail the whole sync.** The connection is
  genuinely authorised; we just cannot publish through it yet, which
  `SocialConnection.is_usable` already reports. An early version let the
  exception escape *before* `save()`, silently discarding the freshly-fetched
  status and leaving connections stuck on `pending`.
- **An unreadable Instagram quota response fails open.** Failing closed would
  stall every queue on a response-shape change, while a genuine cap breach still
  surfaces as an ordinary publish failure.
- **Composio errors return 502, never 500.** Users see "reconnect your account",
  not a crash.

---

## 10. Kill switches are re-read from the database at the point of use

`publish_image_post()` calls `refresh_from_db()` before touching a live account,
rather than trusting the caller's copy of the `Business`. Per spec §4, kill
switches must hold at the worker level, and a Celery task in Phase 4 may hold an
instance that was loaded minutes before it runs.

There is a test for exactly this: flipping the flag via `.update()` while an
in-memory copy still says "running".

---

## 11. Tests assert against real response shapes, not mocks of our own design

`test_composio_client.py` feeds `execute_tool` **plain dicts** rather than mocks
with attributes. This is not stylistic. `ToolExecutionResponse` is a `dict`
subclass, so `response.successful` succeeds against a `MagicMock` and raises
`AttributeError` against the real SDK — a bug that unit tests happily hid until
mypy caught it.

Where a live schema has been confirmed, the exact argument dict is asserted
(see the Instagram and Facebook publish tests), so a future edit that "tidies"
`message` back to `caption` fails loudly instead of at runtime.
