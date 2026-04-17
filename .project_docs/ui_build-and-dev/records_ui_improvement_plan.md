# Records App UI Improvement Plan

Following the **ICS UI Audit & Standardization Plan**, the Records app (Personal Journal) must prioritize speed of entry and high-density information display.

## 1. Visual & Component Audit

| Component | Current State | Target Standardization |
| :--- | :--- | :--- |
| **Journal Filters (Tabs)** | Pill-shaped tabs in a row. | Use the **3-column Wrapping Grid** for journal categories. |
| **Entry List** | `.records-grid` using cards with shadows. | Use standardized `.list-item` group for high-density vertical scanning. |
| **Record Creation** | Inline panel (`#record-create-panel`). | Use the **Application Drawer** (`window.ICSDrawer.open()`) for all entries. |
| **Type Badges** | Custom colors and classes. | Map to standardized `.badge-unit` with semantic colors (e.g., Prayer=Red, Dream=Purple). |
| **Header** | Redundant `records-tab-row`. | Remove redundant top-level tabs; standardise header with `.label-caps`. |

## 2. Structural Improvements

### Fast-Track Entry (Quick Log)
- **Primary Action**: A prominent, sticky action button (or FAB) to "Drop a Note" or "Log Entry" that immediately triggers the `ICSDrawer`.
- **Keyboard Optimization**: Ensure the form fields in the drawer autofocus for instant typing.

### List Density Refactor
- Transition from cards to a clean **List Item Group**.
- **Metadata**: Time and Type should be clearly separated using the `.list-item__meta` row.
- **Dynamic Previews**: Show a 2-line preview of the journal content to maximize information per screen.

## 3. Recommended Implementation Steps

### Step 1: CSS Refactor
- Update `static/css/records.css` to use global design tokens and remove legacy card shadows.
- Define a "Sticky FAB" or standardized Header Action for "New Entry".

### Step 2: Filter & Header Refactor
- Update `my_records.html` to implement the grid categories.
- Remove redundant `base_records.html` navigation.

### Step 3: Drawer Migration
- Refactor `htmx_create` and `htmx_edit` views/templates to return partials designed for the drawer context.
- Update UI triggers to use `window.ICSDrawer.open()`.

### Step 4: List Component Standardization
- Refactor `record_list.html` and `record_card.html` to follow the `.list-item` specification.

---

> [!TIP]
> Use `.badge-unit--primary` for high-importance journals (e.g., Dreams) to make them stand out in a long chronological list.
