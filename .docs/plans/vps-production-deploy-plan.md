# Production Deploy — ichebo-platform + ichebo-website to the existing VPS

**Version:** 1.0 — 2026-06-22
**Status:** Approved — executing
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

- [ ] `https://app.ichebo.org` serves this repo's Django app, login works, static assets load
- [ ] `https://ichebo.org` serves this repo's `ichebo-website`, waitlist form successfully creates a `WaitlistEntry` and the signee receives a confirmation email
- [ ] `python manage.py check --deploy` reports 0 issues against the real production `.env`
- [ ] `bootstrap_platform` has run successfully — Handbook, Induction, Prime, 6 agencies, 24 Service Orders, 6 Qualification Programmes, Genesis Sceptre Community all exist
- [ ] Redis + Celery worker + beat are running; a real notification/email task completes via `.delay()` without a connection error
- [ ] Old app (`/home/scepter/ics`) and old site source (`/home/scepter/ichebo-site-src`) are preserved on disk, not deleted
- [ ] Daily backup cron continues to run against the new `ics_db` content
