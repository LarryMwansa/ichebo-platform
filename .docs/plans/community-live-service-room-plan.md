# Community App — Tenant-Scoped Live Service Room + In-Service Ministry Panel — Roadmap Amendment

**Version:** 1.0 — 2026-06-18
**Status:** Approved — pending implementation scheduling
**Reference documents:** Master Roadmap v7 (Video/Live App feature table, Community App feature table), DOC G — Ichebo Media Product Specification v1.0 (`.docs/2026-05-13-ichebo-media-spec_doc-g_v1.0.md`), Ecosystem Architecture v0.1 Part IV — Separation of Concerns (`.docs/2026-05-13-ichebo-ecosystem-architecture_v0.1.md`), ADR-021, `video_live/models.py`, `video_live/views.py`, `video_live/api_views.py`, `community/models.py`, `community/views.py`, `notifications/service.py`
**Author:** Claude (technical) — reviewed by Chizola

---

## What This Document Is

A roadmap amendment to the Video/Live App and Community App: a per-tenant "attend our service" room, where members of a specific community watch their own community's live broadcast (not a global feed of every tenant's broadcasts), with a steward-staffed ministry panel alongside the video for prayer requests and questions raised during the service.

This does not replace `video_live` — the Go Media Engine, RTMP ingest, HLS delivery, and `BroadcastSchedule` model stay exactly as they are. This adds a Community-scoped consumption surface on top of that existing engine, and a new lightweight interaction model for in-service requests.

---

## The Problem This Solves

Chizola's framing: video already serves Learn (lesson embeds), should serve team conferencing later, and should give a community/tenant "remote/online capacity to host church services" with a steward "ministering to needs for the attendants where prayer requests, questions etc." during the session.

A technical audit (2026-06-18) found two problems that make this currently impossible to do safely:

1. **No tenant scoping exists anywhere in the viewing path.** `BroadcastSchedule.tenant` (`video_live/models.py:23-24`) is a required, protected FK — the data model assumes every broadcast belongs to one tenant. But:
   - `video_live/views.py:_event_qs()` (used by `video_home`, `video_live_view`, `video_schedule`, `video_vod`, `video_watch`, and others) queries `Activity` objects globally with `.exclude(metadata__stream_url=None)` — no tenant filter at all (`video_live/views.py:11-18`).
   - `video_live/api_views.py:VideoFeedView` merges in `BroadcastSchedule.objects.filter(status__in=['scheduled', 'live'])` — also globally unfiltered (`api_views.py:73-75`).
   - `video_live/api_views.py:BroadcastListCreateView.get()` only filters by tenant if the caller explicitly passes `?tenant_id=` — the default behaviour returns every tenant's broadcasts (`api_views.py:129-133`).

   **A member can currently see and watch another community's live service.** This is a real gap, not a hypothetical — it needs fixing regardless of any new feature.

2. **There is zero interaction surface.** `templates/video_live/watch.html` is pure video consumption — no chat, no prayer request box, no Q&A (confirmed by direct read). A steward has no way to "minister to needs" during a live session today; they can only see the same silent player everyone else sees.

There are also **two systems inside `video_live`** worth naming precisely, because they are not a bug — they are the documented, intentional Phase 3 transition state (DOC G §7.1–7.3, Ecosystem Architecture §4.4). The Django template pages (`views.py`) read simple URL-embed `Activity` events (YouTube/Vimeo links in `metadata.stream_url` — DOC G names this "Version 2 Video/Live App," explicitly retained in production with **no forced migration**, §7.2). The DRF layer (`api_views.py`) separately reads `BroadcastSchedule`, the native RTMP/HLS model tied to the Go Media Engine (Ichebo Media, Layer 8, ADR-021). DOC G §7.3 already specifies the discriminator that resolves which player a viewer gets: if `video_url` is `rtmp://` or an HLS manifest, use the HLS player; if it is a YouTube/Vimeo URL, use the iframe embed. The template viewing pages currently never query `BroadcastSchedule` at all — that omission, not the existence of two systems, is the actual gap. The new Community-scoped room must query both sources and apply DOC G's existing discriminator rule, not invent a new one, and not attempt to unify the two systems — that unification is explicitly out of scope per DOC G's own transition strategy.

---

## Decision: extend Community, don't move Video

Video stays infrastructure — it already serves Learn (lesson video embeds), will serve Video/Live, and could later serve team conferencing. Community becomes a consumer of that infrastructure, not its replacement.

