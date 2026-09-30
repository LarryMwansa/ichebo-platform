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

**Done, 2026-09-30.**

Introduced `workspace/handbook/base.html`, extending `apostolic_chrome.html`, as the one place the Library/Mandate/Keys context nav and the shared `hb-*` styling live. `home.html`, `record.html`, `access.html`, and `graph.html` now extend it instead of each independently duplicating the same nav markup and CSS (~150 duplicated lines removed), overriding only page-specific blocks where they genuinely differ.

`record.html`'s Context Bar used to do double duty — both "where am I" navigation and a type-picker that set hidden form fields (an editing action, not navigation). The type dial now lives in the Options bar's Details tab instead, gated to Handbook pages and to records that are actually still editable, and dispatches the same `dialChanged` event the Desk's own dial uses — which also fixed a latent bug where the mobile editor's hidden type field never followed a desktop dial click. `record.html` no longer overrides `context_content` at all; its Context Bar is now identical to every other Handbook page.

Along the way, fixed a second gap in the shared Options bar: its five field groups (journal/governance/activity/community/bible) had hardcoded visibility rather than being driven by the page's actual `active_family`, so Handbook always showed Journal's Mood/Tone field by default and never showed Governance's fields until a dial was clicked. Now computed server-side, correct on first load for both Desk and Handbook.

Verified end-to-end in a real browser: created and saved a Principle record through the moved dial, confirmed `record_family=governance, record_type=principle` in the database, and confirmed the Context Bar carries no type-picker on any Handbook page — live on production, not just locally.

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

All six were found during Stage 0–2 verification and fixed the same day (2026-09-30), before or immediately after reaching production.

| Issue | Where | Fix |
| --- | --- | --- |
| 12 pages silently dropped the shell's design tokens (dark palette, sidebar rule-of-left, stage colors) | Dashboard, Records, Community, Activity, Tenants, Calendar, Handbook/Records graph — all overrode `{% block extra_css %}` without `{{ block.super }}` | Added `{{ block.super }}` to each; pre-existing bug, unrelated to this rework, found while auditing the shell |
| Django's `{# #}` comment tag can't span multiple lines — it silently renders as visible literal text instead of being stripped | 6 templates, including an ASCII banner leaking onto the live Dashboard (twice) and a full doc-comment leaking above the title field on every Desk/Handbook editor | Converted all 6 to `{% comment %}...{% endcomment %}`, which does support multi-line content |
| `/handbook/` 500'd in production right after the Stage 1 launcher shipped | `handbook.ichebo.org` runs a scoped urlconf (`handbook.subdomain_urls`) that only registers `handbook:`/`accounts:` namespaces; the shared launcher grid reversed `activity:`, `community:`, etc., which don't exist there | Added `components/_app_launcher_external.html` (absolute `app.ichebo.org` URLs, no `{% url %}` reverses) and switched to it when `request.site == 'handbook'` — the same pattern the old sidebar used this branch for |
| The launcher fix didn't actually take effect once deployed — click did nothing | `collectstatic` hadn't been run on production since 2026-08-10, so the deployed `staticfiles/js/shell_v2.js` predated the new toggle functions entirely | Ran `collectstatic`; added a `?v=2` cache-bust to the script tag so browsers that had already cached the old file picked up the change too |
| The same multi-line `{# #}` comment bug from row 2 got reintroduced, by the same person who'd just fixed it, while writing the new Type section | `dynamic_options.html`'s new Type panel | Caught in local browser verification before it reached production this time; converted to `{% comment %}`; re-scanned the whole templates tree to confirm no other instances existed |
| Handbook's Options bar always showed the Journal "Mood / Tone" field by default and never showed Governance's fields until a dial was clicked | `dynamic_options.html`'s five field groups had hardcoded `display:none`/visible instead of being driven by `active_family` | Computed each group's visibility server-side from `active_family`, correct on first load for both Desk and Handbook |

All six verified fixed via real browser sessions — the first four against the live site, the last two caught and fixed locally before deploying.

## Status tracker

| Stage | Status | Next step |
| --- | --- | --- |
| 0. Clone & rename shell | Done | — |
| 1. Ecosystem launcher | Done | — |
| 2. Handbook chrome | Done | — |
| 3. Library/Journal/Bible forms | Not started | Scope the form simplification pass |
| 4. Desk stays separate | Scope decided | — |
| 5. app.ichebo.org lighter migration | Not started | Begins after Stage 3 proves out |
