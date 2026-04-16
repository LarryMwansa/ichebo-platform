# ICS Platform — Code Reconciliation Audit
**Date:** 2026-04-14  
**Branch:** `claude/plan-next-phase-fYdmY`  
**Scope:** learn, governance, community, paraclete apps  
**Reference:** Roadmap v3 (`2026-04-12`), each app's system design doc

---

## Executive Summary

| App | Conformance | Verdict |
|-----|------------|---------|
| **Learn** | ~65% | API layer solid. URL paths misaligned. 4 HTMX partials missing. Auto-cert signal absent. |
| **Governance** | ~70% | Logic and permission gates correct. URL paths use `/library/` instead of `/reference/`. 3 endpoints missing. FK naming needs verification. |
| **Community** | ~60% | Data patterns and dual-write correct. URL paths nested under `/management/` vs flat spec. Gatherings list + detail views missing. |
| **Paraclete** | ~95% | All endpoints present. Digest shape exact match. Read-only confirmed. Caching implemented. One minor URL dependency on Learn. |

**Overall assessment:** The initial build has correct *logic and data patterns* across all four apps. The gaps are primarily **URL contract adherence**, **missing HTMX partials**, and **missing signals**. No full rewrites required. Targeted fixes per app.

---

## App 1 — Learn App

### URL Route Comparison

| Route (Spec) | Route (Code) | Status | Fix Required |
|---|---|---|---|
| `GET /learn/` | `GET /learn/` | ✅ Matches | — |
| `GET /learn/catalogue/` | `GET /learn/programmes/` | ⚠️ Path mismatch | Rename to `/catalogue/` |
| `GET /learn/programme/{id}/` | `GET /learn/programmes/<id>/` | ⚠️ Path mismatch | Rename to `/programme/<id>/` |
| `GET /learn/lesson/{id}/` | `GET /learn/lessons/<id>/` | ⚠️ Path mismatch | Rename to `/lesson/<id>/` |
| `GET /learn/htmx/my-learning/` | **Missing** | ❌ Absent | Add HTMX partial |
| `GET /learn/htmx/catalogue/` | **Missing** | ❌ Absent | Add HTMX partial |
| `GET /learn/htmx/progress/{id}/` | **Missing** | ❌ Absent | Add HTMX partial |
| `GET /learn/htmx/cert-queue/` | **Missing** | ❌ Absent | Add HTMX partial |
| `POST /learn/htmx/enrol/{id}/` | `POST /learn/htmx/enrol/<id>/` | ✅ Matches | — |
| `POST /learn/htmx/progress/{id}/update/` | `POST /learn/htmx/complete-lesson/<id>/` | ⚠️ Path + semantic mismatch | Rename; expand to progress % not just complete |
| `GET /api/learn/health/` | `GET /api/learn/health/` | ✅ Matches | — |
| `GET /api/learn/programmes/{id}/curriculum/` | `GET /api/learn/programmes/<id>/curriculum/` | ✅ Matches | — |
| `GET /api/learn/certifications/queue/` | `GET /api/learn/certifications/queue/` | ✅ Matches | — |
| `POST /api/learn/certifications/{id}/confirm/` | `POST /api/learn/certifications/<id>/confirm/` | ✅ Matches | — |

**Extra routes in code not in spec** (not wrong — spec may have omitted them):
- `/learn/certifications/` — full-page steward cert queue
- `/learn/author/`, `/learn/author/programme/`, `/learn/author/course/`, `/learn/author/lesson/` — authorship UI
- `/learn/review/` — Level 5 review queue
- `/learn/htmx/confirm-cert/<id>/` — HTMX cert confirmation
- `/learn/htmx/approve-content/<id>/`, `/learn/htmx/return-content/<id>/` — Level 5 approval

### Data Patterns

| Check | Status | Notes |
|---|---|---|
| `record_family='learning'` | ✅ Correct | Used consistently in all views |
| `record_type`: programme/course/lesson/quiz/certification | ✅ Correct | All types used correctly |
| Curriculum via `Relationship(part_of)` | ✅ Correct | Both views and API use this correctly |
| Enrolment as `Activity(activity_type='programme')` | ✅ Correct | Metadata includes `programme_record_id` |
| `CertificationConfirmation` model | ✅ Exact match | All spec fields present; correct indexes |
| `confirm_certification` is sole writer of `competence_level` | ✅ Correct | Gated to Level 3+; creates audit record |

### Missing Features

| Feature | Status | Notes |
|---|---|---|
| Auto-certification signal (programme Activity → 100% → create draft cert Record) | ❌ Missing | No `signals.py` in learn app; this is Phase E logic |
| 4 HTMX partials (my-learning, catalogue, progress, cert-queue) | ❌ Missing | Views exist but no partial-only counterparts |
| Progress bar update HTMX (not just lesson complete) | ❌ Missing | `htmx_complete_lesson` sets 100% only; no partial progress |