| Option | Why not |
|---|---|
| Move `video_live` app under `community/` | Would break the existing Learn lesson-embed usage and the Go Media Engine's API contract, which are deliberately tenant-agnostic at the infrastructure layer. |
| New "Live Service" feature with its own URLs, separate from both apps | Duplicates `video_live`'s player/embed logic and `community`'s tenant/steward context for no benefit. |
| **New Community-scoped view that queries the existing `Activity`/`BroadcastSchedule` data, filtered to the member's tenant, with a new request panel alongside it** | **Chosen.** Reuses 100% of the existing video infrastructure. Adds exactly the two missing things: tenant filtering and an interaction surface. |

**Note added 2026-06-23 (`video-direction-v2-plan.md`):** the rejected option above ("move `video_live` app under `community/`") and that later document's decision are not in conflict, despite both involving `video_live`. This plan rejected moving the *infrastructure* (`BroadcastSchedule`, the Go engine's API contract) under `community/` — correctly, since Learn also needs it, tenant-agnostic. The later document retires `video_live`'s separate *app surface* (Studio, Schedule, VOD, Watch, its sidebar icon) while leaving the infrastructure exactly where this plan left it. Community's own scheduling UI (built per the v2 plan) calls `BroadcastSchedule` directly, the same tenant-agnostic model this plan already relied on — nothing about the infrastructure moved.

---

## Part 1 — Tenant-scoped Live Service Room

### Fix the scoping gap (required regardless of the new room)

- `video_live/views.py:_event_qs()` — add an optional `tenant` parameter; when called from the new Community room, filter `Activity.objects.filter(tenant=tenant, ...)`. Existing global callers (e.g. a platform-wide VOD library for stewards) keep current behaviour by passing no tenant.
- `video_live/api_views.py:VideoFeedView.get()` — accept `?tenant_id=` and filter both the `Activity`-based `_event_qs()` and the `BroadcastSchedule.objects.filter(...)` query by it when present.
- `video_live/api_views.py:BroadcastListCreateView.get()` — no structural change needed; the new room always passes `tenant_id` explicitly.

### New surface: `/community/live/` (or scoped under the member's active tenant)

- New view in `community/views.py`, following the existing `_require_level` / tenant-context pattern already used by `my_community`, `gatherings_list` etc.
- Queries: today's/current live broadcast for the member's tenant, checking both `Activity` events with `stream_url` and `BroadcastSchedule` with `status='live'`, since either may represent the tenant's actual live service depending on how it was scheduled. This dual-source lookup is not a workaround — it is required by DOC G's documented transition strategy (§7.2: no forced migration from URL-embed to Ichebo Media) and stays correct as-is once Ichebo Media's Go Video Engine (Layer 8) is fully live; the room does not need a second migration when that happens.
- Player selection follows DOC G §7.3's existing rule exactly: if the resolved `video_url`/`viewer_hls_url` is `rtmp://` or an HLS manifest, render the HLS player; if it is a YouTube/Vimeo URL, render the iframe embed. This is read directly off whichever source resolved (`BroadcastSchedule.viewer_hls_url` or `Activity.metadata.stream_url`) — no new discriminator logic invented for this plan.
- If a live session exists: renders the existing player partial (reuse `templates/video_live/_live_player.html` via `{% include %}`, no duplication) plus the new ministry panel (Part 2).
- If no live session: shows the next scheduled service time, pulled from the same query, no-live empty state matching existing `.empty-state` patterns.
- Gathering link: when a `Gathering` Record (`record_family='community'`, `record_type='gathering'`) exists for the same tenant and time window, link the two — using the existing `gathering_record` FK already present on `BroadcastSchedule` (`video_live/models.py:46-49`, currently unused by any view) or the `Relationship(relationship_type='aligns_with')` pattern already used elsewhere in `community/views.py:488-500`. No new model field required — this wiring already exists, it's just never been read.

---

## Part 2 — In-Service Ministry Panel

This is a **different cadence** from the Community support-request flow (`.docs/plans/community-support-requests-plan.md`, 2026-06-18) — that one tracks multi-day SLA response times for asynchronous concerns. This one is real-time, scoped to a single live session (typically 60–90 minutes), and disappears with the session. Building it as a heavier ticket system would be the wrong shape for the cadence.

### Decision: same Record-family pattern, lighter weight, polling not WebSockets

