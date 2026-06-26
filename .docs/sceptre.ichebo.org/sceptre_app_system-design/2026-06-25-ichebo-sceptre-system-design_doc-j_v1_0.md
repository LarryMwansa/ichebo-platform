# Sceptre Community Surface + Ichebo Channel + Access Model

> **—— SYSTEM DESIGN DOCUMENT**

| Field | Value |
|---|---|
| Document | DOC J — Sceptre Community Surface, Ichebo Channel, Access Model |
| Version | 1.3 — 2026-06-26 (corrected against the live repo; v1.2 added cross-references to the four built UI mockups and fixed three prose/mockup mismatches — Correction Log item 12, Parts 3.3/3.4/6/7. v1.3 resolves Part 5.1's 0a/0b "open question" — it was never a gap: 0a/visitor and 0b/seeker are a real, already-implemented distinction via `UserPermission` on an `induction`-tier tenant, confirmed against `community/views.py:my_community`, not a missing `competence_level` value. Locked the participant gate accordingly and corrected `sceptre/auth.py` in §5.2.) |
| Status | Approved — Canonical Reference |
| ADR reference | ADR-023 (subdomain separation), ADR-024 (Ichebo Channel architecture) |
| Data contract | data-contract-v11-canonical-2026-05-13.md — v12 amendments noted |
| Roadmap | Master Roadmap v7 — Phases H.5, H.6, H.7 (new). H.3 and H.4 are already shipped — see Correction Log. |
| Depends on | DOC G (Ichebo Media), ADR-001–022, Community Support Plan (H.3 — shipped), Community Live Service Room Plan (H.4 — shipped), Video Direction v2 Plan |
| Authors | Chizola (domain); Claude (technical) |

---

## Correction Log — v1.0 → v1.1 (2026-06-26)

v1.0 was produced in a session without access to the live codebase. The following corrections were found by checking every claim directly against the repository and the production servers — not by re-deriving the design. The architecture and decisions below are unchanged; only facts that were wrong or had since moved are corrected.

| # | v1.0 said | Actual / corrected |
|---|---|---|
| 1 | ADR-022 (subdomain separation), ADR-023 (channel) | **ADR-022 already exists** — approved 2026-06-09, Handbook/Governance separation (`2026-06-09-adr-022-handbook-governance-separation.md`). Renumbered to **ADR-023** (subdomain separation) and **ADR-024** (channel) throughout this document. |
| 2 | H.3 (Community Support) and H.4 (Live Service Room) listed as new phases to build | **Both already shipped.** H.3: `commit 16bfbab`, 2026-06-22 — `community/services.py:resolve_steward_for_tenant`, `Record(record_type='support_request')`, queue at `/community/support/`. H.4: `commit d6a7854`, 2026-06-22, superseded/corrected by `commit 67878ba` (2026-06-24/25) — tenant-scoped live room at `/community/live/`, `community/views.py:_find_live_session`, in-service ministry panel. The H.3 and H.4 phase plan documents in this folder describe this work as not-yet-built against files (`video_live/views.py:_event_qs`) that no longer exist — see those documents' own correction notes. |
| 3 | Django app server: `/home/ics/ichebo-platform`, Gunicorn on `127.0.0.1:8000` | Real path: **`/home/scepter/ichebo-platform-repo/ichebo-platform`**. Real Gunicorn bind: **`127.0.0.1:8001`** (confirmed in `gunicorn.conf.py` on the server). User is `scepter`, not `ics`. |
| 4 | `ROOT_URLCONF` implied as `ichebo_platform.urls`, settings module as `settings.py` | Real values: `ROOT_URLCONF = 'ics_project.urls'`; settings live in `ics_project/settings/base.py` + `production.py`, not a single `settings.py`. |
| 5 | `competence_level` treated as a string with values like `'0a'`, `'0b'`, `'3'` | Real field: `accounts/models.py` — `competence_level = models.IntegerField(default=0)`. Plain integers `0`–`5`. **There is no `'0a'`/`'0b'` distinction on this field.** Every gating snippet in this document and the phase plans that does `competence_level not in ['0b','1','2',...]` compares an int to a list of strings — always `True`/`False` the wrong way in real Python, which would lock every participant out. All gating code in this document corrected to use integer comparisons. **Resolved 2026-06-26 (see Part 5.1):** the 0a/0b distinction is real, but lives on a second axis — an active `UserPermission` on an `induction`-tier tenant — not on `competence_level`. No longer an open question. |
| 6 | `Tenant` model fields implied as `tenant_path` (on Tenant itself) | Real field is **`Tenant.path`** (materialized path). `tenant_path` is a real field, but it lives on **`UserPermission`**, not `Tenant`. `Tenant.objects.create(...)` also requires `slug` (unique, required), `tier` (required, no default), and `created_by` (required, `PROTECT`) — none of which appeared in this document's or the phase plans' test helpers. Corrected in Part 5 and noted for the phase-plan test suites. |
| 7 | `role__endswith='-steward'` proposed as the steward-role check | Works for every steward role (`branch-steward` … `global-steward`) but **silently excludes `'admin'`**, which does not end in `-steward` and is a real, in-use role (confirmed in `tenants/models.py:UserPermission.STEWARD_ROLES`, built 2026-06-24 for an unrelated tenancy-visibility fix). Corrected to check membership in the real `STEWARD_ROLES` set instead of a suffix match. |
| 8 | `create_notification()` called with `source_app`, `source_record_id`, `message` kwargs (H.5 plan) | Real signature (`notifications/service.py`): `create_notification(user, notification_type, title, body='', data=None)`. No `source_app`/`source_record_id`/`message` parameters exist — corrected in the H.5 plan. |
| 9 | DNS for `sceptre.ichebo.org` and the other new subdomains listed as "not yet configured" / a precondition to check | **Confirmed live** as of 2026-06-26 — `sceptre.ichebo.org`, `join`, `identity`, `learn`, `handbook`, `give` all resolve to the Django VPS (`37.27.82.169`); `media.ichebo.org` resolves to the video VPS (`46.62.211.72`). DNS is no longer a blocker for H.6's Nginx/SSL step. |
| 10 | Nginx config shown as a separate file per subdomain (`/etc/nginx/sites-available/sceptre.ichebo.org`) | The real server keeps **one file**, `/etc/nginx/sites-available/ics`, with every subdomain as its own `server {}` block inside it (confirmed by reading the live file). The corrected H.6 plan adds a new block to that same file rather than creating a separate one, matching the existing convention. |
| 11 | `ALLOWED_HOSTS` / `SESSION_COOKIE_DOMAIN` shown as already containing other entries | Production's actual `.env` currently has `ALLOWED_HOSTS=app.ichebo.org,ichebo.org,www.ichebo.org` — `sceptre.ichebo.org` is genuinely not yet present and must be added. `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` are **not set at all** currently (no cross-subdomain cookie sharing exists yet) — the decision in §11.3 (share a login across subdomains vs. require separate logins) is **locked, 2026-06-26: shared login**, `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` = `.ichebo.org`. |
| 12 | This document had no visual reference for H.4's already-shipped Live Service Room + Ministry Panel | `sceptre_comm_web-ui_mockup/04-sceptre-live-service.html` — built mockup covering all four states (member view with prayer/question form, post-submit confirmation, steward queue, no-live-service empty state). One real inconsistency found and fixed directly in the mockup file: it said the steward queue "refreshes every 20 seconds" in three places — the actual shipped polling interval is 15 seconds (`LIVE_REQUEST_POLL_SECONDS = 15`, `community/views.py`); corrected to 15s in the mockup. |

---

## Part 1 — The Core Decision

The Ichebo platform is infrastructure. It now serves two distinct surfaces with their own subdomains, their own design purpose, and their own users. This subdomain separation is the correct digital expression of the three-layer KGS order.

| Layer | Surface | Domain |
|---|---|---|
| KGS Framework | Agency / Architect surface | app.ichebo.org |
| Sceptre Community Programme | Community surface | sceptre.ichebo.org |
| Ichebo Platform | Backend infrastructure | Serves both |

### app.ichebo.org — The Agency Surface

The current Apostolic Command Shell evolves into the operator domain. Constitutional governance, Handbook authorship, network oversight, licence issuance, formation pipeline oversight, platform administration. This is the Architect's domain — Chizola's primary operating environment — and the steward's governance environment for network-level work.

### sceptre.ichebo.org — The Community Surface

A new Django surface designed from scratch for its actual users: members going through the Sceptre Community Programme, and the stewards who lead them. Two sides — consumer (participant) and steward (community leadership) — within one role-adaptive shell. The pilot is built here.

### The Backend Does Not Change

Same Django backend. Same database. Same API. Same data contract. Django serves both subdomains from one codebase via subdomain-aware URL routing. One new Nginx server block for `sceptre.ichebo.org`. No data separation — only presentation separation.

---

## Part 2 — Subdomain Architecture (ADR-023)

### 2.0 Full Subdomain Topology

The Ichebo ecosystem spans two physical servers. All subdomains are documented here to prevent ambiguity when configuring Nginx, DNS, or SSL certificates.

**Django VPS — `37.27.82.169` (platform VPS, existing). User: `scepter`. Repo: `/home/scepter/ichebo-platform-repo/ichebo-platform`.**

| Subdomain | Purpose | Routes to |
|---|---|---|
| `app.ichebo.org` | Agency / Architect surface — Apostolic Command Shell | Gunicorn `127.0.0.1:8001` |
| `sceptre.ichebo.org` | Sceptre Community surface — participant + steward (new). DNS confirmed live 2026-06-26, points at this server. | Gunicorn `127.0.0.1:8001` (same process) |

**Video VPS — `46.62.211.72` (Helsinki, deployed 2026-06-23)**

| Subdomain | Purpose | Routes to |
|---|---|---|
| `video.ichebo.org` | Go media engine (mediad) — VOD upload, transcoding, webhook handler | `mediad` on `127.0.0.1:8090` |
| `media.ichebo.org` | RTMP ingest (port 1935, no Nginx) + HLS delivery (Nginx → MediaMTX HTTP) | Port 1935 direct (RTMP); MediaMTX HTTP for HLS |
| `stream.ichebo.org` | Allocated, Let's Encrypt cert present — **disabled** (symlink removed from `sites-enabled`). Chizola's decision 2026-06-23: RTMP ingest lives at `media.ichebo.org` per DOC G. Not deleted, not wired to anything. | — |

**Object storage**

| Endpoint | Purpose | Location |
|---|---|---|
| MinIO on Django VPS (`127.0.0.1:9000`) | Interim object storage for Django-side media (bucket: `ics-media`) | Django VPS — to be migrated to Hetzner Object Storage before CDN delivery |
| MinIO on Video VPS (`127.0.0.1:9000`) | Video engine object storage — isolated from Django VPS (buckets: `ics-media-upload`, `ics-media-delivery`) | Video VPS — independent instance, scoped credentials |

`cdn.ichebo.org` — referenced in earlier versions of DOC G — **does not exist** in DNS or any deployed Nginx config. See DOC G amendment (`doc-g-video-pipeline-amendment.md`) for the correction. The live delivery domain is `video.ichebo.org`; the live HLS domain is `media.ichebo.org`.

`ichebo.org` (marketing site) and `handbook.ichebo.org` (deferred) are not part of this document's scope.

---

### 2.1 Approach: Subdomain-Aware URL Routing

Django's `sites` framework (multi-site) is not used. It was built for entirely separate Django projects sharing a database — a different problem. The correct approach is subdomain-aware URL routing within one Django project.

**How it works:**

- Nginx receives requests on both `app.ichebo.org` and `sceptre.ichebo.org`
- Both proxy to the same Gunicorn/Django process (same port, same workers)
- Django's `ALLOWED_HOSTS` includes both subdomains
- A custom middleware reads `request.get_host()` and sets `request.site = 'agency' | 'community'`, and sets `request.urlconf` directly when the host is `sceptre.ichebo.org` — this is the real Django mechanism for per-request URL conf override; it does not require a separate dispatcher function in `ics_project/urls.py`
- `ics_project/urls.py` (the real `ROOT_URLCONF`) handles `app.ichebo.org` — existing URL patterns, completely unchanged
- `sceptre/urls.py` (new) handles `sceptre.ichebo.org` — new URL patterns, used only when `request.urlconf` is set
- Templates: the existing tree under `templates/` is flat (e.g. `templates/community/`, `templates/governance/`) — **no `templates/agency/` namespace exists and none is needed.** Only `templates/sceptre/` is new and additive; nothing existing moves or is relocated.
- Same `User`, `UserPermission`, `Record`, `Activity` models underpin both

**Nginx configuration** — corrected to match the real server, which keeps every subdomain as one `server {}` block inside a single file (`/etc/nginx/sites-available/ics`), not a separate file per subdomain:

```nginx
# /etc/nginx/sites-available/ics — add this block alongside the existing
# app.ichebo.org blocks already in the file. Do not create a separate file.
server {
    listen 80;
    server_name sceptre.ichebo.org;
    return 301 https://sceptre.ichebo.org$request_uri;
}

server {
    listen 443 ssl;
    server_name sceptre.ichebo.org;

    ssl_certificate /etc/letsencrypt/live/sceptre.ichebo.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sceptre.ichebo.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location /static/ {
        alias /home/scepter/ichebo-platform-repo/ichebo-platform/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        proxy_pass http://localhost:9000/ics-media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
    }
}
```

SSL via certbot (same as existing subdomains). DNS: confirmed live 2026-06-26 — `sceptre.ichebo.org` already resolves to the Django VPS IP, no DNS work remains.

**Django settings and middleware** — corrected to the real settings module path and `request.urlconf` mechanism:

```python
# ics_project/settings/base.py — ALLOWED_HOSTS is read from .env via config();
# production's .env currently has ALLOWED_HOSTS=app.ichebo.org,ichebo.org,www.ichebo.org
# — sceptre.ichebo.org must be added to that value.

# middleware/site_router.py (new file, new top-level package)
class SiteRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host == 'sceptre.ichebo.org':
            request.site = 'community'
            request.urlconf = 'sceptre.urls'   # overrides ROOT_URLCONF for this request only
        else:
            request.site = 'agency'
            # request.urlconf intentionally not set — Django falls back to
            # ROOT_URLCONF ('ics_project.urls'), completely unchanged.
        return self.get_response(request)
```

No dispatcher function in `ics_project/urls.py` is needed — setting `request.urlconf` directly in the middleware is the complete mechanism; Django's URL resolver checks it automatically on every request.

**Template directory structure:**

```
templates/
├── base.html, workspace_shell.html, community/, governance/, learn/, ...   # existing — unchanged, untouched, not relocated
└── sceptre/          # sceptre.ichebo.org templates (new — the only addition)
    ├── base.html     # Sceptre shell base
    ├── _nav.html     # Navigation component
    ├── home/         # Participant home
    ├── community/
    ├── learn/
    ├── bible/
    └── steward/      # Steward management views
```

### 2.2 Frontend Approach

`sceptre.ichebo.org` follows the same frontend architecture as `app.ichebo.org`: Django templates + HTMX for all authenticated surfaces. Static HTML/CSS for any public-facing pages (e.g. a landing/welcome page at `sceptre.ichebo.org/`). No vanilla JS application files. No React, Vue, or frontend framework. This is an extension of ADR-005 to the new subdomain — not a new decision.

---

## Part 3 — sceptre.ichebo.org Surface Architecture

### 3.1 The Role-Adaptive Shell

The consumer side and steward side are not separate URLs — they are one role-adaptive shell. A single login. A single session. A single navigation container. What renders inside depends on the authenticated user's competence level and their `UserPermission` role in the active tenant.

| User type | Gating rule | What they see |
|---|---|---|
| Participant | `competence_level` 0–2 (real `IntegerField`, no `'0a'`/`'0b'` split in the model) | Consumer side: Channel, Community (read), Learn, Bible, Support |
| Community Steward | `competence_level >= 3` OR `UserPermission.role in tenants.models.UserPermission.STEWARD_ROLES` | All participant access + steward management panel |
| Architect | `competence_level == 5` AND a direct `UserPermission` on the Prime tenant | Does not use `sceptre.ichebo.org` as primary — works from `app.ichebo.org`; can access `sceptre.ichebo.org` as a steward-equivalent if needed |

The steward layer does not exist in a participant's DOM — it is not hidden via CSS, it is not rendered. Template context is gated at the view level using the same `_require_level` helper pattern already used across the Community and Governance apps.

### 3.2 Participant Consumer Side — Information Architecture

> **—— Navigation model**

`sceptre.ichebo.org` uses a top navigation bar on web (consistent with a consumer website feel, not the sidebar-heavy Apostolic Command Shell), and a five-tab bottom navigation on mobile (Flutter). The web navigation is deliberately simpler than `app.ichebo.org` — participants are not navigating a governance workspace.

**Web Navigation (sceptre.ichebo.org — Desktop/Tablet):**

| Nav item | URL | Who sees it |
|---|---|---|
| Home | `/` | All participants |
| Community | `/community/` | All participants |
| Learn | `/learn/` | Level 1+ |
| Bible | `/bible/` | All participants |
| Support | `/support/` | All participants |
| [Avatar / Profile] | `/profile/` | All participants (top-right) |

On tablet/desktop, navigation is a top bar with the Ichebo brand mark (left), nav links (centre), and profile avatar (right). The shell is clean and light — stone background (`#F5F3F0`), no dark sidebar, no multi-column governance grid. The channel video dominates the Home page.

**Mobile Navigation (Flutter — BottomNavShell, participant variant):**

| Tab | Icon | Label | Who sees it |
|---|---|---|---|
| 1 | `tv_outlined` | Channel | All |
| 2 | `people_outlined` | Community | All |
| 3 | `school_outlined` | Learn | Level 1+ |
| 4 | `menu_book_outlined` | Bible | All |
| 5 | `support_agent_outlined` | Support | All |

The fifth tab (Support) replaces the previous Profile tab in the bottom nav for participants — Profile is accessible from within the Community or Support screens. Five tabs is the maximum per DESIGN.md.

### 3.3 Participant Home Screen

> **—— Channel-first design**
>
> **Visual reference:** `sceptre_comm_web-ui_mockup/01-sceptre-home.html` — built, real HTML/CSS mockup covering all three channel states (live, scheduled VOD, offline). Treat it as the authoritative visual spec where it disagrees with the prose below; two real differences found by reading the mockup directly:
> - The mockup uses a **dark ink top nav bar** (`#0E0E0E`, Playfair wordmark, nav links, notification bell, avatar) spanning full width — not described in the prose layout below at all. Add it as item 0 in the Web Home Layout list.
> - The four tiles render as a **horizontal-scrolling 1×4 row** (`flex: 0 0 160px` each, `overflow-x: auto`), not a "2×2 grid" — and the hero video is full-bleed (`width: 100vw`), not "max content width 800px, centred." The mockup's layout is the one to build from.

The channel video window is the first and dominant element on the participant Home screen. It is not a card, not a thumbnail, not a poster image — it is an actively playing video. The participant opens the app or visits `sceptre.ichebo.org/home/` and the channel is already playing.

**Web Home Layout (`sceptre.ichebo.org/home/`):**

Layout is full-bleed, not centred to a fixed width (corrected per the mockup — see note above). From top to bottom:

0. Top nav bar — dark ink, brand mark + wordmark (left), nav links Channel/Community/Learn/Bible/Support (centre), notification bell + avatar (right). The active nav link gets a left red rule accent, matching the Apostolic Command Shell's existing active-state pattern.
1. Channel video player — full width, 16:9 aspect ratio, autoplay muted (browser policy). Now-playing title and live badge (if live) displayed below the player frame. 'Tap to unmute' prompt on first load.
2. Now-playing strip — slim row beneath the video: channel name/label, current content title, ends-at time (or 'LIVE' badge if live). Left red rule accent on the live badge.
3. Next up — single-line teaser: next scheduled item title and start time. Only shown if `ChannelSlot` exists.
4. Four compact tiles in a **horizontal-scrolling row** (not a 2×2 grid — corrected per the mockup) — Community, Learn, Bible, Support. Each tile: icon, label (Inter 600 13px), brief status line (latest announcement / next lesson / current passage / open requests). White card on stone background, left red rule on hover.

**Flutter Home Screen (Channel tab):**

From top to bottom within the Channel tab:

1. `IcheboAppBar` — dark ink, Ichebo brand mark, notification bell (badge if unread)
2. Channel video player widget — full viewport width, 16:9 aspect ratio. Uses the HLS player widget from Layer 8 (already built). Initialised with URL from `GET /api/broadcast/now/`. Autoplay on mount.
3. Now-playing card — dark ink surface, content title in Playfair Display 20sp, live badge (red pill) or scheduled badge (muted pill). Left red rule.
4. Next scheduled item row — lighter stone surface, compact, shows next title + time.
5. Quick-access tiles row — horizontal scroll, four tiles: Community, Learn, Bible, Support. Each tile is an `IcheboCard` (12dp radius, stone surface) with icon + label + status line.

**Video player states:**

| State | What plays | UI indicator |
|---|---|---|
| Scheduled content | VOD from ChannelSlot — HLS or direct URL | Title + end time in now-playing strip |
| Live override | BroadcastSchedule HLS stream | Red LIVE badge + pulsing dot |
| Fallback playlist | Next VOD in `ChannelConfig.fallback_playlist` | Title only, no end time |
| Loop default | `ChannelConfig.loop_default_video` | Loop icon + title |
| Channel offline | Null — no content configured | Dark frame, 'Channel offline' message, Ichebo brand mark |

**Polling strategy:**

Mobile: `GET /api/broadcast/now/?tenant_id={uuid}` polled every 60 seconds, and on app foreground. If `content_type` changes (e.g. from `vod` to `live`), the player reinitialises with the new URL without requiring a page reload.

Web: HTMX polls the now-playing endpoint every 60 seconds (`hx-trigger='every 60s'`) and swaps the now-playing strip and video `src` attribute. The video element itself is not replaced — only the `src` is updated via a JavaScript bridge to avoid interrupting playback unnecessarily. A live transition forces a full player reload.

### 3.4 Steward Side — Information Architecture

> **—— Role-adaptive panel**
>
> **Visual reference:** `sceptre_comm_web-ui_mockup/03-sceptre-steward-panel.html` — built mockup, and it shows a structurally different mechanism than the prose immediately below: not a permanently-visible nav section, but a **"Manage" trigger button in the top nav** (visible only to Level 3+/steward-role users) that **slides in a steward sidebar from the right** over a dimmed main view, with its own close button. The mockup's mechanism is the one to build from — corrected below.

When a Level 3+ user or a role in `UserPermission.STEWARD_ROLES` logs in to `sceptre.ichebo.org`, a "Manage" button appears in the top nav (participants never see it). Tapping it slides in a steward sidebar from the right — main content dims slightly behind it — labelled 'Community Management' with its own close (×) control; it is not a section appended below the participant nav. On mobile (Flutter), a sixth nav tab appears — 'Manage' — gated by the same competence level check, opening the same six options as a bottom sheet (per the existing FAB sheet pattern, unchanged from the original design intent here).

**Steward navigation additions (web):**

| Nav item | URL | Purpose |
|---|---|---|
| Members | `/steward/members/` | Member roster, competence levels, shepherd assignments |
| Gatherings | `/steward/gatherings/` | Schedule gatherings, link to BroadcastSchedule for digital |
| Formation | `/steward/formation/` | Induction queue, active programmes, certification queue |
| Announcements | `/steward/announcements/` | Author and publish community announcements |
| Support Queue | `/steward/support/` | All open support requests, SLA status, assignment |
| Community Settings | `/steward/settings/` | Community profile, ChannelConfig (if tenant has channel) |

The steward sidebar is fully separate from the participant nav by construction (it's an overlay, not an inline section) — the label tag ('—— COMMUNITY MANAGEMENT') sits at the top of the slide-in panel itself, per the mockup. On mobile, the Manage tab opens a bottom sheet with these six options, following the existing FAB sheet pattern.

---

## Part 4 — Ichebo Channel Architecture (ADR-024)

### 4.1 What the Channel Is

The Ichebo Channel is a continuous broadcast channel — a 24/7 programmed video stream with a defined fallback hierarchy. It is the primary surface of the participant experience, not a feature navigated to. A participant opens the app and the channel is playing.

The channel is not a real-time video stream by default. It is a scheduled playlist — the platform knows what should be playing at any given moment and serves the correct content URL to the client. True real-time live broadcasts (RTMP/HLS via Ichebo Media) take over the channel at their scheduled time. Between live broadcasts, the channel plays pre-recorded VOD content in sequence.

**The fallback hierarchy (locked):**

1. Scheduled content — `ChannelSlot` with `scheduled_start <= now <= scheduled_end`
2. Live override — `BroadcastSchedule` with `status='live'` in the tenant
3. Fallback playlist — `ChannelConfig.fallback_playlist` rotates in order
4. Loop default — `ChannelConfig.loop_default_video_id` plays on repeat

If none of the four resolve, the channel is offline.

### 4.2 New Models — broadcast Django App

> **—— A new broadcast Django app**

Channel configuration models live in a new `broadcast` Django app. This app is infrastructure-only — no sidebar icon, no participant-facing UI. It is accessed by stewards and the Architect through their respective management surfaces, and queried by the now-playing endpoint.

**ChannelConfig model:**

```python
class ChannelConfig(models.Model):
    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant                = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE,
                               related_name='channel_config')
    loop_default_video_id = models.UUIDField(null=True, blank=True)
    # The id of a records.Record with record_family='media' — resolved at
    # read time via media.models.VideoRecord(record), a typed wrapper
    # class around Record, not a separate model with its own primary key
    # (confirmed in media/models.py). video_live has no VideoRecord at all
    # — its only surviving model after Video Direction v2 is BroadcastSchedule.
    fallback_playlist     = models.JSONField(default=list)
    # Ordered list of media-family Record UUIDs (strings)
    fallback_position     = models.IntegerField(default=0)
    # Current position in fallback_playlist — advances on each rotation
    is_active             = models.BooleanField(default=True)
    created_by            = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.SET_NULL, null=True)
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)
    deleted_at            = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Channel Configuration'
```

**ChannelSlot model:**

```python
CONTENT_TYPE_CHOICES = [
    ('vod', 'Video on Demand'),
    ('live', 'Live Broadcast'),
]

class ChannelSlot(models.Model):
    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant                = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE,
                               related_name='channel_slots')
    scheduled_start       = models.DateTimeField()
    scheduled_end         = models.DateTimeField()
    content_type          = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    video_record_id       = models.UUIDField(null=True, blank=True)
    # id of a records.Record with record_family='media' for vod content_type
    # — see ChannelConfig.loop_default_video_id's comment above
    broadcast_schedule_id = models.UUIDField(null=True, blank=True)
    # UUID of BroadcastSchedule for live content_type
    title                 = models.CharField(max_length=255)
    # Denormalised for display without join
    is_recurring          = models.BooleanField(default=False)
    recurrence_rule       = models.CharField(max_length=255, null=True, blank=True)
    # RRULE string — deferred in v1, nullable
    created_by            = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.SET_NULL, null=True)
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)
    deleted_at            = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['scheduled_start']
        indexes = [
            models.Index(fields=['tenant', 'scheduled_start', 'scheduled_end']),
        ]
```

These are configuration models, not content models. ADR-003 (single records table with discriminator) does not apply — `ChannelConfig` and `ChannelSlot` are programme schedule configuration, in the same category as `BroadcastSchedule`. New models are correct.

### 4.3 The Now-Playing Endpoint

> **—— GET /api/broadcast/now/**

```
GET /api/broadcast/now/?tenant_id={uuid}
```

Authentication: required. Rate limit: standard DRF throttle. Called by the Flutter mobile app (every 60 seconds) and by the HTMX now-playing strip (every 60 seconds via `hx-trigger`).

**Resolution logic:**

```python
def resolve_now_playing(tenant_id):
    now = timezone.now()
    tenant = Tenant.objects.get(id=tenant_id)

    # 1. Check for scheduled slot
    slot = ChannelSlot.objects.filter(
        tenant=tenant,
        scheduled_start__lte=now,
        scheduled_end__gte=now,
        deleted_at__isnull=True,
    ).first()
    if slot:
        return build_slot_response(slot)

    # 2. Check for live broadcast override
    live = BroadcastSchedule.objects.filter(
        tenant=tenant,
        status='live',
        deleted_at__isnull=True,
    ).first()
    if live:
        return build_live_response(live)

    # 3. Fallback playlist
    config = getattr(tenant, 'channel_config', None)
    if config and config.fallback_playlist:
        video_id = config.fallback_playlist[config.fallback_position % len(config.fallback_playlist)]
        # advance position for next call
        ChannelConfig.objects.filter(pk=config.pk).update(
            fallback_position=config.fallback_position + 1
        )
        return build_vod_response(video_id, source='fallback')

    # 4. Loop default
    if config and config.loop_default_video_id:
        return build_vod_response(config.loop_default_video_id, source='loop')

    # 5. Offline
    return {'content_type': 'offline', 'title': None, 'video_url': None}
```

**Response schema:**

```json
{
    "content_type": "vod | live | offline",
    "source":        "scheduled | live | fallback | loop | offline",
    "title":         "string | null",
    "video_url":     "https://... | null",
    "hls_url":       "https://... | null",
    "is_live":       "boolean",
    "thumbnail_url": "https://... | null",
    "ends_at":       "ISO-8601 | null",
    "next_scheduled": {
        "title":     "string",
        "starts_at": "ISO-8601"
    }
}
```

### 4.4 Channel Scheduler — Architect Tool at app.ichebo.org

The channel scheduler is an Architect-only tool within the Apostolic Command Shell at `app.ichebo.org`. Participants never see it. Chizola uses it to programme the channel.

**Scheduler views:**

| View | URL (app.ichebo.org) | Purpose |
|---|---|---|
| Channel Overview | `/channel/` | List all ChannelSlots for the selected tenant, ChannelConfig summary |
| Add Slot | `/channel/slots/add/` | HTMX form: select tenant, content type, video, start/end datetime |
| Edit/Delete Slot | `/channel/slots/{id}/edit/` | Modify or remove a scheduled slot |
| Fallback Config | `/channel/config/{tenant_id}/` | Set loop default video, edit fallback playlist order |
| Preview Schedule | `/channel/preview/?tenant_id=` | 7-day view of scheduled content with gap indicators |

The scheduler uses the existing Apostolic Command Shell layout — no new shell required. HTMX handles form submission and slot list refresh inline. Gap indicators in the Preview Schedule view highlight time ranges with no scheduled slot (shown as orange cells), prompting the Architect to add fallback coverage or extend slots.

---

## Part 5 — Three-Tier Access Model

### 5.1 The Three Tiers

| Tier | Level | Primary surface | What they see |
|---|---|---|---|
| Participant | 0b–2 (see below — "0b" is a real, already-implemented state, not a `competence_level` value) | `sceptre.ichebo.org` consumer side + Flutter mobile | Channel, Community (read), Learn (Level 1+), Bible, Support |
| Community Steward | 3+ | `sceptre.ichebo.org` steward side (role-adaptive) | All participant access + member management, gathering scheduling, formation pipeline, certification queue, announcement authorship, support queue |
| Architect | 5 (Prime) | `app.ichebo.org` (primary) + `sceptre.ichebo.org` (steward-equivalent) | All steward access + channel scheduler, constitutional data, Handbook authorship, licence issuance, network-wide oversight |

**The 0a/0b distinction — resolved 2026-06-26, locked, not an open question.** v1.1 of this document mis-read this as a gap because `competence_level` is a single integer with no `'0a'`/`'0b'` value — true, but the distinction was never meant to live on `competence_level` at all. It is a second, already-implemented axis, confirmed directly in `community/views.py:my_community` (the existing `app.ichebo.org` Community home, which this surface's participant home replaces for Level 1+ users):

- **0a — Visitor.** `competence_level == 0`, **no** `UserPermission` on an `induction`-tier tenant at all. Has never entered the induction flow. Per the documented user journey (subdomain map: "Seeker arrives → `join.ichebo.org`"), a visitor's front door is `join.ichebo.org`, not `sceptre.ichebo.org` — they should not reach the channel-first participant home. `my_community`'s real behaviour for this state: `community/seeker_gate.html`.
- **0b — Seeker.** `competence_level == 0`, **has** an active `UserPermission` on an `induction`-tier tenant (placed in induction, not yet graduated to a real Sceptre Community). `my_community`'s real behaviour: `_render_induction_hub`. This is the lowest level that should reach `sceptre.ichebo.org`.
- **1+ — Member.** Has landed in a real, non-induction tenant — a Sceptre Community proper. This is the normal participant case.

**Locked gating rule for `sceptre.ichebo.org`'s participant gate:** `competence_level >= 1` **OR** an active `UserPermission` on an `induction`-tier tenant. A bare `competence_level == 0` with no induction placement (0a) is correctly excluded. See the corrected `sceptre/auth.py` in §5.2 below, which implements exactly this — it does not invent a fake level value, it checks the same two real conditions `my_community` already checks.

**How often 0a is actually reachable, found while verifying this fix against real data:** `accounts/signals.py:auto_place_new_user_in_induction_tenant` (a `post_save` signal on `User`) auto-places every newly-created account into the induction tenant the instant the row is created — so in normal operation, there is no authenticated user who is genuinely 0a; by the time a `User` exists at all, they're already 0b. The 0a branch (`seeker_gate.html` in `my_community`, and the `PermissionDenied` path in the gate above) is real defensive code for a genuine edge case — the signal's own `if not induction_tenant: ... return` fallback (induction tenant missing or misconfigured) or a legacy account created before this signal existed — not a state most users pass through. Confirmed with Chizola (2026-06-26): keep the gate exactly as specified above: it is correct either way, and the edge case is real even though it's rare.

### 5.2 Gating Rules

**sceptre.ichebo.org — view-level gating**, corrected to real field types, the real `STEWARD_ROLES` set (`tenants/models.py`, added 2026-06-24), and the real 0a/0b distinction (resolved above, not modeled as a fake level value):

```python
# sceptre/auth.py
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from tenants.models import UserPermission

STEWARD_LEVELS = (3, 4, 5)


def _is_seeker_or_above(user):
    """0b+ — the real participant gate. Level 1+ always passes. A
    competence_level == 0 user only passes if they have an active
    UserPermission on an induction-tier tenant (placed in induction —
    'seeker', 0b) rather than no placement at all ('visitor', 0a, whose
    front door is join.ichebo.org, not this surface). Mirrors
    community/views.py:my_community's existing Level-0 branch exactly —
    not a new rule, the same one already enforced at app.ichebo.org."""
    if user.competence_level >= 1:
        return True
    return UserPermission.objects.filter(
        user=user, tenant__tier='induction', is_active=True,
    ).exists()


def require_sceptre_participant(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _is_seeker_or_above(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def require_sceptre_steward(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        level_ok = user.competence_level in STEWARD_LEVELS
        role_ok = UserPermission.objects.filter(
            user=user,
            role__in=UserPermission.STEWARD_ROLES,   # includes 'admin' — role__endswith='-steward' silently excludes it
            is_active=True,
        ).exists()
        if not (level_ok or role_ok):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
```

`login_required` (Django's own decorator) replaces the manual `if not request.user.is_authenticated: return redirect('/login/')` check — same effect, standard idiom, one fewer thing to get wrong (e.g. the real login URL is `/accounts/login/`, not `/login/` — confirmed via `accounts/urls.py` — so the hand-written redirect in v1.0 would have 404'd).

**What a 0a visitor sees if they reach `sceptre.ichebo.org` anyway** (e.g. a stale bookmark, or arriving before completing `join.ichebo.org`'s flow): `PermissionDenied` — Django's default 403 page, or a custom one if `sceptre`'s own `urls.py` wires a handler. Not redirected to `join.ichebo.org` automatically in this pass; that redirect is a reasonable follow-up but is new scope beyond what was asked, not assumed here.

**app.ichebo.org — what moves, what stays, what is new:**

| Area | Status | Notes |
|---|---|---|
| Apostolic Command Shell | Stays — evolves | Remains the governance workspace. Gains channel scheduler section. |
| Governance (Handbook, Reference, Mandate, Keys) | Stays | Unchanged. Level 3–5 gated as before. |
| Learn formation pipeline (authorship) | Stays | Lesson authorship, programme management — Level 4+. |
| Activity (Ministry campaigns) | Stays | Ministry-level activity management — Level 3+. |
| Paraclete digest | Stays | Level 3+, existing digest interface. |
| Network-wide oversight | Stays | District/global tenant views — Level 4–5. |
| Channel Scheduler | New — at app.ichebo.org | ChannelConfig + ChannelSlot management. Level 5 / Architect only. |
| DesktopLicence issuance | Stays | Level 5 only. |

**What does NOT belong in the participant front door:**

- DAR (Daily Analysis Record) — a high-level formation discipline tool, not a participant front-door feature
- Activity (Ministry campaigns, tasks) — steward/architect tooling
- Records & Journals — accessible from profile/explore, not the front door
- Governance Library — steward and architect tooling only
- Paraclete digest — Level 3+ only

---

## Part 6 — Community Support Feature

> **—— Already shipped (backend) — H.3, `commit 16bfbab`, 2026-06-22**
>
> **Visual reference for the still-to-build `sceptre.ichebo.org` front end:** `sceptre_comm_web-ui_mockup/02-sceptre-community-support.html`, **Screen C only** ("Member support request list"). Screens A and B in that same file are the Community Chat feature (Part 7 below, H.5), not Community Support — the mockup file bundles both features under one filename; cite it by screen letter, not just filename, to avoid confusion. Screen C shows the real shape: a "My Requests" list with status badges (Acknowledged/Open/Resolved), an overdue flag, and a "+ Raise a Request" button — matches this part's URL table below. The steward-facing queue (with the overdue banner and SLA countdown) is in Mockup 03, Screen B — see Part 3.4's note.

Community Support is fully specified in the Community App — Member-to-Steward Support Requests — Roadmap Amendment (`community-support-requests-plan.md`, approved 2026-06-18) **and the backend is already built and live in production.** This part summarises the spec for completeness and notes its placement within the `sceptre.ichebo.org` surface — the front-end URLs in §6.3 below do not exist yet, since `sceptre.ichebo.org` itself hasn't been built (H.6). The real backend implementation — `community/services.py:resolve_steward_for_tenant`, `community/views.py`'s support-request views, `/community/support/` (the existing, working URL at `app.ichebo.org` today) — is authoritative; the H.3 phase-plan document in this folder describes the work as not-yet-started and should be read as historical/superseded, not as a build checklist.

### 6.1 What It Is

A structured channel for members to raise something to leadership attention. A support ticket pattern — not social messaging. Member submits a request; it routes to their community steward; the steward sees it in a queue with SLA tracking.

### 6.2 Data Shape (Summary)

Uses the existing `Record` model with no schema change:

- `record_class: 'organizational'`
- `record_family: 'community'`
- `record_type: 'support_request'`
- `custom_fields: { response_due_at, acknowledged_at, resolved_at, assigned_steward_id }`
- Status lifecycle: `draft → submitted → active (acknowledged) → completed`

### 6.3 Surface on sceptre.ichebo.org

| URL | View | Who sees it |
|---|---|---|
| `/support/` | My support requests list + 'Raise a request' button | All participants |
| `/support/new/` | HTMX form: subject + body | All participants |
| `/support/{id}/` | Request detail — participant read-only | Request creator only |
| `/steward/support/` | Steward queue — all open requests, SLA status, overdue flagging | Stewards (Level 3+) |
| `/steward/support/{id}/` | Request detail — steward response form | Stewards (Level 3+) |

The `/support/` participant URLs are the `sceptre.ichebo.org` implementation of the H.3 plan's Community app FAB sheet and 'My Requests' list, mapped to the new subdomain's URL structure. The steward queue at `/steward/support/` maps to the H.3 plan's `/community/support/` view.

---

## Part 7 — Community Chat / Intranet

### 7.1 Decision: Spec Now, Defer Build

Community Support (Part 6 / H.3) covers the structured member-to-leadership channel — the primary accountability need for the pilot. Community Chat is a different, additive social surface. Building it now risks absorbing engineering time needed for the formation and certification flow that is the pilot's actual deliverable. Decision: lock the spec in this document, defer build to Phase H.5 (after H.3 completes).

### 7.2 What Community Chat Is (Locked Spec)

> **Visual reference:** `sceptre_comm_web-ui_mockup/02-sceptre-community-support.html`, **Screens A and B** ("Community noticeboard feed" and "Post detail with flat comments and response form") — despite the filename, these two screens are Community Chat, not Community Support (Screen C in the same file is Support — see Part 6's note). Matches the locked spec below: steward-authored posts in a flat feed, post detail with a flat (non-nested) comment list and a single response textarea.

A tenant-scoped community noticeboard with member responses. Not a real-time chat system. Not threaded conversation. Closer to a community feed — stewards post, members respond, the community stays connected between gatherings.

**Scope boundary (what it is not):**

- Not real-time — no WebSockets, no Django Channels (those are L10.3)
- Not threaded — flat responses only, no nesting
- Not a full social network — tenant-scoped only, no cross-community visibility
- Not a direct messaging system — all posts are visible to the whole tenant

**Data shape** (ADR-003 followed — no new models):

- `community_post`: `record_class='organizational'`, `record_family='community'`, `record_type='community_post'`. Create = Level 1+. Steward-moderated.
- `community_comment`: `record_class='organizational'`, `record_family='community'`, `record_type='community_comment'`. `custom_fields: { parent_post_id: uuid }`. Create = Level 1+.

Both use the existing `Record.status` lifecycle. A `community_post` in `'draft'` status is not visible. In `'active'` status it is visible to all tenant members.

**Surface on sceptre.ichebo.org (when built):**

| URL | View | Who |
|---|---|---|
| `/community/` | Community feed — list of `community_post` records + comment count | All participants |
| `/community/post/{id}/` | Post detail + flat comment list + comment form | All participants |
| `/community/post/new/` | New post form (HTMX) | Level 1+ or steward |
| `/steward/community/` | Moderation queue — pending posts, flagged content | Stewards (Level 3+) |

---

## Part 8 — Architecture Decision Records

### ADR-023 — Subdomain Separation: sceptre.ichebo.org

| Field | Value |
|---|---|
| Number | ADR-023 (renumbered from the v1.0 draft's ADR-022, which collides with the already-approved 2026-06-09 ADR-022 — Handbook/Governance separation) |
| Title | Subdomain separation — sceptre.ichebo.org as community surface |
| Status | Approved — 2026-06-25, renumbered 2026-06-26 |
| Context | The Ichebo platform now serves two distinct user populations with different design needs: participants in the Sceptre Community Programme (consumer experience) and the Architect/stewards managing governance operations. `app.ichebo.org` is the Apostolic Command Shell — governance-dense, Level 3+. A separate, consumer-oriented surface is needed for participants. |
| Decision | `sceptre.ichebo.org` is served from the same Django codebase via subdomain-aware URL routing and a custom `SiteRouterMiddleware`. No Django multi-site framework. A new URL conf (`sceptre/urls.py`) and a new, additive template directory (`templates/sceptre/`) — the existing flat `templates/` tree is untouched, not relocated. The same models, database, and authentication underpin both subdomains. ADR-005 (Django templates + HTMX) is extended to cover `sceptre.ichebo.org` — no new frontend technology is introduced. |
| Consequences | One new `server {}` block pair (HTTP redirect + HTTPS) added to the existing single Nginx config file (`/etc/nginx/sites-available/ics`) — not a separate file. `SiteRouterMiddleware` sets `request.site` and `request.urlconf` on every request; Django's resolver picks up `request.urlconf` automatically, no dispatcher function needed. Template isolation prevents accidental cross-surface template reuse. SSL certificate via certbot. DNS A record for `sceptre.ichebo.org` already live, points to the same Django VPS. `sceptre.ichebo.org` must be added to `ALLOWED_HOSTS` in production's `.env` (currently only lists `app.ichebo.org,ichebo.org,www.ichebo.org`). |
| Alternatives rejected | Django multi-site framework: built for separate projects sharing a DB — adds unnecessary complexity. Separate Django process: doubles infrastructure, complicates deployment, shared session/auth becomes harder to manage. |

### ADR-024 — Ichebo Channel Architecture

| Field | Value |
|---|---|
| Number | ADR-024 (renumbered from the v1.0 draft's ADR-023, shifted by the ADR-022 renumbering above) |
| Title | Ichebo Channel — continuous broadcast channel architecture |
| Status | Approved — 2026-06-25, renumbered 2026-06-26 |
| Context | The participant experience requires a channel-first design — video playing immediately when the app opens or the home page loads, without navigation required. A scheduled playlist with live override and fallback hierarchy is the correct model. The existing `BroadcastSchedule` handles individual live events but not continuous channel programming. |
| Decision | A new `broadcast` Django app provides `ChannelConfig` (per-tenant channel configuration: loop default, fallback playlist) and `ChannelSlot` (programme grid slots with scheduled start/end, content type, content reference). A now-playing endpoint (`GET /api/broadcast/now/?tenant_id=`) resolves the current content using a four-level fallback hierarchy: (1) scheduled `ChannelSlot`, (2) live `BroadcastSchedule` override, (3) `ChannelConfig.fallback_playlist` rotation, (4) `ChannelConfig.loop_default`. The channel scheduler UI lives exclusively at `app.ichebo.org` as an Architect tool (Level 5). |
| Consequences | `ChannelConfig` and `ChannelSlot` are configuration models — ADR-003 does not apply. Two new migrations. `GET /api/broadcast/now/` added to the DRF API. Mobile polls every 60s. Web HTMX polls every 60s. Content sources are VOD records from Ichebo Media (already built) and `BroadcastSchedule` live events (already built). No new video infrastructure required. |
| Alternatives rejected | Records table slot entries: `ChannelSlot` is configuration, not content — using the records table would force `record_class`/`record_family` onto a concept that is not a governed content object. True RTMP 24/7 stream: requires always-on FFmpeg transcoding — enormous infrastructure cost. The scheduled-playlist model achieves the same UX at negligible infrastructure cost. |

---

## Part 9 — Data Contract v12 Amendments

The following amendments are required to `data-contract-v11-canonical-2026-05-13.md` to produce v12. v12 inherits all v11 content unchanged except where explicitly noted.

**Part 1 — Core Principles (amendment):**
Add to the Architecture statement: *"`sceptre.ichebo.org` is the Sceptre Community surface — a role-adaptive Django surface serving participants (Level 0–2) and stewards (Level 3+). Served from the same Django codebase as `app.ichebo.org` via subdomain-aware URL routing (ADR-023)."*

**Part 20 — Complete Endpoint Reference (additions):**

| App | New endpoints |
|---|---|
| Broadcast | `GET /api/broadcast/now/?tenant_id={uuid}` |
| Broadcast | `POST /api/broadcast/channel-config/` (Architect only — create ChannelConfig) |
| Broadcast | `PATCH /api/broadcast/channel-config/{id}/` (Architect only — update) |
| Broadcast | `GET/POST /api/broadcast/slots/?tenant_id={uuid}` (Architect only) |
| Broadcast | `PATCH/DELETE /api/broadcast/slots/{id}/` (Architect only) |

**New Part 24 — Broadcast Channel Data Contracts:**
Add Part 24 with the `ChannelConfig` and `ChannelSlot` model schemas, the now-playing response schema, and the fallback resolution algorithm. These schemas are fully specified in Part 4 of this document (DOC J).

**Part 14 additions — Community record types:**

- `community_post`: `record_class='organizational'`, `record_family='community'`, `record_type='community_post'`. Create = Level 1+. Read = Level 1+ within tenant. Steward-moderated (status transitions by Level 3+).
- `community_comment`: `record_class='organizational'`, `record_family='community'`, `record_type='community_comment'`. `custom_fields: { parent_post_id: uuid }`. Create = Level 1+. Read = Level 1+ within tenant.
- `support_request` is already shipped (H.3, `commit 16bfbab`, 2026-06-22) per `community-support-requests-plan.md` — include as a formal data contract entry in v12, documenting existing behaviour rather than planned behaviour.

**ADR cross-reference table additions:**
- ADR-023: Architecture statement — `sceptre.ichebo.org` subdomain separation
- ADR-024: Part 24 — Broadcast channel data contracts

---

## Part 10 — Master Roadmap Amendment

### 10.1 Phases — Status Corrected 2026-06-26

| Phase | Name | Status | Dependency | Commit |
|---|---|---|---|---|
| H.3 | Community Support Requests | **Already shipped** — `commit 16bfbab`, 2026-06-22 | Community App complete — no new infra. | `feat: add member-to-steward support request flow with SLA tracking` |
| H.4 | Community Live Service Room + In-Service Ministry Panel | **Already shipped** — `commit d6a7854`, 2026-06-22; tenant-scoping and timezone bugs corrected in `commit 67878ba`-adjacent work, 2026-06-24/25 | Ichebo Media deployed (Layer 8 complete). | `feat: add tenant-scoped live service room + in-service ministry panel` |
| H.5 | Community Chat / Intranet | Not started | H.3 complete (it is). No new infra — Record table, no WebSockets. | `feat(community): tenant-scoped community noticeboard with member responses` |
| H.6 | sceptre.ichebo.org surface + Participant Home | Not started. DNS for `sceptre.ichebo.org` confirmed live 2026-06-26 — no longer a precondition. | Ichebo Channel (H.7) must be in progress or complete. | `feat(sceptre): sceptre.ichebo.org shell, participant home, steward side` |
| H.7 | Ichebo Channel — broadcast Django app + now-playing endpoint | Not started | Ichebo Media complete (Layer 8). No new infra. | `feat(broadcast): ChannelConfig, ChannelSlot, now-playing endpoint, channel scheduler UI` |

### 10.2 Sequencing Rationale (corrected)

H.3 and H.4 are already built and in production — they are not part of the remaining sequence. The remaining work is H.7 then H.6 then H.5, in that order: H.7 first because the channel backend must exist before the `sceptre.ichebo.org` shell can display it (the participant home screen's video player calls `GET /api/broadcast/now/`, which doesn't exist until H.7 ships). H.6 second — it is the surface that ties everything together, and is the highest-value remaining piece since it's the actual pilot-facing deliverable. H.5 (Community Chat) last — it's additive, lower urgency, and explicitly deferred in the original session ("spec now, defer build," Part 7.1) until the structured channels (Support, Live Service — both already shipped) are proven.

### 10.3 Pilot Readiness Plan Amendment

The pilot readiness plan (v1, 2026-05-24) identified API versioning (`/api/v1/`) as the sole technical blocker for pilot launch. That remains true. The phases defined here (H.3–H.7) are the Wave 3+ build work that strengthens the pilot experience. The sequencing from this document supersedes the Wave 3 community features list in the pilot readiness plan where they overlap.

The `sceptre.ichebo.org` surface (H.6) is a significant addition to pilot scope — it was not contemplated in the original pilot readiness plan. It is the correct move: the pilot should give participants a purpose-built consumer experience, not the governance-dense Apostolic Command Shell. H.6 should be prioritised accordingly.

---

## Part 11 — Nginx and Deployment Notes

### 11.1 SSL Certificate

```bash
certbot --nginx -d sceptre.ichebo.org
```

Certbot will automatically add the `ssl_certificate` and `ssl_certificate_key` directives and configure the HTTPS redirect.

### 11.2 Django ALLOWED_HOSTS

```python
ALLOWED_HOSTS = ['app.ichebo.org', 'sceptre.ichebo.org', '127.0.0.1']
```

### 11.3 Session Cookie

**Locked, 2026-06-26 (Chizola): shared login across both subdomains.** `SESSION_COOKIE_DOMAIN` is set to `.ichebo.org` (with leading dot), allowing a session cookie shared across both subdomains — a steward logs in once, on either subdomain, and is authenticated on both.

```python
if not DEBUG:
    SESSION_COOKIE_DOMAIN = '.ichebo.org'
    CSRF_COOKIE_DOMAIN = '.ichebo.org'
```

Guarded by `not DEBUG` — Django's test client doesn't set domain cookies, which would otherwise break the H.6 test suite (Task 6).

### 11.4 Static Files

Both subdomains serve static files from the same Django staticfiles directory. No change to the existing staticfiles configuration.

### 11.5 Deploy Script

The existing `deploy-site.sh` script deploys to both subdomains — no separate deploy process. Gunicorn serves both from one process. The deploy script restarts Gunicorn once; both subdomains go live together.

---

## Part 12 — Exit Criteria

### H.6 — sceptre.ichebo.org surface

- [ ] `sceptre.ichebo.org` resolves with valid SSL certificate
- [ ] `SiteRouterMiddleware` sets `request.site = 'community'` for `sceptre.ichebo.org` requests
- [ ] `sceptre/urls.py` routes participant and steward URLs correctly
- [ ] Participant home (`/`) renders with channel video player, now-playing strip, four quick-access tiles
- [ ] Steward navigation section visible only to Level 3+ users
- [ ] All participant views return 403 / login redirect for unauthenticated requests
- [ ] All steward views return 403 for Level 0–2 users
- [ ] `python manage.py check` — 0 issues
- [ ] Templates isolated: `templates/sceptre/` renders correctly, no bleed from the existing flat `templates/` tree

### H.7 — Ichebo Channel

- [ ] `broadcast` Django app created with `ChannelConfig` and `ChannelSlot` models
- [ ] Migrations run cleanly against the production schema
- [ ] `GET /api/broadcast/now/?tenant_id={uuid}` returns correct content for each fallback level
- [ ] Level 1: `ChannelSlot` resolution returns scheduled content when a slot is active
- [ ] Level 2: `BroadcastSchedule` live override returns live stream URL
- [ ] Level 3: Fallback playlist rotation advances `fallback_position` on each call
- [ ] Level 4: Loop default returns loop default video URL
- [ ] Level 5 (offline): Returns `content_type='offline'` with null `video_url`
- [ ] Channel scheduler UI at `app.ichebo.org` — add/edit/delete `ChannelSlot`, edit `ChannelConfig`
- [ ] Channel scheduler is not accessible to Level 0–4 users
- [ ] `python manage.py check` — 0 issues
- [ ] 10 passing tests covering the resolution logic and all fallback levels

### Overall

- [ ] Data contract v12 produced with all amendments noted in Part 9
- [ ] ADR-023 and ADR-024 written and added to the ADR document
- [ ] Master roadmap updated with H.5, H.6, H.7 phase entries — H.3 and H.4 are already complete and need only a status-correction note, not a new entry

---

*DOC J — Sceptre Community Surface + Ichebo Channel + Access Model*
*Version 1.0 — 2026-06-25 — Ichebo Christian Services*
*Canonical Reference — supersedes all prior session notes on this topic*
