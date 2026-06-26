# Video Direction v2 — Retiring the Standalone Video App

**Version:** 1.0 — 2026-06-23
**Status:** Approved — pending implementation
**Author:** Claude (technical) — directed by Chizola
**Reference documents:** `2026-05-13-ichebo-media-spec_doc-g_v1.0.md` (and its amendment, `doc-g-video-pipeline-amendment.md`), `2026-05-13-ichebo-adrs-012-021.md` (ADR-021), `.docs/plans/community-live-service-room-plan.md`, `.docs/plans/layer-8-media-scaffold-plan.md`, `.docs/DESIGN.md`

---

## What This Document Is

A full audit of how video is actually consumed today (2026-06-23 — see the
preceding conversation for the audit trail, not repeated here) found that
the web UI has no working path to the video infrastructure deployed to the
video VPS: `BroadcastSchedule` (real RTMP/HLS) and `media`'s upload/transcode
pipeline have **zero** template consumers. The only thing any Django page
can play is a manually-pasted YouTube/Vimeo/mp4 URL on the legacy `Activity`
model.

Fixing that exposed a second, more consequential question: should the fix
live inside a rebuilt standalone `video_live` app, or should `BroadcastSchedule`
and `media` become pure infrastructure consumed directly by `community` and
`learn`? This document settles that question, and is also a real policy
reversal of two prior, explicit decisions — named below, not glossed over.

---

## The Decision

**`video_live`'s app surface — Studio, Schedule, VOD library, Watch, Manage,
and its sidebar icon — is retired.** `BroadcastSchedule`, `media.TranscodeJob`/
`VideoRecord`, and the Go-engine webhook views survive as infrastructure
only, with no UI of their own. `community` and `learn` each build their own
scheduling/upload/viewing surfaces directly against these models, in their
own existing pages, under their own existing navigation.

### Why this reverses two prior decisions — named explicitly

**ADR-021 ("Relationship to Existing Video Approach")** states: *"The
Version 2 Video/Live app... remains in production and is valid for its
scope. Ichebo Media does not replace it immediately."* That was correct
when written — Ichebo Media didn't exist yet, so there was nothing to fold
the app's surface into. It now does, and is deployed and verified live.
This document supersedes that specific clause; ADR-021's other content
(Go engine architecture, two-bucket storage, MediaMTX as ingest) is
unaffected and stays as-is.

**`community-live-service-room-plan.md`'s decision table** explicitly
considered and rejected "Move `video_live` app under `community/`," reasoning
it "would break the existing Learn lesson-embed usage and the Go Media
Engine's API contract, which are deliberately tenant-agnostic at the
infrastructure layer." That reasoning is still correct about the
**infrastructure** — which is exactly why this document does not move
`video_live` under `community`. It deletes `video_live`'s *app surface*
(views, templates, URLs, sidebar icon) while leaving the infrastructure
(`BroadcastSchedule`, the Go engine, the webhooks) exactly where it is,
tenant-agnostic, importable by any app. The thing being rejected then and
the thing being done now are different operations on the same word
"video_live" — worth being precise about so a future reader doesn't think
this document contradicts itself.

### Why this is not "rebuilding bloat"

The actual duplication was never in the models — `BroadcastSchedule` and
`media`'s wrappers are already correctly generic, following the same
pattern as every other infra module in this codebase (`records.Record`
underneath, a thin typed wrapper on top, ADR-003's single-records-table
discipline). The duplication was a **second navigation destination** —
a "Video" app sitting next to Community and Learn, asking a steward to go
somewhere else to manage the thing that's actually about their own
community's services or their own course's lessons. Removing that
destination, and putting the same real model directly where the steward
already is, is the lean direction — one fewer app, one fewer sidebar
icon, two existing pages get the missing piece instead of a third page
duplicating both.

---

## What Survives (Infrastructure — No Changes Needed)

| Module | Role |
|---|---|
| `video_live.models.BroadcastSchedule` | Stream key + lifecycle state machine for any live RTMP broadcast. Tenant-scoped. `gathering_record` FK is generic — points at any `records.Record`, not Community-specific. |
| `video_live.api_views.StreamStartWebhookView` / `StreamEndWebhookView` | MediaMTX → Django → Go engine handshake. Fixed and verified end-to-end during the video VPS deploy (`video-vps-deploy-plan.md` Phase 3.5). |
| `media.models.TranscodeJob` / `VideoRecord` | Upload/transcode job tracking + typed `custom_fields` wrapper over `records.Record`. Already generic — works for any `record_family`. |
| `media.views.UploadInitView` / `UploadCompleteView` / `TranscodeCompleteWebhookView` | Go-engine upload/transcode API. Auth bug fixed during the same deploy session. |

