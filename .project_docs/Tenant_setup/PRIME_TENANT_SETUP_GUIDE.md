# Prime Tenant (Handbook) Setup Procedure

## Overview

Per the data contract and roadmap, **The Handbook is a special singleton tenant** created by management command on first deploy. It's the Prime Tenant where all governance content lives.

---

## What is Prime Tenant / The Handbook?

### Fixed Identity:
```
Name:        "The Handbook"
Slug:        "handbook"
Path:        "/global/handbook/"
Tier:        "handbook" (special tier, only one exists)
Affiliation: "ichebo"
Status:      "active"
```

### Purpose:
- Central knowledge repository for the ICS platform
- Only accessible to Level 3+ (read) and Level 5 (write)
- Contains governance records: Reference Library, Mandate, Keys
- Managed exclusively by Level 5 Architects

### Permissions Model:
| User Level | Access Type | What they see |
|------------|-------------|---------------|
| Level 0-2  | ✗ None      | Cannot access Handbook records at all |
| Level 3+   | ✓ Read      | Reference Library types only (class, principle, concept, divine_pattern) |
| Level 4+   | ✓ Read      | All types (Reference Library + Mandate branch) |
| Level 5    | ✓ Read+Write| All types + can create, approve, lock records |

---

## Current Status in Your Setup

**Problem:** You have a Level 5 user but **no Prime Tenant / Handbook created yet**.

This means:
- ✗ Governance app has no Handbook to read/write to
- ✗ Learning app (Task 5.2) will fail when it tries to reference Handbook records
- ✗ Level 5 approval workflows don't work

---

## How to Create Prime Tenant

### Option 1: Management Command (Recommended)

Per the roadmap: **"Handbook tenant at `/global/handbook/` created by management command on first deploy."**

You need to create a Django management command:

**File: `~/ics/tenants/management/commands/create_handbook.py`**

```python
from django.core.management.base import BaseCommand
from tenants.models import Tenant
from accounts.models import User

class Command(BaseCommand):
    help = 'Create the Handbook (Prime Tenant) singleton'

    def handle(self, *args, **options):
        # Check if Handbook already exists
        handbook = Tenant.objects.filter(
            path='/global/handbook/',
            tier='handbook'
        ).first()
        
        if handbook:
            self.stdout.write(
                self.style.WARNING(
                    f'Handbook already exists: {handbook.id}'
                )
            )
            return

        # Get system user (or first superuser)
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(
                self.style.ERROR(
                    'No superuser found. Create a superuser first: '
                    'python manage.py createsuperuser'
                )
            )
            return

        # Create Handbook tenant
        handbook = Tenant.objects.create(
            name='The Handbook',
            slug='handbook',
            path='/global/handbook/',
            tier='handbook',
            affiliation='ichebo',
            status='active',
            is_collective=False,
            created_by=system_user,
            description='Prime tenant containing governance knowledge: Reference Library and Mandate Branch',
            settings_data={
                'allow_public_records': False,
                'require_approval': True,
                'max_members': None
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Handbook created: {handbook.name} ({handbook.path})'
            )
        )
```

**Run the command:**
```bash
python manage.py create_handbook
```

**Expected output:**
```
✓ Handbook created: The Handbook (/global/handbook/)
```

### Option 2: Django Admin

If you prefer GUI:
1. `python manage.py runserver 8001`
2. Go to `/admin/`
3. Navigate to Tenants
4. Click "Add Tenant"
5. Fill in:
   - **Name:** The Handbook
   - **Slug:** handbook
   - **Path:** /global/handbook/
   - **Tier:** handbook
   - **Affiliation:** ichebo
   - **Status:** active
   - **Is Collective:** unchecked
   - **Description:** Prime tenant containing governance knowledge
   - **Settings:** `{"allow_public_records": false, "require_approval": true, "max_members": null}`
6. Save

### Option 3: Django Shell

```bash
python manage.py shell
```

