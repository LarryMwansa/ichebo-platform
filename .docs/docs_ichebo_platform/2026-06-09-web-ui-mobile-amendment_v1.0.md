# Ichebo Web UI — Mobile Rendering Amendment
**Document:** Amendment to DOC-D (Technical Architecture), DOC-B (Desktop Spec), ADR-015, and the Master Roadmap
**Date:** 2026-06-09
**Status:** Accepted — in implementation

---

## 1. What This Document Covers

During the Version 2 → Version 3 transition, the mobile rendering strategy for the Django web platform was revised. This document records the decisions made, the pattern established, and the amendments required to existing project documents.

---

## 2. Background

The Master Roadmap and ADR-015 described a dual-shell rendering architecture:

- **Stage Mode** (`{% block ws_content %}`) — four-column workspace, desktop only (≥1024px, Level 3+)
- **Mobile Mode** (`{% block content %}`) — mobile shell, all users below 1024px

The original intent was that every template implements both blocks from a single inheritance tree rooted at `workspace_shell.html`. In practice, two problems emerged:

1. Some pages (Ministry, Calendar) were filling the wrong block, causing double-renders on mobile.
2. The Bible reader has fundamentally different interaction patterns on mobile (full-screen reader, sheet-based navigation, no platform topbar) that cannot be cleanly expressed as a `{% block content %}` override inside the workspace shell.

---

## 3. Decisions Made

### Decision 1 — Activity Hub: Single Mobile Entry Point

**Previous state:** Three separate URLs rendered their own mobile page — `/activity/` (Personal), `/activity/ministry/` (Ministry), `/calendar/` (Calendar). Each re-rendered the platform hero and tab nav.

**Amended approach:** `/activity/` is the single mobile Activity Hub shell. Ministry and Calendar pages redirect to it on mobile via JS:

```javascript
if (window.innerWidth < 1024) {
    window.location.replace('{% url "activity:activity-home" %}?tab=ministry');
}
```

Tab content is loaded via HTMX (`?tab=personal|ministry|calendar`). Desktop routes are unchanged.

**Templates affected:**
- `activity/my_activities.html` — becomes the mobile shell with HTMX tab dispatch
- `activity/ministry.html` — JS redirect on mobile; desktop `{% block ws_content %}` unchanged
- `calendar/base_calendar.html` — JS redirect on mobile; desktop unchanged
- `activity/partials/_m_personal.html` — new
- `activity/partials/_m_ministry.html` — new
- `activity/partials/_m_calendar.html` — new

---

### Decision 2 — Bible Reader: Dedicated Mobile URL

