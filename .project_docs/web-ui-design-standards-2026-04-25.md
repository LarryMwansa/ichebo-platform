# Ichebo Platform — Web UI Design & Standards

**Version:** v1.0 — 2026-04-25
**Status:** Approved — Definitive Reference
**Scope:** Django templates + HTMX web application
**Author:** Chizola (brand); Claude (specification)

This document is the single authoritative reference for all visual and interaction design decisions on the Ichebo web platform. Every new template, component, and CSS rule must be grounded here. Do not invent styles — look here first.

---

## Part 1 — Brand Identity

### 1.1 Brand Name & Platform Name

- **Organisation:** Ichebo Christian Services
- **Platform:** Ichebo Platform
- **Short form in UI:** Ichebo

The word "ICS" must not appear in any user-facing text, UI labels, or page titles. It may remain in internal code identifiers (Django app names, URL prefixes) only.

### 1.2 Brand Colours

| Name | Token | Hex | Usage |
|------|-------|-----|-------|
| Primary Red | `--primary` | `#AF3236` | Brand, primary buttons, active states, level badge |
| Secondary Blue | `--secondary-light` | `#185ABC` | Links, secondary actions, info states |
| Near Black | `--text` | `#1A1A1A` | Body text, headings in light mode |
| White | `--bg` | `#FFFFFF` | Background in light mode |
| Surface | `--card` | `#F8F9FA` | Card backgrounds, input backgrounds |
| Border | `--border` | `#E9ECEF` | Dividers, input borders, card outlines |
| Muted | `--muted` | `#6C757D` | Secondary text, placeholders, meta info |
| Hover | `--hover` | `#F1F3F5` | Hover states, subtle backgrounds |
| Success | `--success` | `#16A34A` | Positive states, level advancement, completion |
| Error | `--error` | `#DC2626` | Errors, destructive actions |
| Warning | `--warning` | `#CA8A04` | Caution states, pending items |
| Info | `--info` | `#0C5C9E` | Informational states, help text |

### 1.3 Competence Level Colours

Level colours are used in the level badge (navbar), formation history, and app drawer unlock modals.

| Level | KGS Name | Hex | Meaning |
|-------|----------|-----|---------|
| 0 | Seeker | `#6C757D` | Muted grey — not yet placed |
| 1 | Foundational Disciple | `#16A34A` | Green — growth beginning |
| 2 | Active Contributor | `#185ABC` | Blue — active participation |
| 3 | Functional Minister | `#7E22CE` | Purple — service and coordination |
| 4 | Leader | `#EA580C` | Orange — oversight responsibility |
| 5 | Apostolic Steward | `#AF3236` | Brand red — full authority |

### 1.4 Dark Mode

Dark mode is toggled via `storage.js` and the `body.dark` class. The theme persists to `User.preferences.theme` in the database, not localStorage. `storage.js` reads the DB preference on load and applies the class before first paint to prevent flash.

| Token | Light | Dark |
|-------|-------|------|
| `--bg` | `#FFFFFF` | `#121212` |
| `--card` | `#F8F9FA` | `#1E1E1E` |
| `--text` | `#1A1A1A` | `#F5F5F5` |
| `--muted` | `#6C757D` | `#AAAAAA` |
| `--border` | `#E9ECEF` | `rgba(255,255,255,0.08)` |
| `--hover` | `#F1F3F5` | `#2A2A2A` |
| `--primary-alpha` | `rgba(175,50,54,0.15)` | `rgba(175,50,54,0.25)` |

---

## Part 2 — Typography

### 2.1 Typeface

**Font family:** Roboto (loaded from Google Fonts in `global.css`). Fallback: `system-ui, sans-serif`.
**Body size:** 16px strict — this prevents iOS Safari from auto-zooming form inputs.

### 2.2 Type Scale

Never use arbitrary font sizes. Always use a token.

| Token | Pixels | Rem | Usage |
|-------|--------|-----|-------|
| `--fz--4` | 10px | 0.625rem | Micro labels, legal text |
| `--fz--3` | 11px | 0.6875rem | Uppercase badge text, tight caps |
| `--fz--2` | 12px | 0.75rem | Caption, timestamp, meta info |
| `--fz--1` | 14px | 0.875rem | Body small, card descriptions, secondary labels |
| `--fz-0` | 16px | 1rem | Body base, input text (strict — prevents iOS zoom) |
| `--fz-1` | 18px | 1.125rem | Subtitle, list item titles |
| `--fz-2` | 20px | 1.25rem | Title small, card headings |
| `--fz-3` | 24px | 1.5rem | Title medium, page headers |
| `--fz-4` | 32px | 2rem | Title large, section headers |
| `--fz-5` | 40px | 2.5rem | Display small, hero text |

