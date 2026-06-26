# Ichebo Platform — Subdomain Map

**Version:** v2 — 2026-06-25
**Status:** Living document — updated as surfaces are defined
**Author:** Chizola + Claude

> The Ichebo platform is infrastructure. Subdomains are surfaces that draw from that infrastructure. Each subdomain has one clear purpose and one clear audience. This document is the canonical record of all defined and planned subdomains. Placeholders are noted — they represent surfaces that are directionally confirmed but not yet fully designed.

---

## The Architecture Principle

```
One Django backend → Many surfaces
One database → Many audiences
One platform → Many purposes
```

No subdomain requires a new backend. Every surface is a new front door to the same engine.

---

## The Journey a Person Takes Through the Ecosystem

```
Seeker arrives → join.ichebo.org (induction and entry)
        ↓
Identity established → identity.ichebo.org (Kingdom identity — persistent across all surfaces)
        ↓
Community life → sceptre.ichebo.org (participant and steward)
        ↓
Formation and study → learn.ichebo.org (programmes, lessons, certification)
        ↓
Governance and oversight → app.ichebo.org (stewards and architect)
```

---

## Confirmed Subdomains (Live or In Build)

### `ichebo.org`
**Status:** ✅ Live
**Audience:** General public
**Purpose:** Marketing site — what Ichebo Christian Services is, what the Sceptre Community Programme is, what the platform does. The public face of the institution.
**Technology:** Static HTML/CSS — no Django required for public pages
**Notes:** Progressive revelation approach — KGS framework detail revealed across page sequence (Homepage → Programme → Formation → Platform → About → Waiting List)

---

### `app.ichebo.org`
**Status:** ✅ Live — evolving
**Audience:** Stewards (Level 3+) and Architect (Level 5, Prime)
**Purpose:** The Agency / Architect surface. Constitutional governance, Handbook authorship, network oversight, formation pipeline management, licence issuance, platform administration. The Apostolic Command Shell lives here.
**Technology:** Django 4.2 + HTMX — Apostolic Command Shell (four-column grid)
**Notes:** This is the current platform. It evolves into the dedicated agency/operator domain as the other surfaces are built. Stewards access their community management tools here.

---

### `cdn.ichebo.org`
**Status:** ✅ Live
**Audience:** Internal — served to all surfaces
**Purpose:** Content delivery — Hetzner Object Storage. Media files, HLS streams, static assets.
**Technology:** Hetzner Object Storage (S3-compatible)
**Notes:** Not a user-facing surface. All media delivery routes through here.

---

### `video.ichebo.org`
**Status:** ✅ Live
**Audience:** Internal — Ichebo Media engine
**Purpose:** Video processing VPS — FFmpeg transcoding, RTMP ingest, HLS packaging.
**Technology:** Go + FFmpeg + MediaMTX (Hetzner CX23, Helsinki)
**Notes:** Not a user-facing surface. Powers the channel and VOD library.

---

## In Design (Confirmed Direction — Session Pending)

### `join.ichebo.org`
**Status:** 🔵 In design
**Audience:** Seekers / new invitees — the public and those responding to an invitation
**Purpose:** Dedicated induction and public entry point. The threshold moment — moving from member of the public to participant in the Sceptre Community Programme. Walks someone through:
- Who the Sceptre Community is and what they are joining
- Invitation acceptance
- Account creation (community-framed, not platform-framed)
- Pathway selection (eight Kingdom Pathways)
- The induction programme itself
Once induction is complete, participant transitions to `sceptre.ichebo.org`.
**Technology:** Django 4.2 + HTMX (induction flow), static HTML/CSS (public landing)
**Notes:** Publicly accessible — no authentication required to arrive. The induction system (built in Layer 3) powers the backend. This is a surface decision, not a rebuild.

---

### `identity.ichebo.org`
**Status:** 🔵 In design
**Audience:** All authenticated users — every person in the Ichebo ecosystem
**Purpose:** The Kingdom Identity surface. A person's full Ichebo identity — persistent, portable, and theirs alone. Not a profile tab buried in an app. A dedicated home for who someone is in the Kingdom:
- Personal information and profile
- Competence level and formation history
- Active and completed qualifications
- Pathway and progress
- Service order assignments
- Community memberships (current and historical)
- Certifications — verifiable, permanent record
- Account settings, notifications, security

**Why it is its own surface:** Identity is not a feature of any one surface — it is the foundation every surface draws from. A person's Kingdom identity travels with them across `sceptre.ichebo.org`, `learn.ichebo.org`, and `app.ichebo.org`. It belongs at its own address.

**Future possibility:** A verifiable public profile — certifications and service record publicly viewable at a person's Kingdom identity address. Significant in an apostolic governance context where authority and credentialing matter.