```python
from tenants.models import Tenant
from accounts.models import User

system_user = User.objects.filter(is_superuser=True).first()

handbook = Tenant.objects.create(
    name='The Handbook',
    slug='handbook',
    path='/global/handbook/',
    tier='handbook',
    affiliation='ichebo',
    status='active',
    is_collective=False,
    created_by=system_user,
    description='Prime tenant containing governance knowledge',
    settings_data={
        'allow_public_records': False,
        'require_approval': True,
        'max_members': None
    }
)

print(f"✓ Handbook created: {handbook.name} ({handbook.path})")
```

---

## What About Your Level 5 User?

**Current state:** Your user is Level 5 but has no UserPermission for Handbook.

**Fix:** Grant yourself Handbook access

### Via Django Admin:
1. Go to `/admin/tenants/userpermission/`
2. Click "Add User Permission"
3. Fill in:
   - **User:** (your Level 5 user)
   - **Tenant:** The Handbook
   - **Role:** global-steward (or admin)
   - **Level:** 5
   - **Tenant Path:** /global/handbook/
   - **Granted By:** (yourself or superuser)
4. Save

### Via Django Shell:
```python
from tenants.models import Tenant, UserPermission
from accounts.models import User

your_user = User.objects.get(email='your-email@example.com')
handbook = Tenant.objects.get(path='/global/handbook/')

perm = UserPermission.objects.create(
    user=your_user,
    tenant=handbook,
    role='global-steward',
    level=5,
    tenant_path='/global/handbook/',
    created_by=your_user,
    granted_by=your_user
)

print(f"✓ User permission created: {your_user.display_name} → Handbook (Level 5)")
```

---

## Verification

After creating Handbook and granting yourself access, verify:

**1. Check Handbook exists:**
```python
from tenants.models import Tenant

handbook = Tenant.objects.get(path='/global/handbook/')
print(f"Handbook: {handbook.name} ({handbook.path}, tier={handbook.tier})")
# Expected: Handbook: The Handbook (/global/handbook/, tier=handbook)
```

**2. Check your permission:**
```python
from accounts.models import User

your_user = User.objects.get(email='your-email@example.com')
handbook_perm = your_user.tenant_permissions.filter(
    tenant__path='/global/handbook/'
).first()

print(f"Permission: {your_user.display_name} → Level {handbook_perm.level}")
# Expected: Permission: [Your Name] → Level 5
```

**3. Test in governance app:**
- Navigate to `/governance/` in your browser
- You should now see Reference Library and Mandate options (if logged in as Level 5)
- Click into Reference Library → you should see list page (currently empty, but functional)

---

## Current Governance App Status

**What's working:** UI views, forms, HTMX drawer
**What's blocked:** No Handbook tenant to read/write to

Once you create Handbook:
- ✅ Governance list pages will show empty lists (no records yet)
- ✅ Create buttons will work (records will save to Handbook)
- ✅ Form context-aware FAB will work
- ✅ Ready for Learn app build (which needs Handbook for learning content)

---

## Next Steps

1. **Create Handbook tenant** (choose Option 1, 2, or 3 above)
2. **Grant yourself Handbook access** (UserPermission, Level 5)
3. **Verify in `/governance/`** (should no longer show 403 errors)
4. **Test record creation:**
   - Go to `/governance/reference/`
   - Click FAB (context should detect you're in reference)
   - Create a test Principle record
   - It should save to Handbook with draft status

---

## Learn App Dependency

When you build Task 5.2 (Learn App), it will:
- Create Programmes/Courses as Records with `record_family: "learning"` in Handbook
- Level 4+ authors submit courses for Handbook review
- Level 5 approves courses in review queue

Without Handbook:
- ✗ No place to store learning content
- ✗ Approval workflow breaks
- ✗ Level 5 review queue has nothing to review

---

## Summary

| What | Status | Next Action |
|------|--------|-------------|
| **Handbook Tenant** | ❌ Missing | Create it (Option 1, 2, or 3) |
| **Your Level 5 Account** | ✅ Exists | Grant Handbook permission after creating Handbook |
| **Governance App** | ✅ UI built | Will work once Handbook exists |
| **Learn App** | ⏳ Pending | Depends on Handbook (create Handbook first) |