### 2.3 Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `--font-weight-regular` | 400 | Body text, descriptions, secondary content |
| `--font-weight-medium` | 500 | Button labels, list item titles, nav items |
| `--font-weight-bold` | 700 | Page headings, card titles, emphasis |
| `--font-weight-black` | 800 | Display numbers, level badge, stat values |

### 2.4 Letter Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `--tracking-wide` | 0.05em | Uppercase badge labels, small caps |
| `--tracking-wider` | 0.08em | Section headings in caps |
| `--tracking-widest` | 0.10em | Strict caps labels (e.g. "LEVEL 3") |
| `--tracking` (negative) | -0.05ch | Large display titles only — do not apply to body |

---

## Part 3 — Spacing System

All spacing uses an 8px base grid. Never use arbitrary values. Every margin, padding, and gap must use a spacing token.

| Token | Pixels | Rem | Usage |
|-------|--------|-----|-------|
| `--space-3xs` | 4px | 0.25rem | Tight internal spacing, badge padding |
| `--space-2xs` | 8px | 0.5rem | Icon-text gap, small component gap |
| `--space-xs` | 12px | 0.75rem | Card internal gap, list item gap |
| `--space-s` | 16px | 1rem | Standard padding, list item padding |
| `--space-m` | 24px | 1.5rem | Section gap, card margin-bottom |
| `--space-l` | 32px | 2rem | Page section gap |
| `--space-xl` | 48px | 3rem | Major section spacing |
| `--space-2xl` | 64px | 4rem | Hero / display spacing |

**Page horizontal padding:** 16px (`--space-s`) on mobile. The `.ics-main` class handles this automatically — do not add extra horizontal padding inside page templates.

**Page bottom padding:** 90px — accounts for bottom navigation bar height. Already set in `global.css` on `.ics-main`.

**Max content width:** 800px, centred — set on `.ics-main`. Do not override this on individual pages.

---

## Part 4 — Layout & Shell

### 4.1 The Shell Structure

Every web page uses the same outer shell defined in `base.html`. The shell has four fixed elements:

- **Top navbar** — fixed at top, 56px height, carries the wordmark, drawer toggle, notification bell, and avatar
- **App drawer** — slide-in overlay from left, contains all app navigation links
- **Main content area** (`.ics-main`) — scrollable, 16px horizontal padding, max 800px, centred
- **Bottom navigation bar** — fixed at bottom, 60px height, mobile-only (hidden at 800px+ breakpoint)

### 4.2 CSS File Load Order — Fixed, Never Reorder

```
1. variables.css   — all CSS custom properties (tokens)
2. global.css      — reset, base element styles, Material Symbols
3. theme.css       — dark mode overrides on body.dark
4. main.css        — layout utilities, components, FAB, HTMX progress bar
5. navbar.css      — top navbar, app drawer, bottom nav
6. [app].css       — loaded only on pages that need it (via {% block extra_css %})
```

Never combine these into one file. The order is intentional — each file builds on the tokens defined before it.

### 4.3 Responsive Breakpoints

| Breakpoint | Width | What Changes |
|-----------|-------|--------------|
| Mobile (default) | < 800px | Bottom nav visible, drawer hidden by default, single column |
| Desktop | ≥ 800px | Bottom nav hidden, FAB repositions to bottom-right, wider padding |

The existing code uses 800px as the breakpoint. Do not change this.

---

## Part 5 — Component Library

### 5.1 Buttons

All buttons must have `min-height: 48px`. This is a WCAG 2.1 AA requirement for touch targets and is non-negotiable.

| Class | Appearance | When to Use |
|-------|-----------|-------------|
| `.btn-touch` | Base class — enforces 48px height | Apply to every button regardless of variant |
| `.btn-touch` + primary background | `--primary` bg, white text, 12px radius | Primary action: save, submit, confirm, enrol |
| `.btn-touch` + `--card` border | `--card` bg, `--text` colour, `--border` outline | Secondary action: cancel, back, alternative |
| `.btn-touch` + `--error` background | `--error` bg, white text | Destructive action: delete, reject — always confirm first |
| `.btn-touch` + transparent | No background, `--primary` text | Ghost / text action: view all, see more |

