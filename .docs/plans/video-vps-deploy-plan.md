# Production Deploy — ichebo-media (Go Video Engine) to the Video VPS

**Version:** 1.1 — 2026-06-23
**Status:** Executed — live, full RTMP→MediaMTX→Django→Go-engine chain
verified end-to-end against the real production database. Resource
constraint outstanding (2 vCPU/3.7GB vs. DOC G's 8 vCPU/16GB recommendation
— Chizola's call: proceed now, revisit if real load demands it).
**Server:** `ics@46.62.211.72` (hostname `video`)
**Author:** Claude (technical) — directed by Chizola

---

## What This Document Is

A step-by-step record of deploying `ichebo-media` (the Go video engine),
MinIO (object storage), and MediaMTX (RTMP ingest) to the dedicated video
VPS, per DOC G's two-server topology. The Django VPS (`37.27.82.169`) is
explicitly out of scope for this round — already deployed and live.

---

## Verified Server State (2026-06-23, before any changes)

| Component | Finding |
|---|---|
| Provider/region | Hetzner Cloud, Helsinki (hel1) |
| OS | Ubuntu 22.04.5 LTS |
| Hardware | **2 vCPU, 3.7GB RAM, 38GB disk** — below DOC G's CX42 minimum (8 vCPU/16GB). Chizola's call: proceed now, upgrade later if real load demands it. |
| User | `ics`, sudo requires a password (not passwordless) |
| Existing setup | Per `.docs/2026-06-01-ichebo-video-vps-setup-manual_v1.md` (an earlier session): nginx installed, UFW active (22/80/443 only), 3 domains with real Let's Encrypt certs — `video.ichebo.org`, `media.ichebo.org`, `stream.ichebo.org` |
| Go toolchain | Not installed |
| FFmpeg | Not installed |
| MinIO/Docker | Not installed |
| `/opt`, `/etc/ichebo` | Empty/nonexistent — no app code deployed yet |

**`stream.ichebo.org` discrepancy found:** its nginx config tries to
`proxy_pass` to port 1935 inside an HTTP `location` block — this cannot
work, since RTMP is not HTTP and nginx's HTTP module can't proxy it (would
need the separate `stream {}` module, which isn't configured). Tracing the
setup manual confirms this domain was added later via "Part 11 — Adding a
New Domain," a generic template applied to a "stream" idea that doesn't
match DOC G's actual ingest convention (`rtmp://media.ichebo.org/...`).

**Resolved (Chizola, 2026-06-23):** Drop `stream.ichebo.org` — follow DOC G
exactly, RTMP ingest lives at `media.ichebo.org`. The domain/cert can stay
allocated but unused; not deleted, just not wired to anything.

**Object storage — resolved (Chizola, 2026-06-23):** DOC G specifies
dedicated Hetzner Object Storage (a separate Hetzner Cloud product,
provisioned via Console/API, not reachable over SSH). Rather than blocking
on that or routing video traffic back through the Django VPS's MinIO
(defeating the point of the two-server split), install a **second,
independent MinIO instance directly on this video VPS** — keeps video
storage traffic fully isolated from Django, no Hetzner Console dependency,
fully scriptable over SSH right now.

---

## Step-by-Step Plan

### Phase 1 — Base packages

1. `sudo apt update && sudo apt upgrade -y`
2. Install Go 1.24 (matching `ichebo-media/go.mod`'s `go 1.24` requirement) — not in Ubuntu 22.04's default apt repos at that version, install via the official tarball from `go.dev/dl`, not `apt`.
3. Install FFmpeg via apt (`sudo apt install -y ffmpeg`) — confirm version supports the codecs/profiles `ichebo-media/pkg/transcode/profiles.go` expects before assuming apt's version is sufficient.
4. Create the `ichebo` system user the deploy scaffold expects (`mediad.service`'s `User=ichebo`) — distinct from the `ics` login user, matching the existing Django VPS convention of a dedicated service account.

### Phase 2 — MinIO (this server, not the Django VPS's)

5. Install MinIO server + `mc` client.
6. Configure as a systemd service, data directory under `/opt/minio-data` or similar — confirm disk headroom (38GB total, 33GB free at audit time) is enough for expected video volume before assuming default placement is fine.
7. Create two buckets: `ics-media-upload` (private) and `ics-media-delivery` (public-read) — matching DOC G's naming exactly so no code changes are needed in `ichebo-media`'s config.
8. Create a scoped (non-root) MinIO access key for the Go engine to use — same credential-hygiene pattern as the Django VPS's `ichebo-app` MinIO user, never use root credentials in `.env`.

### Phase 3 — Deploy the Go engine

9. Clone `ichebo-platform` (the mono repo) to this server — same repo as the Django VPS, only `ichebo-media/` is relevant here.
10. `go build` the `mediad` binary from `ichebo-media/cmd/mediad`, install to `/usr/local/bin/mediad` per `deploy/mediad.service`'s `ExecStart`.
11. Build `/etc/ichebo/media.env` from `ichebo-media/.env.example` — point `MEDIA_S3_ENDPOINT` at this server's own new MinIO (not Hetzner Object Storage, not the Django VPS's MinIO), set `MEDIA_DJANGO_WEBHOOK_URL=https://app.ichebo.org`, and set `MEDIA_DJANGO_API_KEY` to **exactly match** the Django VPS's existing `MEDIA_ENGINE_API_KEY` value (already set during the earlier Django deploy) — a mismatch here causes silent 401s per the `.env.example`'s own warning.
12. Install and start `mediad.service`.

### Phase 4 — MediaMTX (RTMP ingest)

13. Install MediaMTX (Go-based, single static binary, per DOC G's recommendation over nginx-rtmp).
14. Configure MediaMTX to listen on port 1935 (RTMP) and write HLS output — confirm exact integration point with `ichebo-media`'s `pkg/stream` package before assuming a default MediaMTX config is sufficient; `pkg/stream/archiver.go`/`session.go` likely expect a specific webhook or file layout.
15. Open UFW port 1935.

### Phase 5 — Nginx — replace placeholders

16. Update `ichebo-video`'s `video.ichebo.org` block: replace the `503` placeholder with `proxy_pass http://127.0.0.1:8090` (mediad's port) using the already-written `ichebo-media/deploy/nginx-media.conf` as the template.
17. Update `ichebo-video`'s `media.ichebo.org` block: this is the RTMP ingest domain — proxies the HLS/HTTP delivery side only (MediaMTX's HTTP API/HLS output), not RTMP itself (RTMP ingest happens directly on port 1935, no nginx involved).
18. Leave `stream.ichebo.org` allocated but disabled (`rm` the symlink in `sites-enabled`, keep `sites-available` and the cert) per Chizola's decision above.

### Phase 6 — Verification

19. `curl -I https://video.ichebo.org` → expect a real response from mediad, not 503.
20. Health check endpoint (per `nginx-media.conf`'s `/health` location).
21. End-to-end: trigger a real transcode job from Django (or directly via the Go engine's API) and confirm the webhook callback reaches `app.ichebo.org` correctly, matching API keys.
22. RTMP: point a test broadcaster (OBS or `ffmpeg` CLI) at `rtmp://media.ichebo.org/live/{test-key}` and confirm MediaMTX accepts the stream.

---

## Open Questions / Confirm Before Executing

- Passwordless sudo for `ics`? (Same pattern as the Django VPS — speeds up the many `sudo` calls ahead, but is a real privilege change worth confirming first, not assumed.)
- Exact FFmpeg codec/profile requirements from `pkg/transcode/profiles.go` — read before assuming apt's FFmpeg build is sufficient.
- Confirm the existing `MEDIA_ENGINE_API_KEY` value from the Django VPS's `.env` (retrieve it there, never regenerate independently, or the webhook will silently 401).

---

## Execution Log

**Phase 0 — passwordless sudo.** Chizola set up `/etc/sudoers.d/ics-nopasswd`
manually (same pattern as the Django VPS). Confirmed working before any
further steps.

**Credential rotation before use.** Retrieving `MEDIA_ENGINE_API_KEY` from
the Django VPS's `.env` to confirm its value printed it into this
conversation — per this project's established discipline (any secret that
becomes visible in tool output gets rotated immediately, even if not yet
"live"). Rotated on the Django VPS via `sed`, restarted
`ics-gunicorn`/`ics-celery`/`ics-celery-beat`, new value never printed.
Transferred the new value server-to-server via a redirected file + `scp`
(never appeared in conversation text), deleted the temp file on both ends
immediately after use.

**Phase 1 — base packages.** `apt update && upgrade` clean. Go 1.24.0
installed via the official tarball (checksum verified against
`go.dev/dl`'s published JSON API before extracting — exact match). FFmpeg
installed via apt (4.4.2) — confirmed `libx264` and `aac` both present and
enabled before assuming apt's build was sufficient, matching exactly what
`pkg/transcode/profiles.go` requires. `ichebo` system user created
(no-login, matches `mediad.service`'s `User=ichebo`).

**Phase 2 — MinIO (this server, independent of the Django VPS's MinIO).**
Server binary + `mc` client downloaded, checksums verified against
`dl.min.io`'s published sha256sum files (exact match) before running
either binary. Installed as a systemd service (`minio.service`),
`/opt/minio-data` (32GB free at provisioning time). Root credentials
generated server-side, written to `/etc/ichebo/minio.env`
(`chmod 640`, `root:ichebo`), never printed to this conversation. Created
`ics-media-upload` (private) and `ics-media-delivery` (public-read, via
`mc anonymous set download`) — matches DOC G's bucket naming exactly, no
code changes needed in `ichebo-media`. Created a scoped non-root user
`ichebo-media-engine` with a policy limited to `s3:*` on only these two
buckets (not full admin) — verified end-to-end with a real
write/read/delete test using the scoped credentials before moving on.

**Phase 3 — Go engine.** Cloned the mono repo to `/home/ics/ichebo-platform-repo`.
`go build` succeeded, `go test ./...` passed for every package with test
files. Binary confirmed to fail fast with a clear error when required env
vars are missing (`MEDIA_DJANGO_WEBHOOK_URL`, `MEDIA_DJANGO_API_KEY`) —
matches the `.env.example`'s own documented validation behavior, not
silent-default behavior. Built `/etc/ichebo/media.env` with all 17 expected
lines — `MEDIA_S3_ENDPOINT` pointed at this server's own new MinIO
(`http://127.0.0.1:9000`, not Hetzner Object Storage, not the Django VPS's
MinIO), `MEDIA_DJANGO_API_KEY` set to the rotated value matching the
Django VPS exactly. Verified every secret field was non-empty by checking
string length only, never the value itself. Installed `mediad.service`
(added `After=minio.service` to the unit, not present in the repo's
template, since mediad depends on MinIO being up first). Service started
cleanly: production mode confirmed, S3 storage pointed correctly, 1
transcode worker (appropriate for this server's 2 vCPUs), listening on
`:8090`. `/health` returns `{"status":"ok","version":"0.1.0"}`.

**Phase 3.5 — found and fixed the live-stream wiring was incomplete on the
Django side (a separate but blocking bug for Phase 4).** While planning
how MediaMTX's hooks should call into this pipeline, traced that the Go
engine's `/engine/stream/start` requires a `record_id` only Django's
`BroadcastSchedule` table can resolve — MediaMTX can't call the engine
directly with a valid one. The real chain has to be
MediaMTX → Django → Go engine. `StreamStartWebhookView`/`StreamEndWebhookView`
already existed and did the lookup, but never made the second call onward
to the engine. Completed both, and found three further pre-existing,
unrelated bugs in the same code while testing it: a wrong import
(`UserPermission` is in `tenants.models`, not `accounts.models` — this
threw on every real call), a missing DRF auth override on all three
engine-webhook views (DRF's global `IsAuthenticated` rejected every call
with 401 before the manual bearer-key check ever ran, even with a correct
key — confirmed this webhook had likely never worked since it was
written), and `TranscodeCompleteWebhookView` never recognizing
`BroadcastSchedule` rows at all for archive-completion callbacks. Fixed
all four, verified each leg of the chain with the Django test client
(mocked engine call) and confirmed live in production via curl
(`/video/api/stream/start/` now correctly returns 404 "Unknown stream key"
for a bad key with valid auth, not a blanket 401). Committed separately
(`371f739`) since it's a real application bug fix, not infra config.

**Phase 4 — MediaMTX.** Binary downloaded and checksum-verified against the
GitHub release's `checksums.sha256` (exact match) before running. v1.19.1 —
confirmed this version renamed the hooks documented in older MediaMTX
guides from `runOnPublish`/`runOnPublishDone` to `runOnReady`/`runOnNotReady`
(checked the actual shipped `mediamtx.yml` template rather than assuming a
remembered hook name was current).

Found via direct, repeated testing (not assumed) that the Go engine's
`/engine/stream/start` can't be called directly by MediaMTX's hooks — it
requires a `record_id` only Django's database has. Fixed by pointing
MediaMTX's hooks at Django's webhooks instead (`/video/api/stream/start/`
and `/video/api/stream/end/`), which already do the lookup and (after the
Phase 3.5 fix above) now complete the call to the Go engine themselves.

Found via direct testing that `runOnReady`/`runOnNotReady` do **not** run
through a shell — an unwrapped command containing a `>` redirect printed
the redirect operator as a literal argument instead of redirecting output.
Every hook is wrapped in `sh -c '...'`. Confirmed (also via direct test,
not assumption) that environment variables ARE inherited from the parent
process — `MEDIA_DJANGO_API_KEY` is passed via `mediamtx.service`'s
`EnvironmentFile`, not hardcoded in the YAML.

Installed as `mediamtx.service` (port 1935 RTMP, port 8888 HLS, MoQ
explicitly disabled after it logged permission-denied warnings trying to
write a TLS cert it doesn't need for this deployment). UFW port 1935
opened.

**Real end-to-end test performed** (not assumed working from config
inspection alone): created a real `BroadcastSchedule` row in production,
streamed real RTMP video to its exact stream key from the video server via
`ffmpeg`, and confirmed in the production database afterward that
`status` correctly progressed `scheduled` → `live` → `ended` and `hls_url`
was populated — proving the full chain (MediaMTX → Django webhook lookup →
Go engine session registration → Django DB write → archive trigger on
end) actually works, not just that each piece independently starts
cleanly. (A `curl: 499` appeared in nginx's access log for the `start`
call during testing — traced this to the synthetic `ffmpeg testsrc` test
stream's RTMP connection closing unusually fast, not a real defect: the
database state confirms Django's handler ran to completion regardless of
the client-side connection closing early. Real broadcaster software (OBS)
holds the RTMP connection open for the actual broadcast duration and
would not trigger this.)

**Phase 5 — nginx.** Replaced both 503 placeholders. `video.ichebo.org` now
proxies `/engine/` and `/health` to mediad (port 8090) per the repo's own
`ichebo-media/deploy/nginx-media.conf` template, plus a new `/media/`
location (not in that template — added here) proxying to MinIO's
`ics-media-delivery` bucket, since `MEDIA_CDN_BASE_URL` was set to
`https://video.ichebo.org/media` in Phase 3 and nothing was serving that
path yet. `media.ichebo.org` proxies to MediaMTX's HLS output (port 8888)
— confirmed this is HTTP-only; RTMP ingest itself bypasses nginx entirely,
binding directly to port 1935. `stream.ichebo.org` disabled (symlink
removed from `sites-enabled`, cert and `sites-available` file left in
place, not deleted) per Chizola's decision to follow DOC G's
`media.ichebo.org` convention instead.

**Phase 6 — verification, all confirmed live:**

- `https://video.ichebo.org/health` → real `{"status":"ok","version":"0.1.0"}` from mediad through nginx
- `https://video.ichebo.org/media/` → real S3 `ListBucketResult` XML from the delivery bucket through nginx through MinIO
- `https://media.ichebo.org/` → `404` from MediaMTX itself (correct — no active stream at the time of the check)
- Real RTMP → MediaMTX → Django → Go engine → Django chain, verified via actual database state change (see Phase 4 above), not just individual service health checks
- Phase 6 — end-to-end verification (real transcode job + webhook
  round-trip to Django, real RTMP test stream)

*(To be filled in as each phase actually runs — not pre-written, per this project's working convention of recording real discrepancies found during execution, not assumed-clean steps.)*
