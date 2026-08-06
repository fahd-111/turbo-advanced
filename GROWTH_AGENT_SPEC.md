# Project: Growth Agent — Autonomous Social Media Marketing SaaS

You are building a multi-tenant SaaS platform called **Growth Agent**. Businesses sign up, connect their Instagram Business/Creator account and Facebook Page, and an AI agent autonomously promotes them: it builds a content strategy, generates posts (text + AI images), publishes them on schedule, and replies to comments and DMs in real time in the business's brand voice.

Read this entire document before writing any code. Follow the phased build order at the bottom. Ask me before deviating from the architecture decisions in this file.

---

## 1. Core Product Requirements

### 1.1 Tenancy & Auth
- Multi-tenant SaaS. Businesses self-serve sign up (email/password + email verification; add Google OAuth later).
- Each business is a tenant. All data is scoped by `business_id`. A user account can own multiple businesses.
- Every Composio entity/connected account, scheduled post, conversation, and analytics row belongs to exactly one business.

### 1.2 Business Onboarding
When a business is added, run an onboarding wizard that captures:
1. Business name, description, industry, website URL, target audience, location/timezone.
2. **Brand profile builder**: optionally scrape the business website (and existing public socials if provided) to extract tone of voice, offerings, key selling points, and audience. Store as a structured `BrandProfile` (JSON: voice_attributes, content_pillars, offerings, audience_personas, hashtag_sets, banned_topics, required_disclaimers).
3. Brand assets: logo, brand colors, photo library uploads (optional). Media stored on the VPS filesystem or S3-compatible storage (configurable via env).
4. Guardrails: a per-business list of things the agent must NEVER say (e.g., pricing promises, refunds, medical/legal claims). These get injected into every generation and reply prompt.
5. Social connection step: connect Instagram (Business/Creator only) + Facebook Page via Composio OAuth. Clearly instruct users that a personal Instagram account must be converted to Business/Creator and linked to a Facebook Page first. Show connection health status.

### 1.3 Content Strategy Engine
- After onboarding, the agent generates a **content strategy** per business: 3–5 content pillars, posting cadence recommendation, campaign ideas, hashtag strategy, and a 2-week rolling content calendar.
- Strategy is regenerated/adjusted monthly and whenever the analytics feedback loop (see 1.7) shows significant performance signals.
- Strategy is visible and editable in the dashboard.

### 1.4 Post Generation
- Agent drafts posts from the strategy: caption (platform-appropriate length, hashtags, CTA, brand voice) + image.
- Images: AI-generated via OpenRouter image models by default; can also pull from the business's uploaded asset library. Every image prompt incorporates brand colors/style from BrandProfile.
- Posts are platform-specific (an IG post and FB post for the same campaign slot are separately rendered, not blindly cross-posted).
- Post types v1: single image + caption. Carousels and reels are v2 — design the data model to allow them (a Post has many MediaItems).

### 1.5 Scheduling & Publishing
- Fully autonomous: generated posts go straight into the schedule; no approval required. BUT every business has a configurable **review buffer** setting (default 0h) — if set, posts sit in the calendar for N hours before publish, giving the owner a window to edit/delete.
- Scheduling modes (both supported, per business): (a) user-defined cadence and time slots ("3 posts/week, 6pm"), (b) agent-optimized timing using platform best-practice heuristics + that business's own engagement analytics. Per-business timezone everywhere.
- **Calendar UI**: month/week view showing queued, published, and failed posts. Inline edit caption/image/time, delete, "publish now".
- Publisher worker (Celery beat, every minute): pick up due `ScheduledPost` rows, publish via Composio (Instagram: create media container → publish; Facebook: create photo post). Before Instagram publish, call the content publishing usage tool and skip+reschedule if the account is near Meta's daily API publish cap.
- **Failure handling**: retry with exponential backoff (3 attempts). Auth/token errors → mark the connection unhealthy, pause the business's queue, notify the owner by email + dashboard banner to reconnect. All publish attempts logged.

