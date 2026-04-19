# Session 4 — Icon Tokens, Calendar Pill Colors, Font Weight/Tracking

## Context

Sessions 1-3 fixed critical/high/medium issues and the main polish layer (spacing grid, color sweep, !important cleanup). This session completes the three explicitly deferred items:

1. **App-drawer icon color system** — 8 semantic icon color pairs, fully hardcoded, 16 values total. Need component-scoped CSS custom properties so dark mode is a property redefinition, not a rule duplication.
2. **Calendar pill colors** — 6 month-view variants + 9 week-view variants, mostly hardcoded hex. No dark mode support at all (live bug). Fix requires new tokens + dark overrides via existing `--*-light/dark` token cascade.
3. **Font weight & tracking tokens** — `font-weight: 800` appears 19 times with no token. Positive letter-spacing (0.05em–0.1em) appears 16+ times on badges/labels with no tokens — the current `--tracking-*` system is negative-only.

---

## Commit 1: App-Drawer Icon Color System

**File:** `static/css/app-drawer.css` only. No other files.

**Strategy:** Replace each `.icon-*` rule with component-scoped `--icon-bg`/`--icon-fg` custom property declarations. Add a single shared rule `[class^="icon-"], [class*=" icon-"]` that applies `background: var(--icon-bg); color: var(--icon-fg)`. Dark mode block redefines only the two properties — no rule duplication.

**Replace lines 132–150 (the full icon block) with:**

```css
/* Icon Colors — component-scoped tokens */
.icon-blue   { --icon-bg: #eff6ff;  --icon-fg: #1d4ed8; }
.icon-orange { --icon-bg: #fff7ed;  --icon-fg: #c2410c; }
.icon-pink   { --icon-bg: #fdf2f8;  --icon-fg: #be185d; }
.icon-green  { --icon-bg: #f0fdf4;  --icon-fg: #15803d; }
.icon-purple { --icon-bg: #faf5ff;  --icon-fg: #7e22ce; }
.icon-cyan   { --icon-bg: #ecfeff;  --icon-fg: #0e7490; }
.icon-teal   { --icon-bg: #f0fdfa;  --icon-fg: #0f766e; }
.icon-slate  { --icon-bg: #f8fafc;  --icon-fg: #334155; }

[class^="icon-"],
[class*=" icon-"] {
  background: var(--icon-bg);
  color: var(--icon-fg);
}

/* Dark Mode Icon Overrides */
body.dark .icon-blue   { --icon-bg: rgba(29, 78, 216, 0.15);   --icon-fg: #60a5fa; }
body.dark .icon-orange { --icon-bg: rgba(194, 65, 12, 0.15);   --icon-fg: #fb923c; }
body.dark .icon-pink   { --icon-bg: rgba(190, 24, 93, 0.15);   --icon-fg: #f472b6; }
body.dark .icon-green  { --icon-bg: rgba(21, 128, 61, 0.15);   --icon-fg: #4ade80; }
body.dark .icon-purple { --icon-bg: rgba(126, 34, 206, 0.15);  --icon-fg: #c084fc; }
body.dark .icon-cyan   { --icon-bg: rgba(14, 116, 144, 0.15);  --icon-fg: #22d3ee; }
body.dark .icon-teal   { --icon-bg: rgba(15, 118, 110, 0.15);  --icon-fg: #2dd4bf; }
body.dark .icon-slate  { --icon-bg: rgba(51, 65, 85, 0.15);    --icon-fg: #94a3b8; }
```

Visual values unchanged — same colors, just structured as properties.

**Commit:** `refactor(css): convert icon color pairs to component-scoped custom properties`

---

## Commit 2: Calendar Pill Color System + Dark Mode Fix

**Files:** `variables.css`, `theme.css`, `calendar.css`

### Step 1 — New tokens in `variables.css` (after `--primary-tint` line)

```css
    --accent-rose: #9d174d;
    --accent-rose-light: #fce7f3;
    --accent-event: #5b21b6;
    --accent-event-light: #ede9fe;
```

### Step 2 — Dark overrides in `theme.css` `body.dark {}` block

```css
    /* Accent tokens — dark mode */
    --accent-rose: #f9a8d4;
    --accent-rose-light: rgba(157, 23, 77, 0.12);
    --accent-event: #c4b5fd;
    --accent-event-light: rgba(91, 33, 182, 0.12);
    /* Semantic dark fg overrides (used as pill text colors) */
    --info-dark: #93c5fd;
    --success-dark: #86efac;
    --warning-dark: #fde68a;
```

Note: `--info-dark`, `--success-dark`, `--warning-dark` have no dark mode overrides today — they're light-mode deep colors (#1e40af, #166534, #92400e) that become invisible on dark tinted backgrounds. This adds those missing dark fg values.

### Step 3 — Calendar pill rules in `calendar.css`

**Month-view pills (replace existing `.cal-pill--*` rules):**