Per ADR-008 (no Celery/Redis-dependent realtime until a felt need is demonstrated) and the existing precedent of 60-second HTMX notification polling (Phase V2.6), this panel uses simple polling — not a new WebSocket surface. That decision is deferred to Phase L10.3 platform-wide if polling latency becomes a felt problem; this feature does not need to jump the queue ahead of that gate.

**Data shape — again no new model, no migration:**

| Field | Value |
|---|---|
| `record_class` | `'personal'` |
| `record_family` | `'community'` |
| `record_type` | `'live_request'` |
| `created_by` | the attending member |
| `tenant` | the broadcast's tenant |
| `title` | `'prayer'` or `'question'` (short discriminator, free text allowed) |
| `content` | the request itself |
| `status` | `'submitted'` (raised) → `'active'` (steward is responding) → `'completed'` (acknowledged/answered) — reuses existing `STATUS_CHOICES`, no new values |
| `custom_fields` | `{'broadcast_id': <uuid>, 'session_date': <date>}` — used to scope the panel query to *this* session only, not the member's whole history |

The `broadcast_id` in `custom_fields` is what separates this from the support-request flow: it scopes the request to one specific live session rather than persisting as an open-ended ticket. Records older than the session naturally fall out of the panel's query (`custom_fields__broadcast_id=<this session>`) without needing a cleanup job.

### Member-facing surface

- A simple form alongside the video player: two buttons ("Prayer request" / "Question"), each opening a small text box, HTMX-submitted, no page reload — matches the existing FAB sheet interaction pattern already used in `community/views.py:htmx_fab_sheet`.
- Member sees their own submitted requests in the same panel with status (raised / steward responding / acknowledged).

### Steward-facing surface

- Visible only to users with a `-steward` role (`UserPermission.role__endswith='-steward'`) for the broadcast's tenant — same routing lookup already specified in the support-request plan, reused here.
- Live list of all `record_type='live_request'` records for `custom_fields.broadcast_id = <this session>`, polling every 15–20 seconds while the steward has the panel open (tighter than the existing 60s notification poll, since this is the active duration of a live event and responsiveness matters more here than for async notifications — still plain HTMX polling, no new infrastructure).
- One-tap "mark responded" action transitions `status` to `'active'`, then `'completed'` once the steward has actually addressed it (e.g. mentioned it in prayer, answered verbally, or replied via a short text response stored back in `custom_fields.steward_response`).
- This list is the actual "is the steward keeping up" visibility Chizola asked for — same principle as the support-request queue, applied to the compressed timescale of one live session instead of multi-day SLAs.

### Notification integration

Minimal — a live session is short enough that polling alone covers it for both sides while the panel is open. One exception: if a request is raised and the steward's panel is not currently open (e.g. they're focused on preaching, not watching the dashboard), there's no way to alert them. Reuses the existing tenant fan-out pattern already proven in `video_live/api_views.py:_notify_broadcast_start()` (currently inline, not yet in `notifications/service.py`) — add a single `notify_live_request_raised()` following that same shape, scoped to users with the steward role for that tenant rather than fanning out to every member.

---

## What This Does NOT Do

- Does not unify the `Activity`-based URL-embed system and the `BroadcastSchedule` native RTMP system — per DOC G §7.2, this is an intentional, documented transition state with an explicit no-forced-migration policy, not a defect to resolve. Both are queried by the new room, using DOC G §7.3's existing player discriminator.
- Does not add WebSockets or Django Channels — polling only, consistent with ADR-008 and the existing notification polling precedent
- Does not change `video_live`'s Go Media Engine, RTMP ingest, or HLS pipeline in any way
- Does not merge with or replace the community support-request flow (separate plan, separate cadence — multi-day SLA vs single-session real-time)
- Does not build team video conferencing — noted by Chizola as a third consumer of the video infrastructure, but out of scope for this phase

---

## Scope of Implementation

