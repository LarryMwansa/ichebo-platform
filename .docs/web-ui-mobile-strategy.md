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

## Web UI mobile situation (current state, verified 2026-06-05)

The shell architecture uses two zones in `workspace_shell.html`:

- `#ics-shell` — the four-column desktop shell (sidebar, context bar, stage, options bar). Hidden below 1024px via `shell_v2.css`.
- `#ws-mobile-shell` — a div that appears below 1024px. Currently **completely empty**. Every page on mobile shows a blank screen.

The CSS system (`shell_v2.css`, `workspace_v2.css`, `variables.css`) is correct and complete. The breakpoint handling is correct. The problem is purely that `#ws-mobile-shell` has no content.

Every page uses `{% block ws_content %}` inside the desktop shell. The `{% block content %}` inside `#ws-mobile-shell` is never filled by any template.

## What was proposed but NOT yet implemented

A two-part fix was proposed:
1. Add mobile nav HTML (navbar + bottom bar — CSS already exists in `navbar.css`, `bottom_bar.css`, `app-drawer.css`) into `#ws-mobile-shell` in `workspace_shell.html`
2. Make `{% block content %}` default to `{% block ws_content %}` so pages work on mobile without per-page changes

**This has NOT been built yet. Do not assume it exists.**

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

