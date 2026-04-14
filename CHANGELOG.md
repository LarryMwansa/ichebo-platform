# Changelog

All notable changes to the ICS (Integrated Community System) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

#### Dashboard UI Improvements (2026-04-13)
- **Scrollable pill tabs on dashboard home** — Overview, Governance, Calendar, Records tabs with horizontal scroll
- **Dashboard tab switching** — Smooth fade-in animations between tab content panes
- **Tab stylesheet** (`static/css/dashboard-tabs.css`) — Complete styling for scrollable pills, active states, animations
- **Tab JavaScript** (`static/js/dashboard-tabs.js`) — Tab click handlers, scroll detection, responsive behavior

#### Dashboard Drawer Refactor (2026-04-13)
- **Context-aware drawer pattern** — Drawer header and content now use template blocks (`{% block drawer_title %}`, `{% block drawer_content %}`)
- **Drawer API** — `window.ICSDrawer.open()` and `window.ICSDrawer.close()` for programmatic control
- **Drawer activation per-page** — Pages/sections add their own drawer triggers instead of global button

#### Bottom Navigation Simplification (2026-04-13)
- **Unified app launcher** — Bottom nav now shows 5 primary apps (Home, Bible, Activity, Learn, Community)
- **Removed redundant drawer button** — App launcher no longer in drawer, only in bottom nav
- **Removed drawer handle** — Swipe-up handle removed; drawer activation is now contextual per-page

#### Material Design Icons (2026-04-13)
- **Material Symbols (M3) integration** — Added Google Fonts Material Symbols Outlined CDN to all templates
- **Icon replacements across UI:**
  - Bottom nav: `home`, `auto_stories`, `check_circle`, `school`, `group`
  - Navbar: `notifications` (bell), `more_vert` (options menu)
  - Dashboard tabs: `dashboard`, `gavel`, `calendar_month`, `description`
  - Drawer: `person`, `settings`
- **Material Symbols CSS** — Base styles with font variation settings (FILL, wght, GRAD, opsz)
- **Icon styling** — Proper sizing, transitions, hover states across all UI elements

#### Bible Reader UI Overhaul (2026-04-13)
- **Full-screen chapter picker** (`/bible/pick/`) — Immersive cascading book/chapter/verse selector (no global chrome)
- **Real-time search page** (`/bible/search/`) — HTMX-powered verse search with sticky input and instant results
- **Refactored topbar** — Linear layout with passage chip + 3 action buttons (versions, search, settings)
- **Sticky navigator strip** — Fixed above bottom bar with prev/chapter/next buttons
- **Synchronized scroll hide behavior** — Topbar + nav strip + bottom bar hide together on scroll down, reappear on scroll up
- **Drawer integration for notes** — Verse taps populate and open the context drawer (replaces annotation overlay)
- **Bible settings drawer** — Settings button opens drawer for font/layout controls
- **Chrome-free base template** (`templates/bible/base_bible_minimal.html`) — Immersive layout for picker and search
- **Scroll watcher JS** (`static/js/bible.js`) — Detects scroll direction, 8px threshold, smooth CSS transitions

#### Bible Search Backend (2026-04-13)
- **`bible_search_view`** — GET endpoint for `/bible/search/` page
- **`htmx_search`** — HTMX endpoint for real-time verse search with 30-verse limit per request
- **Search results partial** (`_search_results.html`) — HTMX-rendered list with book, chapter:verse, and text snippets

#### Bible Picker Backend (2026-04-13)
- **`bible_picker_view`** — GET endpoint for `/bible/pick/` full-screen selector
- **Cascading picker logic** — Step-by-step book → chapter → verse navigation
- **Back URL preservation** — Picker accepts `back` param to return to original reader page

### Changed

#### Dashboard Structure (2026-04-13)
- **Dashboard home now tabbed** — Content organized into 4 tabs instead of single scrolling page
- **Tab placeholders** — Governance, Calendar, Records tabs have placeholder content (ready for future implementation)
- **Better space utilization** — Tabs avoid squashing content, provide dedicated spaces per section

