# Platform Bootstrap & Initialisation — Roadmap Amendment

**Version:** 1.0 — 2026-06-08
**Status:** Approved — pending implementation scheduling
**Reference documents:** Master Roadmap v7, ADR-008, ADR-009, seed_induction_tenant, seed_prime_tenancy, seed_service_orders, create_handbook
**Author:** Claude (technical) — reviewed by Chizola

---

## What This Document Is

A roadmap amendment proposing **Phase L10.6 — Platform Bootstrap** as a new entry in Layer 10 of the master roadmap.

This document:
1. Records the architectural decision to create a single idempotent bootstrap command
2. Defines the full scope of what that command covers
3. Identifies every manual initialisation process currently scattered across the codebase
4. Proposes a first-run detection mechanism and admin UI surface for platform setup

This document does **not** change any ADR. It extends the Layer 10 work queue with a new phase.

---

## The Problem This Solves

The Ichebo platform currently requires the following manual steps after a fresh deployment, performed by a developer with shell access, in an undocumented order:

| Step | Command / Action | If skipped |
|------|-----------------|-----------|
| 1 | `python manage.py migrate` | Nothing works |
| 2 | `python manage.py createsuperuser` | No admin access |
| 3 | `python manage.py create_handbook` | Handbook tenant missing — governance records have no home |
| 4 | `python manage.py seed_induction_tenant` | Induction tenant missing — Level 0 users land in a void |
| 5 | `python manage.py seed_prime_tenancy` | No root governance tenant — steward hierarchy has no apex |
| 6 | `python manage.py seed_service_orders` | 24 service orders not seeded — ministry taxonomy incomplete |
| 7 | `python manage.py grant_handbook_access` | Handbook access not granted — Level 5 users cannot reach it |
| 8 | Create induction `Record` objects | Induction programmes don't exist — Level 0 users see empty seeker gate |
| 9 | Create at least one active programme | Catalogue is empty on first visit |

None of these steps are documented in a single place. Steps 3–7 are management commands in different apps with no shared entry point. Steps 8–9 require a logged-in Level 5 user using the authorship UI. There is no mechanism to detect whether the platform has been initialised at all.

This is a compounding risk: every new deployment, every staging refresh, every developer onboarding repeats this manual process from memory.

---

## Proposed Solution

### Phase L10.6 — Platform Bootstrap

A single idempotent management command — `bootstrap_platform` — that wraps all seed commands, detects what is already done, and reports clearly on every step. Paired with:

1. A **first-run detection flag** that shows a setup banner in the admin surface when the platform has not been bootstrapped
2. A **bootstrap status API endpoint** that the admin surface can poll
3. A **setup checklist page** in the Apostolic Command Shell (Level 5 only) showing the state of every platform singleton

---

## Scope of `bootstrap_platform`

The command runs each step only if it has not already been completed (idempotent by design). Every step prints a clear ✅ / ⚠️ / ❌ status line.

```
python manage.py bootstrap_platform
```

### Steps executed (in order)

| Step | Action | Idempotency check |
|------|--------|-------------------|
| 1 | Check migrations are current | `django.db.connection` pending migrations count |
| 2 | Verify superuser exists | `User.objects.filter(is_superuser=True).exists()` |
| 3 | Create Handbook tenant | `Tenant.objects.filter(tier='handbook').exists()` |
| 4 | Create Induction tenant singleton | `Tenant.objects.filter(tier='induction', slug='induction').exists()` |
| 5 | Create Prime tenancy (root governance) | `Tenant.objects.filter(tier='global').exists()` |
| 6 | Seed 24 Service Orders | `Record.objects.filter(record_type='service_order').count() >= 24` |
| 7 | Grant Handbook access to Level 5 users | Check `UserPermission` records for handbook tenant |
| 8 | Backfill Level 0 users into induction tenant | `backfill_induction_placement` logic |
| 9 | Report: induction programmes present? | Count active `record_type='induction'` records |
| 10 | Report: any active programmes in catalogue? | Count active `record_type='programme'` records |

Steps 9 and 10 are **report-only** — they cannot be automated because content must be authored by a human. They print a reminder with the URL to go create them.

### Output example

```
Ichebo Platform Bootstrap
=========================
✅  Migrations — current (47 applied)
✅  Superuser — found (admin@ichebo.org)
✅  Handbook tenant — exists at /global/handbook/
✅  Induction tenant — exists at /global/induction/
✅  Prime tenancy — exists at /global/
✅  Service Orders — 24 seeded
✅  Handbook access — granted to 2 Level 5 users
✅  Induction backfill — 3 Level 0 users placed
⚠️  Induction programmes — none found
     → Log in as Level 5 and go to /learn/author/ to create one
⚠️  Programme catalogue — empty
     → Log in as Level 5 and go to /learn/author/ to create programmes

Bootstrap complete. 2 warnings require manual action.
```

### Flags

```
--dry-run       Print what would be done without writing anything
--quiet         Only print warnings and errors
--force         Re-run steps even if already complete (for repair scenarios)
```

