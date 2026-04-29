# ICS Workspace UI Plan
**Branch:** version-2  
**Date:** 2026-04-29  
**Author:** Larry Mwansa

---

## Context

The desktop workspace (`ws-layout`) is exclusively for **Level 3+ Sceptre Stewards**. It is not a responsive version of the mobile app — it is a separate, purpose-built governance and stewardship interface.

Mobile users (Level 0–2) use the mobile shell (navbar + bottom nav). They never see the workspace.

The workspace activates automatically when:
- User is authenticated AND `competence_level >= 3`
- Viewport is ≥ 1024px
- `.ws-active` is added to `<body>` by the inline script in `base.html`

---

## Two Separate Layouts — Never Mixed

| Block | Who sees it | Purpose |
|-------|-------------|---------|
| `{% block content %}` | Mobile users, Level 0–2 | Mobile-first layout for `<main id="main-content">` |
| `{% block ws_content %}` | Level 3+ Stewards on desktop | Workspace-native layout for `<div id="ws-content">` |

These are **designed independently**. `ws_content` is never a copy of `content`. Each is designed for its context and canvas width.

---

## The 3 Workspace Layout Patterns

Three reusable layout patterns defined once in `workspace.css`, applied per-app via CSS classes on the `ws_content` wrapper.

### 1. `ws-layout--grid`
**Used by:** Dashboard  
**Description:** Side-by-side columns for stat blocks, digest section, DAR widget, mission items. Takes advantage of full desktop width. No list/detail split — content is self-contained cards in a responsive grid.

### 2. `ws-layout--master-detail`
**Used by:** Governance, Tenants, Community  
**Description:** Fixed-width list panel on the left (~320px), content/detail panel fills the rest. Clicking a list item loads detail into the right panel via HTMX (`hx-target="#ws-detail"`). The `ws-panel` (right slide-in panel) is used for creation/edit forms.

```
┌─────────────┬──────────────────────────────────┐
│  List panel │  Detail / content panel          │
│  (~320px)   │  (fills remaining width)         │
│             │                                  │
│  item 1     │  [Selected record content]       │
│  item 2 ←   │                                  │
│  item 3     │                                  │
└─────────────┴──────────────────────────────────┘
```

### 3. `ws-layout--full-page`
**Used by:** Activity, Learn, Records, Video Live, Notifications  
**Description:** Full content width with optional tab bar (`{% block ws_tabs %}`). Content scrolls naturally. Creation/edit actions open the `ws-panel` slide-in. No permanent split — all available width for the content.

---

## App Map

### Primary Workspace Apps (build `ws_content` for these)

| App | Layout Pattern | Level Gate | Key Steward Actions |
|-----|---------------|------------|-------------------|
| **Dashboard** | `ws-layout--grid` | L3+ | Digest, DAR submit, overdue missions, team stats |
| **Governance** | `ws-layout--master-detail` | L3+ (ref), L4+ (mandates), L5 (handbook) | Browse library, create/lock mandates, version history |
| **Tenants** | `ws-layout--master-detail` | L3+ | Manage agency/node, assign user permissions, shepherd assignments |
| **Community** | `ws-layout--master-detail` | L3+ | Formation pipeline, membership requests, member profiles, shepherd assignment |
| **Activity** | `ws-layout--full-page` | L3+ | Ministry timeline, team activity, campaigns, calendar |
| **Records** | `ws-layout--full-page` | L3+ | Journal, governance, reference records — create via ws-panel |
| **Learn** | `ws-layout--full-page` | L4+ (authorship), L5 (review queues) | Programme authorship, certification review, induction review |
| **Video Live** | `ws-layout--full-page` | L3+ | Schedule events, manage VOD, live stream management |
| **Notifications** | `ws-layout--full-page` | L3+ | Unread list, mark read |

### Secondary Apps (mobile-first, workspace is a wider view only)

| App | Notes |
|-----|-------|
| **Bible** | Immersive reader with its own layout. Workspace = wider text column, same `content` block. |
| **Calendar** | Supportive tool, not primary steward workflow. |
| **Paraclete** | API-only service — surfaces in Dashboard digest, no standalone workspace page. |

---

## Build Sequence

### Phase 1 — Foundation ✅
- [x] Define 3 layout patterns in `workspace.css`
- [x] Add `ws-detail` panel target to `base.html` (for master-detail pattern)
- [ ] Confirm workspace.js wiring is correct end-to-end

### Phase 2 — Dashboard (proof of concept) ✅
- [x] Design `ws_content` grid layout for `dashboard/index.html`
- [x] Clean up duplicate block content left from previous session
- [x] Desktop: stat grid, Divine Intel hero, DAR card, missions list, quick links — two-column grid
- [x] Dashboard components added to `workspace.css` (intel block, DAR card, quick links, streak pills)

### Phase 3 — Governance ✅
- [x] `governance/governance.html` — `ws_content` with master-detail layout
- [x] List panel: branch nav (Reference / Mandate / Keys) + `#ws-list-content` HTMX target
- [x] Detail panel: `#ws-detail` HTMX target, empty state placeholder
- [x] `_shell_or_partial()` injects `active_app`, `ws_page_title`, `detail_target`, `list_target`
- [x] List partials use `{{ detail_target }}` — desktop loads into `#ws-detail`, mobile falls back to `#governance-content`
- [x] Removed stale mobile OOB nav-left swap blocks from all list/detail partials

### Phase 4 — Community ✅

- [x] `base_community.html` — `ws_content` master-detail shell with steward nav tabs
- [x] `ws_community_list` block — per-template list panel content (management, members, pipeline, profile)
- [x] Member directory — workspace search + filter + list loads into `#ws-list-content`, profiles load into `#ws-detail`
- [x] Formation pipeline — compact lane list in panel with member links to `#ws-detail`
- [x] Member profile — back nav in list panel, full profile in detail panel
- [x] `active_app`, `ws_page_title`, `active_community_tab` added to all steward views
- [x] Tenants — API-only (no template views), steward access via Community management nav

### Phase 5 — Full-page apps
- [ ] `activity/` — timeline with filter controls in topbar
- [ ] `records/` — list with ws-panel creation
- [ ] `learn/` — tab bar (catalogue / authorship / review queues)
- [ ] `video_live/` — manage panel + schedule
- [ ] `notifications/` — simple list

---

## Key Files

| File | Role |
|------|------|
| `backend/templates/base.html` | Shell — `ws_content` and `content` blocks, workspace activation script |
| `backend/static/css/workspace.css` | All workspace chrome + layout patterns |
| `backend/static/js/workspace.js` | Active nav, HTMX routing, panel open/close, search shortcut |
| `backend/templates/components/_sidebar.html` | Sidebar nav with `active_app` highlighting |
| `backend/templates/components/_ws_topbar.html` | Topbar — breadcrumb, search, notifications, profile |

---

## Design Principles for Workspace Templates

1. `ws_content` is never a copy of `content` — it is designed for its canvas
2. Sidebar already provides navigation context — no need for page `<h1>` titles inside `ws_content`
3. Use `ws-page-header` + `ws-page-title` for page identity inside the content area
4. Creation and editing happens in the `ws-panel` (right slide-in) via HTMX — not full page loads
5. HTMX targets: `#ws-content` for main navigation, `#ws-detail` for detail panel loads, `#drawerInner` for the mobile drawer (mobile only)
6. Each `ws_content` sets `active_app` in the view context for sidebar highlighting
