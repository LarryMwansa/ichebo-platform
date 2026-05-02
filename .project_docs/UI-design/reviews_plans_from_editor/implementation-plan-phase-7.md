# Implementation Plan: Phase 7 — Global Search & Command Palette

This phase focuses on upgrading the Ichebo Platform's search experience to a high-density, keyboard-first "Command Center" pattern.

## 1. Global Search Overlay (`ws-search-overlay`)
- [ ] **Modal Component:** Create a full-screen or large-centered search modal triggered by `/` or `CMD+K`.
- [ ] **Real-time Results:** Use HTMX to stream search results from all families (Governance, Records, Learning).
- [ ] **Result Categories:** Group results by Family/Type with clear iconography.
- [ ] **Quick Jump:** Implement "Jump to" commands (e.g., `> Governance`, `> Journal`).

## 2. Keyboard Command Palette
- [ ] **Action Registry:** Define a list of global actions:
  - `New Entry` (Journal)
  - `New Mandate` (Governance)
  - `Toggle Theme` (Light/Dark)
  - `Open Bible`
  - `View Profile`
- [ ] **Shortcuts:** Implement common power-user shortcuts:
  - `CMD + K`: Open Command Palette
  - `CMD + J`: Jump to Journal
  - `CMD + G`: Jump to Governance
  - `?`: Show Keyboard Help

## 3. UI/UX Polishing
- [ ] **Aesthetics:** Use a glassmorphic background for the search overlay with smooth transitions.
- [ ] **Accessibility:** Full ARIA compliance for keyboard navigation within the search results.
- [ ] **Empty States:** Useful "Recent Searches" and "Suggested Actions" when the search input is empty.

## 4. Technical Implementation
- [ ] **Backend:** Add a global search endpoint `governance:global-search` that queries multiple models efficiently.
- [ ] **JS:** Expand `workspace.js` to handle the command palette logic and shortcut listeners.
- [ ] **CSS:** Add `.ws-search-overlay` styles to `workspace.css`.

---
> [!TIP]
> Use `Playfair Display` for result headers and `Inter` for metadata to maintain the platform's editorial aesthetic even in the search interface.
