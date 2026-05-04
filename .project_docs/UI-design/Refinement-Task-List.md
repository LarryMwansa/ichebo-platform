TargetFile: /home/mantis/projects/ics/.project_docs/UI-design/Refinement-Task-List.md
Overwrite: true
IsArtifact: true
ArtifactMetadata:
  ArtifactType: implementation_plan
  Summary: A detailed task list for the next phase of Apostolic Command Shell refinements, covering grid architecture, navigation, and app-specific improvements.
Description: Created a detailed refinement task list based on the user's observations.
CodeContent: |
  # Apostolic Command Shell: Refinement Task List

  ## Phase 1: Shell & Grid Finesse
  - [ ] **Draggable Widths**: Implement `interact.js` or native JS resizing for Column 2 (Context Bar) and Column 4 (Options Bar).
  - [ ] **State Memory**: Use `localStorage` to remember sidebar widths and add a "Reset to Default" button in Settings.
  - [ ] **Global Nav (Col 1) Overhaul**:
    - [ ] Group icons: (Governance + Web Graph), (Activity + Calendar).
    - [ ] Implement a "More..." vertical overflow menu for low-height screens.
    - [ ] Add text labels to icons on hover/expand to fix accessibility issues.
  - [ ] **Command Palette**:
    - [ ] Add `> Exit Focus Mode` command.
    - [ ] Add `> Toggle Context Bar` and `> Toggle Options Bar`.

  ## Phase 2: Design System Standardization
  - [ ] **Color Sweep**: Replace all `#FFC0CB` (or similar pinks) with `#AF3236` (Institutional Red) in the Activity and Dashboard apps.
  - [ ] **Button Standard**: Retrofit all Context Bar buttons to match the Governance app's sleek, outlined style.
  - [ ] **Typography Audit**: Ensure `Playfair Display` is correctly applied to all Stage headings and that contrast is sufficient in Light/Stone mode.

  ## Phase 3: The Desk (Next Phase)
  - [ ] **Renaming**: Change "Registry Origin" to "Record Family".
  - [ ] **Navigation**: Ensure Record Types in Column 2 open their respective forms/views in the Stage (Column 3).
  - [ ] **Markdown Editor**:
    - [ ] Integrate a floating formatting toolbar.
    - [ ] Implement a "Live Preview" mode similar to Obsidian (Edit/Preview toggle).
    - [ ] Position the toolbar ~100px from the bottom as requested.

  ## Phase 4: App-Specific Repairs
  - [ ] **Dashboard**: 
    - [ ] Fix white text on light backgrounds.
    - [ ] Add Community status card.
    - [ ] Apply the mobile-style gradient to "Divine Intel".
  - [ ] **Governance & Records**:
    - [ ] Implement "Back" navigation when opening records in the Stage.
    - [ ] Populate the Options Bar with record metadata (Author, Version, Relationship links).
  - [ ] **Learn & Community**:
    - [ ] Fix `TemplateSyntaxError` in Induction and Content reviews.
    - [ ] Retrofit member directory and pipeline views to use the workspace master-detail pattern.

  ## Phase 5: Specialized Tools
  - [ ] **Bible App**: Migrate Book/Chapter navigation into the Context Bar (Col 2) to free up the Stage.
  - [ ] **Live App**: Design the video timeline and schedule manager for the Stage window.
  - [ ] **Tenancy**: Add contextual actions for permission management in the Context Bar.