### 1.6 Engagement Agent (comments + DMs, real time)
- Composio triggers deliver new IG/FB comments and DMs to our webhook in real time. Verify the Composio webhook HMAC signature on every request. If a needed trigger type turns out to be unavailable or polling-only, fall back to a Celery polling loop (every 1–2 min) using the get-comments/get-conversations tools — abstract the event source so both paths feed the same handler.
- Pipeline per inbound event: classify intent + sentiment → route:
  - **Question / neutral / praise** → auto-reply in brand voice.
  - **Complaint, refund request, legal/medical/pricing-commitment topics, abuse, or low classifier confidence** → do NOT reply; escalate to the owner (dashboard inbox item + email notification).
- Facebook DMs: respect Meta's 24-hour messaging window — only reply if within 24h of the user's last message; otherwise escalate.
- Every auto-reply prompt includes: brand voice, banned topics, the original post's content for context, and the instruction to never make commitments about price, refunds, or availability.
- Dashboard **Inbox**: unified view of all comments/DMs across platforms with status (auto-replied / escalated / resolved), and the ability for the owner to reply manually (sent via Composio).
- Per-business kill switch that instantly pauses all auto-replies and/or all publishing.

### 1.7 Analytics & Feedback Loop
- Nightly Celery job pulls post insights (impressions, reach, engagement) and page/account insights via Composio for every published post.
- Dashboard analytics page: per-post performance, best times/pillars, follower growth.
- Feedback loop: monthly strategy regeneration receives a performance summary (top/bottom posts by engagement, per pillar and time slot) so the agent adapts what and when it writes.

### 1.8 Cost Controls
- Track OpenRouter token + image-gen spend per business per month in the DB. Configurable soft/hard monthly budget per business; hard cap pauses generation and notifies.

---

## 2. Tech Stack & Architecture (do not deviate without asking)

- **Monorepo**: Turborepo. `apps/web` = Next.js 15 (App Router, TypeScript, Tailwind, shadcn/ui). `apps/api` = Django 5 + Django REST Framework (Python 3.12). `packages/` for shared config; generate TypeScript API types from the DRF OpenAPI schema (drf-spectacular → openapi-typescript).
- **DB**: PostgreSQL 16. **Queue/broker**: Redis + Celery (workers + celery-beat). No BullMQ — all background work lives in Django/Celery.
- **Composio**: Python SDK inside Django only (the Next.js app never talks to Composio directly). One Meta auth config; each business maps to one Composio user id (`business_{id}`). Single project webhook endpoint `POST /api/webhooks/composio/` with signature verification, which enqueues events onto Celery.
- **LLM**: OpenRouter for everything. Model routing: cheap fast model for reply classification and comment replies; stronger model for strategy + captions; an image model for visuals. Model names in env vars, never hardcoded.
- **Auth (app)**: Django session or JWT (djangorestframework-simplejwt) consumed by Next.js.
- **Deployment target** (later): single VPS via Coolify — Docker Compose with services: web, api, worker, beat, postgres, redis. Write Dockerfiles and compose config in Phase 6, but keep everything 12-factor (env-driven config) from day one.
- **Env vars** in `.env` (never committed): `COMPOSIO_API_KEY`, `COMPOSIO_WEBHOOK_SECRET`, `OPENROUTER_API_KEY`, `DATABASE_URL`, `REDIS_URL`, model name vars, storage config.

### 2.1 Data Model (starting point — refine as needed)
- `User`, `Business` (owner FK, timezone, settings JSON, kill_switch flags, review_buffer_hours, monthly_budget)
- `BrandProfile` (1:1 Business, structured JSON fields listed in 1.2)
- `SocialConnection` (business FK, platform enum [instagram|facebook], composio_connected_account_id, external_account_id, status [healthy|needs_reauth|disconnected], last_checked)
- `ContentStrategy` (business FK, version, pillars JSON, cadence JSON, active flag)
- `Post` (business FK, strategy FK nullable, pillar, status [draft|scheduled|publishing|published|failed|cancelled], caption, hashtags, platform, external_post_id, error_log JSON)
- `MediaItem` (post FK, type, file/url, generation_prompt, source [ai|library])
- `ScheduledPost` view-of/fields-on Post: publish_at (UTC), attempts, next_retry_at
- `Engagement` (business FK, platform, kind [comment|dm], external_id, external_parent_id, author info, text, classified_intent, sentiment, confidence, status [auto_replied|escalated|resolved|ignored], reply_text, replied_at)
- `InsightSnapshot` (post FK nullable / business-level, metrics JSON, captured_at)
- `UsageRecord` (business FK, month, tokens_in, tokens_out, images_generated, est_cost)
- `AuditLog` (business FK, actor [agent|user], action, payload JSON) — log every autonomous action the agent takes.