**Technology:** Django 4.2 + HTMX
**Notes:** The Profile, Settings, and Notifications system (built in Layer 2) powers the backend. This is a surface and experience redesign. Identity is portable — if a person moves between Sceptre Communities, their record travels with them.

---

### `sceptre.ichebo.org`
**Status:** 🔵 In design
**Audience:** Participants (Level 0b–2) and Community Stewards (Level 3+)
**Purpose:** The Sceptre Community surface. Two sides within one subdomain:
- **Consumer side** — participant experience. Channel-first. Community, learning, Bible, support.
- **Steward side** — community leadership tools. Member management, formation pipeline, gathering scheduling, community support queue.
**Technology:** Django 4.2 + HTMX (authenticated surfaces), static HTML/CSS (public pages)
**Notes:** The Ichebo Channel is the primary surface — video window first, community tiles below. This is the pilot surface. Design session in progress.

---

### `learn.ichebo.org`
**Status:** 🔵 In design
**Audience:** Participants enrolled in qualification programmes (Level 1+)
**Purpose:** Dedicated formation and study surface. Programmes, modules, lessons, assessments, certification. Feels like enrolling in an institution of learning — not clicking through a menu inside an app.
**Technology:** Django 4.2 + HTMX
**Notes:** The Learn App (F1–F11, built in Layer 2) powers the backend. This is a surface and experience redesign, not a new system. Direction confirmed — design session pending.

---

## Placeholders (Directionally Confirmed — Not Yet Designed)

### `handbook.ichebo.org`
**Status:** 🟡 Placeholder
**Audience:** TBD — likely Level 3–5 stewards and architects; possibly a public read surface for published governance records
**Purpose:** The standalone Handbook product as its own surface. The Desk, HRS relationships, Scripture Linking, Publish Feed — accessible as a dedicated governance authorship and reference environment.
**Technology:** Django 4.2 + HTMX (Apostolic Command Shell pattern)
**Notes:** Deferred in earlier sessions until standalone Handbook product codebase is deployed (K.1–K.6 complete). Direction confirmed — surface design pending.

---

### `media.ichebo.org`
**Status:** 🟡 Placeholder
**Audience:** TBD — possibly a public or semi-public VOD browsing surface
**Purpose:** A public-facing media library. Past teachings, series, broadcasts available to browse without full platform membership. Could serve as an outreach and discovery surface.
**Technology:** TBD
**Notes:** Not yet scoped. The Ichebo Media engine (Layer 8) powers the content. Surface purpose and audience need defining.

---

### `give.ichebo.org`
**Status:** 🟡 Placeholder
**Audience:** Community members and general public
**Purpose:** Giving / donations surface. Community-scoped giving, tithing, special offerings.
**Technology:** TBD — requires payment provider integration design
**Notes:** Listed as post-pilot deferred item. Captured here as a placeholder.

---

### `[future].ichebo.org`
**Status:** 🟡 Open placeholder
**Audience:** TBD
**Purpose:** The platform is open for additions not yet thought of. As the Sceptre Community Programme grows and new audiences or purposes emerge, new surfaces can be added without touching the backend. This placeholder is a reminder that the architecture is designed for this.
**Technology:** Django 4.2 + HTMX (default pattern)
**Notes:** Any new surface follows the same principle — one backend, new front door.

---

## The Full Picture

```
ichebo.org              → Public — marketing and institution
join.ichebo.org         → Seekers — induction and entry
identity.ichebo.org     → All users — Kingdom identity and account
sceptre.ichebo.org      → Participants — community life
learn.ichebo.org        → Students — formation and study
app.ichebo.org          → Stewards / Architect — agency and governance
handbook.ichebo.org     → Architects — governance authorship (placeholder)
media.ichebo.org        → Public — VOD library (placeholder)
give.ichebo.org         → Community — giving (placeholder)
cdn.ichebo.org          → Internal — content delivery
video.ichebo.org        → Internal — media processing
```

---

## Governing Principles

- One Django backend serves all surfaces
- One database — no data duplication across subdomains
- Each subdomain has one clear audience and one clear purpose
- Authentication is shared — an Ichebo account works across all surfaces
- Kingdom identity is portable — a person's record travels with them across communities and surfaces
- The competence level gating system governs what each user can access regardless of which surface they are on
- New surfaces do not require new backend systems — they are routing and template decisions
- DESIGN.md governs visual decisions across all surfaces — brand consistency is non-negotiable

---

*Subdomain Map — Ichebo Platform — v2 — 2026-06-25*
*Ichebo Christian Services*
*Living document — update when new surfaces are confirmed or placeholders are designed*
