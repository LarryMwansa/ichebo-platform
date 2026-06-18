# Master Roadmap & ADR Set — Doc-Staleness Closure — Roadmap Amendment

**Version:** 1.0 — 2026-06-18
**Status:** Approved — pending implementation
**Reference documents:** `master-roadmap-canonical-2026-05-13.md`, `2026-06-09-adr-022-handbook-governance-separation.md`, `2026-06-09-web-ui-mobile-amendment_v1.0.md`, `2026-05-13-ichebo-adrs-012-021.md`, `2026-05-13-ichebo-technical-architecture_doc-d_v1.0.md`
**Author:** Claude (technical) — reviewed by Chizola

---

## What This Document Is

A full mono-repo production-readiness audit (2026-06-18) found that two approved, dated amendments — ADR-022 (2026-06-09) and the Web UI Mobile Rendering Amendment (2026-06-09) — exist only as standalone documents in `.docs/`. Neither has been merged into the canonical text of `master-roadmap-canonical-2026-05-13.md`, `2026-05-13-ichebo-adrs-012-021.md`, or `2026-05-13-ichebo-technical-architecture_doc-d_v1.0.md`, which they explicitly amend.

This is not a logical contradiction between documents — both amendment docs are unambiguous about what they change and explicitly state what they don't (ADR-022 §"Amendments to Prior ADRs" is explicit that ADR-020 is untouched). It is a **merge gap**: the amendment was written, approved, and (in one case) already built in code, but the source-of-truth documents were never edited to reflect it. Anyone reading only the canonical docs going forward — including a future session of this assistant — would describe Handbook architecture and mobile rendering incorrectly.

This plan closes that gap before any further roadmap work begins, per Chizola's instruction (2026-06-18) to fix this first, then proceed to the two Django production blockers (STORAGES conflict, pending migrations).

---

## Audit Findings — What's Approved vs What's Actually Built

A critical distinction the merge must preserve: **one amendment is fully implemented in code; the other is not.**

| Amendment | Doc status | Code status |
|---|---|---|
| ADR-022 (Handbook/Governance separation) | Approved, unmerged into roadmap | **Implemented.** `handbook/models.py` contains only `HandbookAccess`; `HandbookRecord`/`HandbookRelationship` are gone. Confirmed by `handbook/migrations/0002_retire_content_models.py` — a migration literally named for this retirement. |
| Web UI Mobile Amendment (Activity Hub + Bible `/m/` route) | Approved, unmerged into roadmap | **Partially implemented.** Decision 1 (Activity Hub HTMX tab dispatch) and Decision 3 (`{% block mobile_fullscreen %}` slot) — confirmed NOT present in current `templates/workspace_shell.html` or `bible/urls.py` at time of this audit (2026-06-18). Decision 2 (`/bible/m/<book>/<chapter>/` dedicated route) — confirmed absent from `bible/urls.py`. |

This means the roadmap edits for ADR-022 should mark the architecture as current/complete. The roadmap edits for the mobile amendment should mark it as an **approved direction not yet built** — distinct from "complete and undocumented." Conflating the two would misstate actual platform state to anyone reading the roadmap next.

---

## Edits to `master-roadmap-canonical-2026-05-13.md`

### Edit 1 — Layer 9 (Ichebo Handbook), Phase K.1 description

**Current text (line 670):**

> **What was built:** Standalone `handbook` Django app. `HandbookRecord` (UUID PK, three branches, four status lifecycle, version chain), `HandbookRelationship` (HRS + scripture links in one model), `HandbookAccess` (reader/author/editor roles, global scope). Full DRF API: list/create, detail/patch, publish, lock, new-version, history. Migration `0001_initial` applied.

**Problem:** describes the pre-ADR-022 architecture as current. `HandbookRecord` and `HandbookRelationship` no longer exist.

**Replacement text:**

> **What was built:** Standalone `handbook` Django app. `HandbookRecord` (UUID PK, three branches, four status lifecycle, version chain), `HandbookRelationship` (HRS + scripture links in one model), `HandbookAccess` (reader/author/editor roles, global scope). Full DRF API: list/create, detail/patch, publish, lock, new-version, history. Migration `0001_initial` applied.
>
> **Superseded by ADR-022 (2026-06-09):** `HandbookRecord` and `HandbookRelationship` are retired. Handbook is now a UI-only app over `records.Record` (`record_family='governance'`) — no owned content models, same pattern as Governance and Community. `HandbookAccess` is retained as the permission-gate model for the authorship workspace. The Desk editor (formerly its own sidebar icon) is relocated into Handbook. Migration `0002_retire_content_models.py` applied. See ADR-022 for full rationale and the Governance/Handbook/Records separation of concerns it establishes.

