# Learning App UI Improvement Plan

Following the **ICS UI Audit & Standardization Plan**, the Learning App (ICS Learn) must focus on pedagogical clarity, progression tracking, and seamless authorship workflows.

## 1. Visual & Component Audit

| Component | Current State | Target Standardization |
| :--- | :--- | :--- |
| **Learning Navigation** | Sticky `learn-tab-row`. | Remove top tabs. Use breadcrumbs and section headings within the content area. |
| **Enrolments** | `enrolment-card` with multiple buttons. | Migrate to high-density `.list-item` groups with integrated progress bars. |
| **Programme Cards** | Custom `programme-card` with shadows. | Standardize to high-density cards using design tokens and `.badge-unit` for levels. |
| **Pathway Banner** | Full-width colored banner. | Standardize to a subtle breadcrumb or contextual header with a thematic badge. |
| **Lesson Viewer** | Fixed layout. | Implement "Immersive Reading Mode" using drawer context for curriculum navigation. |

## 2. Structural Improvements

### Progression Tracking
- **Integrated Progress**: Progress bars should be unified with the list item layout, potentially as a subtle 4px track at the bottom of the `.list-item`.
- **Status Signal**: Use `.badge-unit--primary` for "In Progress" and `.badge-unit--enacted` (green) for "Certified".

### Programme Catalogue (Storefront)
- Implement the **3-column Wrapping Grid** for filtering programmes by school (e.g., School of Leadership, School of Ministry).
- High-density cards for programmes to allow scanning a large number of courses.

### Immersive Learning (Drawer)
- Use the **Application Drawer** to host the Curriculm/Lesson Tree so the user doesn't have to navigate away from the current lesson to see their progress.

## 3. Recommended Implementation Steps

### Step 1: CSS Refactor
- Update `static/css/learn.css` to remove legacy hex colors and migrate to global tokens.
- Implement the `.programme-card` and `.lesson-item` specifications.

### Step 2: Shell & Home Refactor
- Update `my_learning.html` to use high-density lists.
- Refactor the Pathway banner into a cleaner header.

### Step 3: Catalogue & Detail Refactor
- Implement the Category filters for the Catalogue.
- Update `programme_detail.html` to follow the standardized record/entity pattern (Header + Attributes + Content).

### Step 4: Immersive Lesson Viewer
- Refactor `lesson_viewer.html` to prioritize readability and integrate the curriculum drawer.

---

> [!NOTE]
> Learning is a high-depth activity. Layouts should be centered and distractions (like the navigation tabs) removed to aid focus.
