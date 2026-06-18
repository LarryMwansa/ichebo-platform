# Community App — Member-to-Steward Support Requests — Roadmap Amendment

**Version:** 1.0 — 2026-06-18
**Status:** Approved — pending implementation scheduling
**Reference documents:** Master Roadmap v7 (Community App feature table, Deferred Items), ADR-003 (single records table), `community/models.py`, `tenants/models.py`, `notifications/service.py`
**Author:** Claude (technical) — reviewed by Chizola

---

## What This Document Is

A roadmap amendment adding a new Community App capability: a member-initiated **support request** flow, distinct from social/chat messaging. A member raises a concern or need; it routes to their community's steward; the steward's response is tracked against a time target so an overseer can see, at a glance, whether reports are being handled in time.

This is not the "Pastoral notes" item already listed as deferred in the master roadmap (that is steward-authored private notes about a member — a different feature, still deferred). This document defines a new, separate capability and proposes where it sits in the Layer/Phase structure.

---

## The Problem This Solves

Chizola has not yet built any community messaging. The instinct to reach for "social messaging" was set aside in favour of a narrower, more accountable pattern: members need a way to reach their steward with a concern, and — critically — someone responsible for oversight needs to be able to see whether requests are being acknowledged and resolved in good time. Plain chat has no accountability surface; a backlog of unread messages is invisible to anyone but the recipient.

This is a support-ticket pattern, not a messaging pattern. It needs:
- A clear status lifecycle (not just "read/unread")
- A response-time target that can be checked against the current time
- A queue view a steward (and their own overseer) can audit

---

## Decision: Record-family slot, not a new model, not Activity

| Option | Why not |
|---|---|
| New dedicated `SupportRequest` model | ADR-003 forbids new content tables — all content goes through `Record` with a `record_family`/`record_type` discriminator. |
| Model as `Activity` | `Activity` has `status` + `created_at`/`updated_at` but no `acknowledged_at`/`resolved_at` equivalent — SLA tracking would require parsing `ActivityLog` transitions, which is workable but awkward compared to dedicated `custom_fields` keys on a `Record`. |
| **`Record` with `record_family='community'`, `record_type='support_request'`** | **Chosen.** Reuses the existing engine, status lifecycle, `custom_fields` for SLA timestamps, `permissions_data` for visibility, `created_by` for ownership. No migration needed beyond what `Record` already provides — `record_type` is free-form (`max_length=50`, no `choices` constraint), confirmed at `records/models.py:55`. |

---

## Data Shape

Using the existing `Record` model (`records/models.py:7`) with no schema change required:

| Field | Value for a support request |
|---|---|
| `record_class` | `'organizational'` |
| `record_family` | `'community'` |
| `record_type` | `'support_request'` |
| `created_by` | the member raising the request |
| `tenant` | the member's community tenant |
| `title` | short subject line, member-authored |
| `content` | the request body |
| `status` | `'draft'` → `'submitted'` (open) → `'active'` (acknowledged) → `'completed'` (resolved). Reuses existing `STATUS_CHOICES` — no new choices needed. |
| `custom_fields` | `{'response_due_at': <iso datetime>, 'acknowledged_at': null, 'resolved_at': null, 'assigned_steward_id': <uuid>}` |
| `permissions_data` | `{'visibility': 'member_and_assigned_steward'}` |

**Status mapping (reuses `Record.STATUS_CHOICES`, no new values):**

```
submitted   → open, awaiting steward acknowledgement
active      → acknowledged, steward is on it
completed   → resolved
```

`response_due_at` is computed at creation time (`created_at + response_window`, default configurable, e.g. 72 hours) and stored in `custom_fields` rather than as a new column.

---

## Steward Routing

Resolve the assigned steward at creation time, in this order:

1. Query `UserPermission` for the member's tenant where `role__endswith='-steward'` and `is_active=True` (`tenants/models.py:100-146`, `ROLE_CHOICES` already includes `branch-steward` through `global-steward`).
2. If none found, fall back to `Tenant.coordinator_user` (`tenants/models.py:59`, nullable FK).
3. If neither resolves, the request is created with `assigned_steward_id=null` and surfaces in a "needs routing" filter in the queue view — it is never silently dropped.