**Previous state:** The Bible reader at `/bible/<book>/<chapter>/` extended `workspace_shell.html`. Attempting to render a full-screen mobile reader inside the workspace shell caused structural conflicts (platform topbar, FAB, and bottom nav competing with the reader's own chrome).

**Amended approach:** The Bible reader uses two separate rendering paths:

| Surface | URL pattern | Template | Extends |
|---|---|---|---|
| Desktop (≥1024px) | `/bible/<book_code>/<chapter>/` | `bible/reader.html` | `bible/base_v2.html` → `workspace_shell.html` |
| Mobile (<1024px) | `/bible/m/<book_code>/<chapter>/` | `bible/reader_mobile.html` | Minimal base (no workspace shell) |

On mobile, `/bible/<book_code>/<chapter>/` redirects to `/bible/m/<book_code>/<chapter>/` via JS.

The mobile reader is a **standalone full-screen page** with its own:
- Sticky topbar (back, book/chapter title button, version badge, search, display settings)
- Chapter content area
- Fixed bottom nav strip (prev · Genesis 1 · next) above the platform bottom nav
- Bottom sheets: Navigator (book + chapter), Annotation (verse tap), Display settings
- Verse toolbar (copy, highlight × 4, note)
- localStorage-backed highlight persistence

**This is not a violation of ADR-015.** ADR-015 mandates that templates implement both Stage Mode and Mobile Mode. The Bible reader still has a Stage Mode path (`reader.html`). The mobile path is a purpose-built full-screen reader — the same principle as a native app's reader view — not a degradation.

---

### Decision 3 — `{% block mobile_fullscreen %}` Block

A new block `{% block mobile_fullscreen %}` was added to `workspace_shell.html` inside `#ws-mobile-shell`, alongside `{% block content %}`. This block is reserved for full-screen mobile views that need to completely replace the standard mobile content area without affecting the desktop stage.

```html
<!-- workspace_shell.html -->
<main class="ics-main" role="main">
    <div id="toast-container-mobile"></div>
    {% block content %}{% endblock %}
    {% block mobile_fullscreen %}{% endblock %}
</main>
```

**Usage rule:** Only use `{% block mobile_fullscreen %}` when the mobile view requires a genuinely different DOM structure (e.g. the Bible reader). For standard pages, use `{% block content %}` as before.

---

## 4. Amendments Required to Project Documents

### DOC-D — Technical Architecture (`2026-05-13-ichebo-technical-architecture_doc-d_v1.0.md`)

**Section 2.1 — Dual-Shell Architecture**, replace:

> Mobile Mode (`{% block content %}`): All users on mobile viewport.

With:

> Mobile Mode: All users on mobile viewport. Standard pages use `{% block content %}`. Pages with full-screen mobile experiences (e.g. Bible reader) use the dedicated `/m/` URL pattern with a standalone minimal template. Both are Mobile Mode — the latter is purpose-built, not a workaround.

**Add to Section 2.1:**

> **Activity Hub pattern:** On mobile, multi-tab app sections (Activity, Calendar) consolidate into a single shell URL with HTMX tab dispatch. Separate desktop URLs for sub-sections remain unchanged. This avoids re-rendering the hero and navigation on each tab.

---

### ADR-015 — Dual-Shell Rendering (`2026-05-13-ichebo-adrs-012-021.md`)

**Append to ADR-015:**

> **Amendment 2026-06-09:** Two rendering patterns are now recognised for Mobile Mode:
>
> 1. **Standard Mobile Mode** — `{% block content %}` inside `workspace_shell.html`. Used by all pages where the platform shell (topbar, bottom nav) is appropriate on mobile.
>
> 2. **Standalone Mobile Mode** — dedicated `/m/` URL with a minimal base template (no workspace shell). Used when the mobile experience requires full-screen control (e.g. Bible reader, future: media player, full-screen map). These pages link back to the workspace shell via a back button.
>
> Both patterns are first-class. Standalone Mobile Mode is not a fallback — it is the correct pattern for full-screen experiences.

---

### Master Roadmap (`master-roadmap-canonical-2026-05-13.md`)

**Section: Phase 5.1 — Bible App**, append:

> **Amendment 2026-06-09 (mobile reader):** A dedicated mobile Bible reader was implemented at `/bible/m/<book_code>/<chapter>/`. The reader is a standalone full-screen page (no workspace shell) with sticky topbar, chapter content, bottom nav strip (prev/next), navigator sheet (book + chapter), annotation sheet, display settings sheet, verse toolbar, and localStorage highlight persistence. Desktop reader at `/bible/<book_code>/<chapter>/` is unchanged.

**Section: Mobile Mode — Characterisation**, append:

> **Amendment 2026-06-09:** The Activity Hub consolidation pattern was established: on mobile, related sub-sections (Personal Activity, Ministry Activity, Calendar) are served from a single shell URL with HTMX tab dispatch. Desktop sub-section URLs redirect to the hub on mobile.

---

### `web-ui-mobile-strategy.md` (memory / `.docs/`)

This document should be updated to reflect current state. The `#ws-mobile-shell` is no longer empty — it is wired with navbar, bottom nav, and `{% block content %}` / `{% block mobile_fullscreen %}`. The "what NOT to do" list remains valid with one addition:

> **Do NOT** put full-screen readers (Bible, future media player) into `{% block content %}`. Use the `/m/` URL pattern with a standalone template instead.

---

## 5. Pattern Reference for Future Pages

| Mobile experience type | Pattern to use |
|---|---|
| Standard page (list, detail, form) | `{% block content %}` in the page template extending `workspace_shell.html` |
| Multi-tab section (Activity, Calendar) | HTMX tab dispatch from a single shell URL; sub-pages redirect on mobile |
| Full-screen immersive (Bible reader, media player) | Dedicated `/m/` URL + standalone template + back link to workspace |
| Desktop-only feature | JS redirect on mobile: `if (window.innerWidth < 1024) { window.location.replace(...) }` |

---

## 6. Files Changed (Session 2026-06-09)

| File | Change |
|---|---|
| `templates/workspace_shell.html` | Added `{% block mobile_fullscreen %}` slot in `#ws-mobile-shell` |
| `templates/bible/reader.html` | Added `{% block mobile_fullscreen %}` block (superseded by Decision 2 — will be removed once `/m/` route is live) |
| `static/css/bible.css` | Added mobile reader styles (`@media max-width: 1023px`); added desktop/mobile mutual exclusion rules |
| `templates/activity/my_activities.html` | Rewritten as HTMX Activity Hub shell |
| `templates/activity/ministry.html` | Mobile JS redirect added |
| `templates/calendar/base_calendar.html` | Mobile JS redirect added |
| `templates/activity/partials/_m_personal.html` | New |
| `templates/activity/partials/_m_ministry.html` | New |
| `templates/activity/partials/_m_calendar.html` | New |
| `bible/views.py` | `all_chapters` dict added to `BibleReaderView` context |
| `activity/views.py` | Tab dispatch logic + `_ministry_partial` + `_calendar_partial` helpers |

**Next:** Add `/bible/m/<book_code>/<chapter>/` URL, view, and `reader_mobile.html` template.
