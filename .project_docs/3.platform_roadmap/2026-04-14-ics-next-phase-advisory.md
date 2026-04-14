# ICS Platform — Next Phase Advisory
**Date:** 2026-04-14  
**Reviewed against:** `production_instance` branch (merged 2026-04-14), Roadmap v3 (2026-04-12), CHANGELOG (2026-04-13)  
**Branch:** `claude/plan-next-phase-fYdmY`  
**Status:** Updated after production_instance merge

---

## Context

The ICS platform has completed its initial build phase. After merging the `production_instance` branch — which is the canonical source of truth — and reviewing roadmap v3 alongside the actual code, this advisory corrects several significant misreadings from the initial plan and establishes the true next phase.

---

## Corrections to Initial Advisory (What Changed After the Merge)

| Area | Initial Assessment | Corrected Assessment |
|------|--------------------|----------------------|
| **Phase 4 (JS services)** | Flagged as "incomplete" | **REMOVED by design in v3** — `@login_required` handles auth guards; tenant context is request-scoped in views; no JS layer needed |
| **Dashboard** | "Minimal — 10 LOC" | **Significantly improved** — tab UI (Overview, Governance, Calendar, Records), context-aware drawer, Material Icons all shipped (CHANGELOG 2026-04-13) |
| **Bible App** | "Complete, HTMX chapter reader" | **Major UI overhaul shipped** — full-screen picker, real-time search page, sticky navigator strip, scroll-hide behavior, drawer-based notes (CHANGELOG 2026-04-13) |
| **Learn/Governance/Paraclete views** | "Production-ready, 70–80% MVP" | **Pending per roadmap v3** — extensive view code exists from initial build on `main` but these tasks are marked IN PROGRESS / PENDING in the canonical roadmap; require reconciliation with system design docs |
| **Settings persistence** | "localStorage only" | **Database** — `User.preferences` JSONField (roadmap v3 confirms this explicitly; the v1/v2 localStorage note is superseded) |
| **Phase numbering** | Used v2 numbering | **Roadmap v3 renumbers**: Dashboard = Phase 6.2, Production hardening = Phase 7 |

---

## Actual State vs Roadmap v3 (Corrected Assessment)

| Phase | Roadmap v3 Description | Canonical Status |
|-------|------------------------|-----------------|
| **0** | VPS + Django scaffold + health check | ✅ Complete |
| **1** | Auth + Tenants + HTMX Shell | ✅ Complete |
| **2** | Records Engine | ✅ Complete |
| **3** | Activity Engine | ✅ Complete |
| **4** | Identity + Tenant JS services | ✅ Removed — not applicable to HTMX architecture |
| **5.1** | Bible App | ✅ Complete + UI overhaul shipped (2026-04-13) |
| **5.2** | Learn App (7 sub-phases A–G) | 🔄 In Progress — system design complete, build pending |
| **5.3** | Activity App UI layer | ⏳ Pending |
| **5.4** | Community App | ⏳ Pending |
| **5.5** | Governance App | ⏳ Pending |
| **5.6** | Profile + Settings | ⏳ Pending |
| **5.7** | Notifications Stub | ⏳ Pending |
| **6.1** | Paraclete Service | ⏳ Pending |
| **6.2** | Dashboard (digest rendering + widgets) | ⏳ Pending — shell UI exists; digest wiring not built |
| **7** | Production Hardening | ⏳ Pending |

---

## The Code Reconciliation Problem

The `main` branch contains extensive view code for apps that roadmap v3 marks as Pending (learn/views.py 478 LOC, governance/views.py 465 LOC, paraclete/service.py 406 LOC). This code was written during a rapid initial build and **may not conform to the system design specifications**.

**Before building any new feature, this must be assessed:**