### Edit 2 — Phase K.2 description (Workspace UI + The Desk)

**Current text (line 676):**

> **What was built:** Four-column Apostolic Command Shell for the Handbook — `home.html` (branch navigator, record list grouped by type), `record.html` (four-tab Properties Sidecar: Props/HRS/Scripture/History, `HBDesk` JS object, auto-save on keystroke), `access.html` (editor-only access management). Sidebar nav entry added to `workspace_shell.html`. Template URLs registered at `/handbook/`.

**Append:**

> **Superseded by ADR-022 (2026-06-09):** The Desk (`governance/desk_views.py`) is relocated from its own sidebar icon into the Handbook surface. Handbook views now query `records.Record` directly rather than `HandbookRecord`. The `edit_note` Desk sidebar icon is removed; Handbook (`auto_stories`) becomes the single entry point for governance authorship, moving to sidebar position 2.

### Edit 3 — ADR table, ADR-014 row (line 63)

**Current text:**

> | ADR-014 | The Desk as governance authorship surface | Canonical authorship environment within the Apostolic Command Shell. All governance record creation routes through The Desk. |

**Replacement:**

> | ADR-014 (amended by ADR-022) | The Desk as governance authorship surface | Canonical authorship environment. **Amended 2026-06-09 (ADR-022):** The Desk is relocated into the Handbook surface. Canonical statement is now "The Handbook is the canonical governance authorship surface; The Desk editor is embedded within it." All governance record creation still routes through this editor — only its navigational home changed. |

### Edit 4 — Add ADR-022 to the ADR table

**Insert new row after ADR-021 (line 70):**