---

## First-Run Detection

A `PlatformConfig` singleton model (single-row table) tracks bootstrap state:

```python
class PlatformConfig(models.Model):
    bootstrapped_at = models.DateTimeField(null=True)
    bootstrapped_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    bootstrap_version = models.CharField(max_length=20, default='')

    class Meta:
        # Enforce singleton
        def save(self, *args, **kwargs):
            self.pk = 1
            super().save(*args, **kwargs)
```

When `bootstrapped_at` is null, the Apostolic Command Shell shows a red banner in the admin zone:

> **Platform not initialised.** Run `python manage.py bootstrap_platform` or go to [Platform Setup](/admin/setup/).

---

## Setup Checklist Page

A new page at `/admin/setup/` (Level 5 only) shows the live state of every platform singleton. No actions — read-only status display. Lets a steward confirm the platform is healthy without shell access.

| Item | Status indicator |
|------|-----------------|
| Migrations current | ✅ / ❌ |
| Superuser present | ✅ / ❌ |
| Handbook tenant | ✅ / ❌ |
| Induction tenant | ✅ / ❌ |
| Prime tenancy | ✅ / ❌ |
| Service Orders (24) | ✅ / count |
| Active induction programmes | count |
| Active catalogue programmes | count |
| Level 0 users without induction placement | count |

---

## What This Does NOT Do

- Does not replace `migrate` — migrations must still be run manually before bootstrap
- Does not create content (programmes, lessons, records) — content is always authored by humans
- Does not manage environment variables or `.env` files — those are infrastructure, not application
- Does not provision servers or install dependencies — this is application-layer only
- Does not become a web-based installer wizard — the command-line first, UI second

---

## Future Extensions (Not In Scope for L10.6)

These are recorded here so they are not forgotten:

| Extension | When | Notes |
|-----------|------|-------|
| Tenant onboarding checklist | Version 3+ | Per-tenant version of the platform setup checklist. Steward sees what their community needs to complete (induction programme, first announcement, etc.) |
| Demo content seeding | Version 3+ | `--demo` flag seeds sample programmes, lessons, and a sample community for evaluation environments |
| Health check endpoint | Version 3+ | `GET /api/health/` returns platform bootstrap state, DB connectivity, cache status, Celery worker status. Used by monitoring (Uptime Kuma, etc.) |
| Automated deployment script | Version 3+ | `deploy/bootstrap.sh` — wraps `git pull`, `pip install`, `migrate`, `bootstrap_platform`, `collectstatic`, `systemctl restart gunicorn` in one idempotent shell script |
| First-run email to superuser | Version 3+ | After bootstrap, email the superuser a checklist of next steps (requires Brevo configured) |

---

## Relationship to Existing ADRs

| ADR | Impact |
|-----|--------|
| ADR-008 (No Celery until Version 3) | Not affected — bootstrap is a management command, not an async task |
| ADR-009 (No Docker until Version 3) | Not affected — bootstrap runs in the existing Nginx/Gunicorn/systemd stack |
| ADR-006 (competence_level one write path) | Not affected — bootstrap does not touch competence_level |

No new ADR is required for L10.6. This is an operational tooling phase, not an architectural decision.

---

## Entry Requirement

Track 1 (induction tenant auto-placement signal) must be complete before L10.6 begins. The backfill step in `bootstrap_platform` reuses the logic from `backfill_induction_placement`.

## Exit Criteria

- [ ] `python manage.py bootstrap_platform` runs end-to-end on a fresh database with 0 errors
- [ ] `python manage.py bootstrap_platform` is idempotent — running it twice produces the same output with no duplicate records
- [ ] `--dry-run` flag prints the plan without writing anything
- [ ] Setup checklist page renders at `/admin/setup/` for Level 5 users
- [ ] Red banner appears in shell when `PlatformConfig.bootstrapped_at` is null
- [ ] All existing seed commands still work independently (backwards compatible)
- [ ] `python manage.py check` — 0 issues

## Commit

```
feat(infra): L10.6 — platform bootstrap command and setup checklist
```

---

## Master Roadmap Amendment

Add the following row to the Layer 10 table in `master-roadmap-canonical-2026-05-13.md`:

```
| L10.6 | 10 | Platform Bootstrap — idempotent seed command, first-run detection, setup checklist | ⏳ Pending |
```

Add the following entry after L10.5 in the Layer 10 phase list:

```
## Phase L10.6 — Platform Bootstrap ⏳

**Goal:** Single idempotent `bootstrap_platform` management command wrapping all
seed commands. First-run detection. Setup checklist page at /admin/setup/.
See .docs/plans/platform-bootstrap-plan.md for full specification.

**Entry requirement:** Track 1 (induction tenant auto-placement) complete.

**Reference:** .docs/plans/platform-bootstrap-plan.md

**Commit:** `feat(infra): L10.6 — platform bootstrap command and setup checklist`
```
