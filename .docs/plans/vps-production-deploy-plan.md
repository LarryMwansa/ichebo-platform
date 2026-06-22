# Production Deploy — ichebo-platform + ichebo-website to the existing VPS

**Version:** 1.1 — 2026-06-22
**Status:** Executed — live in production, one manual follow-up pending (Brevo credentials)
**Server:** `scepter@37.27.82.169` (hostname `scepter-server`)
**Author:** Claude (technical) — directed by Chizola

---

## What This Document Is

A step-by-step record of replacing the currently-live Version 1/MVP deployment
(a different repo, `LarryMwansa/ics.git`) and its accompanying marketing site
(`LarryMwansa/ics_website.git`) with this mono repo's `ichebo-platform`
(Django) and `ichebo-website` (marketing site) on the same VPS.

Confirmed before starting: the current database content is disposable test
data — no migration/preservation plan is needed. `ichebo-media` (the Go video
engine) is explicitly out of scope for this cutover; it requires a separate,
not-yet-provisioned server per DOC G's two-server topology (Server 1 = this
Django VPS, Server 2 = dedicated Video Engine server).

---

## Verified Server State (2026-06-22, before any changes)

| Component | Finding |
|---|---|
| OS | Ubuntu 24.04.4 LTS (roadmap docs say 22.04 — stale, not actionable) |
| Disk | 75G total, 14G used, 58G available |
| Memory | 7.6Gi total, 1.1Gi free, no swap |
| User | `scepter`, in `sudo` group, **requires a password** for sudo (not passwordless) |
| App (old) | `/home/scepter/ics` — git remote `LarryMwansa/ics.git`, branch `mvp-production`, diverged from its own remote (3 local / 1 remote commit) |
| Marketing site (old) | `/home/scepter/ichebo-site` (served static build) + `/home/scepter/ichebo-site-src` (source, remote `LarryMwansa/ics_website.git`) |
| Django version (old) | 5.2.13 — **this repo pins 4.2.30 per ADR-002**, a deliberate downgrade, not an oversight |
| Python | System 3.12.3; old app's venv also 3.12.3 |
| Web server | Nginx 1.24.0, config at `/etc/nginx/sites-available/ics`, valid Let's Encrypt certs for `ichebo.org`, `app.ichebo.org`, plus 301 retirement redirects for a retired `ichebo.online` domain |
| Database | PostgreSQL 16.14, role `ics_user`, database `ics_db`, password auth (not peer) — confirmed working, reusable as-is |
| Object storage | MinIO running (`minio.service`), proxied at `/media/` → `localhost:9000` |
| Process manager | `ics-gunicorn.service`, binds `127.0.0.1:8001`, `WorkingDirectory=/home/scepter/ics`, `DJANGO_SETTINGS_MODULE=ics_project.settings.production` — structure matches this repo's `gunicorn.conf.py` exactly |
| Missing entirely | Redis, Go toolchain, Celery, any `ichebo-media`/MediaMTX service |
| Backups | Daily cron at 2am (`/home/scepter/backup.sh` → `/home/scepter/backups/ics_backup_*.sql.gz`), last run today |

**Conclusion:** this is a code-and-process swap onto already-correct
infrastructure, not a from-scratch provision. Nginx, TLS, MinIO, and
PostgreSQL stay as they are — only the application code, venv, and one
systemd service's working directory change.

---

## Step-by-Step Plan

### Phase 1 — Prepare the new deployment alongside the old one (no downtime risk)

1. Clone `ichebo-platform` into a **new** directory — `/home/scepter/ichebo-platform` — leaving `/home/scepter/ics` (the live old app) completely untouched until cutover.
2. Create a fresh Python venv inside the new directory (`python3 -m venv .venv`) — do not reuse or modify the old app's venv, since it has Django 5.2.13 installed and this repo requires 4.2.30.
3. `pip install -r requirements.txt` into the new venv.
4. Build `.env` for the new app from `ichebo-platform/.env.example`, reusing the **existing** `DB_NAME=ics_db`, `DB_USER=ics_user`, `DB_PASSWORD` (same role, confirmed working, no new Postgres role needed), `DB_HOST=localhost`, `DB_PORT=5432`. Generate a fresh `SECRET_KEY` and `FIELD_ENCRYPTION_KEY` — never reuse the old app's. Set `MEDIA_ENGINE_API_KEY` to a new generated secret (no `ichebo-media` server exists yet, but the var is required — see ADR/earlier session fix removing its insecure default).
5. Run the VPS directory checklist from `production.py`'s own docstring: `mkdir -p /var/log/ics /var/cache/ics /var/log/gunicorn` (idempotent if they already exist from the old app — confirm ownership is `scepter`).