### Verdict
**API layer: ✅ Production-ready.** The `confirm_certification` endpoint, curriculum endpoint, and cert queue are correct and complete.  
**Template view layer: ⚠️ Needs URL alignment + 4 HTMX partials added.**  
**Signal layer: ❌ Auto-cert signal must be built (Phase E).**

---

## App 2 — Governance App

### URL Route Comparison

| Route (Spec) | Route (Code) | Status | Fix Required |
|---|---|---|---|
| `GET /governance/` | `GET /governance/` | ✅ Matches | — |
| `GET /governance/reference/` | `GET /governance/library/` | ❌ Path mismatch | Rename all `/library/` → `/reference/` |
| `GET /governance/reference/{type}/` | `GET /governance/library/{type}/` | ❌ Path mismatch | Same rename |
| `GET /governance/reference/{id}/` | `GET /governance/library/record/{id}/` | ❌ Path + extra `/record/` | Remove `/record/` wrapper |
| `GET /governance/mandate/` | `GET /governance/mandate/` | ✅ Matches | — |
| `GET /governance/mandate/{type}/` | `GET /governance/mandate/{type}/` | ✅ Matches | — |
| `GET /governance/mandate/{id}/` | `GET /governance/mandate/record/{id}/` | ⚠️ Extra `/record/` wrapper | Remove `/record/` wrapper |
| `GET /governance/keys/` | `GET /governance/keys/` | ✅ Matches | — |
| `GET /governance/keys/{id}/` | `GET /governance/keys/<id>/` | ✅ Matches | — |
| `GET /governance/htmx/reference/list/` | **Missing** | ❌ Absent | Add HTMX list partial |
| `GET /governance/htmx/mandate/list/` | **Missing** | ❌ Absent | Add HTMX list partial |
| `POST /governance/htmx/record/create/` | `POST /governance/htmx/record/create/` | ✅ Matches | — |
| `POST /governance/htmx/record/{id}/lock/` | `POST /governance/htmx/record/<id>/lock/` | ✅ Matches | — |
| `POST /governance/htmx/record/{id}/supersede/` | `POST /governance/htmx/record/<id>/supersede/` | ✅ Matches | — |
| `GET /governance/htmx/record/{id}/links/` | `GET /governance/htmx/relationships/<id>/` | ⚠️ Path mismatch | Rename to `/record/<id>/links/` |
| `GET /governance/htmx/record/{id}/history/` | `GET /governance/htmx/versions/<id>/` | ⚠️ Path mismatch | Rename to `/record/<id>/history/` |
| `GET /governance/htmx/journal/search/` | **Missing** | ❌ Absent | Add journal typeahead |
| `GET /api/governance/health/` | `GET /api/governance/health/` | ✅ Matches | — |

### Data Patterns & Logic

| Check | Status | Notes |
|---|---|---|
| Library types (class, principle, concept, divine_pattern, etc.) | ✅ Correct | Present in `LIBRARY_TYPES` constant |
| Mandate types (mandate, statement, programme, protocol, procedure) | ✅ Correct | Present in `MANDATE_TYPES` constant |
| Reference Library: Level 3+ read, Level 5 write | ✅ Correct | Enforced in all library views |
| Mandate: Level 4+ read, Level 5 write | ✅ Correct | Enforced in all mandate views |
| Keys Library: owner only, Level 3+ | ✅ Correct | `created_by=request.user` filter + level check |
| Lock: Level 5 | ✅ Correct | Enforced in `htmx_record_lock` |
| Supersede: Level 5 + `transaction.atomic()` | ✅ Correct | Wrapped in `create_new_version()` |
| HRS custom_fields (complexity, polarity, position, direction, speed, emotional_tone) | ✅ Correct | Present in choices constants + form handling |
| Record lifecycle: draft → active → locked → superseded | ✅ Correct | No approval queue (correct for MVP) |
| HTMX partial detection (HX-Request header) | ✅ Correct | `_htmx()` helper used throughout |
| `previous_version_id` FK naming | ⚠️ **Verify** | Code uses `previous_version=old_record` (FK assignment); confirm Record model field name matches |

### Verdict
**Business logic: ✅ Production-ready.** Access gates, data patterns, version chains, and atomic supersede all correct.  
**URL paths: ❌ `/library/` must be renamed to `/reference/`.** HTMX path names for links and history also need renaming.  
**Missing: ❌ 3 endpoints** — reference list partial, mandate list partial, journal search typeahead.  
**FK naming: ⚠️ Verify `previous_version` field name on `Record` model** before any version chain operations.

---

## App 3 — Community App

### URL Route Comparison

