---
name: web-ui-mobile-strategy
description: Deployment phasing plan and the exact mobile shell approach agreed — what to do and critically what NOT to do
metadata: 
  node_type: memory
  type: project
  originSessionId: 151fcce5-b206-495d-8776-48735f62d886
---

## Deployment phasing (agreed 2026-06-05)

**Phase 1 — Ship now:** `ichebo-platform` (Django backend + web UI) to production.
**Phase 2 — After web is live:** Go sync engine + video engine as services.
**Phase 3 — After backend stable:** Flutter mobile app + Flutter desktop local-first app.

## Web UI mobile situation (superseded — see amendment below)

**Status update (2026-06-18):** The description below described `#ws-mobile-shell` as empty as of 2026-06-05. This is no longer current. As of this date, `#ws-mobile-shell` is wired with navbar (`_navbar.html`), bottom nav (`_bottom_nav.html`), app drawer, FAB, and `<main id="ws-mobile-main">` carrying `{% block content %}`. Mobile drill-down navigation, HTMX targeting conventions (`#ws-mobile-main`), and per-app mobile partials (Activity, Records, etc.) are built and in active iteration. Treat this section as historical record of the starting state, not current state.

The shell architecture uses two zones in `workspace_shell.html`:

- `#ics-shell` — the four-column desktop shell (sidebar, context bar, stage, options bar). Hidden below 1024px via `shell_v2.css`.
- `#ws-mobile-shell` — a div that appears below 1024px. ~~Currently completely empty. Every page on mobile shows a blank screen.~~ **Now built — see status update above.**

The CSS system (`shell_v2.css`, `workspace_v2.css`, `variables.css`) is correct and complete. The breakpoint handling is correct.

Every page uses `{% block ws_content %}` inside the desktop shell. ~~The `{% block content %}` inside `#ws-mobile-shell` is never filled by any template.~~ Mobile content is now filled per-page via `{% block content %}`, with HTMX drill-downs targeting `#ws-mobile-main` specifically (not the whole shell) to preserve chrome.

## What was proposed and has since been implemented

The originally proposed two-part fix was carried out:

1. Mobile nav HTML (navbar + bottom bar) added into `#ws-mobile-shell` in `workspace_shell.html` — done
2. Per-page `{% block content %}` mobile partials built — done, but NOT by defaulting to `{% block ws_content %}` as originally proposed. Instead, each app builds dedicated mobile partials (e.g. `_m_detail.html`, `_m_personal.html`) returned by the view when `HX-Target` matches mobile container IDs. This diverges from the original "default to ws_content" plan — confirm this divergence is intentional before assuming the original plan's exact mechanism when reading older notes.

**Amendment 2026-06-09 (web-ui-mobile-amendment_v1.0.md):** A further refinement was specified on top of the above — a `{% block mobile_fullscreen %}` slot for full-screen mobile experiences (Bible reader) that bypass the standard mobile shell entirely, plus an "Activity Hub" pattern consolidating multi-tab sections into one shell URL with HTMX tab dispatch. **Status as of 2026-06-18 audit: this further amendment is NOT yet built** — no `mobile_fullscreen` block exists in `workspace_shell.html`, no `/bible/m/` route exists. Do not assume this layer exists; it remains open work distinct from the now-completed base mobile shell described above.

## CRITICAL: what not to do in future sessions

**Do NOT:**
- Dismantle `#ws-mobile-shell` or rename it
- Assume the mobile shell is already wired up
- Start pulling `{% block ws_content %}` blocks into separate mobile templates for each page — this creates 30+ diverging templates that are impossible to maintain
- Treat `base.html` and `workspace_shell.html` as competing systems — `base.html` is for auth/public pages only, `workspace_shell.html` is for all authenticated app pages on all devices
- Introduce a third base template for mobile authenticated pages

**The constraint Chizola set:** Don't introduce structural changes without first reading this memory and confirming the current state of the file. The compaction risk is real — future sessions lose context and start dismantling working decisions.

## The one correct approach when this work resumes

1. In `workspace_shell.html`, inside `#ws-mobile-shell`, add the mobile nav (top bar + bottom bar) and `{% block content %}` that defaults to the same content as `{% block ws_content %}`
2. Test on 3-4 key pages (dashboard, community, activity, governance) before touching anything else
3. Do not touch the desktop shell at all

**Why:** Keeps one template hierarchy, no per-page duplication, the CSS is already done.