**Button states:**

- **Hover:** opacity 0.9 or slight background shift — never remove the button on hover
- **Active:** `transform: scale(0.98)` — already in `.btn-touch:active`, do not override
- **Disabled:** `opacity: 0.5`, `cursor: not-allowed` — never hide disabled buttons, show them greyed
- **Loading (HTMX):** add `htmx-request` indicator class; show spinner inside button, disable clicks

### 5.2 Cards

Cards are the primary content container. Use consistently across all apps.

```css
.card-base {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: var(--space-s) var(--space-s);
  margin-bottom: var(--space-xs);
}
```

**Card variants:**

- **Standard:** `.card-base` — white/dark surface, 1px border, 12px radius
- **Elevated:** add `box-shadow: var(--shadow-card)` — use sparingly, only for the primary focus card on a page
- **Tinted** (e.g. formation journey): `background: var(--primary-tint)` — `#fff8f8` in light mode
- **Interactive** (clickable): add `transition: background 0.15s`, `background: var(--hover)` on `:hover`, `transform: scale(0.98)` on `:active`

### 5.3 Badges & Status Indicators

**Status badge** (`.status-badge`) — pill shape, used for record status, user status, formation stage:

```css
.status-badge--active   { background: color-mix(in srgb, var(--success) 12%, transparent); color: var(--success); }
.status-badge--danger   { background: color-mix(in srgb, var(--error) 12%, transparent);   color: var(--error); }
.status-badge--warning  { background: color-mix(in srgb, var(--warning) 12%, transparent); color: var(--warning); }
.status-badge--seeker   { background: color-mix(in srgb, var(--info) 12%, transparent);    color: var(--info); }
.status-badge--muted    { background: var(--hover); color: var(--muted); }
```

**Unit badge** (`.badge-unit`) — rectangular, 4px radius, used for record type, activity type, service order:

- `.badge-unit` — `--hover` background, `--muted` text — default neutral
- `.badge-unit--primary` — primary-alpha background, `--primary` text — for highlighted types

**Level badge** (navbar, formation card) — coloured by level (see Part 1.3). Use a small filled circle + level number. Example: `● 3`

### 5.4 Forms & Inputs

All form inputs must use `.form-input-touch`:

```css
.form-input-touch {
  display: block;
  width: 100%;
  min-height: 48px;        /* strict touch target */
  padding: 0 var(--space-s);
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 16px;         /* strict — prevents iOS Safari zoom */
  font-family: inherit;
}
```

**Input states:**

- **Default:** `--border` outline, `--card` background
- **Focus:** `--primary` border colour, no box-shadow outline
- **Error:** `--error` border colour; add `.form-error-message` below the field in `--error` colour
- **Disabled:** `opacity: 0.6`, `cursor: not-allowed`

**Form group pattern:**

```html
<div class="record-form-group">
  <label class="label-caps" for="field-id">Field Label</label>
  <input class="form-input-touch" id="field-id" name="field" type="text">
  <span class="form-error-message" style="color:var(--error);font-size:var(--fz--2)">
    Error text here
  </span>
</div>
```

**Label style:** always use `.label-caps` — 11px, 700 weight, uppercase, `--muted` colour, `tracking-wide`. This is the standardised label treatment across all apps.

### 5.5 List Items

Dense list items (`.list-item` inside `.list-group`) used for directory listings, record lists, and settings options.

```css
.list-group {
  background: var(--card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
}
.list-item {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  padding: var(--space-s);
  border-bottom: 1px solid var(--border);
  background: var(--card);
}
.list-item:last-child { border-bottom: none; }
```

**List item anatomy:**

- `.list-item__icon` — 40×40px, 8px radius, `--bg` background, `--muted` icon colour
- `.list-item__content` — `flex: 1`, column flex, title + meta
- `.list-item__title` — `--fz-0`, `--font-weight-medium`, `--text` colour, truncated with ellipsis
- `.list-item__meta` — `--fz--2`, `--muted` colour, 2px margin-top
- `.list-item__action` — `flex-shrink: 0`, `--muted` colour (chevron or action icon)

### 5.6 Tabs (Surface Selectors)

Used by Activity, Community, Governance, Learn to switch between surfaces. Tabs are sticky — they stay at the top of the content area when scrolling.

