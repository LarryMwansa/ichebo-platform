TargetFile: /home/mantis/projects/ics/.project_docs/UI-design/Apostolic-Shell-Phase-2-Execution-Plan.md
Overwrite: true
IsArtifact: true
ArtifactMetadata:
  ArtifactType: implementation_plan
  Summary: The finalized execution strategy for Phase 2 of the Apostolic Command Shell, incorporating the Zoom-style vertical navigation stack and draggable workspace architecture.
Description: Re-creating the execution plan to ensure it's saved and up-to-date.
CodeContent: |
  # Apostolic Shell: Phase 2 Execution Plan (Finalized)

  ## 1. Primary Navigation (The "Zoom" Stack)
  - **Pattern**: Vertical stack — Icon on top, 11px Label below.
  - **Typography**: Inter 700, Uppercase, +0.1em tracking for clarity.
  - **Width**: Set Sidebar to `72px` (from 56px).
  - **Grouping**: Stack related apps (Governance+Graph, etc.) to optimize height.
  - **Overflow**: Implement vertical scroll arrows for smaller viewports.

  ## 2. Resizable Architecture (The Grid)
  - **Interaction**: Draggable handles between Column 1/2 and Column 3/4.
  - **Memory**: Persistent widths using `localStorage`.
  - **Commands**: Add `> Reset Layout` to the Command Palette.

  ## 3. The Editorial Desk (High-Density)
  - **Field Rename**: "Registry Origin" -> "**Record Family**".
  - **Markdown Editor**:
    - [ ] Floating toolbar (100px from bottom) with auto-hide.
    - [ ] Obsidian-style Live Preview/Edit toggle.
  - **Routing**: Ensure Context Bar selections correctly load into the Stage.

  ## 4. Visual Identity (Ink & Stone)
  - **Accent Cleanup**: Replace all "pink" accents with `#AF3236` (Institutional Red).
  - **Typography**: Verify Playfair Display for all major Stage headers.
  - **Watermarks**: Apply ghost branding to all new Stage windows.

  ## 5. Technical Maintenance
  - **Error Resolution**: Fix `TemplateSyntaxError` in the Learn app.
  - **Retrofitting**: Align Community and Learn views with the 4-column workspace model.
