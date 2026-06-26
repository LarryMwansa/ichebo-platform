# Sceptre Community Surface + Ichebo Channel + Access Model

> **—— SYSTEM DESIGN DOCUMENT**

| Field | Value |
|---|---|
| Document | DOC J — Sceptre Community Surface, Ichebo Channel, Access Model |
| Version | 1.0 — 2026-06-25 |
| Status | Approved — Canonical Reference |
| ADR reference | ADR-022 (subdomain separation), ADR-023 (Ichebo Channel architecture) |
| Data contract | data-contract-v11-canonical-2026-05-13.md — v12 amendments noted |
| Roadmap | Master Roadmap v7 — Phases H.3, H.4, H.5 (new) |
| Depends on | DOC G (Ichebo Media), ADR-001–021, Community Support Plan (H.3), Community Live Service Room Plan (H.4), Video Direction v2 Plan |
| Authors | Chizola (domain); Claude (technical) |

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

## Part 2 — Subdomain Architecture (ADR-022)

### 2.0 Full Subdomain Topology

The Ichebo ecosystem spans two physical servers. All subdomains are documented here to prevent ambiguity when configuring Nginx, DNS, or SSL certificates.

**Django VPS — `37.27.82.169` (platform VPS, existing)**

| Subdomain | Purpose | Routes to |
|---|---|---|
| `app.ichebo.org` | Agency / Architect surface — Apostolic Command Shell | Gunicorn `127.0.0.1:8000` |
| `sceptre.ichebo.org` | Sceptre Community surface — participant + steward (new) | Gunicorn `127.0.0.1:8000` (same process) |

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
- A custom middleware reads `request.get_host()` and sets `request.site = 'agency' | 'community'`
- Django's `ROOT_URLCONF` routes to a dispatcher that delegates per host
- `agency_urls.py` handles `app.ichebo.org` — existing URL patterns, unchanged
- `sceptre_urls.py` handles `sceptre.ichebo.org` — new URL patterns
- Templates live in `templates/agency/` and `templates/sceptre/` — separate shells, shared HTMX patterns
- Same `User`, `UserPermission`, `Record`, `Activity` models underpin both

**Nginx configuration:**

```nginx
# /etc/nginx/sites-available/app.ichebo.org (existing — unchanged)
server {
    server_name app.ichebo.org;
    location / { proxy_pass http://127.0.0.1:8000; }
}

# /etc/nginx/sites-available/sceptre.ichebo.org (new)
server {
    listen 80;
    server_name sceptre.ichebo.org;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

SSL via certbot (same as existing subdomains). DNS: A record for `sceptre.ichebo.org` pointing to the same Django VPS IP as `app.ichebo.org`.

**Django settings and middleware:**

```python
# settings.py
ALLOWED_HOSTS = [
    'app.ichebo.org',
    'sceptre.ichebo.org',
    '127.0.0.1',
    'localhost',
]

# middleware/site_router.py
class SiteRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        if host == 'sceptre.ichebo.org':
            request.site = 'community'
        else:
            request.site = 'agency'
        return self.get_response(request)

# ichebo_platform/urls.py
def get_urlconf(request):
    if getattr(request, 'site', 'agency') == 'community':
        return 'sceptre.urls'
    return 'agency.urls'
```

**Template directory structure:**

```
templates/
├── agency/           # app.ichebo.org templates (existing, relocated)
│   ├── base.html     # Apostolic Command Shell base
│   ├── _sidebar.html
│   └── [app templates]
└── sceptre/          # sceptre.ichebo.org templates (new)
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
| Participant | competence_level 0b–2 | Consumer side: Channel, Community (read), Learn, Bible, Support |
| Community Steward | competence_level >= 3 OR `UserPermission.role` endswith `'-steward'` | All participant access + steward management panel |
| Architect | competence_level == 5 AND is_prime_tenant | Does not use `sceptre.ichebo.org` as primary — works from `app.ichebo.org`; can access `sceptre.ichebo.org` as a steward-equivalent if needed |

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

The channel video window is the first and dominant element on the participant Home screen. It is not a card, not a thumbnail, not a poster image — it is an actively playing video. The participant opens the app or visits `sceptre.ichebo.org/home/` and the channel is already playing.

**Web Home Layout (`sceptre.ichebo.org/home/`):**

Layout uses a single column, max content width 800px, centred. From top to bottom:

1. Channel video player — full width, 16:9 aspect ratio, autoplay muted (browser policy). Now-playing title and live badge (if live) displayed below the player frame. 'Tap to unmute' prompt on first load.
2. Now-playing strip — slim row beneath the video: channel name/label, current content title, ends-at time (or 'LIVE' badge if live). Left red rule accent on the live badge.
3. Next up — single-line teaser: next scheduled item title and start time. Only shown if `ChannelSlot` exists.
4. Four compact tiles in a 2×2 grid — Community, Learn, Bible, Support. Each tile: icon (48px), label (Inter 600 14px), brief status line (latest announcement / next lesson / current passage / open requests). Stone surface, left red rule on hover.

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

