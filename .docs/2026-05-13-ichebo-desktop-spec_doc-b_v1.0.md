**ICHEBO DESKTOP**

**Product Specification**

_DOC B - Version 1.0 - May 2026_

| **Field**     | **Value**                                            |
| ------------- | ---------------------------------------------------- |
| Document      | DOC B - Ichebo Desktop Product Specification         |
| Version       | 1.0 - May 2026                                       |
| Status        | Approved - Canonical Reference                       |
| ADR reference | ADR-017, ADR-016, ADR-018, ADR-013                   |
| Depends on    | DOC A (Product Vision), DOC C (Sync Engine Spec)     |
| Feeds into    | DOC D (Technical Architecture), DOC E (Engine Specs) |
| Authors       | Chizola (domain); Claude (technical)                 |

**_A community should be able to operate Ichebo Desktop fully and permanently without internet access and lose nothing of operational value._**

**-- PRODUCT DEFINITION**

**What Ichebo Desktop Is**

The primary product in the Ichebo ecosystem. A local-first, offline-capable community operating system.

## **1.1 Product Statement**

Ichebo Desktop is a standalone, installable, offline-capable operating system for a single Sceptre Community. It is the primary product in the Ichebo ecosystem - not a companion to the cloud, but the product that the cloud serves.

It is installed once on a PC, Mac, or Linux machine by the community steward. It runs fully offline. It syncs to the Ichebo Cloud when internet is available. The community's data lives on the device the community controls.

## **1.2 Product Attributes**

| **Attribute**       | **Value**                                                                     |
| ------------------- | ----------------------------------------------------------------------------- |
| Technology          | Flutter - one codebase for Windows, macOS, and Linux                          |
| Database            | SQLite (local, embedded, WAL mode, zero config)                               |
| Network requirement | None for operation. Internet required only for sync and initial activation.   |
| Primary user        | Community steward - local pastor, coordinator, or administrator               |
| Scope               | Single Sceptre Community per installation                                     |
| Sync engine         | Go binary (ichebo-sync) - embedded, runs as background daemon                 |
| Design authority    | DESIGN.md - all visual decisions governed by the locked design system         |
| Dark mode           | Non-optional. Built from day one. Required for low-light church environments. |
| Versioning          | Desktop versioning is independent of Ichebo Web versioning. Starts at v1.0.   |

## **1.3 What Ichebo Desktop Is Not**

- Not a web browser wrapper - it is a native Flutter application
- Not a thin client to the cloud - the device is the primary computer
- Not a backup solution - it is the operational system; the cloud is the backup
- Not a multi-community tool - each installation serves one Sceptre Community
- Not the Apostolic Command Shell - that is the web product for Level 3+ operators on desktop browsers
- Not Ichebo Mobile - Mobile is the individual member's companion; Desktop is the community operating system

## **1.4 The Primary Product Decision - Context**

A strategic question was answered in May 2026 and locked in ADR-017:

**Locked - ADR-017**

Ichebo Desktop is the primary product. The cloud exists to connect, verify, and give network visibility to what is already happening locally on every Desktop installation. The cloud is the passport office. The Desktop is the freedom that follows.

The implication: if the internet goes down permanently in a region for six months, Ichebo Desktop must work perfectly and lose nothing of operational value. The cloud was always the optional layer.

**-- USER**

**The Primary User**

The community steward. The person responsible for the day-to-day governance and operations of a single Sceptre Community.

## **2.1 Who the Steward Is**

The community steward is the person responsible for the day-to-day governance, pastoral care, and operational management of a single Sceptre Community. Within the KGS framework this is typically a Level 3 Functional Minister or higher, carrying a branch-steward role or above within the community tenant.

They are not a technology professional. They may be:

- A pastor running a house church or neighbourhood community
- A community coordinator managing 50-500 members across multiple gatherings
- A senior steward overseeing multiple communities within a district
- An administrator responsible for formation tracking and records management

What they have in common: they are responsible for people and accountable for the community's governance. They need a tool that works in the conditions that actually exist - including when the power is out and the internet is down.