```css
.tab-row {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--card);
  position: sticky;
  top: 56px;   /* navbar height */
  z-index: 10;
}
.tab {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  font-size: var(--fz--1);
  font-weight: var(--font-weight-medium);
  color: var(--muted);
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.tab.active { color: var(--primary); border-bottom-color: var(--primary); }
```

Active tab state is set server-side using Django template conditionals — no JavaScript required.

### 5.7 Progress Bars

```css
.progress-bar-wrap {
  height: 8px;
  background: var(--hover);
  border-radius: 4px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 4px;
  transition: width 0.6s ease;
}
```

In Django templates: `<div class="progress-bar-fill" style="width: {{ progress }}%"></div>`

Never animate on every HTMX swap — add `transition` only on the fill element, not the wrapper.

### 5.8 Floating Action Button (FAB)

One FAB per page. Position: fixed, bottom-right. Used for the primary create action on list views.

- **Desktop (≥ 800px):** `bottom: 32px`, `right: 32px`
- **Mobile (< 800px):** `bottom: 84px` (above bottom nav), `right: 20px`
- **Active state:** rotate the `+` icon 45° to form an `×`. Use `.fab.active .fab-icon { transform: rotate(45deg) }`
- **HTMX pattern:** `hx-get` to open a drawer or modal partial; `hx-target` to the drawer container; `hx-swap: innerHTML`

### 5.9 Modals & Bottom Sheets

Bottom sheets (slide-up panels) are used for verse annotation, record creation drawers, and lock/supersede confirmations. Full-screen modals are not used.

```css
.sheet {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: var(--card);
  border-radius: 20px 20px 0 0;
  padding: var(--space-s);
  z-index: 1000;
  transform: translateY(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.sheet.open { transform: translateY(0); }
.sheet-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 999; }
```

**HTMX pattern:** the FAB or trigger button `hx-get`s a partial that populates the sheet content; the HTMX `afterSwap` hook adds `.open` to the sheet.

### 5.10 Empty States

Every list or surface that can be empty must have an empty state. Never show a blank page.

```html
<div class="empty-state">
  <span class="material-symbols-outlined empty-state__icon">icon_name</span>
  <p class="empty-state__title">Nothing here yet</p>
  <p class="empty-state__message">Descriptive explanation of what will appear here.</p>
  <!-- optional primary action -->
  <a href="..." class="btn-touch" style="background:var(--primary);color:#fff">
    Create First Item
  </a>
</div>
```

Empty state icon: use a Material Symbol that relates to the content type. Size: 48px, `--muted` colour.

### 5.11 Toast Notifications

Toasts appear in `#toast-container` (already in `base.html`). The server sets `HX-Trigger: {"showToast": {"message": "...", "type": "success"}}` and a global `htmx:afterRequest` handler renders the toast.

- **Success toast:** `--success` border, `--success-light` background
- **Error toast:** `--error` border, `--error-light` background
- **Duration:** auto-dismiss after 3 seconds. No permanent toasts.
- **Position:** top of `#main-content` area (not fixed to viewport)

---

## Part 6 — Icons

**Icon set:** Material Symbols Outlined (variable font, loaded via Google Fonts CDN in `global.css`). Do not add a second icon library.

**Usage:**
```html
<span class="material-symbols-outlined">home</span>
```

**Icon sizes:**

| Context | Size |
|---------|------|
| Navigation icons (navbar, bottom nav, app drawer) | 24px (default) |
| Card icons (`.list-item__icon`) | 24px |
| Empty state icons | 48px (add `font-size: 48px` inline) |
| Button icons (alongside text) | 20px |
| Inline text icons | Match surrounding text font-size |

**Fill state:** default is outlined (FILL 0). Use FILL 1 only for active navigation state:

```css
.active .material-symbols-outlined {
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
```

### Standard Icon Assignments

| App / Element | Icon Name |
|---------------|-----------|
| Home / Dashboard | `home` |
| Bible | `menu_book` |
| Learn / Education | `school` |
| Activity / Tasks | `task_alt` |
| Community | `groups` |
| Governance | `gavel` |
| Paraclete | `auto_awesome` |
| Video / Live | `live_tv` |
| Profile / You | `person` |
| Notifications | `notifications` |
| Settings | `settings` |
| Search | `search` |
| Add / Create | `add` |
| Edit | `edit` |
| Delete | `delete` |
| Lock | `lock` |
| Locked (app drawer) | `lock_outline` |
| Chevron right | `chevron_right` |
| Close / Dismiss | `close` |
| Check / Complete | `check_circle` |
| Warning | `warning` |
| Menu (drawer toggle) | `menu` |
| Filter | `filter_list` |
| Calendar | `calendar_month` |

