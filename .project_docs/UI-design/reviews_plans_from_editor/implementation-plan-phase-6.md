# Implementation Plan — ICS Web UI Phase 6 (Master-Detail Refinement)

This phase focuses on refining the Master-Detail pattern used in the **Governance** and **Records** apps to ensure a world-class administrative experience for Level 3+ stewards.

## 1. Global Master-Detail Enhancements
- [ ] **Standardize `ws-list-panel`:**
    - Refine list item typography and spacing.
    - Implement a standardized "Editorial" search input.
    - Add "Branch" indicators (e.g., Library vs Mandate vs Keys) with distinct iconography.
- [ ] **Standardize `ws-detail-panel`:**
    - Improve the "Editorial" readability (serif headings, wide line-height).
    - Implement a metadata sidebar for record attributes (Signatory, Version, Status).
    - Refine empty states with helpful guidance.

## 2. Governance App Refinement
- [ ] **Main Shell (`governance.html`):**
    - Refine the Branch Nav header to look like a premium registry.
    - Add a "Create" floating action or header action for Level 5 users.
- [ ] **List Views (`_library_list.html`, `_mandate_list.html`):**
    - Move horizontal tabs into a more compact sub-toolbar.
    - Ensure active state persistence in the list when viewing details.
- [ ] **Detail Views (`_library_detail.html`, `_mandate_detail.html`):**
    - Layout: Main content (8 cols) + Metadata sidebar (4 cols) on wide screens.
    - Refine property attributes (HRS) visualization.
    - Improve visibility of linked record connections.

## 3. Records App Master-Detail (Advanced)
- [ ] **Relationship Management:**
    - If a record is being linked, use the Master-Detail pattern to browse potential target records while keeping the source record visible.
- [ ] **Search Results:**
    - Refine the global search master-detail view for record exploration.

## 4. Visual Excellence (Phase 6 Polish)
- [ ] **Transitions:** Ensure HTMX transitions between records in the list and detail panels are smooth and state-aware.
- [ ] **Typography:** Solidify use of *Playfair Display* for governing titles and *Inter* for administrative metadata.

---

### Progress Tracking
- **Phase 6.1: Governance Shell & Nav** [ ]
- **Phase 6.2: Library & Mandate List/Detail** [ ]
- **Phase 6.3: Metadata Sidebar Implementation** [ ]
- **Phase 6.4: Records Relationship UI** [ ]