```css
.cal-pill--task      { background: var(--info-light);         color: var(--info-dark); }
.cal-pill--habit     { background: var(--success-light);      color: var(--success-dark); }
.cal-pill--event     { background: var(--accent-event-light); color: var(--accent-event); }
.cal-pill--reminder  { background: var(--warning-light);      color: var(--warning-dark); }
.cal-pill--goal      { background: var(--accent-rose-light);  color: var(--accent-rose); }
.cal-pill--campaign  { background: color-mix(in srgb, var(--info) 10%, transparent); color: var(--info); }
.cal-pill--more      { background: var(--hover, #eee);        color: var(--muted, #666); }
```

**Week-view event cards (replace existing `.cal-wk-event--*` rules):**

```css
.cal-wk-event--task      { background: var(--info-light); }
.cal-wk-event--habit     { background: var(--success-light); }
.cal-wk-event--event     { background: var(--accent-event-light); }
.cal-wk-event--reminder  { background: var(--warning-light); }
.cal-wk-event--goal      { background: var(--accent-rose-light); }
.cal-wk-event--campaign  { background: color-mix(in srgb, var(--info) 10%, transparent); }
.cal-wk-event--project   { background: color-mix(in srgb, var(--success) 8%, transparent); }
.cal-wk-event--skill     { background: var(--accent-event-light); }
.cal-wk-event--programme { background: var(--success-light); }
```

No `body.dark` block needed in calendar.css — all backgrounds now use tokens that are overridden at the token level in `theme.css`.

**Commit:** `fix(css): tokenize calendar pill colors and add missing dark mode overrides`

---

## Commit 3: Font Weight & Tracking Tokens

**Files:** `variables.css` + 8 component CSS files

### Step 1 — New tokens in `variables.css`

After `--font-weight-bold: 700;`:
```css
    --font-weight-black: 800;
```

After `--tracking-3xl: -0.2ch;` (add with comment):
```css
    /* Positive tracking — expanded labels, badges, caps */
    --tracking-wide: 0.05em;
    --tracking-wider: 0.08em;
    --tracking-widest: 0.1em;
```

### Step 2 — `font-weight: 800` → `var(--font-weight-black)` substitutions

Convert semantic reusable patterns only. Skip one-offs (logo, lesson title, hero display).

| File | Selector | Convert? |
|------|----------|----------|
| `main.css` | `.badge-unit` | yes |
| `main.css` | `.status-badge` | yes |
| `main.css` | `.you-name` | yes |
| `main.css` | `.you-stat-value` | yes |
| `main.css` | `.explore-title` | skip (one-off display) |
| `main.css` | `.you-avatar-letter` | skip (fixed px size, intentional) |
| `accounts.css` | `.profile-hero-name` | yes |
| `accounts.css` | avatar initials | yes |
| `accounts.css` | `.formation-level-number` | yes |
| `bible.css` | `.bible-badge-version` | yes |
| `dashboard.css` | `.dash-stat-value` | yes |
| `dashboard.css` | `.dash-streak-val` | yes |
| `navbar.css` | avatar initials | yes |
| `navbar.css` | `.logo-container` | skip (brand one-off) |
| `governance.css` | `.gov-version-num` | yes |
| `community.css` | `.community-name` | yes |
| `community.css` | `.formation-level` | yes |
| `community.css` | badge | yes |
| `learn.css` | `.lesson-title` | skip (display title) |

### Step 3 — Hardcoded letter-spacing → token substitutions

| File | Selector / context | Value | Token |
|------|-------------------|-------|-------|
| `main.css` | `.label-caps` | `0.08em` | `--tracking-wider` |
| `main.css` | `.badge-unit` | `0.05em` | `--tracking-wide` |
| `main.css` | `.status-badge` | `0.05em` | `--tracking-wide` |
| `main.css` | `.you-stat-label` | `0.05em` | `--tracking-wide` |
| `bible.css` | `.bible-badge-version` | `0.05em` | `--tracking-wide` |
| `dashboard.css` | `.dash-hero__label` | `0.1em` | `--tracking-widest` |
| `dashboard.css` | `.dash-stat-label` | `0.05em` | `--tracking-wide` |
| `accounts.css` | `.settings-section-header` | `0.08em` | `--tracking-wider` |
| `learn.css` | programme meta | `0.05em` | `--tracking-wide` |
| `governance.css` | `.gov-attrs dt` | `0.05em` | `--tracking-wide` |
| `app-drawer.css` | `.launcher-label` | `0.05em` | `--tracking-wide` |
| `community.css` | community tier | `0.05em` | `--tracking-wide` |
| `community.css` | stat label | `0.08em` | `--tracking-wider` |

**Leave unconverted:** calendar `.cal-dow`/`.cal-wk-header__dow` (`.06em`, in-between values), `.cal-wk-event__time` (`.04em`), navbar logo (`-0.02em`), bible reading text (`-0.01em`).

**Commit:** `feat(css): add --font-weight-black and positive tracking tokens, apply to badge/label patterns`

---

## Files Modified

| Commit | Files |
|--------|-------|
| 1 (icon tokens) | app-drawer.css |
| 2 (calendar pills) | variables.css, theme.css, calendar.css |
| 3 (font tokens) | variables.css, main.css, accounts.css, bible.css, dashboard.css, navbar.css, governance.css, community.css, learn.css, app-drawer.css |
