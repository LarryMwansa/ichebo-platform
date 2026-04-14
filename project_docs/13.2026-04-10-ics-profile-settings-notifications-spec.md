# ICS Profile, Settings & Notifications
## Build Specification — Tasks 5.6 & 5.7

*2026-04-10 · Data contract reference: v9 · No system design session required*

> **Why no advisory session was needed**
>
> Profile + Settings: no new record types, no new models, no KGS access rules. All data is already defined — `User.preferences` (Part 2.1) and `UserProfile` (Part 2.1) are fully specified in the data contract. This is a UI wrapper over existing endpoints.
>
> Notifications (stub): a nav entry point only. Full implementation depends on trigger sources not yet built (Activity, Community, Governance). The stub wires the shell. No data contract amendment required for either task.

> **Data contract reference: v9**
>
> Profile and Settings: Part 2.1 (User object, UserProfile extension).
> Notifications stub: no contract section — stub returns empty list only.
> Both tasks: Part 6.1 (Django app structure), Part 6.2 (app ownership rules).

---

## Task 5.6 — Profile + Settings

### Overview

Profile and Settings are two views within a single `accounts/` surface. They are not a separate Django app — the `accounts/` app already exists (it owns User, UserProfile, UserPermission). These views are added as new templates and URL routes within `accounts/`.

Profile shows the logged-in user's identity and formation information. Settings provides controls for preferences — theme, language, timezone, and preferred Bible translation — all of which are persisted to the database, not localStorage.

> *The roadmap stub said preferences would be localStorage only. This is superseded by the data contract: `User.preferences` is a JSONField on the User model (Part 2.1) and `preferred_bible_translation` is a FK on UserProfile. All preferences are DB-persisted in MVP.*

---

### What Profile Shows

#### Profile View — `/accounts/profile/`

Single-page view for the logged-in user. Read-only display of identity and formation data. Edit is inline via HTMX for `display_name` and `avatar_url` only.

**Identity section**

- Avatar: `avatar_url` rendered as circular image (placeholder initials if null)
- Display name: editable inline — HTMX PATCH to `/api/auth/me/`; `hx-trigger="click"` on pencil icon opens inline text input; on submit replaces with updated name
- Email: read-only display (not editable — email changes are a security operation, deferred)
- Member since: `created_at` formatted as human-readable date
- Platform status badge: `active` / `seeker` / `suspended`

**Formation section**

- Competence level: label + numeric level (e.g. "Functional Minister — Level 3") sourced from `User.competence_level` mapped to Part 2.3 table
- KGS level name and platform label displayed together
- Tenant memberships: list of active `UserPermission` rows for this user — each showing tenant name, role label, `granted_at` date
- If no tenant memberships: "You are not yet a member of a community." with link to Community App

**Bible preference**

- Current preferred translation label (from `UserProfile.preferred_bible_translation`, or "King James Version (default)" if null)
- Link to change: "Change translation" navigates to Settings → Bible section

---

### What Settings Shows

#### Settings View — `/accounts/settings/`

Organised into three sections, each as a collapsible card or distinct sub-section. All saves are HTMX PATCH to `/api/auth/me/` (preferences JSONField) or dedicated endpoints. No full page reload.

**Section 1 — Appearance**

- Theme selector: three-option radio — System / Light / Dark; current value read from `User.preferences.theme`
- On change: HTMX PATCH `/api/auth/me/` with `{"preferences": {"theme": "{value}"}}`; also applies immediately via `storage.js` theme toggle (keeps UI in sync without reload)
- Success: inline "Saved" confirmation fades in and out (no toast library — CSS transition only)

**Section 2 — Language & Region**

- Language: dropdown (English only in MVP — other options shown but disabled with "(coming soon)" label); current value from `User.preferences.language`
- Timezone: dropdown populated from a curated list of IANA timezone strings (Africa/Johannesburg pre-selected for ZA locale; full list available); current value from `User.preferences.timezone`
- Save button for this section: single PATCH for both fields together
- Note: timezone affects how `scheduled_at` and `due_at` fields are displayed across all apps — it does not shift stored UTC values

**Section 3 — Bible**

- Preferred translation: radio selector showing all `BibleTranslation` rows where `is_public = true`
- Populated via `GET /api/bible/translations/` — same endpoint the Bible App uses
- Current selection read from `UserProfile.preferred_bible_translation` (null = default, shown as "KJV (Default)")
- On save: `POST /bible/htmx/translation/set/` — this endpoint already exists from the Bible App (Part 13.8); no new endpoint needed
- Confirmation: "Preferred translation updated" inline message

---

### Data Flow

#### Endpoints consumed

