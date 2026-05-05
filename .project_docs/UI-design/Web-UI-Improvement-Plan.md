# Web UI Improvement Plan
**Apostolic Command Shell — Audit-Based Refinement Roadmap**
Last updated: 2026-05-05 | Auditor: Claude (Chief Design Engineer)

This document is the single source of truth for Web UI improvement work. It was produced after a live audit of the running shell (architect@ics.test, dark mode, desktop viewport). Each item references the exact screen(s) it affects and the file(s) to change. Work top to bottom — later items depend on earlier ones being stable.

---

## Status Key
- `[ ]` Pending
- `[~]` In progress
- `[x]` Done

---

## Phase 1 — Critical Bugs (Every Screen)

These are broken on every page for every user. Fix before anything else.

### 1.1 Theme init comment rendering at top of page
**Problem:** The synchronous theme script comment `{# Synchronous theme init — runs before paint... #}` is rendering as visible text at the very top of every shell page.
**File:** `backend/templates/workspace_shell.html` — the inline `<script>` block before `</head>`
**Fix:** Wrap the comment in a proper HTML comment `<!-- -->` or remove it. Django template comments `{# #}` do not suppress HTML output inside `<script>` tags.
**Screens affected:** All

### 1.2 Topbar breadcrumb says "Workspace" on every app
**Problem:** Every app shows "Workspace" as the topbar page label. It should reflect the actual app and page context.
**File:** `backend/templates/workspace_shell.html` — `{% block context_header %}` default value
**Fix:** Each app's base template must pass `context_header` (e.g. "Command Center", "The Desk", "Governance Hub"). Audit each app's base template and set the block.
**Screens affected:** All except Dashboard (which already shows "Command Center")

---

## Phase 2 — Primary Sidebar Restructure

Reduces the nav rail from 12 items to 9 (8 top + 1 bottom-pinned). Fixes overflow on smaller screens and makes every item's purpose unambiguous.

### 2.1 Remove Records & Journal from the rail
**Rationale:** Records is the output of The Desk — same workflow, not a separate domain. Move it to The Desk context bar as a first-class link.
**File:** `backend/templates/workspace_shell.html` — remove the Records `<a>` from `.ics-sidebar__nav`
**Also:** Add "View Registry" link to `backend/templates/workspace/governance/desk_sidebar.html` (or equivalent Desk context bar partial)

### 2.2 Remove Apostolic Web (Graph) from the rail
**Rationale:** The graph is a lens on governance/records data, not a standalone domain.
**File:** `backend/templates/workspace_shell.html` — remove the Graph `<a>` from `.ics-sidebar__nav`
**Also:** Add "Apostolic Web" link to Governance context bar (`backend/templates/workspace/governance/base.html`)

### 2.3 Remove Institutional Calendar from the rail
**Rationale:** Calendar is the time-grid view of Activity items — same data, different rendering.
**File:** `backend/templates/workspace_shell.html` — remove the Calendar `<a>` from `.ics-sidebar__nav`
**Also:** Already present in Activity context bar (`backend/templates/activity/partials/activity_sidebar.html`) — confirm it links correctly

### 2.4 Pin Tenancy Hub to bottom of rail
**Rationale:** Tenancy is administrative/elevated-access, not a daily-use domain. It should be visually separated from the core nav — same pattern as VS Code's Settings icon.
**File:** `backend/templates/workspace_shell.html` — move Tenancy `<a>` outside `.ics-sidebar__nav`, into a new `.ics-sidebar__bottom` group
**File:** `backend/static/css/shell_v2.css` — add `.ics-sidebar__bottom { margin-top: auto; padding-bottom: var(--space-s); display: flex; flex-direction: column; align-items: center; gap: var(--space-m); }`

### 2.5 Replace native title tooltips with CSS instant tooltips
**Rationale:** Native `title` attribute tooltips are slow (~1s delay) and unstyled. CSS tooltips appear immediately and match the shell aesthetic.
**File:** `backend/static/css/shell_v2.css` — add tooltip via `.ics-sidebar__item::after` using `data-tooltip` attribute
**File:** `backend/templates/workspace_shell.html` — replace `title="..."` with `data-tooltip="..."`