## **2.2 What the Steward Needs Daily**

| **Need**                                              | **How Desktop serves it**                                              |
| ----------------------------------------------------- | ---------------------------------------------------------------------- |
| Know who their members are                            | People section - member registry, always available offline             |
| Record what happened at a gathering                   | Activity section - attendance and participation logging                |
| See who is in formation and at what level             | People section - competence levels and formation progress              |
| Know their shepherd assignments                       | People section - who is pastoring whom                                 |
| Log service and ministry participation                | Activity section - service record per member                           |
| Know when they last synced                            | Sync status bar - always visible, always honest                        |
| Access governance documents from apostolic leadership | Governance section - read-only Handbook and mandates synced from cloud |

## **2.3 What the Steward Does Not Need from Desktop (MVP)**

These are explicitly out of scope for Desktop MVP. They exist in the cloud web product or are deferred to Desktop Phase 2:

- Authoring governance documents - The Desk is a web/cloud product
- Running formation pathways and Learn programmes - cloud handles this
- Video and live streaming - Ichebo Media is Version 3+
- Multi-community network management - cloud handles this
- Paraclete intelligence and digest - cloud + future Desktop phase
- Full KGS five-level permission complexity - simplified for single community in MVP

**-- MVP SCOPE**

**Three Functions. No More.**

Ruthless minimalism. The MVP that proves local-first works - before adding anything else.

## **3.1 The MVP Principle**

The Ichebo Desktop MVP is defined by ruthless minimalism. Three functions. Not four. Not five. Three.

**MVP scope - locked**

People → Activity → Sync. That is the Ichebo Desktop MVP. Everything else - Learn, Paraclete, Video, full KGS permissions, multi-community management - comes after a community is running the MVP successfully offline.

The discipline: every feature proposed for MVP must answer the question "can a community steward operate their community without this?" If the answer is yes, it is not MVP.

## **3.2 MVP Function 1 - People**

The member registry. The steward's primary reference for who is in their community.

**What it provides**

- Full member list - every person with an active UserPermission in this tenant
- Member profile - name, display name, email, competence level, status
- Level badge - visual indicator of KGS competence level (0b through 5)
- Shepherd assignment - who is pastoring this member; who this member is pastoring
- Service order - which KGS Service Order this member operates in
- Add member - create a new member record locally (synced to cloud on next connection)
- Edit member - update details, level, shepherd, service order
- Search - find a member by name quickly
- Filter - by competence level, service order, shepherd

**What it does not provide in MVP**

- Full pastoral notes - privacy design required; deferred to Desktop Phase 2
- Formation pathway tracking - Learn App is a cloud/web product in MVP
- Attendance history per member - available in Activity section, not in People view
- Bulk import - stewards add members one at a time or via sync from cloud

## **3.3 MVP Function 2 - Activity**

The community's operational record. Every gathering, service, and participation event logged locally.

**What it provides**

- Activity list - all activities for this community, ordered by date
- Gathering log - record that a gathering occurred, who attended, what happened
- Service participation log - who served in what capacity
- Attendance marking - tap to mark a member present at a gathering
- Activity types supported: task, habit, goal, event, gathering
- Status tracking - pending, in progress, completed, cancelled
- Date and time - scheduled_at and due_at per activity
- Assigned to - link an activity to a specific member

**Dual-write maintained**

When a gathering is created in Desktop, it writes both a gathering Record and an event Activity, atomically, in the same SQLite transaction - matching the data contract dual-write pattern. This ensures the data is consistent when it syncs to the cloud.

**What it does not provide in MVP**

- Ministry campaign and project management - simplified in Desktop MVP
- Recurring activity RRULE builder - basic recurrence only
- Calendar grid view - dated list view only; full grid is a Phase 2 feature
- Activity templates - deferred to Desktop Phase 2

## **3.4 MVP Function 3 - Sync**

The sync surface. The community steward's window into the health of the connection between their device and the network.

**The sync status bar - always visible**

