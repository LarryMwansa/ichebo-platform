# Design System — Ichebo Platform

## Product Context

- **What this is:** A three-surface Kingdom governance platform — a marketing site (ichebo.online), a desktop web workspace (app.ichebo.org), and a Flutter mobile app (Android-first).
- **Who it's for:** Desktop workspace = Level 3–5 stewards, coordinators, and administrators managing governance operations. Mobile app = all competence levels (0b–5), the daily interface for community members. Marketing site = public audiences across all entry points.
- **Space/industry:** Faith-based institutional governance, formation, and community management. Closest analogies: Linear (desktop workspace feel), Notion (document/governance layer), a mission-driven B Corp product.
- **Project type:** Multi-surface platform — editorial marketing site + governance dashboard workspace + mobile app.

---

## Aesthetic Direction

- **Direction:** Apostolic Editorial — institutional authority expressed through typographic weight, controlled negative space, and ink-dark surfaces. Not corporate, not evangelical-generic. Closer to *The Economist* meets a well-designed governance institution.
- **Decoration level:** Intentional — every decorative element (the red vertical rule, the ghost watermark text, the stone surface, the left accent border) carries semantic meaning. Nothing is decorative without purpose.
- **Mood:** The platform should feel like it was built by people who take governance seriously. Authoritative without being cold. Principled without being preachy. The design signals that this is a system worth trusting — one that has thought carefully about structure, hierarchy, and purpose.
- **The one thing someone will remember:** The deep ink `#0E0E0E` + stone `#F5F3F0` contrast paired with the red `#AF3236` accent — it reads as a physical institution, not a SaaS product.

---

## Typography

### Typefaces

| Role | Font | Weight | Rationale |
|------|------|--------|-----------|
| Display / Hero | Playfair Display | 700, 800, 900 | Editorial authority. Italic variant for emotional accent. Used for page titles, hero headlines, stat numbers. Never for body or UI labels. |
| Body / UI | Inter | 400, 500, 600 | Clean, legible, neutral. Reads well at 12px–16px on screens. Does the structural work. |
| Code / monospace | Fira Code | 400 | For governance record IDs, technical fields. |

### Font loading

```html
<!-- In global.css @import -->
@import url("https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700;1,800&family=Inter:wght@300;400;500;600&display=swap");
```

### Type Scale

| Token | Size | Usage |
|-------|------|-------|
| `--fz--3` | 11px | Badge labels, uppercase caps |
| `--fz--2` | 12px | Caption, meta, timestamps |
| `--fz--1` | 14px | Body small, secondary labels |
| `--fz-0` | 16px | Body base (strict — iOS Safari anchor) |
| `--fz-1` | 18px | Subtitle, list item title |
| `--fz-2` | 20px | Card title, section sub-heading |
| `--fz-3` | 24px | Page section header (Inter 700) |
| `--fz-4` | 32px | Workspace page title (Playfair) |
| `--fz-5` | 40px | Hero headline (Playfair) |
| `--fz-6` | 48px | Display large (Playfair — marketing/mobile hero only) |

### Typography Rules

1. **Playfair Display** = page titles, hero headings, stat display numbers, section titles in workspace. Never for labels, badges, nav items, or body text.
2. **Inter** = all UI text — navigation, buttons, form labels, table cells, badges, body paragraphs.
3. Italic Playfair Display (`em` tag) = accent on key words in hero headings only. Used sparingly — one italic word per heading maximum.
4. **Negative letter-spacing** (`--tracking-m: -0.1ch`) on all Playfair Display display text.
5. **Uppercase tracking** (`--tracking-widest: 0.1em`) on Inter labels only — `.label-caps` and `.label-tag`.

---

## Colour

### Brand Palette

| Name | Token | Hex | Usage |
|------|-------|-----|-------|
| Primary Red | `--primary` | `#AF3236` | Brand, primary buttons, active states, left accent rule, level badge (L5) |
| Primary Dark | `--primary-dark` | `#8C2A2D` | Hover state on primary |
| Primary Light | `--primary-light` | `rgba(175,50,54,0.12)` | Badge backgrounds, icon containers |
| Secondary Blue | `--secondary` | `#185ABC` | Platform/tech contexts, info states, links |
| Ink | `--ink` | `#0E0E0E` | Dark hero surfaces, sidebar background, dark cards |
| Ink 2 | `--ink-2` | `#1A1A1A` | Dark card surfaces, secondary dark sections |
| Ink Light | `--ink-light` | `#2D2D2D` | Dark hover states |