```
# Profile — read
GET  /api/auth/me/
# Returns: User object (id, email, display_name, avatar_url, competence_level,
#          status, preferences, created_at) + UserProfile (preferred_bible_translation)

# Profile — edit display_name or avatar_url
PATCH /api/auth/me/
{ "display_name": "Updated Name" }
{ "avatar_url": "https://..." }

# Settings — save theme
PATCH /api/auth/me/
{ "preferences": { "theme": "dark" } }

# Settings — save language + timezone
PATCH /api/auth/me/
{ "preferences": { "language": "en", "timezone": "Africa/Johannesburg" } }

# Settings — preferred Bible translation (existing Bible App endpoint)
POST /bible/htmx/translation/set/
{ "translation_code": "ASV" }

# Tenant memberships (for Profile formation section)
GET  /api/permissions/?user_id={user_id}&is_active=true
# Returns: UserPermission rows with tenant detail
```

> *`PATCH /api/auth/me/` uses a partial update — only the fields sent are modified. The `preferences` JSONField is merged at the serializer level, not replaced wholesale. Confirm this is implemented in the `accounts/` DRF serializer before building the Settings UI.*

---

### Django App Structure

#### Files added to `accounts/`

```
~/ics/accounts/
  [existing files unchanged]
  templates/
    accounts/
      profile.html                  ← full-page shell (extends base.html)
      _profile_identity.html        ← identity section partial
      _profile_formation.html       ← formation + memberships partial
      _settings.html                ← settings page partial (all three sections)
      _settings_appearance.html     ← appearance section partial
      _settings_region.html         ← language + timezone section partial
      _settings_bible.html          ← Bible translation section partial
      _display_name_edit.html       ← inline display_name edit partial
      _save_confirm.html            ← inline "Saved" confirmation partial

  # New URL routes added to accounts/urls.py
  GET   /accounts/profile/                        → ProfileView
  GET   /accounts/settings/                       → SettingsView

  # New HTMX routes
  PATCH /accounts/htmx/profile/display-name/      inline name edit
  PATCH /accounts/htmx/settings/theme/            theme save
  PATCH /accounts/htmx/settings/region/           language + timezone save
  # Bible translation uses existing: POST /bible/htmx/translation/set/
```

---

### HTMX Interaction Patterns

| Interaction | HTMX trigger | Server action |
|---|---|---|
| Edit display name | `hx-get` on pencil icon → opens input; `hx-patch` on submit | PATCHes `/api/auth/me/`; returns updated name partial |
| Save theme | `hx-patch` on radio change (no button needed) | PATCHes `preferences.theme`; returns save-confirm partial |
| Save region | `hx-patch` on Save button for this section | PATCHes `preferences.language` + timezone; returns confirm |
| Save Bible translation | `hx-post` on radio change | POSTs to existing `/bible/htmx/translation/set/`; returns confirm |
| Load tenant memberships | `hx-trigger="load"` on memberships div | Returns membership list partial |

---

### Access Rules

Profile and Settings are accessible to all authenticated users (Level 0b and above). There are no competence-level gates.

- Unauthenticated users are redirected to login (`LoginRequiredMixin` on both views)
- A user can only view and edit their own profile — `/api/auth/me/` is always scoped to the requesting user by the DRF auth layer
- No steward can view another user's Settings — this surface is personal only

---

### Exit Criteria — Task 5.6

- `GET /accounts/profile/` renders correctly for a Level 1 user showing identity, formation level, and tenant memberships
- Display name edit via HTMX inline form persists to database and updates the displayed name without page reload
- `GET /accounts/settings/` renders all three sections (Appearance, Language & Region, Bible)
- Theme change via Settings immediately applies the theme to the page (via `storage.js`) AND persists to `User.preferences` in the database
- Timezone selection PATCHes `User.preferences.timezone`; the value is readable back via `/api/auth/me/`
- Bible translation change via Settings uses the existing Bible App endpoint and updates `UserProfile.preferred_bible_translation`
- All HTMX saves show an inline confirmation; no full page reload occurs on any save
- Commit: `git add . && git commit -m "feat: profile and settings"`

---

## Task 5.7 — Notifications Stub

### Overview

The Notifications stub completes the platform shell. Its sole purpose in MVP is to wire the notifications entry point in the navbar so the navigation is complete — every app slot in the shell has a corresponding destination.

Full notifications implementation is post-Dashboard. The trigger sources that would generate notifications (Community App announcements, Activity App assignments, Governance App record locks, Learn App certification confirmations) are not all built yet, and a coherent notification system requires knowing all of them before designing the schema.

> **What the stub is NOT**
>
> Not a working notification system. Not a data model design — no Notification model is added in MVP. Not a real-time system — no WebSockets, no polling, no push. The stub is a placeholder UI that returns an empty list and renders gracefully.

---

### What the Stub Builds

**Four deliverables — nothing more**

- A `notifications/` Django app (scaffold only — no models)
- `GET /api/notifications/` — DRF endpoint returning an empty paginated list
- `GET /notifications/` — Django template view rendering the empty state
- Navbar bell icon badge: reads the count from `/api/notifications/unread-count/` — returns `{"count": 0}` in MVP; badge hidden when count is 0

#### Notification list view — `/notifications/`

- Empty state: bell icon + "No notifications yet." + explanatory subtext: "You'll be notified here about community announcements, assigned tasks, and formation milestones."
- When notifications exist (post-MVP): list of notification cards with icon, message, timestamp, read/unread state, and a link to the originating record or activity
- Mark all as read: button visible when unread count > 0 (post-MVP wiring only — button exists in MVP but calls a stub endpoint that returns 200 with no effect)