When a Level 3+ user or `-steward` role holder logs in to `sceptre.ichebo.org`, the shell gains a steward panel. On web, this appears as an additional navigation section below the participant nav items, labelled 'Community Management'. On mobile (Flutter), a sixth nav tab appears — 'Manage' — gated by the same competence level check.

**Steward navigation additions (web):**

| Nav item | URL | Purpose |
|---|---|---|
| Members | `/steward/members/` | Member roster, competence levels, shepherd assignments |
| Gatherings | `/steward/gatherings/` | Schedule gatherings, link to BroadcastSchedule for digital |
| Formation | `/steward/formation/` | Induction queue, active programmes, certification queue |
| Announcements | `/steward/announcements/` | Author and publish community announcements |
| Support Queue | `/steward/support/` | All open support requests, SLA status, assignment |
| Community Settings | `/steward/settings/` | Community profile, ChannelConfig (if tenant has channel) |

The steward navigation section is separated from the participant navigation by a visual divider and a label tag ('—— COMMUNITY MANAGEMENT'). On mobile, the Manage tab opens a bottom sheet with these six options, following the existing FAB sheet pattern.

---

## Part 4 — Ichebo Channel Architecture (ADR-023)

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
    # FK to video_live VideoRecord or media VideoRecord — resolved at read time
    fallback_playlist     = models.JSONField(default=list)
    # Ordered list of VideoRecord UUIDs (strings)
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
    # UUID of the VideoRecord for vod content_type
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
| Participant | 0b–2 | `sceptre.ichebo.org` consumer side + Flutter mobile | Channel, Community (read), Learn (Level 1+), Bible, Support |
| Community Steward | 3+ | `sceptre.ichebo.org` steward side (role-adaptive) | All participant access + member management, gathering scheduling, formation pipeline, certification queue, announcement authorship, support queue |
| Architect | 5 (Prime) | `app.ichebo.org` (primary) + `sceptre.ichebo.org` (steward-equivalent) | All steward access + channel scheduler, constitutional data, Handbook authorship, licence issuance, network-wide oversight |

### 5.2 Gating Rules

**sceptre.ichebo.org — view-level gating:**

```python
# sceptre/auth.py
from functools import wraps
from django.core.exceptions import PermissionDenied

def require_sceptre_participant(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        if request.user.competence_level not in ['0b','1','2','3','4','5']:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

def require_sceptre_steward(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        level_ok = request.user.competence_level in ['3','4','5']
        role_ok = UserPermission.objects.filter(
            user=request.user,
            role__endswith='-steward',
            is_active=True
        ).exists()
        if not (level_ok or role_ok):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
```

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

> **—— Already approved — H.3 plan**

Community Support is fully specified in the Community App — Member-to-Steward Support Requests — Roadmap Amendment (`community-support-requests-plan.md`, approved 2026-06-18). This part summarises the spec for completeness and notes its placement within the `sceptre.ichebo.org` surface. The H.3 plan document is authoritative for implementation detail.

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

### ADR-022 — Subdomain Separation: sceptre.ichebo.org

| Field | Value |
|---|---|
| Number | ADR-022 |
| Title | Subdomain separation — sceptre.ichebo.org as community surface |
| Status | Approved — 2026-06-25 |
| Context | The Ichebo platform now serves two distinct user populations with different design needs: participants in the Sceptre Community Programme (consumer experience) and the Architect/stewards managing governance operations. `app.ichebo.org` is the Apostolic Command Shell — governance-dense, Level 3+. A separate, consumer-oriented surface is needed for participants. |
| Decision | `sceptre.ichebo.org` is served from the same Django codebase via subdomain-aware URL routing and a custom `SiteRouterMiddleware`. No Django multi-site framework. Separate URL confs (`sceptre/urls.py`) and template directories (`templates/sceptre/`). The same models, database, and authentication underpin both subdomains. ADR-005 (Django templates + HTMX) is extended to cover `sceptre.ichebo.org` — no new frontend technology is introduced. |
| Consequences | One Nginx server block added for `sceptre.ichebo.org`. `SiteRouterMiddleware` sets `request.site` on every request. URL dispatcher routes per host. Template isolation prevents accidental cross-surface template reuse. SSL certificate via certbot. DNS A record for `sceptre.ichebo.org` points to same Django VPS. |
| Alternatives rejected | Django multi-site framework: built for separate projects sharing a DB — adds unnecessary complexity. Separate Django process: doubles infrastructure, complicates deployment, shared session/auth becomes harder to manage. |

### ADR-023 — Ichebo Channel Architecture