### Surface Palette

| Name | Token | Hex | Usage |
|------|-------|-----|-------|
| Background | `--bg` | `#FFFFFF` | Page background (light mode) |
| Card / Stone | `--card` | `#F5F3F0` | Card surfaces, sidebar content area (light) |
| Stone 2 | `--card-2` | `#ECE9E4` | Hover surfaces, dividers, table alternating rows |
| Hover | `--hover` | `#ECE9E4` | Interactive hover states |

### Text Palette

| Name | Token | Hex | Usage |
|------|-------|-----|-------|
| Text | `--text` | `#1A1A1A` | Primary text |
| Muted | `--muted` | `#6B6B6B` | Secondary text, labels, timestamps |
| Muted Light | `--muted-light` | `#9A9A9A` | Placeholder, disabled text |

### Semantic Colours

| State | Token | Hex | Dark Mode Hex |
|-------|-------|-----|---------------|
| Success | `--success` | `#16A34A` | `#4ADE80` |
| Warning | `--warning` | `#CA8A04` | `#FBBF24` |
| Error | `--error` | `#DC2626` | `#F87171` |
| Info | `--info` | `#0C5C9E` | `#60A5FA` |

### Level Colours (KGS Competence)

| Level | Name | Token | Hex |
|-------|------|-------|-----|
| 0 | Seeker | `--level-0` | `#9CA3AF` |
| 1 | Foundational Disciple | `--level-1` | `#16A34A` |
| 2 | Active Contributor | `--level-2` | `#2563EB` |
| 3 | Functional Minister | `--level-3` | `#7C3AED` |
| 4 | Leader | `--level-4` | `#EA580C` |
| 5 | Apostolic Steward | `--level-5` | `#DC2626` |

### Dark Mode Strategy

- Surface shift: `--bg` → `#0E0E0E`, `--card` → `#1A1A1A`, `--card-2` → `#2D2D2D`
- Text shift: `--text` → `#F5F3F0`, `--muted` → `#9A9A9A`
- Borders shift from `rgba(0,0,0,0.08)` → `rgba(255,255,255,0.08)`
- Semantic colours de-saturate by 10–15% and lighten for dark backgrounds
- `--primary` never changes in dark mode — the red is a fixed brand anchor

---

## Spacing

- **Base unit:** 8px
- **Density:** Comfortable on mobile, Compact on desktop workspace (more information per viewport)
- **Scale:**

| Token | Value | Usage |
|-------|-------|-------|
| `--space-3xs` | 4px | Badge padding, tight internal spacing |
| `--space-2xs` | 8px | Icon-text gap, small component gap |
| `--space-xs` | 12px | Card internal gap, form field gap |
| `--space-s` | 16px | Standard padding unit (page horizontal padding) |
| `--space-m` | 24px | Section gap, card margin-bottom |
| `--space-l` | 32px | Page section gap |
| `--space-xl` | 48px | Major section spacing |
| `--space-2xl` | 64px | Hero / display spacing |
| `--space-3xl` | 96px | Maximum section breathing room |

---

## Layout

### Three-Surface Layout System

#### 1. Marketing Site (ichebo.online) — Editorial
- **Grid:** Full-width editorial. Max content width: `1280px`. Centred with `clamp(1.25rem, 4vw, 3rem)` horizontal padding.
- **Sections:** Alternating dark ink / stone / white backgrounds.
- **No sidebar.** No persistent navigation shell.