#### Drawer Architecture (2026-04-13)
- **From global app launcher to context panel** — Drawer is now page-specific, not always visible
- **No permanent activation button** — Pages decide when/how to trigger drawer (reduced global UI clutter)
- **Template block pattern** — Supports per-page customization via template inheritance

#### Bottom Navigation (2026-04-13)
- **From 5+center button to 5 apps** — Removed center drawer button, Activity moved to primary nav
- **Center button removed** — Was a 56px circular button; space now free for topbar/bottom bar simplification
- **Handle removed** — Swipe-up handle for drawer no longer in global UI

#### Bible Reader Layout (2026-04-13)
- **Removed annotation overlay** — Fixes mobile scroll conflicts (page was scrolling instead of panel)
- **Removed side-by-side navigator** — Full-screen picker is more immersive and touch-friendly
- **Topbar restructured** — Prev/next moved to sticky nav strip; action buttons moved to right side
- **Translation row removed from reader** — Inline pills removed; versions functionality moved to dedicated page (future)
- **Verse tap target changed** — Now opens drawer instead of overlay panel

#### CSS & Theming (2026-04-13)
- **Bible.css expanded** — Added topbar, nav strip, scroll-hidden styles (+145 lines)
- **Global.css updated** — Added Material Symbols base styles, font variation settings
- **Bottom bar CSS cleaned** — Removed center-btn and drawer-handle styles
- **App drawer CSS simplified** — Removed drawer section/link styles, kept app-grid

#### JavaScript Architecture (2026-04-13)
- **Navbar.js refactored** — Removed drawer button/handle logic, added `window.ICSDrawer` API
- **New bible.js created** — Scroll watcher with passive event listeners, 8px threshold
- **New dashboard-tabs.js created** — Tab switching, scroll detection, responsive behavior

### Fixed

#### Mobile UX (2026-04-13)
- **Annotation overlay scroll bug** — Removed overlay entirely, using drawer instead (fixes iOS/Android scroll conflicts)
- **Bottom bar always visible** — Now hides on scroll, reclaims vertical space for reading
- **Topbar always visible** — Now hides on scroll, maximizes readable area

#### Icon Consistency (2026-04-13)
- **Emoji icons removed** — All emoji replaced with Material Symbols (consistent, professional, scalable)
- **Icon sizing standardized** — All icons use Material Symbols with proper sizing and transitions
- **Icon colors consistent** — Primary color used for interactive icons, muted for inactive

### Deprecated

- **Annotation overlay pattern** — `#bible-annotation-overlay`, `#bible-annotation-panel` still in CSS but no longer used
- **Sheet navigator pattern** (partial) — Book/chapter navigator sheet still in old code but replaced by picker page

### Removed

- **Drawer global button** — `#drawerToggle` removed from bottom nav
- **Drawer swipe-up handle** — `#drawerHandle` removed from base template
- **Drawer global activation** — No longer has a permanent button in chrome
- **Inline translation selector row** — `bible-translation-row` removed from reader (moved to future versions page)
- **Prev/next buttons from topbar** — Moved to sticky navigator strip above bottom bar

### Security

- **HTMX endpoints authenticated** — `@login_required` on all new Bible endpoints
- **Search query validation** — Requires min 2 characters to prevent empty searches
- **Drawer activation per-page** — Reduces attack surface (no global drawer trigger)

### Performance

- **Scroll listener optimized** — Uses `{ passive: true }` for better scroll performance
- **Search debounce** — 300ms debounce on HTMX requests to reduce server load
- **CSS transitions** — Hardware-accelerated transforms for smooth hide/show animations
- **Tab switching animation** — Slide/fade transitions use `transform` and `opacity` (GPU-accelerated)

### Documentation