The sync status bar is persistent across all sections. It is never hidden. It is always in the same position. It communicates one of four states:

| **State** | **Display**                           |
| --------- | ------------------------------------- |
| Synced    | ● Synced - 2 minutes ago \[Sync now\] |
| Offline   | ○ Offline - 47 changes pending        |
| Syncing   | ⟳ Syncing - 23 of 47 changes...       |
| Conflict  | ⚠ 3 records need attention \[Review\] |

**The Sync section**

- Full sync status - last synced timestamp, pending count, total synced
- Sync now button - triggers immediate push + pull cycle
- Conflict queue - list of records needing user review with two-option resolution (Keep mine / Keep cloud)
- Connection indicator - clear signal whether internet is currently reachable
- Device information - device ID, licence key reference, tenant name

**Design intent**

The Sync section is not a technical diagnostic panel. It is a calm, honest status surface. The steward should be able to glance at it and immediately understand the health of their connection without technical knowledge.

## **3.5 MVP Feature Inventory**

| **Feature**                                         | **MVP** | **Phase 2+**                      |
| --------------------------------------------------- | ------- | --------------------------------- |
| Member registry (view, add, edit, search, filter)   | ✅      | -                                 |
| Competence level display and assignment             | ✅      | -                                 |
| Shepherd assignment                                 | ✅      | -                                 |
| Service order assignment                            | ✅      | -                                 |
| Activity list (view, create, edit, mark complete)   | ✅      | -                                 |
| Gathering log with attendance marking               | ✅      | -                                 |
| Sync status bar (four states)                       | ✅      | -                                 |
| Conflict queue with resolution UI                   | ✅      | -                                 |
| Governance read-only (synced Handbook and mandates) | ✅      | -                                 |
| First-run wizard (three screens)                    | ✅      | -                                 |
| Dark mode                                           | ✅      | -                                 |
| Bible reader (bundled SQLite)                       | ✅      | -                                 |
| Full calendar grid view                             | -       | Phase 2                           |
| Pastoral notes                                      | -       | Phase 2 (privacy design required) |
| Attendance analytics                                | -       | Phase 2                           |
| Formation pathway tracking                          | -       | Phase 2                           |
| Learn programme delivery                            | -       | Phase 2                           |
| Paraclete intelligence                              | -       | Phase 2                           |
| Video playback (offline)                            | -       | Phase 3 (Ichebo Media)            |
| Multi-community management                          | -       | Cloud product always              |
| Governance authorship (The Desk)                    | -       | Cloud product always              |

**-- INFORMATION ARCHITECTURE**

**Five Sections**

Home - People - Activity - Governance - Sync

## **4.1 Navigation Model**

Ichebo Desktop uses a persistent left sidebar for primary navigation - five sections. No more. The navigation is always visible. There is no hamburger menu. There is no drawer. The community steward always knows where they are and where everything else is.

| **Section** | **Purpose**                                                                                                               |
| ----------- | ------------------------------------------------------------------------------------------------------------------------- |
| Home        | Today's snapshot. Upcoming gatherings. Recent activity. Sync status summary. Quick access to the most likely next action. |
| People      | Member registry. The community's full membership. Search, filter, view, add, edit.                                        |
| Activity    | Operational record. Gatherings, service, participation, tasks. The community's history of what happened.                  |
| Governance  | Read-only view of Handbook content and mandates received from the cloud. No authorship.                                   |
| Sync        | Full sync status, conflict queue, connection details, manual sync trigger.                                                |

## **4.2 Section - Home**

**Purpose**

The steward opens Ichebo Desktop and immediately knows: what is happening today, what needs attention, and whether everything is synced. Home is the summary surface - it contains no unique data. Everything on Home is a view into People, Activity, or Sync.

**Home - Ichebo Desktop**

Upcoming gatherings (next 3) ● Synced - 2 minutes ago

─────────────────────────────────────────────────────────────

Sunday Service tomorrow 09:00 34 expected

Cell Group A Wednesday 19:00 12 expected