| Field | Value |
|---|---|
| Number | ADR-023 |
| Title | Ichebo Channel — continuous broadcast channel architecture |
| Status | Approved — 2026-06-25 |
| Context | The participant experience requires a channel-first design — video playing immediately when the app opens or the home page loads, without navigation required. A scheduled playlist with live override and fallback hierarchy is the correct model. The existing `BroadcastSchedule` handles individual live events but not continuous channel programming. |
| Decision | A new `broadcast` Django app provides `ChannelConfig` (per-tenant channel configuration: loop default, fallback playlist) and `ChannelSlot` (programme grid slots with scheduled start/end, content type, content reference). A now-playing endpoint (`GET /api/broadcast/now/?tenant_id=`) resolves the current content using a four-level fallback hierarchy: (1) scheduled `ChannelSlot`, (2) live `BroadcastSchedule` override, (3) `ChannelConfig.fallback_playlist` rotation, (4) `ChannelConfig.loop_default`. The channel scheduler UI lives exclusively at `app.ichebo.org` as an Architect tool (Level 5). |
| Consequences | `ChannelConfig` and `ChannelSlot` are configuration models — ADR-003 does not apply. Two new migrations. `GET /api/broadcast/now/` added to the DRF API. Mobile polls every 60s. Web HTMX polls every 60s. Content sources are VOD records from Ichebo Media (already built) and `BroadcastSchedule` live events (already built). No new video infrastructure required. |
| Alternatives rejected | Records table slot entries: `ChannelSlot` is configuration, not content — using the records table would force `record_class`/`record_family` onto a concept that is not a governed content object. True RTMP 24/7 stream: requires always-on FFmpeg transcoding — enormous infrastructure cost. The scheduled-playlist model achieves the same UX at negligible infrastructure cost. |

---

## Part 9 — Data Contract v12 Amendments

The following amendments are required to `data-contract-v11-canonical-2026-05-13.md` to produce v12. v12 inherits all v11 content unchanged except where explicitly noted.

**Part 1 — Core Principles (amendment):**
Add to the Architecture statement: *"`sceptre.ichebo.org` is the Sceptre Community surface — a role-adaptive Django surface serving participants (Level 0b–2) and stewards (Level 3+). Served from the same Django codebase as `app.ichebo.org` via subdomain-aware URL routing (ADR-022)."*

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
- `support_request` is specified in the H.3 plan (`community-support-requests-plan.md`) — include as a formal data contract entry in v12.

**ADR cross-reference table additions:**
- ADR-022: Architecture statement — `sceptre.ichebo.org` subdomain separation
- ADR-023: Part 24 — Broadcast channel data contracts

---

## Part 10 — Master Roadmap Amendment

### 10.1 New Phases

| Phase | Name | Dependency | Commit |
|---|---|---|---|
| H.3 | Community Support Requests | Community App complete — no new infra. Plan approved 2026-06-18. | `feat(community): support request flow — member-to-steward with SLA tracking` |
| H.4 | Community Live Service Room + In-Service Ministry Panel | Ichebo Media deployed (Layer 8 complete). Plan approved 2026-06-18. | `feat(community): tenant-scoped live service room and ministry panel` |
| H.5 | Community Chat / Intranet | H.3 complete. No new infra — Record table, no WebSockets. | `feat(community): tenant-scoped community noticeboard with member responses` |
| H.6 | sceptre.ichebo.org surface + Participant Home | Ichebo Channel (H.7) must be in progress or complete. | `feat(sceptre): sceptre.ichebo.org shell, participant home, steward side` |
| H.7 | Ichebo Channel — broadcast Django app + now-playing endpoint | Ichebo Media complete (Layer 8). No new infra. | `feat(broadcast): ChannelConfig, ChannelSlot, now-playing endpoint, channel scheduler UI` |

### 10.2 Sequencing Rationale

H.3 first — Community Support is simpler, already fully specced, and delivers immediate pilot value (members can reach leadership). H.4 second — Live Service Room completes the live service experience for existing communities. H.5 third — Community Chat adds the social layer after the structured channels are proven. H.7 in parallel with or just before H.6 — the channel backend must exist before the `sceptre.ichebo.org` shell can display it. H.6 last in this sequence — it is the surface that ties everything together.

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

`SESSION_COOKIE_DOMAIN` must be set to `.ichebo.org` (with leading dot) to allow a session cookie shared across both subdomains. This allows a steward to be logged in once and access both surfaces.

```python
SESSION_COOKIE_DOMAIN = '.ichebo.org'
CSRF_COOKIE_DOMAIN = '.ichebo.org'
```

If subdomain isolation is preferred for security, omit these settings — users will need to log in separately on each subdomain, which is acceptable for the pilot.

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
- [ ] All steward views return 403 for Level 0b–2 users
- [ ] `python manage.py check` — 0 issues
- [ ] Templates isolated: `templates/sceptre/` renders correctly, no bleed from `templates/agency/`

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
- [ ] Channel scheduler is not accessible to Level 0b–4 users
- [ ] `python manage.py check` — 0 issues
- [ ] 10 passing tests covering the resolution logic and all fallback levels

### Overall

- [ ] Data contract v12 produced with all amendments noted in Part 9
- [ ] ADR-022 and ADR-023 written and added to the ADR document
- [ ] Master roadmap updated with H.3–H.7 phase entries

---

*DOC J — Sceptre Community Surface + Ichebo Channel + Access Model*
*Version 1.0 — 2026-06-25 — Ichebo Christian Services*
*Canonical Reference — supersedes all prior session notes on this topic*
