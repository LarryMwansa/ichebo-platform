# Roadmap: ICS Command Shell (v2) Expansion

Following the successful implementation of the core architecture and the Editorial Stage for Governance, this roadmap outlines the strategy for retrofitting the remaining platform modules into the "Apostolic Editorial" workspace.

## Phase 1: Institutional Foundation (Immediate)
*Goal: Bring the entry points and personal stewardship modules into the new workspace.*

- [ ] **Steward Dashboard (`dashboard`)**:
    - Retrofit `index.html` to use `workspace_shell.html`.
    - Implement **High-Density Stat Cards** using the `Stone` aesthetic.
    - Add a "Mission Control" summary of pending acts and community activity.
- [ ] **Identity & Settings (`accounts`)**:
    - Standardize Profile and Settings pages.
    - Ensure the "Level Badge" and "Stewardship Attributes" are editable within the Shell.

## Phase 2: Feature Retrofitting (Weeks 1–2)
*Goal: Migrate specialized apps into the Stage-centric workflow.*

- [ ] **Bible Reader (`bible`)**:
    - **Stage Mode**: Full-screen reading environment with Playfair Display authority.
    - **Sidecar Mode**: Integration into the `Options Bar` for cross-referencing while drafting governance acts.
- [ ] **Records & Journal (`records`)**:
    - Unified list views for personal and official records.
    - Enable the **Editorial Stage** for all journal entries.
- [ ] **Community Management (`community`)**:
    - Migrate the "Formation Pipeline" to the Stone Stage.
    - Implement management tools in the **Context Bar** for coordinators.

## Phase 3: Formation & Activity (Weeks 2–3)
*Goal: Finalize the daily operational modules.*

- [ ] **Learning & Formation (`learn`)**:
    - Retrofit programme views as "Editorial Courseware."
    - Use the Context Bar for curriculum navigation and the Stage for training content.
- [ ] **Activity & Tasks (`activity`)**:
    - Task management as a high-density list within the Stage.
    - Status transitions with visual feedback (pulses).

## Phase 4: Command Center Intelligence (Weeks 3–4)
*Goal: Universal tools and systemic polish.*

- [ ] **Universal Search (`⌘+K`)**:
    - Global Command Palette for jumping between apps, records, and people.
- [ ] **Relationship Graph**:
    - Visualizing the KGS data contract (Relationships) within the Options Bar.
- [ ] **Systemic Watermarks**:
    - Applying section-specific ghost watermarks across all apps to reinforce the "Institutional" feel.

---

## Technical Standards for Retrofitting
1.  **Template Inheritance**: All pages must extend `workspace_shell.html`.
2.  **Context bar**: Must use the `context_content` block for sub-navigation.
3.  **Options Bar**: Must use the `ws_options` block for metadata and secondary tools.
4.  **Ghost Watermarks**: Every app must define a `watermark` block (e.g., `{% block watermark %}BIBLE{% endblock %}`).
5.  **HTMX Everywhere**: Use `hx-boost="true"` for shell navigation to ensure smooth transitions between modules.