Prayer Meeting Friday 06:00 8 expected

Recent activity

─────────────────────────────────────────────────────────────

John Mokoena marked present Sunday Service today

Sarah Dlamini added as member yesterday

Thursday Bible completed 2 days ago

Community snapshot

Members: 247 Active this month: 189 Formation: 34 in progress

## **4.3 Section - People**

**Purpose**

The complete member registry for this Sceptre Community. The steward's primary reference for who is in their community and in what capacity.

**People - Ichebo Desktop**

\[Search members...\] \[+ Add member\] Filter: All levels ▾

─────────────────────────────────────────────────────────────

John Mokoena ●L3 Steward Order of Pastoral Care

Shepherd: Paul Reuben Service: Community Ops

Sarah Dlamini ●L1 Member Order of Discipleship

Shepherd: John Mokoena

Thabo Nkosi ●L2 Disciple Order of Community Building

Shepherd: John Mokoena

\[247 members total - showing 1-50\] \[← Previous\] \[Next →\]

**Member detail view**

Tapping a member opens their full profile in a detail panel:

- Identity - display name, full name, email, avatar
- Formation - competence level with level colour badge, status
- Pastoral - shepherd assignment (who pastors them), flock (who they pastor)
- Service - service order, KGS pathway alignment
- Activity summary - recent participation events (last 10)
- Edit - tap to enter edit mode for any field

## **4.4 Section - Activity**

**Purpose**

The operational record of the community. Every gathering, service event, task, and participation log. The complete history of what happened.

**Activity - Ichebo Desktop**

\[+ New activity\] Filter: All types ▾ Sort: Date ▾

─────────────────────────────────────────────────────────────

Sunday Service Event 26 May 2026 ● Completed

Attended: 34 members Duration: 2h 15min

Cell Group A Event 28 May 2026 ⏳ Upcoming

Expected: 12 members Location: Sandton

Outreach - Diepsloot Campaign 01 Jun 2026 ⏳ Upcoming

Assigned to: John Mokoena

\[128 activities - showing 1-20\] \[← Previous\] \[Next →\]

**Gathering attendance flow**

The most common steward workflow - marking attendance at a gathering:

- Open the gathering from the Activity list
- Tap "Mark attendance"
- Scroll through the member list; tap to mark each person present
- Tap "Save attendance" - all marks written to SQLite and ChangeLog atomically
- Sync status bar increments pending count if offline; pushes immediately if online

## **4.5 Section - Governance**

**Purpose**

Read-only access to governance content received from the Ichebo Cloud. The community steward can view the Handbook, mandates, reference library records, and keys - but cannot author or edit them. Authorship is a cloud/web function (The Desk).

**Governance - Ichebo Desktop**

Reference Library Mandate Branch Keys Library

─────────────────────────────────────────────────────────────

Classes (12) Mandates (8) My Keys (34)

Principles (24) Statements (15)

Concepts (31) Frameworks (6)

Divine Patterns (18) Protocols (11)

Last updated from cloud: 13 May 2026 at 14:32

Governance content is read-only on Desktop.

To author governance records, use Ichebo Web.

**Why read-only on Desktop**

Governance authorship is a deliberate, high-stakes activity that requires The Desk's editorial canvas, the HRS relationship viewer, and the Options Bar as metadata sidecar. These are web/cloud surfaces by design. The community steward reads and applies governance - the architects write it.

## **4.6 Section - Sync**

**Purpose**

The honest status surface. The steward's window into the health of the connection between their device and the network. Not a technical diagnostic panel - a calm, clear status view.

**Sync - Ichebo Desktop**

Sync status \[Sync now\]

─────────────────────────────────────────────────────────────

● Connected to Ichebo Cloud

Last synced: today at 14:32 (4 minutes ago)

Pending changes: 0

Total synced this session: 47 changes

Conflict queue 0 records need attention

─────────────────────────────────────────────────────────────

No conflicts. All data is in agreement.

Device

─────────────────────────────────────────────────────────────

