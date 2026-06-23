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

## A real bug class found and fixed (2026-06-23): duplicate-partial-id data loss

Chizola reported the Handbook editor's toolbar looking squashed on mobile.
Investigating with the `browse` skill at an actual 375px viewport (not just
reading CSS) found something much worse: `handbook/record.html` includes
the shared `workspace/editorial/partials/editor.html` **twice** — once
inside `{% block ws_content %}` (desktop, `#ics-shell`) and once inside
`{% block content %}` (mobile, `#ws-mobile-shell`). That partial hardcodes
ids (`id="cm-editor-mount"`, `id="record-title"`, `id="editorial-form"`,
etc.). Because `#ics-shell` and `#ws-mobile-shell` are sibling DOM subtrees
— CSS only shows/hides which one is visible, neither is removed from the
DOM — every `getElementById`/`form[id]` lookup in `editorial_v2.js` always
bound to the first (desktop) copy, regardless of which one was actually on
screen.

**Confirmed via live testing, not assumption:** typing into the visible
mobile title field or canvas edited a hidden, stale desktop copy. The
visible "Save to Registry" button submitted that stale copy's form. A
mobile user's edits were silently discarded on save. Real data loss, not
cosmetic.

**Fixed** by giving `editor.html` a `mount_suffix` template parameter so
every id is unique per inclusion (mobile passes `mount_suffix="-mobile"`),
and rewriting `EditorialUI` in `editorial_v2.js` from a singleton object to
one keyed by suffix so each instance's state (CodeMirror view, focus mode,
autosave timer) is independent. The `<script src="editorial_v2.js">` tag
and its boot listeners now load only once per page (guarded by
`{% if not sfx %}`), since they're global, not per-instance.

**The general lesson — check before assuming any "duplicate content for
mobile" pattern is safe:** any shared partial that's included into both
`#ics-shell` and `#ws-mobile-shell` on the same page, and that contains
hardcoded ids referenced by JS or `hx-target`, has this exact bug latent
until proven otherwise. `record.html`'s lifecycle action bar
(`id="hb-lifecycle-status"`, used as an `hx-target`) had the identical
issue — fixed the same way, with a `-mobile` suffixed id on the mobile
copy. Before duplicating any further per-page content into both shells,
grep that partial for hardcoded `id="..."` and trace every JS/`hx-target`
reference to it.

## A Django gotcha hit while writing the fix above

`{# ... #}` Django template comments do **not** support multi-line
content — confirmed by direct reproduction in a Django shell, both via
raw `Template()` construction and the real view-rendering pipeline matters
(a raw multi-line `{# #}` was found to literally render as visible page
text). Multi-line documentation inside a template must use
`{% comment %}...{% endcomment %}` instead. Caught this only because the
fix above was screenshot-verified rather than assumed correct from reading
the diff — the first draft's explanatory comments rendered as a wall of
visible text above the editor on the actual page.