#### 2. Desktop Workspace (app.ichebo.org) — Governance Dashboard
- **Primary breakpoint:** ≥ 1024px
- **Layout:** Fixed left sidebar (240px) + main content area (flex: 1) + optional right panel (320px)
- **Sidebar:** Background `--ink` (`#0E0E0E`). White logo. Nav items in Inter 500. Active state: left 3px red rule + `--primary` text colour.
- **Main content:** Background `--card` (`#F5F3F0`). Max content column: `800px` centred within the main area (not the full viewport).
- **Top bar:** 56px, sits above the main content area only (not above sidebar). Carries page title, breadcrumb, and action buttons.
- **Graceful degradation < 768px:** Sidebar collapses to a drawer. Bottom nav appears. Falls back to the existing mobile shell CSS (no regression).

#### 3. Flutter Mobile — Touch-Native
- **Shell:** Bottom navigation bar (4–5 items max). Top app bar (56dp). Content scrolls under both.
- **Max content width on tablet:** 800dp centred.
- **Card density:** Comfortable. 12dp radius (matches `--radius-l` on web).
- **Touch targets:** 48dp minimum — enforced on all interactive elements.

### Border Radius Scale

| Token | Value | Surface | Usage |
|-------|-------|---------|-------|
| `--radius-xs` | 3px | Editorial sharp | Buttons, badges, table rows — website/workspace |
| `--radius-s` | 4px | Editorial card | Workspace sidebar items, data table rows |
| `--radius-m` | 8px | App moderate | Icon containers, form inputs |
| `--radius-l` | 12px | App card | Standard mobile cards (tighter than before) |
| `--radius-xl` | 16px | App elevated | Profile cards, modal headers |
| `--radius-2xl` | 20px | Bottom sheets | Slide-up drawers |
| `--radius-pill` | 999px | Status badges | All pill shapes |

---

## Signature Design Patterns

These are the five visual signatures that create continuity across all three surfaces. Every major component should reference at least one of these.

### 1. The Left Red Rule
A 3px vertical `#AF3236` line on the left edge of a component. Used for:
- Active sidebar nav item (workspace)
- Accent cards (`.card-accent` in web CSS)
- Programme cards on hover (Learn app)
- Editorial callout blocks on marketing site

### 2. The Dark Ink Hero
Background `#0E0E0E`, white Playfair Display headline, red italic accent on a key word, body text at `rgba(255,255,255,0.55)`. Used for:
- Marketing site dark sections
- Platform page-hero blocks (mobile Learn app)
- Workspace sidebar background
- Flutter app bar and page headers (dark variant)

### 3. The Ghost Watermark
Large Playfair Display text at 3–7% opacity floating behind content. Used for:
- Marketing site hero sections (`KINGDOM`, `SCEPTRE`)
- Desktop workspace section backgrounds (app/section name)
- Flutter hero screens (optional — level 3+)

### 4. The Label Tag
`—— LABEL TEXT` in 11px Inter 700, uppercase, `--tracking-widest`, `--primary` colour. The horizontal line before the text is a 20px `#AF3236` block, not a dash character. Used everywhere as a section eyebrow: marketing site, workspace, mobile.

### 5. Stone-to-Ink Contrast
The shift between `#F5F3F0` (stone — light content area) and `#0E0E0E` (ink — dark hero/sidebar) is the primary spatial signal of the design system. This contrast replaces the conventional white/grey pattern and gives the platform its editorial, institutional quality.

---

## Motion

- **Approach:** Minimal-functional. Transitions exist to orient the user, not to entertain them. A governance platform should feel stable and precise.
- **Easing:** `cubic-bezier(0.4, 0, 0.2, 1)` for all transitions (Material Design standard easing — appropriate for a platform used for serious work).
- **Duration:**

| Name | Duration | Usage |
|------|----------|-------|
| Micro | 100ms | Hover colour changes, badge state |
| Fast | 150ms | Button active, icon fill change |
| Standard | 300ms | Card transitions, sidebar collapse |
| Deliberate | 500ms | Page-level transitions, sheet open |

- **What never animates:** Table row data, governance record content, certification status. These must feel instantaneous and certain — no animation on state changes that represent real governance decisions.

---

## Component Inventory

### Shared (all surfaces)
- `.label-tag` — section eyebrow label
- `.label-caps` — form labels, secondary eyebrows
- `.status-badge` — active, warning, danger, muted, seeker
- `.badge-unit` — record type, activity type
- `.progress-bar-wrap` + `.progress-bar-fill` — formation progress
- `.btn-touch` + variants — primary, secondary, danger, ghost
- `.form-input-touch` — all form inputs