> | ADR-022 | Handbook and Governance separation of concerns | Governance App becomes read-only public library (no write UI). Handbook becomes the invited Level 4-5 authorship workspace; The Desk relocates here. `HandbookRecord`/`HandbookRelationship` retired — Handbook is now a UI layer over `records.Record`, same as Governance. Records App gets a dedicated full-width desktop layout. Amends ADR-012 (sidebar order) and ADR-014 (Desk's canonical location). Does not amend ADR-020. |

### Edit 5 — Phase 5.1 (Bible App), append amendment note

**Current text (line 341, full entry ends at "translation switcher.")**

**Append:**

> **Amendment 2026-06-09 (mobile reader) — approved, not yet built:** A dedicated mobile Bible reader was specified for `/bible/m/<book_code>/<chapter>/` — a standalone full-screen page (no workspace shell) with sticky topbar, chapter content, bottom nav strip, navigator/annotation/display-settings sheets, verse toolbar, and localStorage highlight persistence. **Status as of 2026-06-18 audit: not present in code** — `bible/urls.py` has no `/m/` route, and no `reader_mobile.html` template exists. Desktop reader at `/bible/<book_code>/<chapter>/` is unaffected either way. This is open implementation work, not yet a completed phase.

### Edit 6 — Mobile Mode characterisation (wherever ADR-015 / dual-shell architecture is described in the roadmap's prose, if present, or as a new note under Layer 3 / Apostolic Command Shell section)

**Insert as a new note under "The Apostolic Command Shell ✅ COMPLETE (ADR-012)" section (after line 419):**

> **Amendment 2026-06-09 (ADR-015) — approved, partially built:** Two Mobile Mode rendering patterns are now recognised: Standard Mobile Mode (`{% block content %}`, unchanged) and Standalone Mobile Mode (dedicated `/m/` URL with a minimal base template, for full-screen experiences like the Bible reader). A `{% block mobile_fullscreen %}` slot was specified for `workspace_shell.html` to support this. **Status as of 2026-06-18 audit: the `mobile_fullscreen` block is not present in the current `workspace_shell.html`.** The Activity Hub HTMX tab-dispatch pattern (Decision 1 of the same amendment, consolidating Personal/Ministry/Calendar into one mobile shell URL) is similarly specified but not confirmed built as of this audit. See the web-ui-mobile-amendment doc for full pattern reference.

---

## Edits to `2026-05-13-ichebo-adrs-012-021.md`

### Edit 7 — Append to ADR-015 verbatim, exactly as specified in the amendment doc itself

The amendment doc (`2026-06-09-web-ui-mobile-amendment_v1.0.md` §4, "ADR-015") already contains the exact text to append — this is a direct copy, not a new composition:

> **Amendment 2026-06-09:** Two rendering patterns are now recognised for Mobile Mode:
>
> 1. **Standard Mobile Mode** — `{% block content %}` inside `workspace_shell.html`. Used by all pages where the platform shell (topbar, bottom nav) is appropriate on mobile.
>
> 2. **Standalone Mobile Mode** — dedicated `/m/` URL with a minimal base template (no workspace shell). Used when the mobile experience requires full-screen control (e.g. Bible reader, future: media player, full-screen map). These pages link back to the workspace shell via a back button.
>
> Both patterns are first-class. Standalone Mobile Mode is not a fallback — it is the correct pattern for full-screen experiences.
>
> **Implementation status (2026-06-18 audit):** This pattern is approved but not yet built — `workspace_shell.html` does not currently contain a `mobile_fullscreen` block, and no `/m/` route exists. Tracked as open work, not a completed amendment.

### Edit 8 — Append amendment marker to ADR-014

> **Amended by ADR-022 (2026-06-09):** "The Desk as canonical governance authorship surface" is superseded by "The Handbook is the canonical governance authorship surface; The Desk editor is embedded within it." See ADR-022 for full context. This amendment is implemented in code as of the 2026-06-18 audit.

---

## Edits to `2026-05-13-ichebo-technical-architecture_doc-d_v1.0.md`

### Edit 9 — Section 2.1, Dual-Shell Architecture — exact replacement specified by the amendment doc

**Replace:**

> Mobile Mode (`{% block content %}`): All users on mobile viewport.

**With (verbatim from the amendment doc):**

> Mobile Mode: All users on mobile viewport. Standard pages use `{% block content %}`. Pages with full-screen mobile experiences (e.g. Bible reader) use the dedicated `/m/` URL pattern with a standalone minimal template. Both are Mobile Mode — the latter is purpose-built, not a workaround.
>
> **Implementation status (2026-06-18 audit):** approved, not yet built. See roadmap Phase 5.1 amendment note.

**Add to Section 2.1 (verbatim from the amendment doc):**

> **Activity Hub pattern:** On mobile, multi-tab app sections (Activity, Calendar) consolidate into a single shell URL with HTMX tab dispatch. Separate desktop URLs for sub-sections remain unchanged. This avoids re-rendering the hero and navigation on each tab.
>
> **Implementation status (2026-06-18 audit):** approved, not yet confirmed built in current code.

---

## What This Plan Does NOT Do

- Does not re-decide anything — both amendments are already approved; this only merges their already-settled text into the canonical documents
- Does not build the unimplemented mobile amendment work (Activity Hub tab dispatch, `/bible/m/` route, `mobile_fullscreen` block) — that remains separate, open implementation work, now correctly flagged as open rather than silently missing
- Does not touch ADR-020 (Handbook as standalone product) — confirmed by ADR-022 itself to be unaffected
- Does not change any code — this is a documentation-only merge

---

## Scope of Implementation

| Step | Document | Edits |
|---|---|---|
| 1 | `master-roadmap-canonical-2026-05-13.md` | Edits 1–6 above |
| 2 | `2026-05-13-ichebo-adrs-012-021.md` | Edits 7–8 above |
| 3 | `2026-05-13-ichebo-technical-architecture_doc-d_v1.0.md` | Edit 9 above |
| 4 | `web-ui-mobile-strategy.md` | Apply the addition specified in the amendment doc's §4 ("Do NOT put full-screen readers... into `{% block content %}`") — not yet checked against current file content, verify before editing |

No code changes. No new ADR. This plan itself becomes the audit trail for why the canonical docs changed on this date without a corresponding commit to `ichebo-platform/`.

---

## Exit Criteria

- [ ] `master-roadmap-canonical-2026-05-13.md` Layer 9 / Phase K.1, K.2 describe the post-ADR-022 architecture, with the pre-ADR-022 text retained but marked superseded (not deleted — preserves build history)
- [ ] ADR table in the master roadmap includes ADR-022
- [ ] ADR-014 row in the master roadmap reflects the ADR-022 amendment
- [ ] Phase 5.1 (Bible App) and the Apostolic Command Shell section both carry the mobile amendment notes, correctly marked "approved, not yet built" rather than implying completion
- [ ] `2026-05-13-ichebo-adrs-012-021.md` ADR-015 and ADR-014 carry their respective amendment text
- [ ] `2026-05-13-ichebo-technical-architecture_doc-d_v1.0.md` §2.1 carries the corrected Mobile Mode description and Activity Hub pattern note
- [ ] No amendment is described as complete unless independently confirmed present in code (per the 2026-06-18 audit findings table above)

## Commit

Documentation-only change — no code commit required. If tracked in the same git repo as `.docs/`, suggested message:

```
docs: merge ADR-022 and web-ui-mobile-amendment into canonical roadmap and ADR set
```
