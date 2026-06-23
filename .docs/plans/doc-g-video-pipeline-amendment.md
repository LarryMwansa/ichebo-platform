# DOC G (Ichebo Media Spec) — Video Pipeline Amendment

**Version:** 1.0 — 2026-06-23
**Status:** Approved (deployed and verified live) — pending merge into DOC G's canonical text
**Reference document:** `2026-05-13-ichebo-media-spec_doc-g_v1.0.md`
**Author:** Claude (technical) — directed by Chizola

---

## What This Document Is

While deploying the video VPS (46.62.211.72) and wiring up live broadcasting
end-to-end, several gaps were found between DOC G's described architecture
and what is actually buildable/built. Unlike the Handbook/mobile amendment
(`roadmap-doc-staleness-amendment-plan.md`), this is not a case of an
already-approved amendment sitting unmerged — DOC G itself was never
amended for these points. They were found live, during deployment, by
direct testing (real RTMP streams, real database state checks), not by
re-reading the doc.

Two of DOC G's own sections also contradict each other independently of
anything built today (§4.2 vs §5.1's server spec) — flagged here too,
since this is the natural place to record it.

This document follows the same pattern as the staleness-closure plan: it
distinguishes "approved direction, confirmed built" from "DOC G's
description was never accurate to begin with," and proposes exact edits
rather than leaving the gap implicit.

---

## Audit Findings — What DOC G Says vs What Is Actually Built

| DOC G claim | Section | Actual state (2026-06-23) |
|---|---|---|
| `POST /engine/stream/start` is called with `record_id` already in the body | §5.2 | **Inaccurate as written.** Nothing can call this with a valid `record_id` except Django — MediaMTX has no knowledge of Django's data model. The real chain is MediaMTX → Django (`/video/api/stream/start/`, resolves `record_id` from `BroadcastSchedule.stream_key`) → Go engine. Confirmed by reading `pkg/stream/handler.go`'s actual validation (`record_id` is a required field, rejected with 400 if empty) and by the fact no code anywhere could supply it before today. |
| Live pipeline (§4.1) shows MediaMTX → FFmpeg → Object Storage with no Django step | §4.1 | **Incomplete.** Django mediates both stream start and stream end — see above. Diagram should show a Django step between MediaMTX and the Go engine. |
| Scheduling a broadcast creates a **Gathering record** (Community App) with `format: "digital"` and `stream_url` | §4.3 | **Not what was built.** No `Gathering` model exists in `community/models.py`. The real model is `video_live.BroadcastSchedule` — a dedicated model with its own `status`, `stream_key`, `hls_url`, `vod_url` fields, not a generic Gathering/Activity dual-write. |
| CDN domain is `cdn.ichebo.org`; viewer URL is `https://cdn.ichebo.org/live/{stream-key}/index.m3u8` | §4.1, §4.2, §6.1 (throughout) | **Different domain actually deployed.** Live HLS is served from `https://media.ichebo.org/...`; delivered/archived video from `https://video.ichebo.org/media/...`. `cdn.ichebo.org` does not exist in DNS or in any deployed config. |
| Video Engine server: "CX32 minimum for live transcoding" | §4.2 | **Contradicts §5.1's own table**, which says "CX42 minimum (8 vCPU, 16GB RAM)" for the same server. Pre-existing internal inconsistency, not caused by today's deploy. Neither was actually provisioned — the real server is far smaller (2 vCPU / 3.7GB); see Resolution below. |
| `/engine/stream/end` returns `{ archive_record_id }` — "the auto-created VOD record" | §5.2 | **Not what was built.** The Go engine's `End` handler returns `{"status": ..., "broadcast_id": ...}` (no `archive_record_id`). Archive completion is a separate, later, async webhook (`/api/media/transcode-complete/`) carrying a `video_url`, not a record ID handed back synchronously from `stream/end`. |

---

## What Was Actually Built and Verified (2026-06-23)

For the record — this is the real, working contract, confirmed by an
actual RTMP stream test against production (not just service health
checks):

1. Broadcaster streams to `rtmp://media.ichebo.org/live/{stream-key}` — MediaMTX (not nginx — RTMP is not HTTP) accepts it on port 1935.
2. MediaMTX's `runOnReady` hook calls Django: `POST /video/api/stream/start/` with just `{stream_key, hls_url}` — authenticated by the same shared `MEDIA_ENGINE_API_KEY`/`MEDIA_DJANGO_API_KEY` used elsewhere.
3. Django (`StreamStartWebhookView`) looks up `BroadcastSchedule.objects.get(stream_key=...)`, sets `status='live'`, fires community notifications, then itself calls the Go engine: `POST /engine/stream/start` with the resolved `record_id` (= `BroadcastSchedule.id`).
4. The Go engine registers the session in its in-memory registry.
5. On disconnect, MediaMTX's `runOnNotReady` hook calls Django: `POST /video/api/stream/end/` with `{stream_key}`.
6. Django sets `status='ended'`, then itself calls the Go engine: `POST /engine/stream/end`.
7. The Go engine's archiver compiles the DVR recording asynchronously and, on completion, calls Django's `/api/media/transcode-complete/` with `job_id="archive-{record_id}"` and a `video_url` — Django's webhook handler recognizes the `archive-` prefix and saves it to `BroadcastSchedule.vod_url` (this branch did not exist before today — see the deploy plan's Phase 3.5 entry for the four bugs found and fixed to make this work at all).

Verified end-to-end: created a real `BroadcastSchedule`, streamed real RTMP
video to its exact stream key from the video server, and confirmed in the
production database afterward that `status` correctly progressed
`scheduled → live → ended` with `hls_url` populated.

---

## Proposed Edits to DOC G

