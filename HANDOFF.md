# Growth Agent — Handoff

**Last updated:** 2026-08-06 · **Phase 1 complete and verified against live accounts.**

Read this first when picking the project up in a new session. It covers where
things stand, how to prove they still work, and what to do next.

| Document | What it is for |
|---|---|
| `HANDOFF.md` (this file) | Current state, how to resume, next steps |
| `GROWTH_AGENT_SPEC.md` | The product spec and the 6-phase build plan |
| `DECISIONS.md` | Architecture decisions and deliberate deviations from the spec |
| `CLAUDE.md` | Day-to-day commands, Composio setup, operational gotchas |

---

## 1. Status

| Phase | State |
|---|---|
| **1 — Skeleton & connect flow** | **Done.** Verified end to end with real posts on real accounts. |
| 2 — Onboarding & brand profile | Not started. Next up. |
| 3 — Strategy & content engine | Not started |
| 4 — Scheduler & calendar | Not started |
| 5 — Engagement agent | Not started |
| 6 — Analytics, budgets, deploy | Not started |

Phase 1 delivered: the `growth` Django app (tenant + connection models), the
Composio service layer, Business CRUD and connect/callback/health endpoints,
two management commands, and 66 passing tests.

**Proof it worked** — both posts were published by `publish_test_post` and then
confirmed by reading them back from the platform APIs:

- Instagram: <https://www.instagram.com/p/DbsjMofIPaG/>
- Facebook: <https://www.facebook.com/122105256717419862/posts/122105256237419862>

### ⚠️ The work is not committed

Everything below lives in the working tree only. The last commit is `94328a6`,
which predates all Phase 1 work. **Commit before doing anything risky.**

```
new:       backend/growth/           (the entire app)
new:       GROWTH_AGENT_SPEC.md, HANDOFF.md, DECISIONS.md
modified:  backend/api/settings.py, backend/api/urls.py
modified:  backend/pyproject.toml, backend/uv.lock
modified:  CLAUDE.md, .env.backend.template, frontend/pnpm-workspace.yaml
modified:  frontend/packages/types/api/   (33 regenerated files)
```

---

## 2. Getting running

```bash
docker compose up -d
docker compose exec api uv run -- pytest .        # expect 66 passed
```

`.env.backend` is gitignored and already holds working Composio credentials on
this machine. A fresh machine needs it created from `.env.backend.template`;
see the Composio section of `CLAUDE.md` for where each value comes from.

**Editing `.env.backend` requires `docker compose up -d --force-recreate api`.**
`docker compose restart` reuses the baked-in environment and silently ignores
your changes. This costs people half an hour if they do not know it.

---

## 3. What exists

```
backend/growth/
  models.py                    Business, SocialConnection, AuditLog
  api.py                       BusinessViewSet, SocialConnectionViewSet, callback
  serializers.py  urls.py  admin.py
  services/
    composio_client.py         the ONLY module that talks to the Composio SDK
    connections.py             OAuth initiate, status sync, disconnect
    publishing.py              IG container→publish, FB photo post, quota, kill switch
    tools.py                   every Composio tool slug, in one place
  management/commands/
    publish_test_post.py       the Phase 1 end-to-end smoke test
    composio_tools.py          prints live tool slugs and input schemas
  tests/                       66 tests
```

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET/POST/PATCH/DELETE` | `/api/businesses/` | Business CRUD, scoped to the owner |
| `POST` | `/api/businesses/{id}/connect/` | Start OAuth; returns a consent URL |
| `GET` | `/api/connections/` | List connections, scoped to the owner |
| `POST` | `/api/connections/{id}/check/` | Re-read status from Composio |
| `DELETE` | `/api/connections/{id}/` | Revoke and disconnect |
| `GET` | `/api/connections/callback/?token=` | Composio's post-OAuth redirect target |

---

## 4. Live test fixtures on this machine

These exist in the local Postgres volume, not in git. Recreate them if the
`data/` volume is wiped.

| Thing | Value |
|---|---|
| Dev user | `smoke@example.com` / `SmokeTest!2345` — local throwaway, not a secret |
| Business | id `1`, "Smoke Coffee", timezone `Europe/Berlin` |
| Instagram | `@acme._.coffee`, ig user id `27697800669843148`, healthy |
| Facebook | Page "Acme Coffee", page id `1246363021896476`, healthy |

Recreate the dev user:

```bash
docker compose exec api uv run -- python manage.py shell -c "
from django.contrib.auth import get_user_model
get_user_model().objects.create_user(
    username='smoke@example.com', password='SmokeTest!2345', is_active=True)"
