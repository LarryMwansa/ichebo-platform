# Induction Tenant Auto-Placement — Implementation Plan

**Version:** 1.0 — 2026-06-08
**Status:** Approved for implementation
**Reference documents:** Master Roadmap v7, ADR-011, DOC I (onboarding-spec)
**Author:** Claude (technical) — reviewed by Chizola

---

## What This Document Is

A precise implementation plan for wiring new user registration to automatic placement in the Induction tenant. This is **Track 1** of the induction community decision taken on 2026-06-08.

Track 2 (platform bootstrap command) is a separate document: `platform-bootstrap-plan.md`.

---

## Problem Statement

When a user registers on the Ichebo platform they are assigned `competence_level = 0` (Seeker). They have no community, no tenant membership, and no home until they manually navigate to the seeker gate and complete induction. The gap between registration and first meaningful experience is a void.

The induction system — the Learn records, the `_induction_status()` gate logic, the `induction_enrolled_at` / `induction_completed_at` fields on `User`, the `/global/induction/` tenant singleton — all exist and are complete. The single missing wire is: **auto-placement into the induction tenant on registration.**

---

## What Already Exists (Do Not Re-Build)

| Component | Location | Status |
|-----------|----------|--------|
| `Tenant` model with `induction` tier | `tenants/models.py` | ✅ Built |
| `/global/induction/` tenant singleton | `seed_induction_tenant` command | ✅ Seeded |
| `User.induction_enrolled_at` field | `accounts/models.py` | ✅ Built |
| `User.induction_completed_at` field | `accounts/models.py` | ✅ Built |
| `_induction_status()` gate in community | `community/views.py:751` | ✅ Built |
| Induction programme catalogue fix | `learn/views.py` catalogue query | ✅ Built (2026-06-08) |
| `MembershipRequest` community gate | `community/views.py` | ✅ Built |

---

## Architecture Decision

The auto-placement must happen exactly once per user, at registration, without any user action. The correct Django mechanism is a `post_save` signal on `User` with `created=True`.

**Where the signal lives:** `accounts/signals.py` — this file does not yet exist. It must be created and connected via `accounts/apps.py` `ready()` method.

**What the signal does:**
1. Fires only when `created=True` (new user, not a profile update)
2. Looks up the `/global/induction/` tenant singleton
3. Creates a `UserPermission` record placing the user in that tenant with role `seeker`
4. Sets `user.induction_enrolled_at = now()` and saves
5. Logs a warning and continues silently if the induction tenant does not exist — the platform must not break registration if the seed command has not been run

**What the signal does NOT do:**
- Does not advance `competence_level` (that happens only via certification confirmation — ADR-006)
- Does not create a `MembershipRequest` (the user is placed directly, no approval required)
- Does not send a notification (no meaningful notification to send at this point)
- Does not enrol the user in any specific induction programme (enrolment happens when the user taps "Start" in the seeker gate)

---

## Files to Change

### 1. `accounts/signals.py` — NEW FILE

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='accounts.User')
def auto_place_new_user_in_induction_tenant(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from tenants.models import Tenant, UserPermission
        induction_tenant = Tenant.objects.filter(
            tier='induction', slug='induction'
        ).first()
        if not induction_tenant:
            logger.warning(
                'Induction tenant not found — user %s placed with no community. '
                'Run: python manage.py seed_induction_tenant',
                instance.pk,
            )
            return
        UserPermission.objects.get_or_create(
            user=instance,
            tenant=induction_tenant,
            defaults={'role': 'seeker'},
        )
        if not instance.induction_enrolled_at:
            instance.induction_enrolled_at = timezone.now()
            instance.save(update_fields=['induction_enrolled_at'])
    except Exception:
        logger.exception(
            'Failed to auto-place user %s in induction tenant', instance.pk
        )
```

### 2. `accounts/apps.py` — EDIT

Add signal import in `ready()`:

```python
def ready(self):
    import accounts.signals  # noqa: F401
```

### 3. `community/views.py` — VERIFY (no change expected)

Confirm `seeker_gate` renders correctly for a user who is already a member of the induction tenant. The gate currently checks `_induction_status(user)` against active induction `Record` objects — this is independent of tenant membership and should continue working unchanged.

---

## Existing Users

Users who registered before this signal was wired have `competence_level = 0` and no induction tenant membership. A one-time backfill management command is needed:

### `accounts/management/commands/backfill_induction_placement.py` — NEW FILE

```python
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Place all Level 0 users without an induction tenant membership into /global/induction/'

    @transaction.atomic
    def handle(self, *args, **options):
        from accounts.models import User
        from tenants.models import Tenant, UserPermission

        induction_tenant = Tenant.objects.filter(tier='induction', slug='induction').first()
        if not induction_tenant:
            self.stdout.write(self.style.ERROR(
                'Induction tenant not found. Run seed_induction_tenant first.'
            ))
            return

        seekers = User.objects.filter(competence_level=0)
        placed = 0
        already = 0

        for user in seekers:
            _, created = UserPermission.objects.get_or_create(
                user=user,
                tenant=induction_tenant,
                defaults={'role': 'seeker'},
            )
            if created:
                if not user.induction_enrolled_at:
                    user.induction_enrolled_at = timezone.now()
                    user.save(update_fields=['induction_enrolled_at'])
                placed += 1
            else:
                already += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Placed: {placed}. Already placed: {already}.'
        ))
```

---

## Implementation Order

1. Create `accounts/signals.py`
2. Edit `accounts/apps.py` to call `import accounts.signals` in `ready()`
3. Run `python manage.py check` — 0 issues
4. Run `python manage.py backfill_induction_placement` on the existing database
5. Register a new test user — confirm `UserPermission` row exists for `/global/induction/`
6. Confirm seeker gate renders the induction programme list correctly for the new user

---

## Exit Criteria

- [ ] New user registration creates a `UserPermission` row in the induction tenant automatically
- [ ] `user.induction_enrolled_at` is set on registration
- [ ] Seeker gate shows induction programmes to the new user without any manual steps
- [ ] Existing Level 0 users are backfilled by the management command
- [ ] `python manage.py check` — 0 issues
- [ ] Induction tenant missing (seed not run) — registration still completes, warning logged, no 500 error

---

## What Happens After Induction

When induction is complete and `competence_level` advances to 1, the existing community flow steers the user to select a real tenant. The `MembershipRequest` gate in `community/views.py` already handles this. No changes needed there.

The user retains their `UserPermission` in the induction tenant after advancing — this is intentional. The induction tenant becomes a read-only reference, not an active community. Cleanup of stale induction memberships is a Version 3+ concern.