---

## Part 7 — HTMX Interaction Patterns

HTMX is the only dynamic interaction mechanism on the web platform. There is no React, Vue, Alpine, or custom JS framework. Vanilla JS is used only for theme toggle (`storage.js`) and navbar state (`navbar.js`).

### 7.1 Partial vs Full Page

- Files prefixed with `_` are partials (HTMX fragments). They do not extend `base.html`.
- Files without `_` prefix are full pages. They extend `base.html`.
- Views detect the `HX-Request` header and return the appropriate template.

```python
class MyView(LoginRequiredMixin, View):
    def get(self, request):
        context = self.get_context()
        if request.headers.get('HX-Request'):
            return render(request, 'app/_list.html', context)
        return render(request, 'app/list.html', context)
```

### 7.2 Standard HTMX Attributes

| Pattern | HTMX Attributes | Notes |
|---------|----------------|-------|
| Load list | `hx-get="/url/" hx-trigger="load" hx-target="#container"` | Load content on page render |
| Form submit | `hx-post="/url/" hx-target="#result" hx-swap="outerHTML"` | Submit and replace form with response |
| Mark complete | `hx-post="/url/" hx-target="closest .card" hx-swap="outerHTML"` | Replace the card with updated state |
| Search/filter | `hx-get="/url/" hx-trigger="keyup changed delay:300ms" hx-target="#results"` | Debounced search on input |
| Polling badge | `hx-get="/url/" hx-trigger="load, every 60s" hx-target="#badge"` | Notification count, live status |
| Infinite scroll | `hx-get="/url/?page=2" hx-trigger="intersect once" hx-swap="afterend"` | Load more on scroll |
| Open sheet | `hx-get="/url/" hx-target="#sheet-content" hx-swap="innerHTML"` | Populate bottom sheet; JS adds `.open` via `afterSwap` |

### 7.3 HTMX Progress Indicator

The `.htmx-progress-bar` at the top of the page shows during any HTMX request. It is already wired in `main.css` and `base.html`. Do not add per-component loading spinners unless the component is large and the load time is slow.

### 7.4 CSRF

CSRF is wired once in `base.html` via the `htmx:configRequest` event listener. Do not add `{% csrf_token %}` inside HTMX target containers — the header is set globally. Only add `{% csrf_token %}` inside standard Django `<form>` elements.

### 7.5 HTMX Response Headers

| Header | When to Use |
|--------|-------------|
| `HX-Redirect: /url/` | After a successful create/delete — redirect to the new page |
| `HX-Trigger: {"showToast": {...}}` | After save — trigger a success/error toast |
| `HX-Retarget: #new-target` | Override the target declared on the element — useful for error states |
| `HX-Reswap: outerHTML` | Override the swap strategy from the server side |

---

## Part 8 — Accessibility Standards

Minimum standard: WCAG 2.1 AA. These rules are non-negotiable.

### 8.1 Touch Targets

Minimum touch target size: **48×48px**. Already enforced by `.btn-touch` and `.form-input-touch`. Any interactive element not covered by these classes must be explicitly given `min-height: 48px` and sufficient padding.

### 8.2 Colour Contrast

- Body text (`--text` on `--bg`): 16.75:1 — exceeds AA
- Muted text (`--muted` on `--bg`): 4.6:1 — passes AA for body text
- Primary red (`--primary` on white): 4.8:1 — passes AA for large text
- Do not use `--muted` colour for text below 14px or non-bold text

### 8.3 Focus Management

- All interactive elements must show a visible focus indicator. Do not use `outline: none` without a custom focus replacement.
- After an HTMX swap that changes the primary content, move focus to the first heading in the new content.
- Bottom sheets: on open, move focus to the first interactive element inside. On close, return focus to the trigger element.

### 8.4 ARIA

- **App drawer:** `aria-expanded` on the toggle button, `aria-controls` pointing to the drawer id, `aria-hidden="true"` on the drawer when closed
- **Bottom sheets:** `role="dialog"`, `aria-modal="true"`, `aria-label` with descriptive name
- **Notification badge:** `aria-label="X notifications"` on the bell icon
- **Progress bars:** `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`
- **Loading states:** `aria-live="polite"` on the toast container (already in `base.html`)

