# Ichebo UI Rework — Staged Plan

2026-09-30 · Larry Mwansa

## Overview

The Ichebo UI feels too heavy to work in, and that's now holding day-to-day work back rather than just looking imperfect. The rework's goal is a simpler, faster, more enjoyable working model — not a cosmetic reskin.

**Operating principle:** make it work first, then make it sophisticated. Ship incrementally; the app stays functional after every stage. No new framework, state layer, or design system — same Django templates + HTMX, restructured.

**Navigation model, four levels:**
- Ecosystem (moving between Ichebo applications)
- Application (primary features of the app you're in)
- Feature (context/navigation within that feature)
- Context (actions/options at that point)

**Staging order (as agreed):**
1. Clone & rename the shell
2. Ecosystem launcher
3. Handbook gets its own chrome
4. Simplify Library/Journal/Bible forms together
5. Desk stays its own app, unmerged
6. `app.ichebo.org` migrates toward the lighter sceptre pattern — last

## Stage 0 — Clone & rename the shell

**Done, 2026-09-30.** Cloned `templates/workspace_shell.html` (the "Apostolic Chrome") to `templates/apostolic_chrome.html`. The original is untouched and stays live in production; nothing extended the clone until Stage 2 started building on it. Zero production risk at the point of cloning.

Renamed to match the brief's own term for the shell, since its long-term home is Handbook-exclusive (Stage 5).

## Stage 1 — Ecosystem launcher

**Done, 2026-09-30.** Replaced the always-on 9-icon sidebar with a slim rail (logo + one "apps" trigger + account icon) and a floating **Ichebo Apps** launcher popover.

Built entirely from `components/_app_launcher.html` — a fully-styled, level-gated app grid that already existed in the codebase from an earlier attempt at this exact idea, but was never wired to anything until now.

Verified live in a real browser session: Handbook correctly shows locked for a Level 3 user, Governance unlocked; popover opens/closes via trigger, outside-click, and Escape.

## Stage 2 — Handbook gets its own chrome

**In progress.** First slice shipped 2026-09-30.

Introduced `workspace/handbook/base.html`, extending `apostolic_chrome.html`, as the one place the Library/Mandate/Keys context nav and the shared `hb-*` styling live. `home.html`, `record.html`, `access.html`, and `graph.html` now extend it instead of each independently duplicating the same nav markup and CSS (~150 duplicated lines removed), overriding only page-specific blocks where they genuinely differ.

**Still open:** `record.html`'s Context Bar currently does double duty — it's both "where am I" navigation and a type-picker that sets hidden form fields (an editing action, not navigation). That's the concrete instance of the brief's complaint that too much gets forced into the Context Bar. Splitting the type-picker out into the Options bar, where it belongs as part of editing the record, is the next piece of Stage 2.

## Stage 3 — Simplify Library, Journal & Bible forms together

**Not started.**

Forms for Libraries and Journals need real simplification — they're one of the things currently making the system slow to work in. The Bible reader gets the same Context/Options treatment in this stage rather than as a separate afterthought, per explicit direction: fold it into the same pass, not a bolt-on later.

Principle carried over from the brief: a simpler form that works beats an elaborate one that's technically impressive but slows the actual work down.

## Stage 4 — The Desk stays its own app

**Decision made, no work started.**

Earlier proposal was to eventually fold the Desk's "draft with related context visible" job into the Library/Journal editors once they were simplified. That's now explicitly rejected: **the Desk is preserved as a separate app**, so its development track stays independent. The simplification work goes into the Library and Journal forms directly (Stage 3) instead of being routed through a Desk merge.

No changes needed here — this stage is a scope boundary, not a build.

## Stage 5 — app.ichebo.org migrates toward the lighter pattern

**Not started — last in the sequence, by design.**

Moved to last so it lands only after Handbook, and the Library/Journal/Bible forms, have proven the lighter approach out. For the general apps (Dashboard, Community, Activity, Journal), the plan is to drop the persistent Options bar and heavy chrome in favor of something closer to `sceptre_v2.css`'s flat nav + content model (`templates/sceptre/base.html` + `_nav.html`), keeping HTMX partials for in-page interactivity.

End state: the Apostolic Chrome becomes exclusive to the Handbook; `app.ichebo.org` runs the sceptre-style shell.

## Incidents found and fixed along the way

All four were found during Stage 0–2 verification and fixed the same day (2026-09-30), before or immediately after reaching production.

| Issue | Where | Fix |
| --- | --- | --- |
| 12 pages silently dropped the shell's design tokens (dark palette, sidebar rule-of-left, stage colors) | Dashboard, Records, Community, Activity, Tenants, Calendar, Handbook/Records graph — all overrode `{% block extra_css %}` without `{{ block.super }}` | Added `{{ block.super }}` to each; pre-existing bug, unrelated to this rework, found while auditing the shell |
| Django's `{# #}` comment tag can't span multiple lines — it silently renders as visible literal text instead of being stripped | 6 templates, including an ASCII banner leaking onto the live Dashboard (twice) and a full doc-comment leaking above the title field on every Desk/Handbook editor | Converted all 6 to `{% comment %}...{% endcomment %}`, which does support multi-line content |
| `/handbook/` 500'd in production right after the Stage 1 launcher shipped | `handbook.ichebo.org` runs a scoped urlconf (`handbook.subdomain_urls`) that only registers `handbook:`/`accounts:` namespaces; the shared launcher grid reversed `activity:`, `community:`, etc., which don't exist there | Added `components/_app_launcher_external.html` (absolute `app.ichebo.org` URLs, no `{% url %}` reverses) and switched to it when `request.site == 'handbook'` — the same pattern the old sidebar used this branch for |
| The launcher fix didn't actually take effect once deployed — click did nothing | `collectstatic` hadn't been run on production since 2026-08-10, so the deployed `staticfiles/js/shell_v2.js` predated the new toggle functions entirely | Ran `collectstatic`; added a `?v=2` cache-bust to the script tag so browsers that had already cached the old file picked up the change too |

All four verified fixed via real browser sessions against the live site, not just server-side checks.

## Status tracker

| Stage | Status | Next step |
| --- | --- | --- |
| 0. Clone & rename shell | Done | — |
| 1. Ecosystem launcher | Done | — |
| 2. Handbook chrome | In progress | Split record.html's type-picker out of the Context Bar into the Options bar |
| 3. Library/Journal/Bible forms | Not started | Scope the form simplification pass |
| 4. Desk stays separate | Scope decided | — |
| 5. app.ichebo.org lighter migration | Not started | Begins after Stage 3 proves out |
