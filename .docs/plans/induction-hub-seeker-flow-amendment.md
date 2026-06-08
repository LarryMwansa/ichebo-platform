# Amendment: Induction Hub — Level 0 Seeker Entry Point

**Date:** 2026-06-08
**Status:** Implemented
**Relates to:** `induction-tenant-auto-placement-plan.md`, ADR (system tiers, community access)

---

## Problem

After email verification, a newly registered user has:
- `status = 'seeker'` (Level 0)
- A `UserPermission` record in the induction tenant (placed by `post_save` signal on `User`)

However, navigating to `/community/` routed them to the **Seeker Gate** — the community
membership-request flow intended for users who are not yet part of any community tenant.
This was incorrect. A Level 0 user placed in the induction tenant is already a tenant member;
they should land in the **Induction Hub**, not be asked to apply to join.

---

## Decision

The Induction Tenant is the **only** tenant open to Level 0 (seeker-status) users.
It is a system singleton (`tier='induction'`, `slug='induction'`) whose membership is
granted automatically at registration, not through the standard membership-request flow.

A Level 0 user who has a live `UserPermission` for the induction tenant must always be
directed to the Induction Hub as their primary community view, bypassing the Seeker Gate.

---

## Changes

### `community/views.py` — `my_community` guard

Added an early check before the seeker-gate redirect. When `level < 1`, the view now
queries for an active induction tenant permission. If found, it delegates to
`_render_induction_hub`; only if absent does it fall through to the seeker gate.

```python
if level < 1:
    induction_perm = UserPermission.objects.filter(
        user=user, tenant__tier='induction', is_active=True,
    ).select_related('tenant').first()
    if induction_perm:
        return _render_induction_hub(request, user, induction_perm)
    return render(request, 'community/seeker_gate.html', {...})
```

### `community/views.py` — `_render_induction_hub` helper

New view helper that renders the induction hub template. Provides:
- All active induction-type `Record` objects (`record_family='learning'`,
  `record_type='induction'`)
- Per-programme enrolment state from `Activity` (`activity_type='programme'`)
- Progress percentage and status for each programme card
- Announcements scoped to the induction tenant (latest 3)
- `all_complete` flag: true when all programme cards are `status='completed'`

### `templates/community/induction_hub.html` — new template

Extends `workspace_shell.html` directly (not `base_community.html`). Level 0 users
do not have access to the full community nav, so using the community base would expose
steward-level UI elements.

Sections:
1. **Left sidebar** — per-programme progress bars in the context panel; "Your Journey" nav
2. **Options panel** — status card (Seeker · Level 0), next-step hint, completion notice
3. **Main content (desktop)** — hero, programme cards with progress bars and
   Start/Continue/Review CTAs, completion notice, announcements
4. **Mobile block** — status card, programme cards, completion notice, announcements,
   link to Learn

---

## User Flow (post-amendment)

```
Register → email sent → manual or link verification → status='seeker'
    ↓
/community/ → level=0 → check UserPermission(induction) → found
    ↓
Induction Hub: view induction programme cards
    ↓
Start/continue induction programme via /learn/programme/<id>/
    ↓
Steward marks programme complete (Activity.status='completed')
    ↓
all_complete=True → hub shows "Induction Complete" notice
    ↓
Steward issues Induction Certification → level advanced to 1 (seeker→member)
    ↓
/community/ → normal community home
```

---

## What Has Not Changed

- The **Seeker Gate** still exists for `status='seeker'` users who are NOT placed in the
  induction tenant (edge case: a user somehow reaches `status='seeker'` without the signal
  firing — unlikely, but the gate is preserved).
- The **induction tenant auto-placement signal** is unchanged (registered in
  `induction-tenant-auto-placement-plan.md`).
- Level 1+ users are unaffected; the guard fires only when `level < 1`.
- The induction tenant is still a steward-managed system tenant visible to Level 5/superuser
  via the Steward Dashboard (implemented 2026-06-08 as a separate patch).

---

## ADR Amendment Note

The original ADR for community access control specified that Level 0 (seeker) users see
only the Seeker Gate. This amendment supersedes that for users who hold an active
induction tenant permission. The revised rule:

> **Level 0 users with an active induction tenant permission are routed to the
> Induction Hub. The Seeker Gate applies only to Level 0 users with no active
> tenant membership.**
