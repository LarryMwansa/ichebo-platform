# Ichebo Platform Data Contract — v10 Amendments
**Version:** v10 — 2026-04-25
**Previous version:** v9 — 2026-04-10
**Status:** Approved

> **v10 Amendments:** All changes required for Version 2 build. Covers Induction system, Flutter mobile, Activity linking, relationship type addition, and certification endpoint extension.
>
> **Everything in v9 not listed below is carried forward unchanged.**

---

## Amendment 10.1 — Tenant Tier Enum: Add "induction"

**ADR:** ADR-002
**Phase:** Version 2.1 (G1 — Induction Tenant seed)

### Change

`Tenant.tier` enum gains a new value: `"induction"`.

**Updated enum:**
```
tier: "branch" | "district" | "province" | "national" | "regional" | "continental" | "global" | "induction"
```

### Induction Tenant — Seeded Singleton

```js
Tenant {
  id:       "<system-uuid>",
  name:     "Induction",
  slug:     "induction",
  path:     "/global/induction/",
  tier:     "induction",          // new value
  affiliation: "ichebo",
  status:   "active",
  settings: {
    allow_public_records: false,
    require_approval: false,      // auto-enrolment on registration
    max_members: null
  }
}
```

### Rules
- There is exactly one Induction Tenant. It is a system singleton.
- It cannot be deleted, renamed, or modified via normal UI flows.
- All users with `tier == "induction"` in their `UserPermission.tenant_path` are Level 0 Seekers in the induction pipeline.
- Content scoping: Level 0 users in the Induction Tenant see only Records with `metadata.source_app == "induction"` — no governance, community, or general learn content.

### Migration
```python
# tenants/migrations/00XX_add_induction_tier.py
# Alter field: tier — add "induction" to choices
```

---

## Amendment 10.2 — User Model: Induction Fields

**ADR:** ADR-003
**Phase:** Version 2.1 (G2 — Sign-up & Profile Registration)

### New fields on User (or UserProfile — match existing model location)

```js
User {
  // ... all existing fields unchanged ...

  // NEW — Induction tracking
  induction_enrolled_at:   "ISO-8601 | null",  // set on G2 profile setup completion
  induction_completed_at:  "ISO-8601 | null",  // set on G4 steward confirmation
  induction_pathway:       "reconditioning | beginners | null"  // set on entrant type selection
}
```

### Rules
- `induction_pathway` is set from the user's entrant type selection in the profile registration form.
- `induction_enrolled_at` is set when the `UserPermission` row for the Induction Tenant is created.
- `induction_completed_at` is set when `POST /api/learn/certifications/{id}/confirm/` is called with `metadata.context == "induction_completion"`.
- `induction_pathway` is immutable after the steward review — the steward may adjust the pathway during induction review if the initial self-selection was incorrect, but this is a steward action, not a user edit.

### Migration
```python
# accounts/migrations/00XX_add_induction_fields.py
# Add: induction_enrolled_at (DateTimeField, null=True)
#      induction_completed_at (DateTimeField, null=True)
#      induction_pathway (CharField, max_length=20, blank=True, null=True)
```

---

## Amendment 10.3 — UserProfile: Profile Registration Fields

**ADR:** N/A (domain decision — Chizola)
**Phase:** Version 2.1 (G2 — Sign-up & Profile Registration)

### New fields on UserProfile

```js
UserProfile {
  // ... all existing fields unchanged ...

  // NEW — Profile registration (G2)
  full_name:         "string",             // replaces or supplements display_name
  address:           "string | null",
  country:           "string | null",      // ISO 3166-1 alpha-2 code
  id_number:         "string | null",      // National ID or passport number — SENSITIVE
  age:               "integer | null",     // or store date_of_birth
  gender:            "male | female | prefer_not_to_say | null",
  occupation:        "string | null",
  education:         "string | null",      // highest qualification description
  born_again:        "boolean | null"      // Yes / No — Kingdom participation indicator
}
```