- **CHANGELOG.md created** — Comprehensive changelog for production tracking
- **Plan file updated** — `/home/mantis/.claude/plans/fizzy-petting-pumpkin.md` documents full architecture
- **Memory files updated** — `bible_ui_vision.md` documents Bible reader vision and requirements

---

## [2026-04-12] — Initial Dashboard & Auth Phase

### Added

- **Dashboard app** — Main landing page with activity summary, reminders, learning progress
- **User authentication** — Login, register, logout via Django auth
- **User profile** — Display name, avatar, competence level, preferred Bible translation
- **User preferences** — Theme preference (light/dark mode), stored in localStorage
- **Tenant system** — Multi-tenant support with user permissions hierarchy
- **Bible reader** (initial) — Basic reader with annotation overlay, side-by-side navigator
- **Drawer system** — Slide-up modal for app launching and overlays
- **Bottom navigation bar** — 5-item primary navigation
- **Navbar** — Logo, notifications bell, theme toggle, profile dropdown, options menu
- **Material Symbols** — Material Icons (partial) for navbar items
- **Activity tracking** — Activity/task models with signals for event logging
- **Learning system** — Courses, lessons, certifications, progress tracking
- **Community management** — Announcements, gatherings, community updates
- **Governance records** — Record storage for governance documents and decisions
- **Calendar app** — Event calendar with gatherings integration

### Technical Stack

- **Backend:** Django 5.2 LTS, DRF, django-htmx, python-decouple
- **Frontend:** HTMX + vanilla JS (IIFE modules), Material Icons (partial)
- **Auth:** Django SessionAuthentication + DRF TokenAuthentication
- **Database:** SQLite (dev), PostgreSQL (prod)
- **CSS:** Custom design system with CSS variables, mobile-first

---

## [Unreleased — Future Enhancements]

### Planned

- **Bible versions page** — Browse/filter Bible translations by language
- **Bible settings drawer** — Font size, family, line spacing controls
- **Notification system** — Real-time notifications with drawer badge
- **Search across all apps** — Global search spanning Bible, records, learning, community
- **Offline support** — Service worker for offline Bible reading (PWA)
- **Dark mode refinements** — Improved dark theme contrast and animations
- **Accessibility audit** — WCAG 2.1 AA compliance review
- **Mobile app** — Native mobile client (React Native or Flutter)
- **API documentation** — OpenAPI/Swagger for all endpoints
- **Admin panel** — Backend admin for managing users, tenants, content
- **Analytics** — Usage tracking and reporting
- **Integration testing** — E2E tests for critical user flows

---

## Version History

### Versioning Scheme

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** — Incompatible API changes, significant new features, major refactors
- **MINOR** — Backward-compatible new features, enhancements
- **PATCH** — Backward-compatible bug fixes, minor improvements

### Current Status

**Latest Release:** TBD (pre-1.0 in active development)  
**Current Branch:** `production_instance`  
**Development Lead:** Larry Mwansa  

---

## How to Use This Changelog

- **For releases:** Copy the [Unreleased] section to a new version header before tagging
- **For commits:** Reference the relevant section (Added, Changed, Fixed, etc.)
- **For documentation:** Link to the CHANGELOG in pull request descriptions
- **For issues:** Link to the CHANGELOG in issue descriptions to show related changes

---

## Contributing

When contributing changes:

1. **Update CHANGELOG.md** — Add your change to the [Unreleased] section
2. **Use proper headings** — Added, Changed, Fixed, Deprecated, Removed, Security, Performance
3. **Include date** — Format: `(YYYY-MM-DD)` after the feature name
4. **Link to commits** — Reference commit hashes for traceability
5. **Explain impact** — Describe why the change matters to users/developers

---

## Contact

- **Project Lead:** Larry Mwansa  
- **Repository:** https://github.com/LarryMwansa/ics  
- **Issues:** Report via GitHub Issues  
- **Documentation:** See `/project_docs/` and `/.project_docs/`

---

*Last Updated: 2026-04-13*  
*Changelog Maintained By: Claude Haiku 4.5*
