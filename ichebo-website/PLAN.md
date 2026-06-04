# ICS Website — Refactor & Fix Plan

Branch: `refactor/code-cleanup-and-fixes`

This document tracks all planned changes identified during the code review. Work through each item in order. Do not skip items or reorder without reason.

---

## Deployment Context

The site is a plain static HTML/CSS/JS site built with Vite and deployed as follows:

1. Built locally: `npm run build` → outputs to `dist/`
2. Copied to server: `cp -r dist/* /home/scepter/ichebo-site/`
3. Nginx serves `/home/scepter/ichebo-site/` as the web root for `ichebo.org`

All files land **flat at the root level** — `training.html`, `find-a-church.html` etc. There are no subdirectories. Therefore **all internal links must use `.html` filenames** — not clean URL paths like `/training/`. Clean URL style links (`/training/`) cause 404s on this server setup unless nginx is specially configured to handle them. The `.html` approach is simpler, explicit, and requires no server workarounds.

---

## Priority 1 — High (Correctness / Production Bugs)

### 1.1 Standardise all internal links to use `.html` filenames

**Problem:** The majority of internal links across all pages use clean URL style paths (`/training/`, `/programme/`, `/contact/` etc.). On this server these cause 404s. The correct form for a flat static deployment is the explicit filename (`training.html`, `programme.html` etc.).

**Conversion rules:**

| Current (broken) | Replace with |
| --- | --- |
| `/` (root only) | `index.html` |
| `/programme/` | `programme.html` |
| `/training/` | `training.html` |
| `/find-a-church/` | `find-a-church.html` |
| `/watch/` | `watch.html` |
| `/platform/` | `platform.html` |
| `/contact/` | `contact.html` |
| `/about/` | `about.html` |
| `/programme/#start` | `programme.html#start` |
| `/programme/#levels` | `programme.html#levels` |
| `/training/#certificate` | `training.html#certificate` |
| `/training/#diploma` | `training.html#diploma` |
| `/training/#degree` | `training.html#degree` |
| `/training/#masters` | `training.html#masters` |
| `/training/#doctorate` | `training.html#doctorate` |
| `/contact/#partner` | `contact.html#partner` |
| `/contact/?ref=xxx` | `contact.html?ref=xxx` |
| `/watch/#series` | `watch.html#series` |
| `/watch/#formation` | `watch.html#formation` |
| `/watch/#notify` | `watch.html#notify` |

**Dead links to remove or resolve separately (no matching HTML file exists):**

- `/start-a-church/` — appears in `index.html` and `platform.html`. Either create `start-a-church.html` or point to `programme.html#start`
- `/find-a-church/pretoria-north/` — no file exists
- `/find-a-church/soweto/` — no file exists
- `/find-a-church/cape-town/` — no file exists
- `/find-a-church/london-southwark/` — no file exists
- `/find-a-church/online-global/` — no file exists
- `/find-a-church/durban/` — no file exists

**Files affected:** All 8 HTML pages — `index.html`, `platform.html`, `programme.html`, `training.html`, `watch.html`, `find-a-church.html`, `contact.html`, `about.html`

**Acceptance:** No internal link uses a trailing-slash clean URL path. Every internal link either uses a `.html` filename or is a same-page `#anchor`. All pages navigate correctly in `npm run preview`.

---

### 1.2 Remove `src/` scaffolding (dead Vite template code)

**Problem:** `src/main.js`, `src/counter.js`, and `src/style.css` are leftover from the default Vite template. They are not imported by any HTML page and serve no purpose. `src/assets/hero.png`, `src/assets/javascript.svg`, and `src/assets/vite.svg` are similarly unused.

**Files to delete:**
- `src/main.js`
- `src/counter.js`
- `src/style.css`
- `src/assets/hero.png`
- `src/assets/javascript.svg`
- `src/assets/vite.svg`