None of these move, rename, or change behavior. They stop being consumed
indirectly through `video_live`'s app pages and start being consumed
directly by `community` and `learn`.

---

## What Is Deleted

**Views** (`video_live/views.py`): `video_home`, `video_live_view`,
`video_schedule`, `video_vod`, `video_watch`, `video_manage`,
`video_delete_event`, `video_studio`, `htmx_studio_now_playing`,
`htmx_studio_timeline`, `htmx_studio_quick_schedule`,
`htmx_studio_set_fallback`, `video_library`, and their helpers
(`_event_qs`, `_annotate_event`, `_parse_local_datetime`, `_steward_tenant`,
`_get_fallback`, `_studio_context`) — `_event_qs`/`_annotate_event`'s
legacy-`Activity` query logic is retired along with the views that used
it, not ported forward; see "What Happens to Legacy Activity Embeds"
below for why.

**Templates** (`templates/video_live/`): `base_video.html`, `home.html`,
`live.html`, `schedule.html`, `vod.html`, `watch.html`, `manage.html`,
`studio.html`, `library.html`, and the `partials/` directory
(`studio_fallback_form.html`, `video_sidebar.html`,
`studio_quick_schedule.html`, `studio_timeline.html`).
`_live_player.html` is also deleted — its only consumer was
`video_live_view`, which is itself deleted; Community already has its own
correctly-built equivalent (`_live_session.html`).

**Navigation**: the "Video" sidebar item in `_sidebar.html`, and the
`video_live:*` link in `_app_launcher.html`.

**URLs** (`video_live/urls.py`): every `template_urlpatterns` entry. The
`api_urlpatterns` entries for `BroadcastListCreateView`/`BroadcastDetailView`/
the two webhook views stay — they're the infrastructure API, not app
surface.

**External references to fix** (found by grep, not assumed complete —
re-check before deleting):
- `templates/workspace_shell.html`, `templates/components/_app_launcher.html`, `templates/components/_sidebar.html` — remove the Video nav entry
- `templates/dashboard/partials/_today_schedule.html` — "view full schedule" link currently points at `video_live:schedule`; repoint at Community's new schedule view (built below)

---

## What Happens to Legacy Activity Embeds

DOC G §7.2/§7.3 established a deliberate, documented coexistence policy
between the legacy `Activity` URL-embed model and the native
`BroadcastSchedule` model — explicitly **not** to be unified. This
document does not reopen that policy for existing data: any `Activity`
row with a `metadata.stream_url` that already exists keeps whatever
historical value it has. This document **does** end the policy's forward
half — there is no longer a page where a steward can create a *new*
`Activity`-based embed event. Going forward, scheduling a service inside
Community always creates a `BroadcastSchedule`. Existing legacy events are
not migrated or deleted; they simply have no surviving UI to view them in
once `video_live`'s templates are gone.

**Open question, not resolved here:** whether any currently-live legacy
`Activity` events need a one-time read-only display somewhere before
their viewing page disappears (e.g. a past Sunday's YouTube-embedded
service someone might still want to reference). Check `Activity.objects.filter(activity_type='event').exclude(metadata__stream_url='').count()`
in production before deleting `watch.html`/`_live_player.html` — if
non-zero, decide whether to render them via Community's new player (which
already has an `embed_type` fallback path) before retiring the dedicated
page, rather than silently losing access.

---

## What Gets Built

### 1. Shared HLS player partial

One template, used by both Community and Learn. Loads `hls.js` from CDN
only when the player type is `hls` (live or HLS VOD); falls back to a
plain `<video>` tag for direct mp4. Replaces:
- `community/partials/_live_session.html`'s inline `<video src="{{ session.embed_url }}">` for `player_type == 'hls'` (currently only plays in Safari — every other browser shows nothing)
- `templates/video/_player.html`'s `video_type == 'direct'` branch (same gap, currently only feeds it manually-pasted mp4 links)

No new model, no new app — a partial template plus a small JS init,
following the existing `editorial_v2.js` pattern of one shared controller
keyed by element id (not a new framework or player library beyond
`hls.js` itself).