| Step | What | Files touched |
|---|---|---|
| 1 | Add tenant-filter parameter to `_event_qs()` | `video_live/views.py` |
| 2 | Add `?tenant_id=` filtering to `VideoFeedView` for both `Activity` and `BroadcastSchedule` queries | `video_live/api_views.py` |
| 3 | New Community view: live session lookup scoped to member's tenant, checking both data sources | `community/views.py`, `community/urls.py` |
| 4 | New template reusing existing `_live_player.html` partial + empty state | new template, `templates/video_live/_live_player.html` (reused via include, no change) |
| 5 | Member-facing request form (prayer/question), HTMX submit | new template partial, `community/views.py` |
| 6 | Steward-facing live request queue, polling, mark-responded action | new template partial, `community/views.py`, `community/urls.py` |
| 7 | Wire `gathering_record` FK / `aligns_with` Relationship to link Gathering ↔ session, if present | `community/views.py` (read existing data, no new write path required) |
| 8 | Add `notify_live_request_raised()` following existing `_notify_broadcast_start()` shape | `notifications/service.py`, `notifications/models.py` (NOTIFICATION_TYPES) |

No new Django app. No new models. No migrations beyond the one `NOTIFICATION_TYPES` choice addition.

---

## Relationship to Existing ADRs

| ADR | Impact |
|---|---|
| ADR-003 (single records table with discriminator) | Followed — `live_request` is a `record_type`, not a new model |
| ADR-007 (URL-based video only in Version 2) | Not affected — this plan does not change how video itself is delivered, only who can see which session and what surrounds it |
| ADR-008 (no Celery/Redis automation, no realtime until needed) | Followed — polling only, no WebSockets |
| ADR-021 (Ichebo Media as standalone product) | Not affected — Go Media Engine, RTMP, HLS pipeline unchanged |

No new ADR required.

---

## Exit Criteria

- [ ] A member visiting `/community/live/` sees only their own tenant's current/next live session, never another tenant's
- [ ] `VideoFeedView` and `BroadcastListCreateView` correctly scope to `tenant_id` when provided, with existing global behaviour preserved when it is not
- [ ] Member can raise a prayer request or question during a live session without leaving the video page
- [ ] Steward sees a live-updating queue of requests for their tenant's current session, scoped to that session only
- [ ] Steward can mark a request as responded/completed
- [ ] Requests do not leak across sessions — a request raised in last week's service does not appear in this week's panel
- [ ] `python manage.py check` — 0 issues
- [ ] No regression to existing Learn lesson video embeds or the Go Media Engine pipeline

## Commit

```
feat(community,video): tenant-scoped live service room + in-service ministry panel
```

---

## Master Roadmap Amendment

Add to the Video / Live App feature table in `master-roadmap-canonical-2026-05-13.md` (after line 227, "VOD library"):

```
| Tenant-scoped live service room (Community-embedded) | ⏳ Pending — see .docs/plans/community-live-service-room-plan.md |
| In-service ministry panel (prayer/question, steward queue) | ⏳ Pending — see .docs/plans/community-live-service-room-plan.md |
```

Add to the Community App feature table (after line 200, "Membership request flow"):

```
| Live service attendance + in-session ministry panel | ⏳ Pending — see .docs/plans/community-live-service-room-plan.md |
```

Add the following entry to the Layer 4 (Stabilisation) phase list, alongside the support-requests amendment (Phase H.3) — recommended as Phase H.4 since both strengthen Version 2 in real-world use without new infrastructure:

```
## Phase H.4 — Community Live Service Room ⏳

**Goal:** Tenant-scoped live service viewing room embedded in the Community
app, reusing the existing video_live engine — both the Activity URL-embed
system and the native BroadcastSchedule/Go Media Engine path, per DOC G's
documented coexistence policy — with correct tenant filtering added, which
is currently missing from both. Adds an in-service ministry panel for prayer
requests and questions, steward-visible as a live queue scoped to the
current session.

**Entry requirement:** Community App (Phase 5.4) and Video/Live App (Phase
V2.7) both complete. No new infrastructure — uses existing Record engine,
notification plumbing, and HTMX polling pattern.

**Reference:** .docs/plans/community-live-service-room-plan.md

**Commit:** `feat(community,video): tenant-scoped live service room + in-service ministry panel`
```

Add to the Deferred Items / Community App section, for visibility of what remains genuinely separate after this phase ships:

```
### Community App (remaining after Phase H.4)
- Team video conferencing as a third video-infrastructure consumer (after Learn, Community) — not scoped in H.4
- Real-time delivery via WebSockets for the ministry panel, if 15-20s polling proves too slow in practice — gated behind L10.3 platform-wide
```

Note: unification of the Activity URL-embed system and native BroadcastSchedule is intentionally **not** listed as deferred work — per DOC G §7.2, coexistence is the permanent, documented design, not a temporary state awaiting cleanup.
