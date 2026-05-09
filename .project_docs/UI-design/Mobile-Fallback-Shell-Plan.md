# Mobile Fallback Shell — Implementation Plan
**Status:** Known Gap — Deferred post-V2 roadmap
**Audited:** 2026-05-09 | Auditor: Claude (Chief Design Engineer)

---

## Background

The platform has two client surfaces:
- **Desktop Web UI** — Django templates + HTMX, operators only (Level 1+, desktop/tablet)
- **Mobile App** — Flutter + DRF API, all users

The mobile fallback is a **browser-based mobile UI** served by Django templates when the Flutter app is unavailable. It is not the primary mobile surface — it is an emergency fallback so operators can still function on their phones if the app is down.

---

## How the Dual-Shell Architecture Works

`base.html` implements the dual-shell pattern correctly:

1. **Both blocks defined** — `{% block content %}` (mobile) and `{% block ws_content %}` (desktop)
2. **JS switching** — inline script on `base.html` toggles `.ws-active` on `<body>` at viewport ≥ 1024px
3. **CSS switching** — `workspace.css` hides/shows based on `.ws-active`:

```css
body.ws-active .ics-main { display: none !important; }    /* hide mobile */
body.ws-active .ws-layout { display: flex; }              /* show desktop */
```

**The problem:** `workspace_shell.html` is a separate root template built for the desktop rebuild. It has no `{% block content %}` block. Any template extending it is desktop-only — mobile users see an empty 4-column grid.

---

## Current State (Audited 2026-05-09)

### Templates with both shells intact ✅

| Template | Notes |
|----------|-------|
| `dashboard/index.html` | Full mobile layout present |
| `notifications/notifications.html` | Full mobile layout present |

### Templates missing mobile fallback ❌

| Template | Extends | Priority |
|----------|---------|----------|
| `dashboard/you.html` | workspace_shell.html | High — personal hub |
| `activity/my_activities.html` | workspace_shell.html | High — daily use |
| `community/my_community.html` | workspace_shell.html | High — daily use |
| `learn/my_learning.html` | workspace_shell.html | High — daily use |
| `records/my_records.html` | records/base_records.html → workspace_shell | Medium |
| `workspace/governance/home.html` | governance/base.html → hub.html → workspace_shell | Medium — L3+ only |
| `tenants/steward_dashboard.html` | base_tenants.html → workspace_shell | Low — L3+ only |

---

## Implementation Plan

### Step 1 — Add `{% block content %}` to `workspace_shell.html`

**File:** `backend/templates/workspace_shell.html`

Add after the closing `{% endblock %}` of `ws_content`, before `</body>`:

```html
{# ═══════════════════════════════════════════════════════
   MOBILE FALLBACK — renders on viewport < 1024px.
   Only used when Flutter app is unavailable.
   ═══════════════════════════════════════════════════════ #}
{% block content %}{% endblock %}
```

This unblocks all seven templates — they can now define `{% block content %}` without changing their shell inheritance.

---

### Step 2 — Wire mobile content per template (Priority order)

For each template, add a `{% block content %}` section at the bottom that mirrors the mobile UI patterns from `base.html`. Use existing mobile CSS classes: `dash-header`, `dash-section`, `dash-widget`, `list-group`, `list-item`, `btn-touch`, etc.

---

#### 2A — `dashboard/you.html` (High)

Mobile block should contain:
- User avatar + display name + level badge
- Formation progress bar
- Apostolic Digest list (overdue, due today, reminders)
- Jurisdictional Access links (Profile, Active Duties, Community, Formation)
- Registry Inventory stat grid (Level / Acts / Records)
- Settings link

Reference: the existing `{% block ws_content %}` in the same file has all the data — the mobile block is a simplified linear version.

---

#### 2B — `activity/my_activities.html` (High)

Mobile block should contain:
- Header with "My Activities" title + "New" CTA
- Filter pills (All / Overdue / Today / Upcoming)
- Flat list of activities using `list-item` component
- Each item: title, type badge, due date, status

---

#### 2C — `community/my_community.html` (High)

Mobile block should contain:
- Community name + tier badge header
- Announcements list (most recent 3, "View all" link)
- Upcoming gatherings list (next 3)
- Member count stat
- Management CTA (Level 3+ only)

---

#### 2D — `learn/my_learning.html` (High)

Mobile block should contain:
- Active enrolments with progress bars
- Next lesson CTA (if any)
- "Browse Catalogue" link
- Habit streaks strip (from digest)

---

#### 2E — `records/my_records.html` (Medium)

Mobile block should contain:
- Record type filter tabs
- Flat list of recent records using `list-item`
- "New Entry" CTA

---

#### 2F — `workspace/governance/home.html` (Medium)

Mobile block should contain:
- Branch selector tabs (Reference / Mandate / Keys)
- Recent records list per branch
- "New Act" CTA (Level 4+)
- Locked state for Level < 3

---

#### 2G — `tenants/steward_dashboard.html` (Low — L3+ only)

Mobile block should contain:
- My Communities list (tap to open)
- Pending invitations count badge
- "New Community" CTA (Level 3+)
- Agency tenants section (Level 5+)

---

### Step 3 — Verify CSS switching still works

After adding blocks, test at 375px (iPhone), 768px (tablet), 1280px (desktop):

- Mobile viewport: only `{% block content %}` visible, desktop 4-column grid hidden
- Desktop viewport: only `{% block ws_content %}` visible, mobile layout hidden
- Transition point: 1024px (defined in `workspace.css`)

Confirm `.ws-active` class is being toggled correctly for users at all competence levels. The current toggle script checks `competence_level >= 3` — confirm whether the fallback should apply to Level 1+ users too (likely yes, since Level 1–2 use the platform via web on mobile as the only option).

---

## Key Files Reference

| File | Role |
|------|------|
| `backend/templates/workspace_shell.html` | Desktop root shell — needs `{% block content %}` added |
| `backend/templates/base.html` | Mobile root shell — dual-shell pattern reference |
| `backend/static/css/workspace.css` | `.ws-active` switching CSS |
| `backend/static/css/app.css` or `base.css` | Mobile component classes |

---

## Definition of Done

- [ ] `{% block content %}` block added to `workspace_shell.html`
- [ ] Mobile fallback added to all 7 templates (2A–2G)
- [ ] Tested at 375px — mobile layout visible, desktop grid hidden
- [ ] Tested at 1280px — desktop workspace visible, mobile layout hidden
- [ ] Level 1 user on mobile sees correct mobile fallback for all major pages
- [ ] Level 3+ user on desktop sees correct workspace shell for all major pages
- [ ] No regression on `dashboard/index.html` or `notifications/notifications.html` (already working)