### Phase 2 — Database reset (confirmed disposable data)

6. Confirm one more time interactively before this step runs, since it is destructive: `DROP DATABASE ics_db` (or `TRUNCATE` every table) and recreate it fresh, OR simply let Django's `migrate` run against the existing schema and accept that the old app's tables (different model shapes, since this is Django 4.2 vs 5.2 and a different schema entirely) will conflict.
   - **Recommended:** drop and recreate `ics_db` cleanly, since the old schema doesn't match this repo's models at all (different repo, confirmed disposable data) — migrating onto an incompatible schema would fail loudly anyway.
7. `python manage.py migrate` — apply this repo's full migration history to the fresh database.
8. `python manage.py createsuperuser` — create the production admin account.
9. `python manage.py bootstrap_platform` — run the command built earlier this session. Confirms migrations, creates Handbook/Induction/Prime/agencies/Service Orders/6 Qualification Programmes/Genesis Sceptre Community in one idempotent pass.
10. `python manage.py collectstatic --noinput` — populate `staticfiles/` (nginx already points `/static/` at this path for `app.ichebo.org`).

### Phase 3 — Cutover (brief downtime window)

11. Stop the old `ics-gunicorn.service`.
12. Update the systemd unit (`/etc/systemd/system/ics-gunicorn.service`) — change `WorkingDirectory` and the venv path from `/home/scepter/ics` to `/home/scepter/ichebo-platform`. Keep the same bind address (`127.0.0.1:8001`) and service name so nginx needs no changes.
13. `systemctl daemon-reload && systemctl start ics-gunicorn`.
14. Verify `app.ichebo.org` responds correctly (login page, static assets load, no 500s).
15. Replace marketing site: build/copy this repo's `ichebo-website` output into `/home/scepter/ichebo-site` (the path nginx already serves `ichebo.org` from). Back up the old `ichebo-site` directory first (rename, don't delete, in case of rollback).
16. Verify `ichebo.org` loads correctly, and specifically test the waitlist form end-to-end (the fix from earlier this session) — confirm `CORS_ALLOWED_ORIGINS` in the new `.env` includes `https://ichebo.org`.

### Phase 4 — Production-only verification checklist

These are the items flagged earlier this session as impossible to verify outside a real server — verify each explicitly now that we have one:

17. Real `SECRET_KEY` — confirm it's the freshly generated one, not a placeholder (`check --deploy` will flag this if wrong).
18. MinIO/Object Storage — upload a real file through the app (e.g. set an avatar) and confirm it lands in MinIO, not local disk.
19. Brevo email delivery — trigger a real email (waitlist signup, or password reset) and confirm it arrives.
20. TLS/HTTPS — confirm `SECURE_SSL_REDIRECT` and HSTS headers are present on a live response (`curl -I https://app.ichebo.org`).
21. `python manage.py check --deploy` against the real production `.env` — should report 0 issues now that a real `SECRET_KEY` is set.

### Phase 5 — Explicitly deferred (not part of this cutover)