---

### Django App Structure

```
~/ics/notifications/
  __init__.py
  apps.py
  views.py        ← NotificationListView (template) + API views
  serializers.py  ← empty stub serializer
  urls.py
  templates/
    notifications/
      notifications.html        ← full-page shell (extends base.html)
      _notification_list.html   ← list partial (empty state in MVP)

  # No models.py in MVP
  # No migrations beyond app registration
```

---

### Endpoints

```
# DRF endpoints (notifications/urls.py → api/notifications/)

GET  /api/notifications/
# Returns: { "count": 0, "next": null, "previous": null, "results": [] }
# Pagination structure kept so post-MVP implementation drops in without UI changes

GET  /api/notifications/unread-count/
# Returns: { "count": 0 }
# Read by navbar to conditionally show badge

POST /api/notifications/mark-all-read/
# Returns: { "marked": 0 }
# Stub — no effect in MVP; wired up when Notification model exists

GET  /api/notifications/health/
# Returns: { "status": "ok" }

# Template view
GET  /notifications/    → NotificationListView
```

---

### Navbar Integration

The navbar bell icon already exists in `base.html`. The stub wires it:

- Bell icon links to `/notifications/`
- Badge count: fetched on page load via HTMX — `GET /api/notifications/unread-count/`; badge element hidden via CSS when count is 0
- No polling in MVP — count is fetched once on page load only

> *The badge fetch is the one place where a small inline `hx-get` on the bell icon wrapper is appropriate — `hx-trigger="load"` fetches the count and swaps the badge element. This is consistent with the lazy-load HTMX pattern used in the Linked Records panel and the Version History panel.*

---

### Post-MVP Design (not built now — reference only)

When the Notifications App is fully implemented, it will need:

- A `Notification` model: `id`, `user_id`, `notification_type`, `source_app`, `source_record_id` (nullable), `source_activity_id` (nullable), `message`, `is_read`, `created_at`
- Trigger points: Community App announcement create → notify all tenant members; Activity App task assignment → notify `assigned_to` user; Learn App certification confirmation → notify learner; Governance App record lock → notify Level 4 stewards in scope
- A signal-based or post-save hook architecture to avoid tight coupling between apps
- The `/api/notifications/` endpoint returning real `Notification` rows, paginated
- Real-time delivery: either short-poll (simplest — HTMX polling on the bell badge every 60s) or Django Channels WebSocket (deferred)

> *The stub's paginated empty response format is intentional — the post-MVP implementation slots in without changing the frontend contract.*

---

### Exit Criteria — Task 5.7

- `GET /api/notifications/` returns `{"count": 0, "next": null, "previous": null, "results": []}`
- `GET /api/notifications/unread-count/` returns `{"count": 0}`
- `GET /api/notifications/health/` returns `{"status": "ok"}`
- `GET /notifications/` renders the empty state with explanatory text; no errors
- Navbar bell icon is linked to `/notifications/` and the badge is hidden (count = 0)
- No `Notification` model exists — no migration for a model table
- Commit: `git add . && git commit -m "feat: notifications stub"`

---

## Combined Build Order — Tasks 5.6 + 5.7

These two tasks are the final items before Phase 6 (Paraclete) and Phase 7 (Dashboard). Build in this order:

| Step | Action | Files | Commit |
|---|---|---|---|
| 1 | Verify `/api/auth/me/` PATCH supports partial preferences merge | `accounts/serializers.py` — confirm JSONField merge behaviour | — |
| 2 | Add Profile view | `accounts/views.py`, `accounts/urls.py`, `profile.html`, `_profile_identity.html`, `_profile_formation.html` | — |
| 3 | Add Settings view | `_settings.html`, `_settings_appearance.html`, `_settings_region.html`, `_settings_bible.html`, HTMX routes | — |
| 4 | Verify all exit criteria for 5.6 | — | `feat: profile and settings` |
| 5 | Scaffold `notifications/` app | `notifications/__init__.py`, `apps.py`, `views.py`, `serializers.py`, `urls.py`, `notifications.html`, `_notification_list.html` | — |
| 6 | Register `notifications/` in settings + root URLs; wire navbar bell | `ics_project/settings.py`, `ics_project/urls.py`, `base.html` (bell icon) | — |
| 7 | Verify all exit criteria for 5.7 | — | `feat: notifications stub` |

---

> **After Task 5.7 — what comes next**
>
> Phase 5 is complete. All app shells are live.
> Phase 6: Paraclete service (`paraclete/service.py` + DRF endpoints).
> Phase 7: Dashboard (reads `ParacleteDigest`, role-aware widgets).
> Phase 8: Calendar App Phase 2 (full month/week grid, Record events).
> Phase 9: Production hardening (SSL, static files, logging, systemd).

---

*ICS Build Specification — Tasks 5.6 & 5.7 · 2026-04-10 · Data contract v9*