**Final rail order (top to bottom):**
1. Dashboard
2. The Desk
3. Governance
4. Community
5. Formation
6. Activity
7. Bible Reader
8. Video & Broadcast
— (separator) —
9. Tenancy Hub (bottom-pinned)

---

## Phase 3 — Shell-Wide Polish

Fixes that apply across multiple apps but don't require per-app logic.

### 3.1 Stage topbar — "Workspace" label in topbar title area
**Problem:** The topbar title area between the sidebar toggle and search shows a generic label.
**Fix:** Each app base template sets `{% block hub_context_title %}` — audit and set correct values for any that still say "Workspace".

### 3.2 Context bar header titles
**Problem:** Some apps show generic context bar headers.
**Fix:** Verify each app's context bar header block shows the correct app name. Reference list:
- Dashboard → "Strategic Actions" ✓
- Desk → "Editorial Control" ✓
- Records → "Registry Browser" ✓
- Governance → "Governance Hub" ✓
- Community → "Community Ops" ✓
- Formation → "Formation Ops" ✓
- Activity → "Tactical Intel" ✓
- Bible → "Bible" (needs book/chapter nav — see Phase 4)

### 3.3 Grouped section labels — dash style consistency
**Problem:** Some context bars use `——` red dash prefix on section labels (`.ws-label-tag` with red line), others don't. The red dash prefix on labels is distinctive and should be uniform.
**Fix:** Audit all context bar partials and confirm the `ws-label-tag` component renders consistently. No raw uppercase text without the component.

---

## Phase 4 — Bible App Context Bar

The most finished stage in the app has the emptiest context bar. High-value fix.

### 4.1 Book/chapter navigation in context bar
**Problem:** Bible context bar is completely empty — blank dark panel. The reader is showing John 20 AMP with no way to navigate from the sidebar.
**Fix:** Add book list and chapter selector to `backend/templates/bible/` context bar partial. At minimum: current book name, chapter selector (scrollable list or number input), and version selector.
**Reference:** `backend/templates/bible/base_sidecar.html` and bible URL patterns

### 4.2 Version selector
**Fix:** Add a version selector (AMP, KJV, NIV etc.) as a `.ctx-btn` style dropdown or toggle in the Bible context bar.

---

## Phase 5 — Dashboard Stage

The hero is strong. The cards and lower sections need work.

### 5.1 Stat cards — light mode contrast
**Problem:** Daily Briefing, Active Mandates, Formation Progress cards blend into the background in light mode (similar surface colours).
**Fix:** In `backend/static/css/` — add a light-mode override that gives stat cards a visible border or slightly darker background. Do NOT add coloured left borders (AI slop pattern).

### 5.2 "The Handbook" heading in Community stage
**Problem:** Community stage home page shows "The Handbook" as its heading. This doesn't match the app name "Community Ops" and reads like a placeholder.
**Fix:** `backend/templates/community/` home template — update heading to match the app's purpose (e.g. "Community Hub" or "Kingdom Node").

### 5.3 Divine Intel gradient
**Problem:** The refinements doc requests the same gradient treatment the mobile app uses on the Divine Intel card.
**Fix:** Inspect the mobile design reference and apply a matching gradient background to the Divine Intel section in `backend/templates/dashboard/`.

### 5.4 Registry Activity section length
**Problem:** The registry activity list is too long — runs off screen without natural break.
**Fix:** Cap the list at 5 items with a "View all" link. Update the dashboard view or template to apply `[:5]` limit.

---

## Phase 6 — Activity Stage

The most visually raw screen. The timeline chart is unreadable without context.

### 6.1 Timeline chart — data labels and legend
**Problem:** The scatter/timeline chart shows floating dots and icons with no labels, no legend, and no axis context. Looks like a skeleton.
**Fix:** Add dot labels (task title or truncated), a legend (Tasks / Goals / Events / Habits by icon/colour), and axis labels (dates or week markers).