```

---

## 5. Proving it still works

```bash
# 1. Unit tests, types, lint
docker compose exec api uv run -- pytest .
docker compose exec api uv run -- mypy
cd backend && uvx ruff@0.14.2 check --no-fix growth api

# 2. Composio credentials are live
docker compose exec api uv run -- python manage.py composio_tools --toolkit instagram
#    expect "instagram: 36 tools"

# 3. Connections still authorised
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"smoke@example.com","password":"SmokeTest!2345"}' \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['access'])")
curl -s -X POST http://localhost:8000/api/connections/1/check/ \
  -H "Authorization: Bearer $TOKEN"
#    expect "status":"healthy","is_usable":true

# 4. Dry run the publisher without posting anything
docker compose exec api uv run -- python manage.py publish_test_post \
    --business 1 --platform instagram --dry-run
```

Only step 4 without `--dry-run` posts publicly. Remember the test accounts are
real: every run leaves a real post behind.

---

## 6. Traps worth knowing

Each of these cost real debugging time and none are guessable from the docs.

1. **`ToolExecutionResponse` is a TypedDict, not an object.** Subscript it.
   Attribute access passes against a `MagicMock` and fails against the real SDK.
2. **Use `connected_accounts.link()`, never `initiate()`.** The latter is retired
   for Composio-managed OAuth configs and returns a 400.
3. **Toolkit versions must be pinned.** Composio rejects `"latest"` for manual
   tool execution. Versions are date stamps in `api/settings.py`.
4. **The SDK raises from two unrelated exception hierarchies** — transport errors
   from `composio_client`, semantic ones from `composio.exceptions`. Catch
   `COMPOSIO_FAILURES`, which covers both, or errors surface as 500s.
5. **Instagram's own account id needs `ig_user_id="me"`** via
   `INSTAGRAM_GET_USER_INFO`. Every other tool wants the id you are looking for.
6. **Facebook's caption parameter is `message`.** `caption` is undeclared in the
   schema. Prefer the composite `post_id` (`PageID_PostID`) over the photo `id`.
7. **Meta fetches image URLs server-side and rejects redirects.** `picsum.photos`
   302s and fails. Test images must serve bytes directly.
8. **Consent links expire within minutes.** Re-POST to `connect/` for a fresh one.

### Known broken upstream

`INSTAGRAM_GET_IG_MEDIA` fails at the pinned toolkit version — it requests a
`total_views_count` field Instagram does not support on the Media node. This is
Composio's bug. It matters in **Phase 6** for per-post insights;
`INSTAGRAM_GET_IG_USER_MEDIA` works as an alternative.

---

## 7. Next: Phase 2

Onboarding wizard, website scraper, LLM-built brand profile, asset uploads,
guardrails input. See §5 of `GROWTH_AGENT_SPEC.md`.

Before starting, add to `.env.backend`:

```
OPENROUTER_API_KEY=
OPENROUTER_MODEL_FAST=       # classification and replies
OPENROUTER_MODEL_STRONG=     # strategy and captions
OPENROUTER_MODEL_IMAGE=      # visuals
```

Phase 2 introduces the first LLM calls, so it also introduces:

- `growth/prompts/` — versioned prompt template functions. The spec is explicit
  that prompt strings never get inlined into business logic.
- A `BrandProfile` model (1:1 with Business) with the JSON fields listed in
  spec §1.2, plus the per-business banned-topics guardrail list that must be
  injected into every generation and reply prompt from here on.

Models deliberately deferred until the phase that uses them: `ContentStrategy`,
`Post`, `MediaItem` (Phase 3), `Engagement` (Phase 5), `InsightSnapshot`,
`UsageRecord` (Phase 6). See `DECISIONS.md`.

**Start a new session with:** "Read HANDOFF.md and GROWTH_AGENT_SPEC.md, then
begin Phase 2 — restate your plan first."