### 2.2 Key Composio facts to build around
- Instagram toolkit supports Business/Creator accounts only; publishing is a two-step container→publish flow; there is a content-publishing-usage tool — check it before publishing (Meta caps API posts per 24h).
- Facebook toolkit supports Pages only; has create post/photo/video post, comment CRUD, Messenger send-message tools, and native scheduled-post tools (usable as fallback).
- Triggers: one webhook URL per Composio project; events are HMAC-signed (`webhook-signature` header, verify with `COMPOSIO_WEBHOOK_SECRET`); trigger instances are created per connected account — create them automatically right after a business connects an account, and delete them on disconnect.
- For production we will register our own Meta developer app (custom OAuth credentials in Composio) and go through Meta App Review for: `instagram_content_publish`, `instagram_manage_comments`, `instagram_manage_messages`, `pages_manage_posts`, `pages_read_engagement`, `pages_messaging`. Dev/testing can use Composio's managed app with test accounts. Structure the auth config so swapping to custom credentials is a config change, not a code change.

---

## 3. Engineering Conventions
- Type hints everywhere in Python; strict TypeScript. Ruff + mypy for Python, ESLint + prettier for TS.
- Tests: pytest for Django (models, services, webhook signature verification, publisher retry logic, escalation routing MUST have tests). Vitest/Playwright optional for web in v1.
- All LLM prompts live in a `prompts/` module as versioned template functions — never inline prompt strings in business logic.
- Service layer pattern in Django: views are thin; logic lives in `services/` (e.g., `services/publishing.py`, `services/engagement.py`, `services/strategy.py`, `services/composio_client.py`).
- Every external call (Composio, OpenRouter) goes through a wrapper with timeout, retry, structured logging, and usage recording.
- Idempotency: webhook events carry external IDs — dedupe on `Engagement.external_id` so retried deliveries never double-reply.
- Never let the agent reply to its own comments/replies (check author == connected account).

## 4. Safety Rails (non-negotiable)
- Banned-topics list injected into every generation/reply prompt.
- Classifier confidence threshold (default 0.7) below which we escalate instead of replying.
- Hard rule in reply prompts: no commitments on pricing, refunds, availability, medical or legal claims; when in doubt, say a team member will follow up.
- Kill switches respected at the worker level (check flags immediately before any publish/reply, not just at enqueue time).
- Rate-limit auto-replies per business per hour (default 30) as a runaway guard.

---

## 5. Build Phases (work in this order; complete + test each before moving on)

**Phase 1 — Skeleton & connect flow.** Turborepo scaffold, Django project, models + migrations, auth, Business CRUD, Composio integration: OAuth connect flow for IG + FB, store SocialConnection, connection-health check, and a management command that publishes one hardcoded test post to a connected account end-to-end. This de-risks everything — get it working against a real test account before anything else.

**Phase 2 — Onboarding & brand profile.** Wizard UI, website scraper → BrandProfile via LLM, asset uploads, guardrails input.

**Phase 3 — Strategy & content engine.** Strategy generation, post drafting (caption + image gen), draft management UI.

**Phase 4 — Scheduler & calendar.** ScheduledPost pipeline, celery-beat publisher with retries + IG quota check + failure notifications, calendar UI with edit/delete/publish-now, review buffer.

**Phase 5 — Engagement agent.** Composio triggers auto-created on connect, webhook endpoint with signature verification, classification → auto-reply/escalate pipeline, polling fallback abstraction, unified Inbox UI, DM support with 24h-window check, kill switches, rate guard.

**Phase 6 — Analytics, budgets, deploy.** Insights sync job, analytics dashboard, feedback loop into strategy regen, usage/budget tracking, Dockerfiles + Coolify-ready compose, docs.

At the start of each phase, restate your plan for that phase and list the files you'll create/modify before writing code.
