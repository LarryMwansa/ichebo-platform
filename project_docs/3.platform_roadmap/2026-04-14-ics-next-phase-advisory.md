# ICS Platform — Next Phase Advisory
**Date:** 2026-04-14  
**Branch:** `claude/plan-next-phase-fYdmY`  
**Status:** Approved — Pending Implementation

---

## Context

The ICS (Ichebo Christian Services) platform has completed its **initial build phase**, which turns out to be substantially more complete than a typical scaffold. Based on thorough exploration of both the project documentation (roadmap, system designs, data contract) and the actual source files, the platform is approximately **70–80% complete toward MVP**. Most roadmap phases (0–6) have working implementations.

This document identifies what is genuinely missing, what needs hardening, and the recommended priority order for the next phase of development.

---

## Actual State vs Roadmap (Honest Assessment)

| Phase | Roadmap Description | Actual State |
|-------|---------------------|--------------|
| **0** | VPS + Django scaffold + health check | ✅ Complete |
| **1** | Auth + Tenant + Identity + Permissions | ✅ Complete — User (UUID, competence_level 0–5), Tenant (9-tier hierarchy), UserPermission, Token auth |
| **2** | Records Engine (Django + DRF) | ✅ Complete — Record (40+ fields, versioning, soft delete), Relationship (16 types), full DRF |
| **3** | Activity Engine (Django + DRF) | ✅ Complete — Activity (9 types, recurrence, progress%), ActivityLog, DRF |
| **4** | Identity + Tenant JS services | ⚠️ Partial — Only `navbar.js`, `storage.js` exist; `identity.service.js`, `tenant.service.js` not found |
| **5a** | Bible App | ✅ Complete — BibleTranslation/Book/Verse models, HTMX chapter reader |
| **5b** | Learn App (7 sub-phases A–G) | ✅ Complete — 14 view endpoints + 6 HTMX partials; enrolment, progression, certification, authorship, review queue |
| **5c** | Community App | ⚠️ Partial — Views exist (584 LOC) but MembershipRequest explicitly "deferred to Phase 2" |
| **5d** | Governance App | ✅ Complete — Library (Level 3+), Mandate (4+/5+), My Keys, version chains, HRS attributes, atomic supersede |
| **5e** | Profile + Settings | ✅ Complete — profile read/write, theme/language/timezone in preferences JSONField |
| **5f** | Notifications (stub) | ⚠️ Explicit stub — "no Notification model in MVP" per source comments |
| **6** | Paraclete Service | ✅ Complete — Real orchestration logic (406 LOC), 9 dataclasses, digest engine; only "suggestions" deferred |
| **7** | Dashboard | ⚠️ Minimal — `dashboard/views.py` is only 10 LOC; needs Paraclete digest rendering |
| **8** | Production Hardening | ⚠️ Partial — Gunicorn configured; SSL/certbot, systemd, static file caching unverified |

> **Only 1 confirmed stub in production code:** `paraclete/service.py` lines 88–90 — suggestions feature explicitly deferred to post-MVP.

---

## Critical Gaps (Priority Order)

### 1. Test Coverage — Zero Tests Written (HIGHEST RISK)
- **All 11 `tests.py` files are empty stubs**
- Risk: Any refactor or deployment change could silently break core journeys
- Recommended: Write tests before adding any new features

### 2. Dashboard Depth (Phase 7 Incomplete)
- `dashboard/views.py` — only 10 LOC; Paraclete digest exists but is not rendered
- The service (`paraclete/service.py`) returns a full `ParacleteDigest` object but the dashboard view does not render widgets
- Needs: Role-aware widget rendering, Today's focus, pending activities, active prayer count, discipline prompt

### 3. Template Completeness — Unknown
- Views are implemented but templates have not been fully verified
- HTMX partial templates (e.g. `learn/partials/`, `governance/partials/`) need a complete audit
- Risk: Views can reference templates that don't exist yet

### 4. Community Membership Flow (Deferred)
- `community/models.py` — MembershipRequest model exists but is explicitly deferred
- `community/views.py` — 584 LOC of views but the membership approval flow is incomplete
- Needs: Request submit → tenant steward review → approve/reject → UserPermission creation

### 5. Frontend JS Service Layer (Phase 4 Incomplete)
- Roadmap calls for: `identity.service.js`, `tenant.service.js`, `records.service.js`, `activity.service.js`, `paraclete.service.js`
- Only `navbar.js` and `storage.js` currently exist
- HTMX likely replaces most JS service layer needs, but competence-level-aware route guarding is still missing

### 6. Auth: Token vs JWT — Decision Needed
- `requirements.txt` uses `djangorestframework` authtoken
- Roadmap specifies **JWT token auth**
- Risk: If external clients (mobile app, third-party integrations) are planned, JWT is strongly preferred
- Decision required: Commit to Token auth (simpler, web-only) OR migrate to JWT (`djangorestframework-simplejwt`)

### 7. Production Hardening (Phase 8)
- SSL via Let's Encrypt (certbot) — status unverified
- Static files served by Nginx — status unverified
- Systemd service for Gunicorn auto-restart — not created
- Error logging to file — not configured
- Django admin model registration — likely empty across all apps

---

## Recommended Next Phase: Focus Areas