For each pending app (5.2 Learn → 5.5 Governance), compare the existing view code against the relevant system design document:
- Does the existing code implement the correct URL routes per roadmap v3?
- Does it use the correct Record discriminators (`record_family`, `record_type`) per the data contract?
- Does it follow the correct access level gates (Level 3+, Level 4+, Level 5)?
- Does it use the correct HTMX partial pattern (HX-Request header detection)?

If yes — retain and clean up. If no — rewrite per the system design doc. **Do not build on top of code that doesn't match the spec.**

---

## Recommended Next Phase (Priority Order)

### Priority 1 — Code Reconciliation Audit (2–3 days)

Before writing a single new line, audit what the initial build produced vs what roadmap v3 requires.

**Process for each pending app:**
1. Open the app's system design doc (referenced in roadmap v3 per task)
2. Compare existing views against the spec'd URL routes, data patterns, access gates
3. Mark each view as: ✅ Conforms | ⚠️ Needs adjustment | ❌ Rewrite required
4. Document findings before touching code

**Apps to audit:**
- `learn/views.py` → `.project_docs/5.learn_app/2026-04-07-ics-learn-app-system-design_v2.md`
- `governance/views.py` + `governance/services.py` → `.project_docs/8.governance_app/2026-04-10-ics-governance-app-system-design.md`
- `community/views.py` → `.project_docs/7.community_app/2026-04-08-ics-community-app-system-design.md`
- `paraclete/service.py` + `paraclete/views.py` → `.project_docs/9.paraclete/2026-04-10-ics-paraclete-service-system-design.md`

### Priority 2 — Task 5.2: Learn App (1–2 weeks)

This is the current roadmap task. Build in strict phase order per the system design doc.

**7 phases (A–G):**

| Phase | What it builds |
|-------|----------------|
| A | `CertificationConfirmation` model, `/api/learn/certifications/{id}/confirm/` endpoint, `/api/learn/certifications/queue/` |
| B | Verify Records endpoint filters work for `record_family: "learning"`; curriculum endpoint |
| C | Django template views + HTMX partials: My Learning, Catalogue, Enrolment, Lesson Viewer |
| D | Quiz renderer, Assignment submission |
| E | Auto-certification signal, steward cert queue UI, competence level advancement |
| F | Content authorship UI (Level 4+), Handbook review queue (Level 5) |
| G | Role-aware navigation, Pathway banner, mobile smoke test |

**Critical reference:** `.project_docs/5.learn_app/2026-04-07-ics-learn-app-system-design_v2.md`

**Exit criteria:** `POST /api/learn/certifications/{id}/confirm/` increments `competence_level` in DB. Verifiable in Django admin.

### Priority 3 — Task 5.3: Activity App UI (3–5 days)

Build the UI layer on top of the already-complete Activity Engine (Phase 3).

**Two surfaces:**
- My Activities: personal (`tenant_id: null`), types: task, habit, goal, skill, reminder
- Ministry: tenant-scoped, types: campaign, project, task, event

**Reference:** `.project_docs/6.activity_app/2026-04-08-ics-activity-app-system-design.md`

### Priority 4 — Tasks 5.4, 5.5, 5.6, 5.7 (2–3 weeks combined)

Build in strict roadmap order:
1. **5.4 Community App** — member directory, announcements, gatherings (dual-write with activity/event via `transaction.atomic()`)
2. **5.5 Governance App** — Reference Library (Level 3+), Mandate (Level 4+/5+), Keys, version chains
3. **5.6 Profile + Settings** — profile read/write, settings persist to `User.preferences` JSONField
4. **5.7 Notifications Stub** — empty list endpoint + HTMX badge poll; no new model in MVP

### Priority 5 — Phase 6: Paraclete + Dashboard (1 week)

Only begin after all Phase 5 apps are complete (Paraclete reads from all of them).

- **6.1 Paraclete service** — orchestration engine: digest, reminders, prompt, suggestions stub
- **6.2 Dashboard** — wire `build_digest()` to dashboard template; role-aware widgets (Level 3+ sees ministry summary); HTMX partial refresh

