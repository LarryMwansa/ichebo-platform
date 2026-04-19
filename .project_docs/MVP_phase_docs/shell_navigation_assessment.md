# ICS Shell Navigation: Assessment & Recommendation

## Your Proposal (from `ui_rooting.md`)

You have two navigation models documented. The **original** (what we mostly have now):

| Top Nav | Bottom Nav |
|---|---|
| Logo, Notification, Theme, Profile | Home, Bible, Activity, Community, Menu |

And the **new config** which reorganizes everything around **user intent**:

| Tab | Purpose |
|---|---|
| **Home** | Dashboard, Paraclete, basic routing |
| **Create** | Drawer for new entries (Records, Activities, etc.) |
| **Explore** | Reference browsing — Journals, Governance, Tenants, Events |
| **You** | Personal hub — Profile, Activity, Community, Learning, Gifts |
| **More** | App launcher + misc |

---

## Honest Assessment

### What Works Well

1. **The "intent-based" grouping is smart.** Instead of mapping 1 tab = 1 Django app, you're grouping by *what the user wants to do*. This is how best-in-class mobile apps work (Instagram, YouTube, etc.).

2. **"Create" as a first-class action is correct.** Content-creation apps (Instagram, Twitter/X, Notion) all give creation a permanent, prominent position. For ICS, where users write DARs, prayers, journal entries, and activities daily — this makes sense.

3. **"Explore" as a read-only reference surface is clean.** Separating "things I browse" from "things about me" reduces cognitive load significantly.

4. **"You" as the personal hub is strong.** Consolidating profile, activity history, community membership, and competence level into one surface gives users a single place to understand their standing. This mirrors YouTube's "You" tab.

### What Needs Rethinking

> [!WARNING]
> **1. "More" is a graveyard.**
> 
> Every UX study on mobile navigation shows the same result: items placed behind a "More" tab see 50-70% less engagement than items in the primary tabs. If Community, Governance, and Learn are behind "More", users will forget they exist.
> 
> The current App Launcher is fine as a *power-user escape hatch*, but it should NOT be the primary way users reach core apps.

> [!WARNING]
> **2. "Create" as a bottom tab is wasteful on a 5-slot bar.**
> 
> A "Create" action that opens a drawer doesn't need a permanent bottom tab. It's a *verb*, not a *place*. Better patterns:
> - **Floating Action Button (FAB)** — anchored above the bottom nav (like Google's Material pattern)
> - **"+" icon** integrated into the top navbar
> - **Long-press** on the Home tab
> 
> This frees up a slot for a more frequently visited destination.

> [!WARNING]  
> **3. "Home" and "You" have significant overlap.**
> 
> In your current dashboard, "Overview" already shows the user's activities, streaks, learning progress, and community status. If "You" _also_ shows Profile, Activity, Community, and Learning — the user gets confused about where to go for what.

---

## My Recommendation

A hybrid of your original and new config that matches best practices for **community/discipleship platforms** (think: church apps like YouVersion, Subsplash, Planning Center; or learning apps like Duolingo, Coursera):

### Bottom Navigation (5 slots)

| Slot | Icon | Label | What it does |
|---|---|---|---|
| 1 | `home` | **Home** | Dashboard. Paraclete digest, action items, streaks, learning progress. The "control center." |
| 2 | `auto_stories` | **Bible** | Bible reader. This is the most-used tool in a faith platform — it earns a permanent slot. |
| 3 | `explore` | **Explore** | Reference browser: Governance docs, community directory, events, records journal. The "library." |
| 4 | `person` | **You** | Profile, activity history, competence level, gifts, community membership, settings. |
| 5 | `apps` | **More** | App launcher grid for Learn, Governance detail, Activity create, Records, and future expansions. |

### Top Navigation

| Left | Right |
|---|---|
| Logo (🏛️ ICS) | Notifications, Theme Toggle, Profile Avatar |

### The "Create" Action → FAB (Floating Action Button)

Instead of a bottom tab, place a **Floating Action Button** anchored to the bottom-right corner (above the nav bar). Tapping it opens the existing **App Drawer** with a context-sensitive creation form:

- On **Home**: Quick-create a DAR, prayer, or journal entry
- On **Explore**: Create a new governance document or record
- On **You**: Update profile or log an activity

This is the exact pattern used by Gmail, Google Keep, and Notion.

### Why This Configuration

```
┌─────────────────────────────────────────────┐
│  🏛️ ICS                    🔔  ☀️  [avatar] │  ← Top Nav: brand + utilities
├─────────────────────────────────────────────┤
│                                             │
│              Page Content                   │
│                                             │
│                                             │
│                                        [+]  │  ← FAB: contextual create
├─────────────────────────────────────────────┤
│  🏠      📖       🔍       👤       ⊞      │  ← Bottom Nav: places
│  Home   Bible   Explore    You     More     │
└─────────────────────────────────────────────┘
```

**Key principles:**
1. **Bottom nav = places** (nouns, not verbs). Users navigate between their 4 most-frequented destinations.
2. **FAB = action** (verb). Always accessible, context-aware.  
3. **More = overflow**. Power-user access to full app catalogue. Keeps the bar clean.
4. **Top nav = identity + utilities**. Minimal, stays out of the way.

---

## How "Explore" Would Work

The Explore tab replaces the need for separate Community and Governance tabs in the bottom bar. It becomes a **unified reference browser**:

```
┌─────────────────────────────────┐
│  Explore                        │
├─────────────────────────────────┤
│  [🔍 Search everything...]      │
├─────────────────────────────────┤
│  📋 Records & Journals          │  → /records/
│  📖 Governance Library          │  → /governance/
│  👥 Community Directory         │  → /community/member-directory/
│  📅 Events & Gatherings         │  → /community/gatherings/
│  🏫 Course Catalogue            │  → /learn/
│  📊 Formation Pipeline          │  → /community/pipeline/  (L3+)
└─────────────────────────────────┘
```

This surface acts as a **universal search and browse** interface. Each item deep-links into the existing app, so no content duplication is needed.

---

## Migration Path from Current State

| Current | Proposed | Change |
|---|---|---|
| Bottom: Home | Bottom: Home | ✅ Keep |
| Bottom: Bible | Bottom: Bible | ✅ Keep |
| Bottom: Activity | Merged into You + FAB | 🔄 Move |
| Bottom: Learn | Inside More launcher | 🔄 Move |
| Bottom: Apps | Bottom: More | ✅ Keep (rename) |
| — | Bottom: Explore | ✨ New |
| — | Bottom: You | ✨ New |
| — | FAB (Create) | ✨ New |

> [!TIP]
> **Implementation effort is low.** We already have the App Launcher drawer, the profile menu, and all the sub-app views. The main work is:
> 1. Create an `explore/` view with a link-grid template
> 2. Create a `you/` view that aggregates profile + activity + community
> 3. Add a FAB component to `base.html`
> 4. Update `_bottom_nav.html` with the new 5 items

---

## Decision Required

Which direction would you like to go?

- **Option A**: Implement the full recommendation above (Home, Bible, Explore, You, More + FAB)
- **Option B**: Implement your original new config as-is (Home, Create, Explore, You, More)
- **Option C**: A different hybrid — tell me which elements you want to keep/change