### 6.2 Activity stage — real data
**Problem:** Cards and sections show empty states or minimal data.
**Fix:** Wire the stage to real queryset data. Confirm the activity view is passing the correct context variables.

---

## Phase 7 — Records Stage

Records has data but the interaction flow is incomplete.

### 7.1 Record opens in stage on click
**Problem:** Clicking a record in the list doesn't open it in the stage (unknown behaviour — needs verification). The refinements doc specifies records should open inline.
**Fix:** Add an HTMX `hx-get` on each record row that loads the record detail into the stage content area. Add a back button in the detail view.

### 7.2 Record edit → Desk flow
**Approach confirmed in refinements doc:** Clicking edit on a record opens it in The Desk canvas. After saving, return to Records.
**Fix:** Wire the edit pencil icon to `{% url 'governance:desk-edit' record.id %}`.

### 7.3 "New Entry" button styling
**Problem:** The "New Entry" button in Records stage is a red pill that clashes with the design system (should be `.btn-touch` or `.btn-touch--primary`).
**Fix:** Replace inline style with `.btn-touch--primary` from `workspace_v2.css`.

---

## Phase 8 — Governance Stage

Context bar is the best in the app. Stage content needs wiring.

### 8.1 Governance record renders in stage
**Problem:** Clicking a governance record (Classes, Principles, Concepts, Divine Patterns etc.) doesn't render content in the stage — shows the empty "Select a registry" state or navigates away.
**Fix:** Wire list item clicks to load record detail in the stage via HTMX or standard Django view returning stage-scoped content.

---

## Phase 9 — The Desk Stage

Functional but raw. Focus on the writing canvas.

### 9.1 Writing canvas max-width
**Problem:** The writing canvas spans the full stage width. Body text should have a max-width of ~680px centred in the stage for comfortable reading/writing measure.
**Fix:** `backend/static/css/editorial_v2.css` — set `.ics-canvas { max-width: 680px; margin: 0 auto; padding: var(--space-l) var(--space-m); }`

### 9.2 Toolbar weight
**Problem:** The B / I / H1 / H2 / Saved toolbar at top of stage is very thin and easy to miss.
**Fix:** Give the toolbar a proper surface — border-bottom, background distinct from stage, consistent height (44px), and proper button styles using `.ws-icon-btn`.

### 9.3 Rename "Registry Origin" → "Record Family"
**As noted in refinements doc.**
**File:** `backend/templates/workspace/governance/` Desk context bar partial — update label text.

---

## Phase 10 — Community & Formation Stages

Both are structurally sound but empty. Lowest priority until data exists.

### 10.1 Community — wire Announcements and Gatherings to real data
**Problem:** Both columns show empty states.
**Fix:** Confirm the community home view passes `announcements` and `gatherings` querysets; template renders them.

### 10.2 Formation — active programmes list
**Problem:** "No active enrolments. Your formation awaits." is the only content.
**Fix:** Wire to real enrolment data; add empty state CTA that links to Programme Catalogue.

---

## Appendix: Deferred / Future

These are noted but not scheduled in this plan. Raise when the above is stable.

- **Options Bar (Column 4)** — Currently unused across all apps. Each app needs a properties pane: record metadata, links/relationships, versioning. Design per-app.
- **Command palette exit from Focus Mode** — Focus Mode has no reverse command.
- **Draggable panel widths** — Context bar and Options bar width adjustable by drag, saved to localStorage.
- **PWA manifest** — Shell is close to PWA-ready. Add `manifest.json` and service worker.
- **Fira Code** — Load for governance record IDs and technical fields (per DESIGN.md).
- **Live / Video & Broadcast stage** — No context bar actions defined yet. Needs product decision.
- **Tenancy stage** — Needs product decision on content structure.

---

## Execution Notes

- One commit per fix. Format: `style(ui): Phase X.Y — short description`
- Do not bundle multiple fixes. Each fix should be independently revertable.
- Test both dark and light mode after every CSS change.
- After Phase 2 (sidebar restructure) verify all `active_app` conditionals still highlight correctly.
