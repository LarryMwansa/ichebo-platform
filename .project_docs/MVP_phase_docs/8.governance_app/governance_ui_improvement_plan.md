# Governance App UI Improvement Plan

Following the **ICS UI Audit & Standardization Plan**, the Governance app must transition from a "Document Library" feel to a "Hierarchical App" experience.

## 1. Visual & Component Audit

| Component | Current State | Target Standardization |
| :--- | :--- | :--- |
| **Branch Nav (Tabs)** | Custom `.gov-tab-row` with purple accents. | Standardize with Activity App; remove persistent tabs or refactor to 3-column grid. |
| **Record List** | Uses `.list-item` but with custom inline styles for tags. | Use standardized `.badge-unit` for tags and statuses. |
| **Category Selection** | Wrapping flexbox pills. | Use the **3-column Wrapping Grid** refactor for high-density navigation. |
| **Status Indicators** | Hardcoded colors and custom classes. | Map to semantic tokens: `Draft` (Gray), `Enacted` (Green), `Locked` (Apostolic Blue). |
| **Detail Headers** | Nested `H2` and custom back links. | Use `.label-caps` for contextual parent path and `.title-large` for records. |

## 2. Structural Improvements

### The "Drill-Down" Pattern
To handle deep hierarchies (Prophet's Handbook -> Categories -> Records):
- **Smooth Viewport Replacement**: Continue using HTMX but ensures that the headers follow a strict hierarchy (`Parent Category > Current Record`).
- **Mobile Density**: Ensure that the `Record List` items are edge-to-edge on mobile, removing heavy borders and using subtle background colors to group data.

### Standardized Detail Panels
Replace the custom `.gov-panel` and `.gov-attrs` with a standardized "Attribute List" component that uses the 8px grid.

## 3. Recommended Implementation Steps

### Step 1: CSS Refactor
- Update `static/css/governance.css` to remove all hex codes in favor of CSS variables.
- Standardize `.gov-type-pill` to match the chip pattern established in Bible and Activity apps.
- Refine the `.gov-tab-row` to match the refined Activity shell.

### Step 2: List Refactor
- Update `_library_list.html`, `_mandate_list.html`, and `_keys_list.html` to use the standardized `.list-item` group.
- Implement the **3-column wrapping grid** for the category filters.

### Step 3: Density & Hierarchy
- Refactor the record detail views (`_library_detail.html`, etc.) to use `.label-caps` for metadata sections.
- Ensure the `Linked Records` and `Version History` lists use the dense `list-item` pattern instead of custom list structures.

### Step 4: Component Unification
- Unify `_record_form.html` with the standard form patterns.
- Ensure all "New" and "Edit" actions trigger the **Bottom Sheet** (drawer) where appropriate, especially for adding Links or Keys.

---

> [!TIP]
> Use `.label-caps` for parent indicators (e.g., "REFERENCE LIBRARY > CORE TENETS") to provide constant orientation without cluttering the screen.