### Priority 1 — Test Foundation (1–2 weeks)
Establish test coverage for all core journeys before building anything new.

**Critical test targets:**

| File | What to test |
|------|-------------|
| `accounts/tests.py` | User registration, login, competence_level assignment |
| `tenants/tests.py` | Tenant creation, UserPermission assignment, role hierarchy |
| `records/tests.py` | Record CRUD, Relationship creation, version chain (supersede), soft delete, permission gating |
| `activity/tests.py` | Activity create/complete, ActivityLog entries, recurrence logic |
| `learn/tests.py` | Enrolment, lesson completion, certification confirmation, competence advancement |
| `governance/tests.py` | Library access (Level 3+), mandate CRUD, atomic supersede transaction |
| `paraclete/tests.py` | `build_digest()` returns correct `ParacleteDigest` shape for various user states |

**Approach:** Django `TestCase` + DRF `APITestCase`; use `factory_boy` for fixtures; start with happy path, then permission gates.

### Priority 2 — Dashboard (Complete Phase 7) (3–5 days)
- Expand `dashboard/views.py` to render `ParacleteDigest` with role-aware widgets
- Leverage the already-working `paraclete/service.py::build_digest()`
- Wire all digest fields into `templates/dashboard/dashboard.html`
- Add HTMX refresh for live digest updates

### Priority 3 — Template Audit (2–3 days)
- Audit every app's `templates/` directory
- For each app verify: base template, list/detail pages, HTMX partials all exist and render
- Smoke test each view via Django test client
- Priority apps: `learn` (complex HTMX partials), `governance` (versioning UI), `bible` (chapter navigation)

### Priority 4 — Community Membership Flow (1 week)
- Complete MembershipRequest submit/approve/reject flow
- Wire `community/views.py` to create `tenants.UserPermission` on steward approval
- This unblocks onboarding for real users joining tenant communities

### Priority 5 — Production Hardening (Phase 8) (3–5 days)
- **SSL:** `certbot --nginx -d yourdomain.com`
- **Static files:** verify `STATIC_ROOT`, run `collectstatic`, confirm Nginx serves from that path
- **Systemd:** create `/etc/systemd/system/ics-gunicorn.service` for auto-restart on reboot
- **Logging:** configure `LOGGING` in `settings/production.py` → `/var/log/ics/`
- **Django admin:** register all models in each app's `admin.py`

---

## Risk Flags

| Risk | Impact | Mitigation |
|------|--------|------------|
| Zero test coverage | **High** — silent regressions on any change | Write tests for core models and permission gates first |
| Token auth vs JWT undecided | **Medium** — API client compatibility | Decide now; JWT migration touches all auth flows |
| Template gaps | **High** — broken views in production | Audit templates directory; add missing partials |
| Dashboard is minimal | **Medium** — primary UX surface is broken | Implement digest rendering before any demo or release |
| Community membership deferred | **Medium** — onboarding is incomplete | Schedule for next sprint |
| Notifications stubbed | **Low** (explicitly planned) | Accept for now; build post-MVP |
| Paraclete suggestions stubbed | **Low** (explicitly planned) | Accept for now; build post-MVP |

---

## Immediate Top-5 Actions

1. **Audit templates directory** — Map every view to its template; identify missing templates before any new feature work
2. **Write model-level tests** — Start with `records` and `accounts`; these are the foundation everything else depends on
3. **Implement dashboard rendering** — Connect `build_digest()` to a real dashboard template; this is the primary user-facing surface
4. **Decide JWT vs Token auth** — One-time architectural decision; document the outcome and implement consistently
5. **Run production smoke test** — Manually exercise each core journey end-to-end: register → login → enrol in programme → complete lesson → view governance mandate

---

## Verification Checklist

```bash
# Run all tests (baseline — currently all empty)
python manage.py test

# Core journey smoke test (manual or test client):
# 1. Register new user → verify competence_level=0
# 2. Login → verify token returned
# 3. Create tenant → assign UserPermission
# 4. Access /learn/ → view catalogue
# 5. Enrol in programme → verify Activity created with correct metadata
# 6. Complete lesson → verify ActivityLog entry
# 7. Access /governance/ → verify Level 3+ gate enforced
# 8. GET /api/paraclete/digest/ → verify ParacleteDigest JSON shape

# Check for template/config issues
python manage.py check --deploy
```

---

## Files to Act On

| File | Action Required |
|------|----------------|
| `accounts/tests.py` | Write: User model tests, auth endpoint tests |
| `records/tests.py` | Write: Record CRUD, Relationship, version chain tests |
| `learn/tests.py` | Write: Enrolment, completion, certification tests |
| `governance/tests.py` | Write: Permission gates, atomic supersede transaction tests |
| `paraclete/tests.py` | Write: `build_digest()` output tests |
| `dashboard/views.py` | Expand: Wire `ParacleteDigest` to template (currently 10 LOC) |
| `templates/dashboard/` | Audit/Create: Dashboard template with all widget sections |
| `community/views.py` | Complete: Membership request submit/approve/reject flow |
| `ics_project/settings/production.py` | Review: Logging, static files, ALLOWED_HOSTS |
| All `admin.py` files | Register: Models for Django admin access |