### Rules
- `id_number` is sensitive PII. It must be stored encrypted (Django's `encrypt-field` or equivalent). It must not appear in any API response by default — only accessible to Level 4+ administrators via an explicit admin endpoint.
- `country` is used for geographic tenant matching during induction placement (G4 — suggest + steward confirms).
- `born_again` is used by the Induction Coordinator to inform pathway assignment (Reconditioning vs Beginners), cross-referenced with `induction_pathway` from the entrant type selection.
- `full_name` should be treated as the display identity. `User.display_name` (existing) may be kept as a preferred name; `full_name` is the legal/formal name.

### Migration
```python
# accounts/migrations/00XX_add_profile_registration_fields.py
# Add: address, country, id_number (encrypted), age (or date_of_birth),
#      gender, occupation, education, born_again
```

### Security note
`id_number` must never be returned in `UserSerializer` or `UserProfileSerializer` unless the requesting user is Level 4+ and the endpoint is explicitly designed for it. Add to `extra_kwargs: {'id_number': {'write_only': True}}` at minimum. Consider field-level encryption.

---

## Amendment 10.4 — Activity Model: `linked_record` FK

**ADR:** ADR-010
**Phase:** Version 2 Pre-Build (code alignment)

### Change

Add an explicit foreign key on Activity to replace the loose metadata coupling currently used for linking activities to Records.

```js
Activity {
  // ... all existing fields unchanged ...

  // NEW — Explicit Record link (replaces metadata['programme_record_id'] etc.)
  linked_record_id:  "uuid | null"  // FK → records.Record, SET_NULL on delete
}
```

### Rules
- `linked_record_id` is nullable — not all activities are linked to a Record.
- Existing metadata keys (`metadata['programme_record_id']`, `metadata['lesson_record_id']`) are retained for backward compatibility but deprecated. New code must use `linked_record_id`.
- The FK is `SET_NULL` on Record deletion — activities are not deleted when a linked Record is deleted.
- Queryable: `Activity.objects.filter(linked_record_id=record.id)` replaces metadata JSON lookups.

### API change
`linked_record_id` is exposed as a writable field in `ActivitySerializer`.

### Migration
```python
# activity/migrations/00XX_add_linked_record_fk.py
# Add: linked_record = ForeignKey('records.Record', on_delete=SET_NULL, null=True, blank=True)
```

---

## Amendment 10.5 — Relationship Type: Add "community_ref"

**ADR:** ADR-009
**Phase:** Version 2.3 (Infrastructure — P2)

### Change

`Relationship.relationship_type` enum gains a new value: `"community_ref"`.

**Updated enum (full list):**
```
relationship_type:
  "part_of"
  "derived_from"
  "aligns_with"
  "authorised_by"
  "references"
  "tracks"
  "community_ref"    // NEW — community content → governance Record
```

### Usage
```js
// Community content linked to a governance record
Relationship {
  from_record_id:    "<community_record_uuid>",  // gathering, announcement, etc.
  to_record_id:      "<governance_record_uuid>", // doctrine, mandate, etc.
  relationship_type: "community_ref",
  direction:         "directed"
}
```

### Rules
- Used exclusively by the Community App to link community records (gatherings, announcements) to the governance records that inform or authorise them.
- Created via the existing `POST /api/relationships/` endpoint — no new endpoint needed.
- Browseable in the Linked Records panel of governance records (flat list, as per current implementation).

---

## Amendment 10.6 — Certification Confirm Endpoint: Induction Completion Extension

**ADR:** ADR-003
**Phase:** Version 2.1 (G4 — Induction Completion & Tenant Placement)

### Change

`POST /api/learn/certifications/{id}/confirm/` is extended to handle induction completion as a special case.

### Extended request body (when `metadata.context == "induction_completion"`)

```js
// Standard request body (unchanged for non-induction confirmations):
{
  "notes": "string | null"
}

// Extended request body for induction completion:
{
  "notes": "string | null",
  "placement_tenant_id": "uuid"  // NEW — required when context == "induction_completion"
}
```

### Extended logic (when `metadata.context == "induction_completion"`)

In addition to the standard confirm logic (set certification Record to `active`, increment `competence_level` to 1):

1. Set `user.induction_completed_at = now()`
2. Create `UserPermission`: `tenant_id = placement_tenant_id`, `level = 1`, `role = "disciple"`, `is_active = True`, `granted_by = confirming_steward`
3. Deactivate Induction Tenant `UserPermission`: `is_active = False`
4. Write `ActivityLog` entry: `"Induction completed — placed in {tenant.name}"`
5. Trigger notification to user: "Your induction is complete. Welcome to {tenant.name}."

### Validation
- `placement_tenant_id` is required in the request body when `metadata.context == "induction_completion"`.
- The confirming user must be Level 3+ within the Induction Tenant (Induction Coordinator role).
- `placement_tenant_id` must be a valid, active, non-induction tenant.

### Migration
No migration required — endpoint logic change only.

---

## Amendment 10.7 — User Model: FCM Token

**ADR:** ADR-001 (Flutter mobile), ADR-006 (Delta Sync)
**Phase:** Version 2.3 (Infrastructure — P4)

### New field on User

```js
User {
  // ... all existing fields unchanged ...

  // NEW — Firebase Cloud Messaging token for push notifications
  fcm_token:  "string | null"  // max 255 chars, updated on mobile app login
}
```

### Rules
- Updated by the Flutter app on each login via `PATCH /api/auth/me/` with `{"fcm_token": "<token>"}`.
- Nullable — users without the mobile app have no token; web-only users are unaffected.
- Not exposed in public-facing serializers — internal use only for notification dispatch.

### Migration
```python
# accounts/migrations/00XX_add_fcm_token.py
# Add: fcm_token = CharField(max_length=255, blank=True, null=True)
```

---

## Amendment 10.8 — New API Endpoint: Delta Sync

**ADR:** ADR-006
**Phase:** Version 2.3 (Infrastructure — P3)

### New endpoint

```
GET /api/sync/changes/?since={iso_timestamp}
```

### Response

```js
{
  "since": "2026-04-01T00:00:00Z",
  "retrieved_at": "2026-04-25T10:00:00Z",
  "records":       [...],   // Records modified after 'since', scoped to user's tenants
  "activities":    [...],   // Activities modified after 'since', scoped to user
  "notifications": [...]    // Notifications for this user modified after 'since'
}
```

### Rules
- Uses existing `updated_at` fields on all models — no model changes required.
- Response is scoped to the requesting user's tenant permissions — same filtering as all other API views.
- Pagination: returns max 500 items per type per request. If more exist, response includes `"has_more": true` and the client must paginate using `since` + the last `updated_at` in the batch.
- Requires authentication.

### File
New: `core/views/sync.py` — `SyncChangesView(APIView)`
New URL: `path('api/sync/changes/', SyncChangesView.as_view(), name='sync-changes')` in `ics_project/urls.py`

---

## Amendment 10.9 — New API Endpoint: Aggregated Relationships

**Phase:** Version 2.3 (Infrastructure — P2)

### New endpoint

```
GET /api/records/{id}/related/
```

### Response

```js
{
  "record_id": "uuid",
  "outgoing": {
    "part_of":     [...],
    "references":  [...],
    "tracks":      [...],
    // ... other types with outgoing links
  },
  "incoming": {
    "derived_from": [...],
    // ... other types with incoming links
  }
}
```

### Rules
- Reuses `get_linked_records()` from `governance/services.py` — no new query logic.
- Added as a `@action(detail=True, methods=['get'])` on `RecordViewSet`.
- Requires authentication; respects existing record-level visibility rules.

### File
Modify: `records/views.py` — add `related` action on `RecordViewSet`

---

## Summary of All v10 Changes

| Amendment | Change | Phase |
|-----------|--------|-------|
| 10.1 | `Tenant.tier`: add `"induction"` | 2.1 G1 |
| 10.2 | `User`: add `induction_enrolled_at`, `induction_completed_at`, `induction_pathway` | 2.1 G2 |
| 10.3 | `UserProfile`: add profile registration fields (full_name, address, country, id_number, age, gender, occupation, education, born_again) | 2.1 G2 |
| 10.4 | `Activity`: add `linked_record = FK(records.Record)` | Pre-Build |
| 10.5 | `Relationship.relationship_type`: add `"community_ref"` | 2.3 P2 |
| 10.6 | `certifications/confirm/`: extend for induction completion + placement | 2.1 G4 |
| 10.7 | `User`: add `fcm_token` | 2.3 P4 |
| 10.8 | New endpoint: `GET /api/sync/changes/` | 2.3 P3 |
| 10.9 | New endpoint: `GET /api/records/{id}/related/` | 2.3 P2 |

### Migrations required (bundle per phase)

**Pre-Build:**
- `activity`: add `linked_record` FK (Amendment 10.4)

**Version 2.1 (before G1 build):**
- `tenants`: add `"induction"` to tier choices (Amendment 10.1)
- `accounts`: add induction fields to User (Amendment 10.2)
- `accounts`: add profile registration fields to UserProfile (Amendment 10.3)

**Version 2.3:**
- `records`: update relationship_type choices (Amendment 10.5)
- `accounts`: add `fcm_token` to User (Amendment 10.7)