**Acceptance:** The `src/` directory is empty or removed. `npm run build` still completes without errors.

---

## Priority 2 — Medium (Code Quality / Maintainability)

### 2.1 Extract shared CSS into a single stylesheet

**Problem:** Every HTML page contains a full copy of the CSS inside a `<style>` block. This means:
- Any design change must be replicated manually across all 8 pages.
- The browser cannot cache shared styles between page navigations.
- Vite cannot fingerprint/minify CSS it doesn't own.

**Approach:**
1. Create `src/shared.css` and move all common styles into it.
2. Create `src/main.js` (clean, new file) that imports `./shared.css`.
3. Add `<script type="module" src="/src/main.js"></script>` to the `<head>` of every HTML page.
4. Remove the `<style>` block from each page, keeping only page-specific overrides if any exist.

**Files affected:** `index.html`, `platform.html`, `programme.html`, `training.html`, `watch.html`, `find-a-church.html`, `contact.html`, `about.html`

**Acceptance:** All pages share one CSS file. `npm run build` produces a single hashed CSS asset linked from all pages. Visual appearance is unchanged.

---

### 2.2 Extract shared JavaScript into a module

**Problem:** The nav scroll handler, mobile menu open/close logic, and IntersectionObserver for `.fade-up` animations are copy-pasted inside `<script>` tags on every page. A bug fix or enhancement must be applied to every file individually.

**Approach:**
1. Create `src/ui.js` containing the three shared behaviours (scroll nav, mobile menu, fade-up observer).
2. Import `./ui.js` from `src/main.js` (created in step 2.1).
3. Remove the inline `<script>` block from each HTML page.

**Files affected:** Same 8 HTML pages as 2.1.

**Acceptance:** All shared JS lives in one module. `npm run build` bundles and hashes it. Behaviour is unchanged in the browser.

---

### 2.3 Add `{ passive: true }` to the scroll event listener

**Problem:** The scroll event listener does not declare itself passive. This can cause layout jank on mobile because the browser must wait to see if `preventDefault()` is called before it can scroll.

**Change:**
```js
// Before
window.addEventListener('scroll', () => { ... });

// After
window.addEventListener('scroll', () => { ... }, { passive: true });
```

**Note:** This will be done inside `src/ui.js` as part of item 2.2.

**Acceptance:** Scroll listener has `{ passive: true }` flag in `src/ui.js`.

---

## Priority 3 — Low (Housekeeping)

### 3.1 Add `dist/` to `.gitignore`

**Problem:** The `dist/` build output directory is committed to the repository. Build artifacts should not be tracked in git — the server deploys by copying from `dist/` after a local build.

**Change:** Add `dist/` to `.gitignore`, then remove it from git tracking:

```bash
git rm -r --cached dist/
```

**Acceptance:** `dist/` is listed in `.gitignore` and no longer appears in `git status`.

---

### 3.2 Replace placeholder social links in the footer

**Problem:** The footer's YouTube, Facebook, and WhatsApp social links all point to `href="#"`. These are non-functional.

**Options (decide before implementing):**
- Replace with real social profile URLs when available.
- Remove the social link row entirely until URLs are ready.

**Files affected:** All pages that contain the footer with social links.

**Acceptance:** No footer link points to `href="#"`.

---

## Order of Execution

```
1.1 → 1.2 → 2.1 → 2.2 → 2.3 → 3.1 → 3.2
```

Complete each item fully before moving to the next. Run `npm run build` after each step to confirm no regressions.

---

## Definition of Done

- [ ] All items above are marked complete
- [ ] `npm run build` succeeds with no errors or warnings
- [ ] All pages navigate correctly in the browser (`npm run preview`)
- [ ] No internal link uses a trailing-slash clean URL path
- [ ] No dead files in `src/`
- [ ] `dist/` is not tracked by git
- [ ] PR is raised from `refactor/code-cleanup-and-fixes` into `main`
