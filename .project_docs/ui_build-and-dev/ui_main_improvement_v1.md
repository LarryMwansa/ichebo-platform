# UI Improvement Plan v1: Shell Standardization & App Shell Transition

This plan builds on the recommendations in `shell_navigation_assessment.md` and `ICS-UI-audit-&-standardization-plan.md` to transition the ICS platform into a high-density, mobile-first application shell.

## 1. Contextual Navigation (The "View Header")
Currently, the top navbar is static. We will refactor it to act as a "View Header" that adaptively shows relevant context.

- [x] **Refactor `base.html`**: Wrap the navbar in a `{% block navbar %}` to allow full overrides.
- [x] **Standard Navbar (`_navbar.html`)**: Add a `{% block navbar_content %}` inside the `.navbar` container.
- [x] **Contextual Navbar Pattern**: Create a pattern for detail views:
  - Left: Back button (using `arrow_back` icon).
  - Center: Truncated Title (e.g., "Editing Policy Name").
  - Right: Actions (e.g., Save, More).
- [x] **Implement transition**: Start with `records` and `governance` detail views.

## 2. Information Density & Component Unification
Standardize lists across all apps to maximize screen utility.

- [x] **Unify Cards to List Items**:
  - Replace `.explore-card` in `Explore` and `You` apps with a standardized `.list-item` (high-density list).
  - Consistently use `.list-group` to wrap related items.
- [x] **Refine `badge-unit`**:
  - Implement full semantic color mapping (Primary, Success, Warning, Danger, Muted).
  - Apply to `activity` and `records` status indicators.
- [x] **Touch Targets**:
  - Ensure all action buttons (edit, delete, complete) meet the 48px minimum tap target requirement via the `.btn-touch` class.

## 3. FAB (Floating Action Button) Context-Awareness
Ensure the creation flow is seamless across all primary surfaces.

- [x] **Update `Home` context**: Default to Quick Journal Entry.
- [x] **Update `Explore` context**: Offer Quick Create for Governance or Records.
- [x] **Update `You` context**: Quick Log Activity or Update Status.
- [x] **Refine `navbar.js`**: Expand the path-matching logic for current `pathname`.

## 4. App-by-App Rollout (Current Priorities)
- [x] **Records**: Standardize record lists and detail headers.
- [x] **Activity**: Unify list layout with the dashboard's "Action Items" pattern.
- [x] **Explore/You**: Finalize the layout and transition cards to standardized list items.
- [x] **Learn**: Adjust programme cards to use the same vertical grid as activities.

## 5. Next Phase: Global Polish & Micro-interactions
- [ ] **Tab Reconciliation**: Unify the `dashboard-tabs.js` pills with the global bottom navigation.
- [ ] **State Persistence**: Ensure the drawer state persists across quick-create transitions.
- [ ] **Drawer Ergonomics**: Add pull-to-dismiss gesture for the app drawer on mobile.
- [ ] **Accessibility Audit**: Ensure all icons have proper `aria-label` and `label-caps` use semantic `<label>`.