### 8.5 Semantic HTML

- `<header>` for the navbar, `<main>` for the content area, `<nav>` for tab rows and bottom nav
- `<h1>` once per page — the page title. `<h2>` for section headers. Never skip heading levels.
- `<button>` for actions that do not navigate. `<a href>` for navigation. Never use `<div>` as a button.
- `<label>` for every form input — never use placeholder text as the only label

---

## Part 9 — App-Specific CSS Files

Each app loads its own CSS file via the `{% block extra_css %}` block. These files contain only styles unique to that app — they never redefine global tokens or override `main.css`.

### 9.1 File Naming Convention

| App | CSS File | Load Location |
|-----|---------|---------------|
| Bible | `static/css/bible.css` | `bible/templates/bible/*.html` (full pages only) |
| Learn | `static/css/learn.css` | `learn/templates/learn/*.html` |
| Activity | `static/css/activity.css` | `activity/templates/activity/*.html` |
| Community | `static/css/community.css` | `community/templates/community/*.html` |
| Governance | `static/css/governance.css` | `governance/templates/governance/*.html` |
| Video/Live | `static/css/video.css` | `video_live/templates/video_live/*.html` |
| Induction | `static/css/induction.css` | `learn/templates/learn/induction*.html` |

### 9.2 What Goes Where

| Put in global (`main.css`) | Put in app CSS |
|---------------------------|----------------|
| Buttons, badges, list items, form inputs, progress bars, FAB, empty states, toasts, tabs, sheets | App-specific card layouts, surface-specific colours, component variants unique to that app |
| Any component used in 2+ apps | Components used only in one app |

### 9.3 Token Consistency Rule

App CSS files must never define raw colour values. All colours must reference CSS custom properties. If you find yourself writing `#AF3236` in an app CSS file, use `var(--primary)` instead.

---

## Part 10 — Naming Conventions

### 10.1 CSS Class Naming

Use BEM-lite: `block__element--modifier`. Single hyphens for multi-word blocks.

- `.formation-card` — the block
- `.formation-card__title` — an element
- `.formation-card__badge--active` — a modifier

App-specific components are prefixed with the app name: `.learn-card`, `.bible-chapter`, `.activity-tab`.

Utility classes (from `main.css`) use a flat name: `.label-caps`, `.status-badge`, `.btn-touch`.

### 10.2 Template File Naming

- **Partial (HTMX fragment):** `_name.html` (underscore prefix)
- **Full page:** `name.html` (no underscore)
- **Base templates:** `base.html`, `base_partial.html`
- **App base templates:** `base_[app].html` (e.g. `base_learn.html`)

### 10.3 URL Naming

- **Full page views:** simple noun — `learn-home`, `learn-catalogue`, `learn-programme`
- **HTMX partials:** `htmx-[action]-[subject]` — `htmx-enrol-programme`, `htmx-complete-lesson`
- **API endpoints:** `api/[app]/[resource]/` — `api/learn/certifications/`

---

## Part 11 — What Not to Do

| Never Do This | Do This Instead |
|---------------|----------------|
| Use arbitrary pixel values (`padding: 13px`) | Use spacing tokens (`var(--space-xs)` = 12px) |
| Use raw colour values (`#af3236`) | Use colour tokens (`var(--primary)`) |
| Add `outline: none` to remove focus ring | Replace with a custom focus style using `var(--primary)` outline |
| Use `<div onclick="...">` as a button | Use `<button>` or `<a href>` with `hx-*` attributes |
| Use placeholder as the only form label | Use `<label class="label-caps">` above every input |
| Make touch targets smaller than 48px | Use `.btn-touch` or add `min-height: 48px` explicitly |
| Write JS for interactions HTMX can handle | Use `hx-get`, `hx-post`, `hx-swap` for all server interactions |
| Load all app CSS files globally | Load app CSS only via `{% block extra_css %}` on relevant pages |
| Define colours in app CSS files directly | Reference `var(--primary)`, `var(--success)`, etc. always |
| Reorder the CSS load sequence | Maintain the fixed order: variables → global → theme → main → navbar → app |
| Use font sizes not in the type scale | Use only `--fz-*` tokens |
| Show an empty white page when a list is empty | Use the empty state component every time |
