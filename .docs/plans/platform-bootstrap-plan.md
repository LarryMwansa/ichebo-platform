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

### Phase L10.6 — Platform Admin Shell + Bootstrap

A single idempotent management command — `bootstrap_platform` — that wraps all seed commands, detects what is already done, and reports clearly on every step. Paired with a **Platform Admin Shell** — a UI surface at `/platform/` that abstracts terminal-only operations into a browser-accessible management panel.

Access gate: Level 5 OR `user.is_superuser`.

The shell covers three surfaces:

1. **Setup Checklist** (`/platform/`) — live health status of every bootstrap step. Red banner shown in the workspace shell when `PlatformConfig.bootstrapped_at` is null.
2. **System Tenants** (`/platform/tenants/`) — induction, handbook, and prime. Click-through to assign stewards, view members, manage without terminal access.
3. **Bootstrap Actions** — buttons that trigger seed logic (idempotent). Equivalent to running seed commands but from the browser.

**Prerequisite patch (done — 2026-06-08):** System tenants (induction, handbook) are now visible on the Steward Dashboard and manageable via `tenant_detail` for Level 5 / superuser. This unblocks steward assignment immediately without waiting for L10.6.

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
| 9 | Seed the 6 nested Qualification Programmes (Induction → New Life → Foundation → Leaders → Builders → Architect's) | `seed_induction_programme` + `seed_programmes` — `Record.objects.filter(record_family='learning', record_type__in=['induction','programme']).count() >= 6` |
| 10 | Create Genesis Sceptre Community (default Sceptre One tenant) | `Tenant.objects.filter(tier='church_node', slug='genesis-sceptre').exists()` |
| 11 | Report: any active programmes in catalogue beyond the 6 seeded? | Count active `record_type='programme'` records `> 6` |

Step 11 is **report-only**. Steps 9–10 are now fully automatable — see "Doctrinal Grounding" below for why the 6 programmes are seed data, not author-created content like step 11's free catalogue additions.

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
✅  Qualification Programmes — 6 seeded (Induction → Architect's)
✅  Genesis Sceptre Community — created at /global/genesis-sceptre/
⚠️  Programme catalogue — only the 6 seeded programmes exist
     → Log in as Level 5 and go to /learn/author/ to add more

Bootstrap complete. 1 warning requires manual action.
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

    # ── Email verification toggle (L10.6) ──────────────────────────────────────
    # When True: new users are created with status='pending_verification' and
    # receive a verification email before they can log in.
    # When False: new users are created with status='seeker' immediately (dev/test default).
    # Managed via the Platform Admin Shell at /platform/ by Level 5 / superuser.
    # The accounts/views.py register flow reads this flag at signup time.
    require_email_verification = models.BooleanField(default=True)

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

A new page at `/platform/` (Level 5 / superuser only) shows the live state of every platform singleton. No actions — read-only status display. Lets a steward confirm the platform is healthy without shell access.

| Item | Status indicator |
|------|-----------------|
| Migrations current | ✅ / ❌ |
| Superuser present | ✅ / ❌ |
| Handbook tenant | ✅ / ❌ |
| Induction tenant | ✅ / ❌ |
| Prime tenancy | ✅ / ❌ |
| Service Orders (24) | ✅ / count |
| Qualification Programmes (6 nested, Induction–Architect's) | ✅ / count |
| Genesis Sceptre Community | ✅ / ❌ |
| Additional catalogue programmes (beyond the 6 seeded) | count |
| Level 0 users without induction placement | count |
| Email verification required | ON / OFF toggle |

---

## What This Does NOT Do

- Does not replace `migrate` — migrations must still be run manually before bootstrap
- Does not create content (programmes, lessons, records) — content is always authored by humans
- Does not manage environment variables or `.env` files — those are infrastructure, not application
- Does not provision servers or install dependencies — this is application-layer only
- Does not become a web-based installer wizard — the command-line first, UI second

---

## Access Gating Configuration (L10.6 — System Panel)

**Decision (2026-06-10):** Access level gates for Handbook and Governance libraries are
currently hardcoded constants. They must become `PlatformConfig` fields so a Level 5
steward can adjust them from the System Panel at `/platform/` without a code deploy.

### Current hardcoded values (as of 2026-06-10)

| Constant | App | Value | Meaning |
| --- | --- | --- | --- |
| `MANDATE_ACCESS_LEVEL` | `governance/views.py` | 4 | Minimum level to read Mandate Library in Governance |
| `KEYS_ACCESS_LEVEL` | `handbook/views.py` | 4 | Minimum level to access Keys Library in Handbook (entity/narrative are L4-5 content) |
| `REFERENCE_ACCESS_LEVEL` | `handbook/views.py` | 3 | Minimum level to read Reference Library in Handbook |

**Resolved (2026-06-18):** `handbook/views.py` also defined its own `MANDATE_ACCESS_LEVEL = 3`
(unused dead reference, but inconsistent with `governance/views.py`'s value of 4). Canonical
value confirmed as **4** — `handbook/views.py` corrected to match. This removes the conflict
before it gets baked into `PlatformConfig.mandate_access_level`'s default.

### PlatformConfig model additions (L10.6)

```python
class PlatformConfig(models.Model):
    # ... existing fields ...

    # ── Library access gates ───────────────────────────────────────────────────
    # Minimum competence_level required to access each library.
    # Default values match the current hardcoded constants.
    mandate_access_level   = models.IntegerField(default=4)
    keys_access_level      = models.IntegerField(default=4)
    reference_access_level = models.IntegerField(default=3)
```

### System Panel UI (L10.6)

Add a **Library Access Gates** section to `/platform/` alongside the email verification toggle:

| Setting | Input | Default | Description |
| --- | --- | --- | --- |
| Mandate Library gate | Number 1–5 | 4 | Who can read Mandate documents in Governance |
| Keys Library gate | Number 1–5 | 4 | Who can access personal Keys Library in Handbook |
| Reference Library gate | Number 1–5 | 3 | Who can read Reference Library in Handbook |

### Migration path (L10.6)

When L10.6 is implemented:

1. Add `mandate_access_level`, `keys_access_level`, `reference_access_level` to `PlatformConfig`
2. Replace the hardcoded constants in `governance/views.py` and `handbook/views.py` with reads from `PlatformConfig.get_solo()` (or equivalent singleton fetch, cached)
3. Add the gate inputs to the System Panel template at `/platform/`
4. The values default to the current constants so no behaviour changes on first deploy

### Standing rule — the operator bypass (2026-06-23)

**Every access gate the System Panel can set must have a guaranteed
operator bypass that cannot itself be configured away.** A Level 5 steward
(or whoever holds the System Panel) can set `mandate_access_level` to a
value no real account meets — accidentally or otherwise — and without a
hardcoded escape hatch, that locks out the very person who would need to
fix it. There is no recovery path from inside the app at that point; it
becomes a `manage.py shell` operation on the server.

This is not hypothetical. Auditing the *current* hardcoded gates
(2026-06-23) found `handbook/views.py` already guards every
`KEYS_ACCESS_LEVEL` check with `not (request.user.is_staff or
request.user.is_superuser)`, but `governance/views.py`'s
`MANDATE_ACCESS_LEVEL` check had no such guard at all — a superuser could
already be locked out of the Mandate Library today, before the System
Panel even exists. Fixed to match `handbook/views.py`'s pattern.

**Rule for L10.6 and anything added to the System Panel after it:** the
bypass condition (`is_staff or is_superuser` — the platform's existing
"operator" concept, not a new role) is checked in code at the enforcement
point, never read from `PlatformConfig` or any other database value the
panel itself controls. The panel may change *who else* gets access; it must
never be able to remove the operator's own access as a side effect.

---

## Doctrinal Grounding (2026-06-18)

Reference documents: `.docs/kingdom-governance-system_v1.md` (KGS), `.docs/sceptre-community-programme-concept-note_v2.md` (Sceptre Community Programme), `Things-for-systems-setup.md` (Chizola).

### Agency Tenants — already built, no change needed

KGS §4.2 / Sceptre Community Programme's six Service Domains describe Prime
Tenancy plus six agency offices (Apostolic & Spiritual Ministry, Leadership &
Governance Support, Formation & Teaching, Mission & Outreach, Community Life
& Care, Operations & Stewardship). Confirmed at the 2026-06-18 readiness
check: `seed_prime_tenancy.py` already creates Prime Tenancy and all six
agencies as children of Prime, by these exact names. Step 5 in the bootstrap
scope table covers this — no new step required.

### Genesis Sceptre Community — genuine gap, now added as step 10

`seed_induction_tenant.py` creates the Induction Tenant singleton but no
default Sceptre Community (Church Node) tenant exists anywhere in the
codebase. Per KGS §4.2.5.1 and the concept note's Part B, the Sceptre
Community is the foundational unit of the whole movement — a fresh platform
with zero communities is a materially incomplete first-run state, not just a
content gap. Added as bootstrap step 10: creates one default `church_node`
tier tenant ("Genesis Sceptre Community" / slug `genesis-sceptre`) so a fresh
deployment has at least one working Church Node to demonstrate and test
against.

### The 6 Qualification Programmes are seed data, not authored content

Earlier drafts of this plan treated programme creation as something "content
must be authored by a human" and left it report-only. That was incorrect for
the 6 core programmes specifically. Per Chizola (2026-06-18): `competence_level`
(0–5) is not merely an access gate — it is a credential corresponding to real
formation, and the 6 programmes (Induction → New Life → Foundation → Leaders
→ Builders → Architect's) are not generic e-learning content sitting beside
the movement; they **are** the Qualification Programmes Framework (KGS §25)
that operationalises the Sceptre Community Programme's 7-year formation
pathway (concept note §15). Each programme nests the one below it
(`prerequisites` field in `seed_programmes.py`), and `required_level` gates
access — confirmed in `learn/services.py:check_prerequisites()`, already
enforcing this correctly.

Because these 6 programmes are fixed, doctrinally-defined seed data — not
open-ended catalogue content — they belong in `bootstrap_platform` as step 9,
reusing the existing `seed_induction_programme` and `seed_programmes`
commands. Only programmes *beyond* these 6 remain human-authored
(report-only, step 11).

### Correction — level-up automation is not a gap

An earlier readiness assessment flagged "no automatic level-up on programme
completion" as a missing feature. This was incorrect and is retracted.
`learn/services.py:confirm_certification_record()` is the designed, sole
write path for `competence_level` (per the file's own header comment and
ADR-006), and it deliberately requires a confirming steward (Level 3+) to
call it — it is not, and should not be, triggered automatically by programme
completion alone. This matches KGS §24.3: "Leadership is service-based...
formed, tested, and affirmed" — affirmation is a human governance act, not a
system event. No change needed to `bootstrap_platform` or `PlatformConfig`
for this; recorded here only to correct the prior assessment.

---

## Future Extensions (Not In Scope for L10.6)

These are recorded here so they are not forgotten:

| Extension | When | Notes |
|-----------|------|-------|
| `require_email_verification` toggle | L10.6 | Platform Admin Shell toggle. When ON: new users start as `pending_verification` and must verify before login. When OFF: users start as `seeker` immediately (default for dev). Managed via `PlatformConfig.require_email_verification`. The `accounts/views.py` register flow reads this flag. Manual verification via Level 4+ member profile button remains available regardless of this toggle. |
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

## Implementation Order (2026-06-18)

**Readiness check performed 2026-06-18:** all 6 seed commands the plan wraps
(`create_handbook`, `seed_induction_tenant`, `seed_prime_tenancy`,
`seed_service_orders`, `grant_handbook_access`, `backfill_induction_placement`)
already exist and work independently. `Tenant` model already has all three
tiers (`handbook`, `induction`, `global`) this plan depends on.
`EmailVerificationToken` model and `pending_verification` user status already
exist. `bootstrap_platform` is genuinely orchestration over existing logic,
not new business logic — the project is ready to implement this phase now.

Missing pieces confirmed at the same readiness check:

1. `PlatformConfig` singleton model — does not exist yet
2. `/platform/` app, URLs, views, templates — no scaffolding at all
3. `bootstrap_platform` management command itself — does not exist
4. Access-level constants are still hardcoded in two files (see resolved conflict above)
5. A `genesis-sceptre` seed step/command — does not exist yet (see Doctrinal Grounding above)

Scope finalised 2026-06-18 — `Things-for-systems-setup.md` and the doctrinal
review against KGS / the Sceptre Community Programme concept note are folded
in above. No further items pending; the command now wraps 11 steps (was 10).

Suggested build order:

1. **`PlatformConfig` model + migration** — collapses the `MANDATE_ACCESS_LEVEL`
   conflict into the model's default in the same change. Include
   `mandate_access_level`, `keys_access_level`, `reference_access_level`,
   `require_email_verification`, `bootstrapped_at`, `bootstrapped_by`,
   `bootstrap_version` fields from this document.
2. **`seed_genesis_sceptre_community` management command** — new, creates the
   default `church_node` tier tenant. Needed before step 3 since
   `bootstrap_platform` step 10 wraps it.
3. **`bootstrap_platform` management command** — steps 1–11 as specified above,
   idempotent, with `--dry-run`, `--quiet`, `--force` flags.
4. **`/platform/` app — Setup Checklist page only** — read-only status display,
   lowest risk, no write actions yet. Level 5 / superuser gated.
5. **System Tenants management UI** (`/platform/tenants/`) — induction, handbook,
   prime, and Genesis Sceptre Community tenant detail with steward assignment.
6. **Bootstrap Actions** — buttons that trigger seed logic from the browser
   (idempotent, same logic as the CLI command).

## Entry Requirement

Track 1 (induction tenant auto-placement signal) must be complete before L10.6 begins. The backfill step in `bootstrap_platform` reuses the logic from `backfill_induction_placement`.

## Exit Criteria

- [ ] `python manage.py bootstrap_platform` runs end-to-end on a fresh database with 0 errors
- [ ] `python manage.py bootstrap_platform` is idempotent — running it twice produces the same output with no duplicate records
- [ ] All 6 Qualification Programmes (Induction → Architect's) exist after bootstrap, correctly nested via `prerequisites` and gated by `required_level`
- [ ] Genesis Sceptre Community tenant exists after bootstrap (`tier='church_node'`, slug `genesis-sceptre`)
- [ ] `--dry-run` flag prints the plan without writing anything
- [ ] Platform Admin Shell renders at `/platform/` for Level 5 / superuser
- [ ] System Tenants list renders at `/platform/tenants/` with induction + handbook + Genesis Sceptre Community
- [ ] Red banner appears in workspace shell when `PlatformConfig.bootstrapped_at` is null
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
| L10.6 | 10 | Platform Admin Shell — bootstrap command, system tenant oversight UI, setup checklist at /platform/ | ⏳ Pending |
```

Add the following entry after L10.5 in the Layer 10 phase list:

```
## Phase L10.6 — Platform Admin Shell ⏳

**Goal:** Platform Admin Shell at /platform/ (Level 5 / superuser) with setup
checklist, system tenant management (induction + handbook), and bootstrap
actions. Backed by idempotent `bootstrap_platform` management command.
See .docs/plans/platform-bootstrap-plan.md for full specification.

**Entry requirement:** Track 1 (induction tenant auto-placement) complete.

**Reference:** .docs/plans/platform-bootstrap-plan.md

**Commit:** `feat(infra): L10.6 — platform bootstrap command and setup checklist`
```
