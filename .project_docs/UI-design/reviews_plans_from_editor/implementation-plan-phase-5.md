# Implementation Plan — ICS Web UI Phase 5 [COMPLETED]

This plan outlines the steps to complete **Phase 5 (Full-page apps)** of the Desktop Workspace UI. The goal is to ensure all remaining apps follow the established `ws-layout--full-page` pattern and maintain the "Apostolic Editorial" aesthetic.

## 1. Activity App Refinement [DONE]
- [x] **My Activities (`my_activities.html`):**
    - Ensure it uses `ws-layout--full-page`.
    - Move filter pills into a `ws-toolbar` component.
    - Standardize the "New Activity" button in the `ws-page-header`.
- [x] **Ministry (`ministry.html`):**
    - Align with `ws-layout--full-page`.
    - Ensure tabs (All / Assigned to Me) and type filters work seamlessly within the workspace toolbar.
- [x] **Calendar View (`calendar_view.html`):**
    - Implement a workspace-native version of the dated list view.
- [x] **Activity Detail (`activity_detail.html`):**
    - Premium workspace detail view implemented.

## 2. Records App Refinement [DONE]
- [x] **My Journal (`my_records.html`):**
    - Verify `ws-layout--full-page` implementation.
    - Ensure "New Entry" opens the right `ws-panel` via HTMX.
    - Standardize toolbar filters.
- [x] **Record Detail (`record_detail.html`):**
    - Created a premium full-page detail view for the workspace.

## 3. Learn App Workspace Experience [DONE]
- [x] **Tabbed Navigation:**
    - Add a `ws_tabs` block to `base_learn.html`.
    - Tabs: `My Learning`, `Catalogue`, `Authorship` (Gate: Level 4+), `Review Queues` (Gate: Level 5).
- [x] **Catalogue (`catalogue.html`):**
    - Align with `ws-layout--full-page`.
    - Use a grid of programme cards.
- [x] **Authorship Dashboard (`authorship.html`):**
    - Workspace-native layout for content creators.
- [x] **Review Queues:**
    - Standardize `review_queue.html` and `induction_review_queue.html` for the workspace.

## 4. Video Live App [DONE]
- [x] **Home & Manage (`home.html`, `manage.html`):**
    - Align with `ws-layout--full-page`.
    - Ensure live player and schedule list look premium on desktop.

## 5. Notifications [DONE]
- [x] **Notifications (`notifications.html`):**
    - Align with `ws-layout--full-page`.
    - Standardized header pattern.

## 6. Global Polish [DONE]
- [x] **Sidebar Sync:** Verified `active_app` context.
- [x] **Top Bar Breadcrumbs:** Standardized `ws_topbar` blocks.
- [x] **HTMX Targets:** Verified `#ws-content` usage.

---

### Progress Tracking
- **Phase 5.1: Activity** [x]
- **Phase 5.2: Records** [x]
- **Phase 5.3: Learn** [x]
- **Phase 5.4: Video Live** [x]
- **Phase 5.5: Notifications** [x]