Community: Sceptre Community Pretoria North

Device ID: 3f4a-8c2d-... (abbreviated)

Licence: Active - issued 01 March 2026

**-- FIRST-RUN EXPERIENCE**

**Three Screens**

The only time the steward interacts with the cloud before going offline for good.

## **5.1 Design Principle**

The first-run experience is the most critical moment in Ichebo Desktop's user journey. It is the handshake between the community and the cloud - the point at which the licence is verified, the identity is established, and the initial data is loaded.

Three screens. No more. Each screen has one question and one action. The steward should be operational within five minutes of installing the app.

## **5.2 Screen 1 - Activation**

**Welcome to Ichebo Desktop**

─────────────────────────────────────────────────────────────

Your community's operating system.

Works offline. Syncs when connected.

To begin, enter your licence key.

Your key was issued when your community was

registered on Ichebo Cloud.

Licence key: \[\_**\_**\_**\_**\_**\_**\_**\_**\]

\[Activate\]

Don't have a key? Apply at ichebo.org

─────────────────────────────────────────────────────────────

What happens on Activate:

- App calls POST /api/sync/validate-licence/ with the entered key
- Cloud verifies: valid key, active tenant, KGS compliant
- On success: cloud returns tenant identity, device ID is generated and stored
- On failure: clear error message (revoked / expired / not found) with link to apply

## **5.3 Screen 2 - Administrator Account**

**Set up your account**

─────────────────────────────────────────────────────────────

Create the administrator account for this device.

This account will have full access to all Desktop features.

Your name: \[\_**\_**\_**\_**\_**\_**\_**\_**\]

Email: \[\_**\_**\_**\_**\_**\_**\_**\_**\]

Password: \[\_**\_**\_**\_**\_**\_**\_**\_**\]

Confirm: \[\_**\_**\_**\_**\_**\_**\_**\_**\]

\[Create account and continue\]

─────────────────────────────────────────────────────────────

This account is the local device administrator. It maps to an existing Ichebo Cloud user account - the email must match a registered Level 3+ user in the community tenant. The password is stored locally using platform secure storage (Keychain on macOS, Credential Manager on Windows).

## **5.4 Screen 3 - Initial Sync**

**Loading your community**

─────────────────────────────────────────────────────────────

Sceptre Community Pretoria North

Licensed to: Chizola

Downloading your community data...

████████████████████████░░░░░░░░ 73%

Members: 247 loaded

Activities: 1,842 loaded (last 90 days)

Governance: 89 records loaded

Bible data: ready (bundled)

This usually takes 30-60 seconds.

Your device will work offline after this completes.

─────────────────────────────────────────────────────────────

What the initial sync loads:

- Tenant settings - name, tier, path, settings fields
- Full member roster - all current UserPermission rows for this tenant
- Last 90 days of activities - attendance, service, participation logs
- Governance snapshot - active Handbook and mandate records (read-only)

What the initial sync does NOT load:

- Bible verse data - bundled with the installer (30MB SQLite file, KJV + ASV + WEB). Ready from minute one, no download needed.
- Full activity history beyond 90 days - available on demand
- Learn programme content - not in Desktop MVP scope

**Performance target**

The initial sync must complete in under 60 seconds on a 5 Mbps connection for a community of 500 members. If the payload exceeds this, paginate. Never block the first-run experience.

After Screen 3 completes: the steward lands on the Home section. Ichebo Desktop is fully operational. The internet connection can now be removed. The community continues.

**-- DESIGN LANGUAGE**

**Desktop Design Standards**

DESIGN.md governs all visual decisions. These are the Desktop-specific applications.

## **6.1 Design Authority**

All visual decisions for Ichebo Desktop are governed by DESIGN.md and design-preview.html (ADR-013). These documents are the co-equal locked design authority. No design decision that contradicts them may be implemented without first amending both.

The Flutter implementation of the design system:

- tokens.dart - all DESIGN.md tokens as Dart constants (colours, spacing, typography sizes)
- app_theme.dart - ThemeData for light + dark, derived from DESIGN.md
- All component widgets reference tokens - no hardcoded colour or spacing values