### 2. Community — service scheduling, extending the existing Gathering form

**Correction (2026-06-24):** an earlier version of this section proposed a
new "Schedule a Service" action and claimed no Gathering record existed to
attach it to. Both were wrong — found by reading
`community/views.py:htmx_create_gathering` directly, not assumed.
A Gathering record is real (`Record(record_family='community',
record_type='gathering')`, dual-written to `Activity`, exactly as DOC G
describes), already has a working form
(`management.html`'s "Schedule" button → `htmx-create-gathering`), and
already has a `format` field with a `digital` option. The actual gap is
one field: for `format == 'digital'`, that form writes a plain typed-in
`custom_fields.stream_url` string, never a real `BroadcastSchedule`.

The fix is to extend this existing form, not add a parallel one: when a
steward picks `format = digital`, create a `BroadcastSchedule` (not a
typed URL field) linked via its existing `gathering_record` FK, and show
the generated `rtmp_ingest_url` for the steward to paste into their
streaming software. Community already has the correct *viewing* half
(`community/live_service_room.html`, `_find_live_session`, checks
`BroadcastSchedule.status='live'` first, falls back to legacy `Activity`
for old data only per the policy above) — this closes the loop so a
digital Gathering scheduled today actually produces something the viewing
page can find.

### 3. Learn — real lesson video, not pasted links

Lesson authoring (`learn/views.py`'s lesson edit form, currently a raw
`video_url` text input) gets a real upload step calling `media`'s existing
`UploadInitView`/chunked-upload flow, writing the result into the lesson
`Record`'s `custom_fields` using the same key shape `media.VideoRecord`
already defines (`video_url`, `thumbnail_url`, `duration_seconds`,
`quality_variants`) — no new field names invented. Lesson viewing
(`lesson_viewer.html`) swaps to the shared player from #1. Live lectures
(if a course session is run live, not just pre-recorded) use the same
`BroadcastSchedule` primitive Community uses — same scheduling pattern,
surfaced inside Learn's own course-session UI instead of Community's.

### 4. Video conferencing — explicitly not in this round

DOC G already classifies bidirectional video (team meetings, breakout
discussion) as **Version 4+**, requiring WebRTC — a different protocol,
different server software, no code shared with the HLS/RTMP broadcast
work above. Not addressed by this document. If raised again, treat it as
its own scoping conversation, not an extension of this one.

---

## Fresh Design Pass

Per `.docs/DESIGN.md`, both new surfaces must use the existing system, not
invent new patterns:

- **Page hero:** `.page-hero.page-hero--watermark` with the existing
  eyebrow (`.page-hero__eyebrow-line` + `.page-hero__label`) and `<em>`
  italic accent — exactly as `live_service_room.html` and
  `lesson_viewer.html` already do correctly. No new hero variant needed.
- **Live indicator:** `live_service_room.html`'s current inline-styled
  "LIVE NOW" badge should become `.status-badge` (the component inventory
  already defines this pattern) rather than a one-off inline style —
  small fix alongside the player swap, not a new component.
- **Schedule action / stream-key display:** use `.card-accent` (left red
  rule) for the "your stream key" reveal — matches the signature pattern
  already used for accent cards elsewhere, and signals "this is the
  important, copy-this-carefully value" the same way a governance accent
  card signals "this matters."
- **Upload progress (Learn):** `.progress-bar-wrap`/`.progress-bar-fill` —
  already exists for formation progress, same visual language applies
  directly to upload/transcode progress, no new progress component.
- **Empty states:** `.empty-state` — already used correctly in
  `_live_session.html` for "Not live yet" / "No service scheduled"; carry
  the same pattern into Learn's "no video yet" lesson-authoring state.
- **Color:** live/recording uses `--error` (red `#DC2626`/dark
  `#F87171`) per the existing semantic palette — not `--primary`, which is
  reserved for brand/action, not state. `_live_session.html` already gets
  this right; keep it.
- **Motion:** per DESIGN.md's motion rules, a stream's live/ended state
  transition is a real, certain fact (an RTMP webhook fired) — treat it
  like the governance-record rule ("what never animates"): no fade/slide
  when a broadcast flips from scheduled to live, just an instant badge
  swap. Reserve actual motion (300ms standard) for the player loading in,
  not for state changes themselves.

No new typeface, no new color, no new spacing scale, no new radius value —
this is explicitly an assembly of existing DESIGN.md primitives into two
pages that don't exist yet, not a new design language for video.

---

## Amendments Required to Canonical Documents

Found by grep across `.docs/` for `video_live`/"Video app" — every hit
listed, not a sample:

| Document | Location | Current text | Required change |
|---|---|---|---|
| `2026-05-13-ichebo-adrs-012-021.md` | ADR-021, "Relationship to Existing Video Approach" | "The Version 2 Video/Live app... remains in production and is valid for its scope" | Add a superseding note: as of this document's date, the standalone app is retired; `BroadcastSchedule`/`media` are consumed directly by Community and Learn. Do not delete the original text — mark superseded, matching the precedent in `roadmap-doc-staleness-amendment-plan.md`. |
| `data-contract-v11-canonical-2026-05-13.md` | repo tree listing | `video_live/ ← Video / Live App (no models — uses Activity + records)` | Already stale even before this decision — `BroadcastSchedule` is a real model. Update to describe `video_live` as a models/webhooks module, no app templates. |
| `2026-05-13-ichebo-technical-architecture_doc-d_v1.0.md` | repo tree listing | `video_live/ ← Video / Live App (no models - uses Activity + records)` | Same fix as above. |
| `master-roadmap-canonical-2026-05-13.md` | Phase/layer description, line ~484 | "video_live/ Django app, Broadcast Scheduler... Live Stream Surface... VOD Library... Programme Grid... individual event player" | Mark superseded — describes the retired app surface. Add note pointing to this document and to wherever Community/Learn's new surfaces land once built. |
| `master-roadmap-canonical-2026-05-13.md` | line ~893, version table | `v2-video ← V2.7 live video app` | Same — mark superseded, not deleted (preserves build history per the established convention). |
| `.docs/plans/community-live-service-room-plan.md` | decision table | Explicitly rejected moving `video_live` under `community/` | Add a note: that rejection was correct for "move the infrastructure," and remains correct — this document does not move `BroadcastSchedule`. It retires the separate *app surface* that plan didn't propose touching. Cross-reference this document so a future reader sees both decisions and why they don't conflict. |
| `.docs/plans/layer-8-media-scaffold-plan.md` | §"Video library management page in video_live app" | Describes `library.html` as planned | Mark as built-then-retired — it was built (confirmed, 179 lines), then removed by this document. |
| `.docs/plans/doc-g-video-pipeline-amendment.md` | "What This Amendment Does NOT Do" | Silent on app-surface scope | Add a cross-reference to this document, since that amendment's §4.3 edit (Gathering record vs. BroadcastSchedule) and this document's Community scheduling work touch the same model from different angles. |

No edits to `2026-05-13-ichebo-media-spec_doc-g_v1.0.md` itself beyond what
`doc-g-video-pipeline-amendment.md` already covers — this document is
about the app/UI layer, that one is about the API contract layer. Keep
them separate, cross-referenced.

---

## What This Document Does NOT Do

- Does not change `BroadcastSchedule`, `TranscodeJob`, `VideoRecord`, or
  any Go-engine code — infrastructure is correct as-is
- Does not migrate or delete existing `Activity` rows with legacy
  `stream_url` data — only retires the page that displayed them going
  forward (see "Open question" above — check production data before
  deleting the viewing template)
- Does not build video conferencing — explicitly deferred, see §4 above
- Does not invent new design components — assembles existing DESIGN.md
  primitives only
- Does not change the Go engine, MediaMTX, or anything on the video VPS —
  this is a Django app/template/doc-only change

---

## Exit Criteria

- [ ] `video_live`'s template-rendering views, templates, and URLs deleted; API views/webhooks retained
- [ ] Sidebar/app-launcher Video entry removed; dashboard's schedule link repointed
- [ ] Shared HLS player partial built and used by both Community and Learn
- [ ] Community has a real "Schedule a Service" flow creating `BroadcastSchedule` rows with a visible stream key
- [ ] Learn's lesson authoring uploads real video via `media`'s API instead of a pasted URL field
- [ ] Production checked for live legacy `Activity` embed events before their viewing page is deleted (see "Open question")
- [x] All seven canonical-doc amendments above applied, each marked superseded (not deleted) per this project's established convention
- [ ] `community-live-service-room-plan.md` and this document cross-reference each other so the two related-but-distinct decisions are both visible from either

## Commit

```
docs: retire the standalone video_live app surface, fold scheduling into Community and Learn
```