**Dashboard tab structure already built (CHANGELOG 2026-04-13)** — the shell is ready. What's missing is the data wiring from Paraclete.

### Priority 6 — Phase 7: Production Hardening (3–5 days)

- Error logging → `/var/log/ics/django_errors.log`
- `collectstatic` verified, Nginx serving from `staticfiles/`
- Systemd unit (`/etc/systemd/system/ics.service`) for Gunicorn auto-restart
- SSL via certbot (may already be configured from Task 0.5)
- Django admin: register all models across all apps
- All health endpoints return 200

---

## Risk Flags

| Risk | Impact | Mitigation |
|------|--------|------------|
| Initial build code doesn't match system design specs | **High** — building on misaligned code causes cascading rework | Reconciliation audit before any new development |
| Build order violation | **High** — Learn depends on Activity; Paraclete depends on all Phase 5 apps | Follow roadmap v3 dependency rules strictly |
| Zero test coverage | **High** — any rework or deployment change can silently break things | Write tests as each app is completed, not deferred to end |
| Dashboard digest wiring absent | **Medium** — dashboard shell exists but has no live data | Wire Paraclete service to dashboard at Phase 6.2 |
| Community gathering dual-write complexity | **Medium** — atomically writes Community Record + Activity event | Use `transaction.atomic()` as specified in roadmap v3 |
| Notifications deferred | **Low** (explicitly planned) | Accept stub in MVP; build triggers post-MVP |

---

## Build Dependency Chain (Non-Negotiable)

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Task 5.1 ✅
                                       → Task 5.2 (Learn) 🔄 NOW
                                       → Task 5.3 (Activity UI)
                                       → Task 5.4 (Community)
                                       → Task 5.5 (Governance)
                                       → Task 5.6 (Profile)
                                       → Task 5.7 (Notifications stub)
                                       → Phase 6.1 (Paraclete)
                                       → Phase 6.2 (Dashboard)
                                       → Phase 7 (Hardening)
```

> Phase 4 is permanently removed from this chain.

---

## Test Strategy

Write tests per app as each task is completed — not deferred to the end.

**Pattern for each app:**
- `TestCase` for Django model logic (relationships, computed fields, signal handlers)
- `APITestCase` for DRF endpoint auth, permissions, response shape
- Competence-level gate tests: verify Level 2 user cannot access Level 3+ views

**Start with** records and accounts (foundation); every other app depends on these.

---

## Immediate Next Action

1. Read `.project_docs/5.learn_app/2026-04-07-ics-learn-app-system-design_v2.md` in full
2. Compare existing `learn/views.py` against the spec — mark conforming vs non-conforming
3. Begin Task 5.2 Phase A: verify `CertificationConfirmation` model matches spec
4. Build Phases B–G in order per the system design doc
5. Commit per phase: `git commit -m "feat: learn app — phase A: model + confirm endpoint"`

---

## Key Reference Documents (Post-Merge Paths)

| Document | Path |
|----------|------|
| Roadmap v3 | `.project_docs/2026-04-12-ics-build-roadmap_v3.md` |
| Data contract v9 | `.project_docs/2.platform_data-contract/ver/2026-04-10-ics-platform-data-contract_v9-amendments.md` |
| Learn App system design | `.project_docs/5.learn_app/2026-04-07-ics-learn-app-system-design_v2.md` |
| Activity App system design | `.project_docs/6.activity_app/2026-04-08-ics-activity-app-system-design.md` |
| Community App system design | `.project_docs/7.community_app/2026-04-08-ics-community-app-system-design.md` |
| Governance App system design | `.project_docs/8.governance_app/2026-04-10-ics-governance-app-system-design.md` |
| Paraclete system design | `.project_docs/9.paraclete/2026-04-10-ics-paraclete-service-system-design.md` |
| HTMX Migration ADR | `.project_docs/ui_build-and-dev/2026-04-07-ics-htmx-migration-adr.md` |
| CHANGELOG | `CHANGELOG.md` |