## **6.2 Flutter Design Tokens (Dart)**

The DESIGN.md token system translated to Dart:

| **Token**              | **Dart value**    | **Usage**                                     |
| ---------------------- | ----------------- | --------------------------------------------- |
| IcheboColors.primary   | Color(0xFFAF3236) | Brand red - buttons, active states, left rule |
| IcheboColors.secondary | Color(0xFF185ABC) | Blue - info states, links, secondary actions  |
| IcheboColors.ink       | Color(0xFF0E0E0E) | Sidebar, dark surfaces, app bar background    |
| IcheboColors.stone     | Color(0xFFF5F3F0) | Card surfaces, main content background        |
| IcheboColors.muted     | Color(0xFF6B6B6B) | Secondary text, timestamps, labels            |
| IcheboSpacing.xs       | 8.0               | Icon-text gap, small component spacing        |
| IcheboSpacing.s        | 16.0              | Standard padding unit                         |
| IcheboSpacing.m        | 24.0              | Section gap, card margin                      |
| IcheboSpacing.l        | 32.0              | Page section gap                              |
| IcheboRadius.card      | 12.0              | Standard card radius                          |
| IcheboRadius.button    | 4.0               | Button and badge radius                       |

## **6.3 Navigation Shell**

Ichebo Desktop uses a fixed left navigation rail - not a bottom navigation bar (that is Ichebo Mobile) and not a browser tab bar. The rail is:

- Always visible - no collapse, no hamburger, no drawer on desktop
- 72px wide - matches the Apostolic Command Shell Primary Sidebar width
- Ink dark background (#0E0E0E) - consistent with the design language
- Active state: 3px red left rule + red icon + red label - the Left Red Rule signature pattern
- Five items - Home, People, Activity, Governance, Sync
- Sync status indicator in the rail - small dot showing current state colour

## **6.4 Dark Mode**

Dark mode is non-optional. It is built from day one and treated as a first-class surface - not an afterthought. Dark mode is particularly important in church environments where screens may be used in low-light settings during gatherings.

The dark mode surface shift follows DESIGN.md:

- \--bg → #0E0E0E (app background)
- \--card → #1A1A1A (card and panel surfaces)
- \--card-2 → #2D2D2D (hover states, dividers)
- \--text → #F5F3F0 (primary text on dark)
- \--muted → #9A9A9A (secondary text on dark)
- \--primary (#AF3236) never changes - the red is the fixed brand anchor in all modes

System preference detection: Ichebo Desktop reads the OS dark/light preference on launch and defaults to it. The steward can override in Settings.

## **6.5 Core Flutter Widgets**

| **Widget**        | **Description**                                                          |
| ----------------- | ------------------------------------------------------------------------ |
| IcheboAppBar      | Dark ink (#0E0E0E) app bar with SVG logo and sync status indicator       |
| IcheboNavRail     | Fixed left navigation rail - five items, active Left Red Rule state      |
| IcheboCard        | 12dp radius card with Stone surface (light) or #1A1A1A (dark)            |
| LevelBadge        | Coloured competence level indicator (L0 grey through L5 red)             |
| StatusBadge       | Status pill - active, pending, completed, cancelled                      |
| IcheboButton      | Primary / secondary / danger / ghost variants per DESIGN.md              |
| MemberListTile    | Dense member list item - name, level badge, service order                |
| ActivityListTile  | Dense activity list item - title, type badge, date, status               |
| SyncStatusBar     | Persistent sync state bar - four states with appropriate colour and icon |
| ConflictCard      | Conflict review card - two versions side by side, two resolution buttons |
| EmptyState        | Empty section state - icon, heading, body, optional CTA                  |
| IcheboProgressBar | Formation progress bar - red fill, stone track                           |

**-- TECHNICAL ARCHITECTURE**

**How Desktop Is Built**

Flutter + SQLite + Go Sync Engine. Three concerns. Clean boundaries.

## **7.1 Repository**

Ichebo Desktop lives in a separate repository from both the Django web platform and the Flutter mobile app:

| **Repository**                   | **Contents**                                                                      |
| -------------------------------- | --------------------------------------------------------------------------------- |
| ichebo (Django web)              | The cloud platform - Django, DRF, PostgreSQL, HTMX templates                      |
| ichebo-mobile (Flutter mobile)   | The individual companion app - Flutter, Android/iOS                               |
| ichebo-desktop (Flutter desktop) | Ichebo Desktop - Flutter, SQLite, Go Sync Engine FFI                              |
| ichebo-sync (Go)                 | The Sync Engine - standalone Go binary, shared across Desktop and future products |

## **7.2 Architecture Overview**

Three clean layers with clear boundaries:

| **UI LAYER - Flutter / Dart**<br><br>All screens, widgets, navigation, state management. Reads SQLite directly for display data. Calls Sync Engine via FFI for control only.                                                                       |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ENGINE LAYER - Go / ichebo-sync**<br><br>Sync Engine daemon (background goroutine). Domain engines: Records, Activity, Relationships, Bible, Calendar. ChangeLog. Conflict resolution. FFI bridge (six exported functions). Reads/writes SQLite. |
| **DATA LAYER - SQLite (WAL mode)**<br><br>The local database. Members, Activities, Records, ChangeLog, Settings, ConflictQueue. Go writes to it. Flutter reads from it. Single file on disk. Backed up locally.                                    |

The critical boundary: FFI is for control. SQLite is for data. Flutter calls the Sync Engine's six FFI functions to start, stop, trigger, query status, get conflict count, and resolve conflicts. Flutter reads all display data directly from SQLite using the sqflite package. No data passes through the FFI boundary.

## **7.3 Key Flutter Packages**

| **Package**        | **Purpose**                                                             |
| ------------------ | ----------------------------------------------------------------------- |
| sqflite            | SQLite database access - Flutter reads all display data here            |
| drift (optional)   | Type-safe SQLite layer - alternative to raw sqflite for complex queries |
| riverpod           | State management - community data, user session, sync status            |
| go_router          | Navigation - five sections, detail views, first-run flow                |
| ffi                | dart:ffi - calls Go Sync Engine functions from Dart                     |
| path_provider      | File system paths - locating the SQLite database file                   |
| window_manager     | Desktop window management - size, title, minimize/maximize              |
| google_fonts       | Playfair Display + Inter loading from Google Fonts CDN                  |
| shared_preferences | Auth token and device preferences storage                               |

## **7.4 Platform Targets**

| **Platform**       | **Status**                                                                            |
| ------------------ | ------------------------------------------------------------------------------------- |
| Windows (x64)      | Primary build target for the African market. Most community stewards use Windows PCs. |
| macOS (arm64, x64) | Secondary build target. Supported from day one (same codebase).                       |
| Linux (x64)        | Tertiary build target. Self-hosted and technical users.                               |
| Android            | Not Ichebo Desktop - that is Ichebo Mobile.                                           |
| iOS                | Not Ichebo Desktop - that is Ichebo Mobile.                                           |

**-- BUILD SEQUENCE**

**How Desktop Gets Built**

Layer 6 of the master roadmap. Begins after Sync Engine (Layer 5) is tested and proven.

## **8.1 Entry Requirement**

**Gate - non-negotiable**

Ichebo Desktop build does not begin until the Sync Engine (ichebo-sync) has passed its 7-day offline integration test - 500+ changes made offline, full sync on reconnect, zero data loss, zero corruption. The Sync Engine is the foundation. The Desktop UI is built on top of it.

## **8.2 Build Phases**

| **Phase**                       | **What it builds**                                                                                                                                                                                                                                  |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D.1 - Flutter Desktop Project   | Flutter project setup targeting Windows, macOS, Linux. Design tokens in Dart (tokens.dart, app_theme.dart). Core widget library. Empty navigation shell with five sections.                                                                         |
| D.2 - Local Data Layer          | sqflite integration, WAL mode configuration, Go Sync Engine FFI bridge wiring. All reads routed through SQLite. All writes through Go engines.                                                                                                      |
| D.3 - First-Run Wizard          | Three-screen activation flow. Licence validation, account setup, initial sync with progress display. Exit: a community steward can activate and reach Home in under 5 minutes.                                                                      |
| D.4 - People Section            | Member list, search, filter, member detail view, add member, edit member. All reads from SQLite. All writes through Records Engine (Go). Exit: steward can find any member within 3 seconds.                                                        |
| D.5 - Activity Section          | Activity list, gathering log, attendance marking flow, create activity, edit, mark complete. Dual-write pattern (gathering + event Activity atomically). Exit: steward can log a gathering and mark attendance for 100 members in under 10 minutes. |
| D.6 - Sync Section + Status Bar | Full sync status surface, conflict queue with resolution UI, sync status bar persistent across all sections. Exit: steward can understand sync state without technical knowledge. Conflict resolution takes under 30 seconds per conflict.          |
| D.7 - Governance Section        | Read-only view of synced Handbook content. Reference Library browse, Mandate Branch browse, Keys Library. Exit: steward can access any governance record within 5 seconds.                                                                          |
| D.8 - Home Section              | Today's snapshot assembled from People and Activity data. Upcoming gatherings, recent activity, community statistics. Exit: Home provides meaningful at-a-glance status with no configuration.                                                      |
| D.9 - Dark Mode                 | Dark mode applied to all screens and widgets. System preference detection. Manual override in Settings. Exit: every screen passes visual review in both light and dark mode.                                                                        |
| D.10 - Installer                | Windows: MSIX installer. macOS: .dmg. Linux: .AppImage. Auto-update mechanism. Bible SQLite bundled. Exit: a non-technical steward can install Ichebo Desktop in under 5 minutes from the downloaded installer.                                     |

## **8.3 Exit Criteria - MVP Complete**

Ichebo Desktop MVP is complete when:

- A community steward can install the app on a Windows PC without technical assistance
- They can activate with a licence key and complete initial sync in under 5 minutes
- They can add a member, log a gathering, and mark attendance - all offline
- They can go offline for 7 days, make changes, reconnect, and sync cleanly
- Zero data loss across the 7-day offline test with 500+ changes
- The sync status bar always reflects the true state
- Conflicts (if any) are resolvable by a non-technical steward in under 30 seconds each
- Both dark and light mode pass visual review against DESIGN.md
- The app launches in under 3 seconds on a 4GB RAM Windows PC from 2019

# **Part 9 - Deferred Items**

Everything below is explicitly deferred from Desktop MVP. It is not forgotten. It is here so it can be planned when the MVP is proven in real-world use.

## **9.1 Desktop Phase 2**

- Full calendar grid view - dated list only in MVP
- Pastoral notes - privacy design required before implementation
- Attendance analytics - aggregate views of participation over time
- Formation pathway tracking - basic level display in MVP; full pathway tracking in Phase 2
- Activity templates - recurring workflow patterns
- Member bulk import - CSV or cloud sync; stewards add manually in MVP
- Multi-community view (for stewards who oversee multiple communities)
- Paraclete intelligence layer (local rule-based - reads SQLite, no cloud call)

## **9.2 Desktop Phase 3 (requires Ichebo Media)**

- Offline video playback - learning content downloaded to device
- Teaching video library - local cache of community video content
- Live stream receiver - watch a network broadcast offline-cached

## **9.3 Always Cloud/Web - Never Desktop**

- Governance authorship (The Desk) - cloud/web product by design
- Learn programme delivery - LMS complexity belongs in the cloud
- Multi-community network management - cloud product by design
- KGS onboarding and licence issuance - cloud product by design
- Cross-community reporting and analytics - cloud product by design

**Ichebo Christian Services**

_DOC B - Ichebo Desktop Product Specification v1.0 - May 2026 - Canonical Reference_