### Web Platform (Django/HTMX)
- `.page-hero` — dark ink section header for each app home
- `.page-hero--watermark` — ghost text variant
- `.card` + `.card-dark` + `.card-accent` — card variants
- `.list-group` + `.list-item` — dense list pattern
- `.tab-row` + `.tab` — surface switching
- `.empty-state` — empty list states
- `.fab` — floating action button (mobile shell only)

### Desktop Workspace (new — to be built)
- `.ws-layout` — sidebar + main + optional right panel
- `.ws-sidebar` — fixed left navigation
- `.ws-sidebar__nav-item` — nav item with active left rule
- `.ws-topbar` — 56px page header bar
- `.ws-panel` — right detail panel
- `.ws-data-table` — governance record tables
- `.ws-stat-card` — dashboard metric cards
- `.ws-section-header` — section title + action row

### Flutter Mobile (Dart — to be built)
- `IcheboAppBar` — dark app bar with SVG logo
- `PageHeroHeader` — dark ink header widget matching web page-hero
- `IcheboCard` — 12dp radius card
- `LevelBadge` — coloured level indicator
- `StatusBadge` — status pill
- `IcheboButton` — primary / secondary / danger / ghost
- `ListItemTile` — dense list item
- `EmptyState` — empty screen widget
- `IcheboProgressBar` — formation progress bar
- `BottomNavShell` — role-adaptive bottom navigation

---

## Build Sequence

### Phase 1 — Foundation (complete)
- [x] Marketing site (ichebo.online) — 8 pages
- [x] Design tokens (`variables.css`)
- [x] Global CSS (`global.css`, `main.css`, `navbar.css`)
- [x] `DESIGN.md` (this document)

### Phase 2 — Desktop Workspace (next)
- [ ] `workspace.css` — sidebar layout, topbar, panels
- [ ] Updated `base.html` — workspace shell (sidebar + main)
- [ ] `_sidebar.html` — workspace sidebar component
- [ ] `_ws_topbar.html` — workspace topbar component
- [ ] App templates updated: Bible, Learn, Activity, Community, Governance, Profile
- [ ] Dashboard (`home/`) — workspace home with stat cards

### Phase 3 — Flutter Mobile
- [ ] `tokens.dart` — all design tokens as Dart constants
- [ ] `app_theme.dart` — ThemeData for light + dark
- [ ] Core widgets: `IcheboAppBar`, `IcheboCard`, `LevelBadge`, `StatusBadge`, `IcheboButton`, `ListItemTile`, `EmptyState`, `IcheboProgressBar`
- [ ] Navigation shell: `BottomNavShell` with role-adaptive items
- [ ] Feature screens per app (Bible, Learn, Activity, Community, Profile)

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-25 | Playfair Display + Inter as dual typeface | Editorial authority for display, legibility for UI — matches ichebo.online aesthetic |
| 2026-04-25 | Stone `#F5F3F0` as card surface (not white) | Warmer, more institutional than white. Matches marketing site. |
| 2026-04-25 | Desktop workspace is Level 3+ only | Governance-dense interface inappropriate for seekers and new disciples. Mobile serves L0–L2 daily. |
| 2026-04-25 | Card radius reduced to 12px (`--radius-l`) | Tighter than old 16px. Closer to website's editorial sharpness without being jarring on touch. |
| 2026-04-25 | Sidebar background: `--ink` (`#0E0E0E`) | Mirrors marketing site's dark hero sections. Creates strong spatial signal between nav and content. |
| 2026-04-25 | Ghost watermark pattern carried into workspace | Visual continuity with marketing site. Used as section identifier behind workspace page headers. |
| 2026-04-25 | No animation on governance record state changes | Governance decisions must feel certain and instantaneous. Animation implies uncertainty. |
| 2026-04-25 | Flutter app targets Android-first | Primary Global South market. iOS deferred to Version 3. |
| 2026-04-25 | Sidebar collapses to drawer below 768px | Mobile graceful degradation — existing mobile CSS continues to work unchanged below breakpoint. |