This avoids relying solely on `coordinator_user`, which is nullable and represents a single point of contact rather than the tenant's steward-tier role assignment.

---

## Steward Queue View (the actual accountability surface)

Notifications alone do not give an overseer visibility into a backlog — this view is the deliverable that answers "are reports being handled in time."

**New page:** `/community/support/` (Level 3+ / steward role gated, matches existing Community app gating pattern in `community/views.py:_require_level`)

- Lists `Record` objects with `record_type='support_request'`, scoped to tenants the requesting user stewards
- Sorted by `custom_fields.response_due_at` ascending (soonest-due first)
- Status filter: open / acknowledged / resolved / needs routing
- Overdue requests (now > `response_due_at` and `status != 'completed'`) flagged visually (red), matching existing `--error` design token usage elsewhere in the workspace shell
- A higher-tier steward (e.g. district-steward) can view the same queue scoped to all tenants beneath their tenant path — uses the existing `tenant_path` field already on `UserPermission` (`tenants/models.py:127`) for hierarchy scoping, no new field needed

No automatic escalation in this phase — confirmed with Chizola (2026-06-18). Overdue items are visible in the queue; a higher steward escalates manually by reassigning `assigned_steward_id` if needed. This keeps the phase within ADR-008 (no Celery/cron automation beyond what already exists) and avoids deciding escalation depth/rules before the manual flow is proven.

---

## Member-Facing Surface

- A "Raise a request" action in the member's community view (`community/views.py:my_community`, where the existing FAB sheet pattern at `htmx_fab_sheet` already lives) — adds one more sheet option
- A "My Requests" list showing the member's own submitted requests and their current status — read-only, mirrors the existing pattern of `htmx_pending_requests` (membership requests) but filtered to the member's own `support_request` records

---

## Notification Integration

Reuses `notifications/service.py:create_notification()` exactly as-is (`notifications/service.py:16`) — no change to the dispatch mechanism, only two new notification types and two new handler functions following the existing pattern (e.g. `notify_membership_approved` at `notifications/service.py:56`):

```python
def notify_support_request_created(record):
    if not record.custom_fields.get('assigned_steward_id'):
        return  # needs-routing case — no recipient yet
    steward = User.objects.get(id=record.custom_fields['assigned_steward_id'])
    create_notification(
        user=steward,
        notification_type='support_request_created',
        title=f'New support request: {record.title}',
        body=record.content[:200],
        data={'record_id': str(record.id), 'url': f'/community/support/{record.id}/'},
    )

def notify_support_request_acknowledged(record):
    create_notification(
        user=record.created_by,
        notification_type='support_request_acknowledged',
        title='Your support request has been seen',
        body='A steward has acknowledged your request and is working on it.',
        data={'record_id': str(record.id), 'url': f'/community/support/{record.id}/'},
    )
```

Both new types added to `Notification.NOTIFICATION_TYPES` (`notifications/models.py:16`). Neither needs to be in `EMAIL_TYPES` (`notifications/service.py:13`) initially — in-app + FCM push only, matching the urgency of most other Community notifications. Can be added to `EMAIL_TYPES` later if real usage shows email is needed.

Signal wiring follows the existing pattern in `notifications/signals.py` — `post_save` on `Record` filtered to `record_type='support_request'`, dispatching to `notify_support_request_created()` on creation and `notify_support_request_acknowledged()` on the `status` transition to `'active'`.

---

## What This Does NOT Do

- Does not implement social/chat messaging between members — that remains a separate, unscheduled feature
- Does not implement automatic escalation — manual only in this phase (see Steward Queue View)
- Does not touch `Tenant`, `UserPermission`, or `Activity` schemas — no migrations to those models
- Does not overlap with the deferred "Pastoral notes" roadmap item — that is steward-authored private notes about a member; this is member-initiated and visible to both parties
- Does not require Celery/cron — SLA overdue state is computed at read-time by comparing `now()` to `custom_fields.response_due_at`, not via a scheduled job