### Edit 1 — §4.1 Pipeline Overview

**Current** implies a direct MediaMTX → Object Storage flow with no
Django involvement in starting/ending the session.

**Add**, after "MediaMTX receives the RTMP stream and begins transcoding
via FFmpeg":

> **Implementation note (2026-06-23):** MediaMTX cannot resolve a stream
> key to a Gathering/Broadcast record — it has no knowledge of Django's
> data model. In the deployed pipeline, MediaMTX's `runOnReady`/`runOnNotReady`
> hooks call Django directly (not the Go engine) on stream start/end;
> Django resolves the record and then calls the Go engine itself. See §5.2
> amendment below for the corrected API contract.

### Edit 2 — §4.2 The RTMP Ingest Server, table

**Change** `Server` row from "CX32 minimum for live transcoding" to match
§5.1's CX42 figure, or reconcile to a single intended value — currently
contradicts §5.1's own table for the same server. Neither figure reflects
the server actually provisioned (2 vCPU/3.7GB) — add:

> **Implementation note (2026-06-23):** the deployed server is below both
> figures above. Chizola's call: proceed at this size, revisit if real
> broadcast load demands it.

**Change** `Viewer URL` row from `https://cdn.ichebo.org/live/{stream-key}/index.m3u8`
to `https://media.ichebo.org/live/{stream-key}/index.m3u8` — matches the
domain actually provisioned and live (no `cdn.ichebo.org` exists).

### Edit 3 — §4.3 Broadcast Scheduling

**Replace** "A Gathering record (Community App) with format: 'digital'
and stream_url set to the HLS viewer URL" with:

> A `video_live.BroadcastSchedule` row — not a Gathering record as
> originally specified. No `Gathering` model exists in `community/models.py`
> as of this audit; the live-broadcast scheduling flow was built as its
> own dedicated model instead, with `status`, `stream_key`, `hls_url`, and
> `vod_url` fields. **Open question, not resolved by this amendment:**
> whether `BroadcastSchedule` should additionally dual-write into Activity
> as the original spec intended for community-feed visibility — confirmed
> absent today, not in scope of today's deploy work, flagged for a
> separate decision.

### Edit 4 — §5.2 Video Engine Service - Go, API contract

**Replace:**

> POST /engine/stream/start
>
> Body: { stream_key, record_id, quality_profiles }
>
> Returns: { rtmp_ingest_url, hls_viewer_url }

**With:**

> POST /engine/stream/start
>
> Called by Django (`video_live.api_views.StreamStartWebhookView`), not
> directly by MediaMTX — MediaMTX has no way to supply a valid `record_id`.
>
> Body: { stream_key, record_id, tenant_id, hls_base_url }
>
> Returns: { stream_key, record_id, started_at } (201 Created)
>
> **Implementation note (2026-06-23):** `quality_profiles` is not part of
> the actual request body; live-stream quality is fixed by MediaMTX's own
> HLS configuration, not negotiated per-session through this endpoint.

**Replace:**

> POST /engine/stream/end
>
> Body: { stream_key }
>
> Returns: { archive_record_id } // the auto-created VOD record

**With:**

> POST /engine/stream/end
>
> Called by Django (`video_live.api_views.StreamEndWebhookView`), same
> reasoning as stream/start above.
>
> Body: { stream_key }
>
> Returns: { status, broadcast_id } (200 OK) — does NOT return an archive
> record id synchronously. Archive compilation is asynchronous; on
> completion the engine calls Django's existing
> `POST /api/media/transcode-complete/` webhook with `job_id` prefixed
> `"archive-"` and a `video_url`, which Django then saves to
> `BroadcastSchedule.vod_url`.

### Edit 5 — §6.1 Flutter Video Player (viewer URL references)

Find and replace every `cdn.ichebo.org` reference with the domain actually
relevant to context — `media.ichebo.org` for live HLS, `video.ichebo.org`
for delivered/archived content. Not individually itemized here since the
exact line numbers may shift; do a full-document search before merging
this amendment, not a single targeted edit (this section was not
exhaustively re-read for this audit — confirm before assuming only the
sections listed above mention the old domain).

---

## What This Amendment Does NOT Do

- Does not change any deployed code or config — the real implementation
  (described in "What Was Actually Built" above) is correct and already
  live; this amendment only brings DOC G's text in line with it
- Does not resolve the CX32/CX42 internal contradiction to a specific
  number — flags it, leaves the actual decision (and whether to upgrade
  the live server) to a future call
- Does not decide whether `BroadcastSchedule` should also dual-write to
  Activity — flags the gap, does not close it
- Does not re-audit §6 (Flutter player) or §7 (transition strategy)
  exhaustively for further `cdn.ichebo.org` references or other drift —
  only the sections touched by today's actual deploy work were checked

---

## Exit Criteria

- [ ] DOC G §4.1 carries the Django-mediation implementation note
- [ ] DOC G §4.2's table is reconciled with §5.1 (single server-spec figure, or an explicit note that they differ and why) and its viewer URL uses the real domain
- [ ] DOC G §4.3 describes `BroadcastSchedule`, not a Gathering record, with the Activity dual-write question flagged as open
- [ ] DOC G §5.2's API contract for `/engine/stream/start` and `/engine/stream/end` matches the real request/response shapes
- [ ] A full search for `cdn.ichebo.org` across DOC G is done and every instance is corrected or explicitly left as a future/aspirational domain (not silently wrong)
- [ ] This document itself is referenced from `.docs/plans/video-vps-deploy-plan.md`'s execution log so a future reader following the deploy plan finds this amendment

## Commit

Documentation-only change — no code commit required.

```
docs: amend DOC G's live-streaming pipeline section to match the deployed implementation
```
