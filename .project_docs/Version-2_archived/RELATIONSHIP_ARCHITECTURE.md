# ICS Relationship Architecture Overhaul

This document outlines the implementation of the unified linking and relationship management system across the ICS platform (Bible, Activity, Records, and Governance).

## 1. Core Objectives
*   **Establish a Unified Mesh**: Transition from isolated app modules to a traversable relationship graph.
*   **Contextual Intelligence**: Ensure that relationship types and actions are relevant to the user's current domain (Learning, Governance, etc.).
*   **Mobile-First Ergonomics**: Optimize complex linking workflows for 400px mobile devices.
*   **Visual Density**: Provide clear indicators of relationship "depth" within content surfaces (e.g., Bible reader).

## 2. Key Features Implemented

### A. Activity Detail Surface
*   **New Management View**: Created `activity/activity_detail.html`, providing a glassmorphic home for individual activities.
*   **Deep Relationship Traversal**: Integrated the `_linked_records_section.html` partial to allow users to see records related to the activity's primary anchor (e.g., seeing Governance Principles related to a Lesson being tracked).
*   **Status Management**: Unified completion logic with real-time detail-page redirects.

### B. Bible Annotation & Linking
*   **Cross-App Anchoring**: Enabled formal relationships between Bible verses and any record type (Principle, Mandate, Activity).
*   **State-Aware Drawer**: The Bible annotation panel now preserves tab state (e.g., staying on the "Links" tab after creating a link).
*   **Visual Indicators**: Implemented a color-coded indicator system in the Bible reader:
    *   **Purple**: Personal Reflections.
    *   **Light Blue**: Community Insights.
    *   **Green**: Formal Record Links.

### C. Context-Aware Relationship Filtering
*   **Intelligent Dropdowns**: Standardized the relationship creation UI to filter available types based on the source record's family:
    *   **Governance**: `Authorised By`, `Aligns With`, `Has Subject`.
    *   **Learning**: `Part Of`, `Answers`, `Fulfills`.
    *   **Activity**: `Assigned To`, `Completes`, `Tracks`.
*   **Centralized Mapping**: Implemented in `records/template_views.py` via the `RELATIONSHIP_CONTEXTS` dictionary.

### D. Global Relationship Trail (Breadcrumbs)
*   **Spatial Awareness**: Added a "Linked via: [Source]" breadcrumb to detail views in Records, Governance, and Activity.
*   **Navigation Logic**: Updated view logic to pass a `via` parameter through URL parameters, allowing users to "crawl" the mesh and return to their specific point of origin.

## 3. UI/UX Optimizations

### Responsive Linking Modal
*   **Adaptive Layout**: Refactored `_link_modal.html` to switch from a sidebar layout to a stacked layout on screens smaller than 600px.
*   **Search Ergonomics**: Moved filters to the top on mobile to maximize space for results.
*   **Premium Aesthetics**: Added glassmorphic blur, rounded corners (16px), and Material Symbol integration.

### Navigation Chrome Fixes
*   **Double-Nav Resolution**: Fixed a critical bug where HTMX OOB swaps caused nested navigation bars. Implemented conditional OOB logic in `record_detail.html` and `activity_detail.html`.
*   **Smart Back Buttons**: The top-navbar back arrow now intelligently uses the `via` parameter to return users to the referring record.

## 4. Technical Architecture
*   **Model Core**: Built upon `records.models.Relationship` which targets `from_record`, `to_record`, and `bible_verse`.
*   **HTMX Integration**: 
    *   Used `hx-swap-oob` for real-time indicator updates.
    *   Used `HX-Redirect` and `HX-Push-Url` for seamless navigation without full page reloads.
*   **DRY Partials**: Reused `_link_modal.html` and `_linked_records_section.html` across all four major app domains.

## 5. Next Steps / Future Considerations
*   **AI Suggestions**: (Placeholder UI added) Integrate Paraclete AI to suggest cross-references based on symbolic patterns.
*   **Bulk Linking**: Allow selecting multiple records at once in the search modal.
*   **Relationship Visualizer**: Consider a graph-based visualization for extremely dense relationship clusters.

---
*Created: April 22, 2026*
*Status: Phase 4 Complete*
