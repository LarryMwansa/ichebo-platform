# Activity App UI Improvement Plan

Following the **ICS UI Audit & Standardization Plan** and incorporating patterns established in the Bible UI refactor, here is the assessment and roadmap for the Activity App.

## 1. Visual & Component Audit

| Component | Current State | Target Standardization |
| :--- | :--- | :--- |
| **Activity Header** | Custom `.activity-header` with inline styles. | Merge with contextual top-bar or use standardized `.section-header` padding. |
| **Activity Items** | Uses `list-item` but adds custom `.activity-item` overrides. | Strictly adhere to `.list-item` from `main.css`. |
| **Status Labels** | Custom `.activity-type-tag` with hardcoded font sizes. | Use `.badge-unit` or `.status-badge` classes. |
| **Semantic Colors** | Hardcoded hex codes (`#ef4444`, `#10b981`). | Use `--danger`, `--success`, and `--info` tokens. |
| **Group Labels** | Custom `.activity-group-label`. | Use `.label-caps` for consistent metadata headers. |
| **Type Filter** | Pill-style links. | Standardize as `chip` components, matching Bible search UI. |

## 2. Structural Improvements

### Transition to Bottom Sheets
The current creation flow swaps a form into an inline panel. To achieve a "Mobile-First App" feel:
- **New Activity**: Trigger `window.ICSDrawer.open()` via HTMX, loading `create_form.html` into the bottom sheet.
- **Edit Activity**: Move editing logic to the drawer as well, preventing layout shifts in the main list.

### Contextual Top Bar
Refactor `my_activities.html` to leverage the `navbar.css` logic, displaying "My Activities" in the top bar with the "Add" button as a primary contextual action.

## 3. Recommended Implementation Steps

### Step 1: CSS Refactor
- Update `static/css/activity.css` to remove all hex codes.
- Map `.activity-type-pill` to standardized chip styles.
- Delete redundant spacing logic in favor of `--space-s`, `--space-m`, etc.

### Step 2: Template Refactor
- **`activity_card.html`**: Replace inline styles and custom tags with `.badge-unit` and `.list-item__meta`.
- **`my_activities.html`**: Use `.label-caps` for "Overdue", "Due Today", etc.
- **`create_form.html` & `edit_form.html`**: Ensure inputs use `.form-input-touch` and buttons use `.btn-touch`.

### Step 3: Logic & Connectivity
- Clean up `views.py` to remove hardcoded HTML strings, moving them into a dedicated `_completed_item.html` partial or similar.
- Update HTMX targets to point to `#drawerContent` for creation and editing.

### Step 4: Refined Information Density
- Use the 8px grid to ensure list items are exactly `64px` or `72px` tall, providing a predictable rhythm.
- Truncate long titles but keep metadata (pathway, date) visible in a secondary gray color.

---

> [!TIP]
> By moving the **Creation Form** to the **Bottom Sheet**, we free up the screen for content and align with the most common pattern in modern productivity apps (like Things 3 or Todoist).