---

## Scope of Implementation

| Step | What | Files touched |
|---|---|---|
| 1 | Add `support_request_created`, `support_request_acknowledged` to `Notification.NOTIFICATION_TYPES` | `notifications/models.py` (+ migration) |
| 2 | Add `notify_support_request_created()`, `notify_support_request_acknowledged()` to service layer | `notifications/service.py` |
| 3 | Add `post_save` signal handler for `Record(record_type='support_request')` | `notifications/signals.py` |
| 4 | Add steward-routing helper (`resolve_steward_for_tenant(tenant)`) | `community/services.py` (new file, or add to `community/views.py` helpers) |
| 5 | Add "Raise a request" HTMX view + form | `community/views.py`, `community/urls.py`, new template partial |
| 6 | Add "My Requests" member-facing list view | `community/views.py`, new template partial |
| 7 | Add steward queue view `/community/support/` with hierarchy scoping via `tenant_path` | `community/views.py`, `community/urls.py`, new template |
| 8 | Add overdue visual flagging in queue template | template only, reuses `--error` design token |

No new Django app required — this is scoped entirely within the existing `community` app.

---

## Relationship to Existing ADRs

| ADR | Impact |
|---|---|
| ADR-003 (single records table with discriminator) | Followed exactly — no new model |
| ADR-008 (no Celery/Redis automation beyond what exists) | Followed — SLA overdue state computed at read-time, not scheduled |
| ADR-006 (competence_level one write path) | Not affected — this feature does not touch competence_level |

No new ADR required.

---

## Exit Criteria

- [ ] Member can raise a support request from the Community app FAB sheet
- [ ] Request is routed to a steward via `UserPermission` role lookup, falling back to `Tenant.coordinator_user`, or flagged "needs routing" if neither resolves
- [ ] Steward receives a notification on request creation
- [ ] Member receives a notification when steward acknowledges
- [ ] `/community/support/` queue view renders, scoped to tenants the viewing user stewards (including sub-tenants via `tenant_path`)
- [ ] Overdue requests (past `response_due_at`, not resolved) are visually flagged in the queue
- [ ] Member can view their own request history and current status
- [ ] `python manage.py check` — 0 issues
- [ ] No new migrations to `Tenant`, `UserPermission`, or `Activity`

## Commit

```
feat(community): support request flow — member-to-steward with SLA tracking
```

---

## Master Roadmap Amendment

Add the following row to the Community App feature table in `master-roadmap-canonical-2026-05-13.md` (after line 200, "Membership request flow"):

```
| Member-to-steward support requests (SLA-tracked) | ⏳ Pending — see .docs/plans/community-support-requests-plan.md |
```

Add the following entry to the Layer 4 (Stabilisation) or Layer 10 (Scale) phase list — recommended as a Layer 4 item since it strengthens Version 2 in real-world use (Phase H.2) rather than introducing new infrastructure:

```
## Phase H.3 — Community Support Requests ⏳

**Goal:** Member-initiated support request flow routed to community stewards,
with SLA-style response tracking visible in a steward queue view. Distinct
from the deferred "Pastoral notes" item — this is member-initiated and
mutually visible, not steward-private.

**Entry requirement:** Community App (Phase 5.4) complete. No new
infrastructure — uses existing Record engine and notification plumbing.

**Reference:** .docs/plans/community-support-requests-plan.md

**Commit:** `feat(community): support request flow — member-to-steward with SLA tracking`
```

Add to the Deferred Items / Community App section for awareness of what remains genuinely deferred after this phase ships:

```
### Community App (remaining after Phase H.3)
- Pastoral notes (privacy design required) — distinct from support requests; steward-private
- Automatic SLA escalation up tenant hierarchy — manual-only in Phase H.3, automation deferred pending real usage data
- Attendance tracking (privacy-sensitive)
- Community analytics dashboard, collective-level gathering visibility
- PastoralAssignment model (upgrade from UserPermission.metadata.shepherd_id)
```