- `ichebo-media` (Go video engine) — needs its own dedicated server per DOC G. Not built, not deployed, no action this round.
- Redis + Celery — not installed. `bootstrap_platform` and the app function without them (Celery tasks degrade to... actually, confirm: `notifications`/`waitlist` tasks use `.delay()`, which requires a broker. **Flag this as a real gap to resolve in Phase 1 or Phase 4** — see Open Question below.
- Old app/site backup — `/home/scepter/ics` and `/home/scepter/ichebo-site-src` are left in place (not deleted) after cutover, in case anything needs to be referenced or rolled back to.

---

## Open Question Resolved Before Execution

**Redis is not installed, but `waitlist_register` and `notifications` call `.delay()` on Celery tasks — this will throw a connection error on every request that hits those code paths**, exactly as reproduced locally earlier this session. This must be resolved before Phase 3 cutover, not after, since the waitlist form (just fixed) would break immediately in production otherwise.

Resolution: install Redis + run Celery worker on this VPS as part of Phase 1, before cutover — small addition to the plan, not deferred. (ADR-008 "no Celery until Version 3 in real-world use" — that gate is already passed per `L10.1` in the roadmap, Redis+Celery is approved code, just not yet deployed infrastructure here.)

**Added to Phase 1:**

1a. Install Redis (`apt install redis-server`), enable + start it.
1b. Add `celery-worker` and `celery-beat` systemd services (per the deploy
    notes in `ics_project/celery.py` / the L10.1 commit), pointed at the new
    `/home/scepter/ichebo-platform` directory and venv.

---

## Rollback Plan

If cutover fails at Phase 3:
- `systemctl stop ics-gunicorn`, revert the systemd unit's `WorkingDirectory` back to `/home/scepter/ics`, `systemctl start ics-gunicorn` — old app comes back immediately since its directory and venv were never touched.
- Marketing site: rename the new `ichebo-site` back, restore the renamed-backup old directory.
- Database: since old data was confirmed disposable and the old app's schema is incompatible with the new code anyway, there is no meaningful "roll back the database" step — the old app was already going to lose its data in this cutover regardless of success.

---

## Exit Criteria

- [x] `https://app.ichebo.org` serves this repo's Django app, login works, static assets load
- [x] `https://ichebo.org` serves this repo's `ichebo-website`, waitlist form successfully creates a `WaitlistEntry` — confirmation email queued correctly but **not yet delivered** (Brevo credentials still placeholders, see Execution Log)
- [x] `python manage.py check --deploy` reports 0 issues against the real production `.env`
- [x] `bootstrap_platform` has run successfully — Handbook, Induction, Prime, 6 agencies, 24 Service Orders, 6 Qualification Programmes, Genesis Sceptre Community all exist
- [x] Redis + Celery worker + beat are running; task dispatch confirmed (`.delay()` reaches the worker with no connection error) — actual email send blocked on Brevo credentials, not the queue/worker pipeline
- [x] Old app (`/home/scepter/ics`) and old site source (`/home/scepter/ichebo-site-src`) are preserved on disk, not deleted
- [x] Daily backup cron continues to run against the new `ics_db` content (unmodified, still points at `ics_db`)

---

## Execution Log (2026-06-22)

Executed in full, Phases 1–3 and the Phase 4 verification checklist. Real
discrepancies found and corrected during execution, recorded here rather
than silently fixed, per this project's working convention:

1. **GitHub repo rename mid-session** — `origin` was `LarryMwansa/icebho-platform.git`
   (typo). GitHub auto-redirected the push but the local remote was corrected
   to `LarryMwansa/ichebo-platform.git` before the VPS clone, to avoid relying
   on the redirect long-term.

2. **Mono repo layout vs. the plan's assumed path** — the plan's Phase 1
   describes cloning to `/home/scepter/ichebo-platform`. Since this is a mono
   repo (contains `ichebo-platform/`, `ichebo-website/`, `ichebo-media/`,
   etc. as siblings), it was cloned to `/home/scepter/ichebo-platform-repo/`
   and the systemd unit's `WorkingDirectory` points at the nested
   `ichebo-platform-repo/ichebo-platform/` directory instead.

3. **`manage.py`'s `setdefault('DJANGO_SETTINGS_MODULE', 'ics_project.settings.base')`
   wins over `.env`'s value for any manually-run CLI command** — `migrate`,
   `bootstrap_platform`, and the first `collectstatic` run were executed
   without `DJANGO_SETTINGS_MODULE` explicitly exported, so they silently ran
   against `base.py`, not `production.py`. This does not affect the live
   running app (the systemd unit's `Environment=` line sets it correctly for
   gunicorn), but it meant `collectstatic` initially ran without
   `ManifestStaticFilesStorage`'s content-hashing. Fixed by re-running
   `collectstatic` (and confirming `migrate` needed no changes — `DATABASES`
   doesn't differ between `base` and `production`) with
   `DJANGO_SETTINGS_MODULE=ics_project.settings.production` explicitly
   exported in the shell.

4. **First-generated `SECRET_KEY` was 45 characters, not 50** — written via a
   bash heredoc containing a literal `$` character that the shell partially
   consumed before it reached the file. `check --deploy` caught this
   (`security.W009`). Regenerated using `sed` instead of a heredoc, verified
   the byte length before writing.

5. **`ics_user` lacks `CREATEDB` privilege** — `DROP DATABASE` succeeded as
   `ics_user`, but `CREATE DATABASE` required `sudo -u postgres psql`.
   Resolved by creating the fresh `ics_db` as the `postgres` superuser,
   `OWNER ics_user`, so the app's existing role continues to own and access
   it normally afterward.

6. **MinIO root credentials existed in `/etc/default/minio`, but no
   app-scoped access key did** — the old app's `.env` had no MinIO/S3 config
   at all, implying it never actually exercised object storage. Created a
   dedicated `ichebo-app` MinIO user with a `readwrite` policy rather than
   embedding root credentials in the new `.env`. The first generated secret
   for this user was visible in this session's tool output and was rotated
   immediately via `mc admin user add` (which updates an existing user's
   secret) before being used anywhere.

7. **Brevo SMTP credentials were not available this session** — `.env`
   contains `EMAIL_HOST_USER=REPLACE_ME_BREVO_LOGIN` and
   `EMAIL_HOST_PASSWORD=REPLACE_ME_BREVO_SMTP_KEY` as explicit placeholders.
   Confirmed via live Celery worker logs that the waitlist confirmation and
   internal-notification emails correctly queue, dispatch to the worker, and
   retry on `SMTPAuthenticationError` exactly as designed — the retry/backoff
   logic itself is proven correct. **Outstanding: replace these two values
   in `/home/scepter/ichebo-platform-repo/ichebo-platform/.env` with real
   Brevo SMTP credentials, then `sudo systemctl restart ics-celery
   ics-celery-beat ics-gunicorn`** so the new `.env` is re-read.

8. **Admin superuser password was generated server-side but printed to this
   session's tool output once** (to test the login flow end-to-end) —
   rotated immediately after the test login succeeded. Current password
   lives only in `/home/scepter/.admin-temp-password` on the server
   (`chmod 600`); retrieve and change it via the admin UI, then delete that
   file.

9. **nginx's `/static/` alias was never updated and still pointed at the old
   app's path** (`/home/scepter/ics/staticfiles/`) — missed during Phase 3
   because the plan's cutover steps focused on the systemd unit
   (`WorkingDirectory`), not nginx's separate, independently-hardcoded static
   path. Found after deploy when a logged-in user reported the dashboard
   rendering with no CSS (screenshot showed the workspace shell completely
   unstyled). Root cause confirmed precisely: `variables.css` and `main.css`
   returned 200 (likely stale copies of the same filenames existed in the old
   app's `staticfiles/` too), but `workspace.css`/`shell_v2.css`/`workspace_v2.css`
   — files specific to the Apostolic Command Shell built later in this
   project's history — returned 404, since they only exist in the new app's
   `staticfiles/`. Fixed by updating the `alias` in
   `/etc/nginx/sites-available/ics`'s `location /static/` block to
   `/home/scepter/ichebo-platform-repo/ichebo-platform/staticfiles/`,
   `nginx -t` validated, `systemctl reload nginx`. Re-verified: all CSS, JS,
   and image assets spot-checked now return 200 with real (non-empty)
   content. **`location /media/` was already correct** — it proxies to MinIO
   at `localhost:9000`, not a filesystem path, so it needed no change.

**Verified live, end to end:**

- `https://app.ichebo.org/` → 302 to login (correct, unauthenticated)
- Full HSTS / `X-Frame-Options: DENY` / secure-cookie headers present on a
  real response — confirms `production.py` hardening is active
- POST login with the real superuser credentials → 302 (successful auth)
- `https://ichebo.org/` → 200, correct title, correct content length matching
  the Vite build output
- `POST https://app.ichebo.org/api/waitlist/` with `Origin: https://ichebo.org`
  → 201, `access-control-allow-origin: https://ichebo.org` present (CORS
  correctly scoped, not wildcard), `WaitlistEntry` created, both Celery tasks
  dispatched and visible in the worker log within ~1 second
- Test waitlist entry removed from production data after verification
- All static assets (`variables.css`, `main.css`, `workspace.css`, `shell_v2.css`,
  `workspace_v2.css`, `htmx.min.js`, `navbar.js`, `images/logo.svg`) confirmed
  200 with real content after the nginx static-path fix (discrepancy 9 above)

**Not yet done (explicitly deferred per the plan, no action taken):**

- `ichebo-media` (Go video engine) — no Go toolchain on this server, no
  second server provisioned yet. Confirmed out of scope for this cutover.
