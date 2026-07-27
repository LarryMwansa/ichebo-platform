
---

## 8. Interactive Verse Actions & Bookmarks Drawer (Phase 3)

Added click-to-select verse popover menus, clipboard text/link copying with toast notifications, and a dedicated Saved Bookmarks drawer on **`bible.ichebo.org`**.

### Implementation Highlights
- **Verse Selection Popover (`templates/bible/community_reader.html` & `_community_chapter.html`):**
  - Clicking any verse row opens a floating micro-toolbar popover positioned above the selected verse.
  - **Copy Text:** Formats and copies scripture text + translation reference (e.g. `2 Chronicles 15:7 (KJV) — Be ye strong therefore...`) directly to the system clipboard.
  - **Copy Link:** Copies permalink URL (`https://bible.ichebo.org/read/2CH/15/#v-7`) for instant sharing.
  - **Bookmark:** Toggles saving the verse into the user's bookmarks list with real-time toast feedback.
- **Bookmarks Backend & Drawer (`bible/views.py` & `_community_bookmarks_drawer.html`):**
  - Added `community_toggle_bookmark` and `htmx_community_bookmarks` endpoints.
  - Stores bookmarked verses in session storage for guest readers and syncs to `user.preferences['bible_bookmarks']` for authenticated users.
  - Interactive **Saved** header button (`#openBookmarksBtn`) opens a drawer allowing readers to view all saved verses, jump to passages, or remove bookmarks.
