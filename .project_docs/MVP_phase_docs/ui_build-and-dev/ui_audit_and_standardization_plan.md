# ICS UI Audit & Standardization Plan

## 1. Executive Summary: The "App" Paradigm
The ICS platform is not a marketing website; it's a deep, highly functional **application** representing the Kingdom Governance System (KGS). 
The current UI possesses a solid CSS foundation (tokens, variables), but to transition into a true **Mobile-First App** experience, we must prioritize **information density, touch acoustics (tap targets), and state clarity.**

This audit outlines a standardized UI framework devoid of generic styling ("AI slop") and deeply focused on the project's complex data requirements—handling dense hierarchies, roles, records, and curriculums elegantly on small screens.

---

## 2. Structural & Layout Foundation

### The 8px Grid System
For a functional web app, strict predictability is better than fluid marketing scales.
- **Action:** Transition from fully fluid padding spacing (`clamp()`) to a strict **8px base grid** (8px, 16px, 24px, 32px, 48px). This ensures components snap together predictably when stacking on mobile.
- **Mobile Margins:** Standardize a strict `16px` left/right safe area for all mobile screens.

### The Application Shell
- **Bottom Navigation:** Ensure the `bottom_bar.css` is strictly adhered to for primary app switching (Home, Activity, Governance, Learn). Hide on desktop.
- **Contextual Top Bar:** The top bar (`navbar.css`) must act as the "View Header". Instead of a generic logo on every sub-page, it should display the current context (e.g., `< Back` | `Editing Policy Name` | `Save`).
- **Modals vs. Bottom Sheets:** Standardize creation flows (like "New Journal Entry" or "New Task"). On desktop: Modal overlays. On mobile: **Bottom Sheets** (slide-up from the bottom) so users don't have to reach the top of the screen to close/save.

---

## 3. Typography & Information Density

The KGS platform involves complex documents, statuses, and hierarchical structures. The font scale must support dense information without feeling cluttered.

- **Readability over Flair:** Use the system font stack (`Roboto`, `Inter`, `system-ui`) with strict weights. 
- **Typography Scale Standard:**
  - `Display / Title`: For main screen headers only.
  - `Subtitle (16px/18px, Medium)`: For grouping sections.
  - `Body (14px/16px, Regular, 1.5 line-height)`: Standard reading text.
  - `Caption (12px, Regular)`: For metadata (timestamps, "Created by", status labels).
- **Contrast & Hierarchy:** Use color (`var(--muted)`) and weight (`500` vs `400`) instead of just size to establish hierarchy in dense lists. 

---

## 4. Component Standardization (KGS Needs)

### 1. The "List Item" Pattern
Governance records, habits, and tasks cannot always be "Cards" on mobile, as cards waste horizontal space.
- **Standard:** Use a dense `List Item` component. 
  - Left slot: Icon or Status Badge.
  - Center slot: Title (truncate line 1) + Metadata underneath (Caption).
  - Right slot: Action (Chevron right, or toggle).
  - *Example:* Dashboard Recent activity and Record lists should use edge-to-edge list items separated by a subtle 1px border.

### 2. State & Status Badges
Governance uses complex statuses (e.g., `Draft`, `Enacted`, `Superseded`). 
- **Standard:** Create a unified `StatusBadge` CSS component. 
  - Small, high-contrast, bold, uppercase caps (10px or 11px font).
  - Tied to semantic contextual colors: Red (Danger/Overdue), Blue (Active/In Progress), Green (Complete/Enacted), Gray (Draft/Archived).

### 3. Touch Targets & Forms
- **Tap Acoustics:** All clickable elements (buttons, list items, dropdowns) must have a minimum height of `44px` to `48px` to pass mobile accessibility standards.
- **Form Inputs:** Ensure inputs have `font-size: 16px` minimum. *Why?* iOS Safari automatically zooms in on inputs if the text size is smaller than 16px, ruining the mobile layout.

---

## 5. View-Specific Implementation Plans

### 1. Dashboard (The Digest)
- **Problem:** Currently relies heavily on isolated "widgets" which can feel disjointed on mobile.
- **Standardization:** Group related metrics into tight horizontal scrollable areas (e.g., habit streaks), and use vertical dense lists for action items. Reduce structural borders and use subtle background grouping instead of heavy card shadows.

### 2. Governance App (Hierarchical Data)
- **Problem:** Displaying nodes, branches, and laws. 
- **Standardization:** Implement an "Accordion" or "Drill-down" list pattern. Instead of massive tables (which break on mobile), use stacked list items where tapping navigates a level deeper, replacing the viewport smoothly.

### 3. Learn App (Curriculum)
- **Problem:** Course material tracking.
- **Standardization:** Use step-progress indicators. A dedicated sticky bottom bar during a "Lesson View" offering `Previous` and `Next` buttons, keeping navigation in the thumb zone.

---

## 6. Actionable Next Steps

If approved, the engineering implementation will proceed in this order:
1.  **Token Refactor:** Standardize `variables.css` to an 8px grid and lock down the 5 core typographical sizes.
2.  **Component Library:** Build/Refine `.list-item`, `.status-badge`, and `.btn-touch` in `global.css`/`main.css`.
3.  **Layout Update:** Adjust `base.html` and the navbar/bottom navigation to adhere strictly to the "App Shell" patterns.
4.  **App-by-App Rollout:** Systematically apply these components to `dashboard`, `records`, `governance`, and `learn`.
