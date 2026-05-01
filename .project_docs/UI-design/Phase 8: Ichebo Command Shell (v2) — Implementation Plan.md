# Phase 8: Ichebo Command Shell (v2) — Implementation Plan

## 1. The Core Architecture (Four-Column Grid)
We will implement a unified `workspace_shell.html` that uses a responsive CSS Grid to manage four distinct vertical zones.

| Zone | Width | Style | Function |
| :--- | :--- | :--- | :--- |
| **Primary Sidebar** | 64px | Ink (#0E0E0E) | Global App Switcher (Icons) |
| **Context Bar** | 240px | Ink 2 (#1A1A1A) | App Nav, Folders, File Explorer |
| **The Stage** | Flexible | Stone (#F5F3F0) | Editorial Markdown Canvas |
| **Options Bar** | 300px | Stone 2 (#ECE9E4) | Metadata, Links, Relationships |

## 2. Centralized State Management (`WorkspaceUI`)
A single JS controller in `shell_v2.js` will manage the visibility and width of all panels.
- `localStorage` persistence for panel states.
- `Focus Mode`: Single command to collapse both side panels for 100% stage width.
- `Keyboard Shortcuts`: `[`, `]`, and `\` to toggle left, right, and both panels.

## 3. The Editorial Stage (Main Stage)
- **Markdown Core:** The stage will be retrofitted with a document-centric design using `Playfair Display` for headers.
- **Formatting Toolbar:** A minimalist, sticky toolbar at the top of the Stage.
- **Auto-Save Stub:** A debounced JS function that triggers a "Draft Saved" pulse.
- **File Manager:** A "Local Files" section in the Context Bar to handle governance drafts and reference attachments.

## 4. Design System Compliance
- **Rule of Left:** Persistent 3px red rule for active icons in the Primary Sidebar.
- **Typography:** Strict adherence to `Playfair Display` for display/authority and `Inter` for functional UI.
- **Stone-to-Ink:** Clear contrast between navigation (Ink) and creation (Stone).