| Route (Spec) | Route (Code) | Status | Fix Required |
|---|---|---|---|
| `GET /community/` | `GET /community/` | ✅ Matches | — |
| `GET /community/members/` | `GET /community/management/members/` | ⚠️ Path nested under `/management/` | Consider flattening |
| `GET /community/gatherings/` | **Missing** | ❌ Absent | Add gatherings list view |
| `GET /community/{id}/` | **Missing** | ❌ Absent | Add gathering/announcement detail view |
| `GET /community/htmx/members/` | `GET /community/htmx/members/search/` (different semantics) | ⚠️ Path mismatch | Add `/htmx/members/` partial or align |
| `GET /community/htmx/announcements/` | `GET /community/htmx/announcements/` | ✅ Matches | — |
| `GET /community/htmx/gatherings/` | **Missing** | ❌ Absent | Add gatherings HTMX partial |
| `POST /community/htmx/gathering/create/` | `POST /community/htmx/gathering/create/` | ✅ Matches | — |
| `POST /community/htmx/announcement/create/` | `POST /community/htmx/announcement/create/` | ✅ Matches | — |
| `GET /api/community/health/` | Registered inside `community/urls.py` (wrong location) | ⚠️ Routing issue | Move to `ics_project/urls.py` prefix |

**Extra routes in code (bonus, not wrong):**
- `/community/management/` — management home
- `/community/management/pipeline/` — formation pipeline (Level 3+)
- `/community/management/members/<id>/` — member profile detail
- HTMX tools: shepherd assignment, service order, deactivate member, member search — all Level 3+

### Data Patterns & Logic

| Check | Status | Notes |
|---|---|---|
| `record_family='community'`, types: `announcement`, `gathering` | ✅ Correct | Used consistently |
| Gathering `custom_fields`: format, location, stream_url, capacity | ✅ Correct | All four fields present |
| `format` choices: `in_person`, `digital`, `hybrid` | ✅ Correct | Validated in form |
| Dual-write gathering via `transaction.atomic()` | ✅ Correct | Both Record + Activity created atomically |
| Activity type for gathering: `event` with `metadata.source_app='community'` | ✅ Correct | Feeds correctly into Calendar |
| Relationship linking gathering Record to Activity | ✅ Present | Uses `aligns_with` relationship type with `metadata.linked_activity_id` |
| `MembershipRequest` model: schema stubbed, no UI | ✅ Correct | Model exists with correct fields; no views wired |
| My Community: Level 1+ | ✅ Correct | `my_community` checks level >= 1 |
| Management surface: Level 3+ | ✅ Correct | All management views check level >= 3 |
| Tenant-scoped member directory | ✅ Correct | Uses `UserPermission.tenant.path__startswith` |

### Verdict
**Data logic: ✅ Production-ready.** Dual-write is correct, data patterns are correct, access gates are correct.  
**URL paths: ⚠️ Management routes nested under `/management/` prefix.** Spec uses flat routes like `/community/members/`. Decide whether to flatten or treat the spec URL as the "steward-facing" entrypoint.  
**Missing: ❌ Gatherings list, gatherings HTMX partial, and detail view** for gathering/announcement.  
**Health endpoint: ⚠️ Registered in wrong URL file** — should be under `/api/` prefix in `ics_project/urls.py`.

---

## App 4 — Paraclete Service

### Endpoint Comparison

| Endpoint (Spec) | Code | Status | Notes |
|---|---|---|---|
| `GET /api/paraclete/digest/` | `DigestView` | ✅ Matches | With 5-min cache |
| `GET /api/paraclete/reminders/` | `RemindersView` | ✅ Matches | Returns from digest |
| `GET /api/paraclete/suggest/{record_id}/` | `SuggestView` | ✅ Matches (stub) | Returns `[]` + `"method": "deferred"` |
| `GET /api/paraclete/prompt/` | `PromptView` | ✅ Matches | Returns prompt + pathway |
| `POST /api/paraclete/respond/` | `RespondView` | ✅ Matches (stub) | Returns 200 OK, no DB write |
| `GET /api/paraclete/health/` | `health` | ⚠️ Missing `AllowAny` | Add `@permission_classes([AllowAny])` |

### ParacleteDigest Shape

| Field (Spec) | Dataclass | Status |
|---|---|---|
| `generated_at` | ✅ Present | — |
| `user_id` | ✅ Present | — |
| `competence_level` | ✅ Present | — |
| `pending_count` | ✅ Present | — |
| `overdue_count` | ✅ Present | — |
| `due_today` | ✅ Present | Up to 5 items |
| `overdue_items` | ✅ Present | Up to 5 items |
| `habit_streaks` | ✅ Present | Daily habits only |
| `pending_reminders` | ✅ Present | Within 24h window |
| `active_enrolments` | ✅ Present | `ProgrammeCard[]` |
| `next_lesson` | ✅ Present | `LessonCard | null` |
| `discipline_prompt` | ✅ Present | — |
| `prompt_pathway` | ✅ Present | — |
| `dar_today` | ✅ Present | `DARCard | null` |
| `suggestions` | ✅ Present | Always `[]` in MVP |
| `suggestion_method` | ✅ Present | Always `"deferred"` in MVP |
| `team_pending_count` | ✅ Present | `null` for Level 0–2 |
| `team_overdue_count` | ✅ Present | `null` for Level 0–2 |

### Service Behaviour

| Check | Status | Notes |
|---|---|---|
| Read-only — never writes to any table | ✅ Confirmed | Source comment + code verified |
| Called as Python import (not via HTTP) | ✅ Confirmed | `from .service import build_digest` |
| 5-minute cache per user | ✅ Implemented | `cache.set(key, data, 300)` |
| Graceful with empty data (no crash if Learn/Community data absent) | ✅ Confirmed | All ORM queries use `filter()` → empty QuerySet |
| `ParacletePrompt` model used for prompts | ✅ Confirmed | Falls back to default if no prompts seeded |
| `next_lesson` URL | ⚠️ Minor | Uses `/learn/lesson/{id}/` — must match actual Learn URL once aligned |

### Verdict
**✅ Near-complete. Only two minor issues:**
1. Health endpoint missing `@permission_classes([AllowAny])` — one-line fix
2. `next_lesson` URL in `service.py` must be updated to match final Learn URL path once Learn URLs are aligned

---

## Consolidated Fix List

### Blocking fixes (before any new build work)

| # | App | Fix | Effort |
|---|-----|-----|--------|
| 1 | Governance | Rename all `/governance/library/` → `/governance/reference/` in `urls.py` + `views.py` + templates | 30 min |
| 2 | Governance | Remove `/record/` wrapper from detail routes (`/governance/reference/<id>/`, `/governance/mandate/<id>/`) | 15 min |
| 3 | Governance | Rename HTMX paths: `/htmx/relationships/<id>/` → `/htmx/record/<id>/links/`, `/htmx/versions/<id>/` → `/htmx/record/<id>/history/` | 20 min |
| 4 | Governance | Verify `Record.previous_version` FK field name vs `previous_version_id` UUID field — adjust `services.py` line 161 if needed | 15 min |
| 5 | Learn | Rename `/learn/programmes/` → `/learn/catalogue/`, `/learn/programmes/<id>/` → `/learn/programme/<id>/`, `/learn/lessons/<id>/` → `/learn/lesson/<id>/` | 20 min |
| 6 | Community | Add `/community/gatherings/` list view + `/community/<id>/` detail view | 1–2 h |
| 7 | Community | Add `GET /community/htmx/gatherings/` HTMX partial | 30 min |
| 8 | Community | Fix health endpoint — move from `community/urls.py` to `ics_project/urls.py` under `/api/` prefix | 10 min |
| 9 | Paraclete | Add `@permission_classes([AllowAny])` to health endpoint | 5 min |

### Non-blocking (part of normal build phases)

| # | App | Item | Build Phase |
|---|-----|------|-------------|
| 10 | Learn | Add 4 HTMX partials: my-learning, catalogue, progress, cert-queue | Phase C |
| 11 | Learn | Auto-certification signal (programme Activity → 100% → draft cert Record) | Phase E |
| 12 | Learn | Update `htmx_complete_lesson` to log partial progress (not just 100%) | Phase C |
| 13 | Governance | Add `GET /governance/htmx/reference/list/` HTMX list partial | Task 5.5 |
| 14 | Governance | Add `GET /governance/htmx/mandate/list/` HTMX list partial | Task 5.5 |
| 15 | Governance | Add `GET /governance/htmx/journal/search/` journal typeahead | Task 5.5 |
| 16 | Community | Evaluate whether to flatten `/community/management/members/` → `/community/members/` | Task 5.4 |
| 17 | Paraclete | Update `next_lesson` URL to match final Learn URL path | After Learn URLs fixed |

---

## Recommended Sequence

1. **Apply all 9 blocking fixes** (items 1–9 above) — ~3–4 hours total
2. **Continue Task 5.2 Learn App** from Phase A (model verified ✅) → Phase C (HTMX partials) → Phase E (auto-cert signal)
3. **Continue Task 5.3 Activity App UI** once Learn is complete
4. **Continue Task 5.4 Community App** — add gatherings list/detail, evaluate URL flattening
5. **Continue Task 5.5 Governance App** — add 3 missing HTMX endpoints after URL fixes
6. **Paraclete final update** — fix health endpoint + sync `next_lesson` URL after Learn is aligned
