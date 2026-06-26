# Ichebo — Design Session Prompt
## Sceptre Community Surface + Ichebo Channel + Access Model

**Session type:** Advisory → Lock → Design
**Prepared by:** Home Chat — 2026-06-25
**For:** Fresh chat session

---

## Context for Claude at the start of this session

You are Claude — Chizola's technical adviser, architect, and build partner on the Ichebo platform. Read the Project Instructions (PROJECT_INSTRUCTIONS.md) in full before proceeding. Upload the following canonical documents at the start of this session:

- `PROJECT_INSTRUCTIONS.md`
- `master-roadmap-canonical-2026-05-13.md` (from repo — supersedes project folder copy)
- `data-contract-v11-canonical-2026-05-13.md`
- `DESIGN.md`
- `2026-05-13-ichebo-media-spec_doc-g_v1_0.docx` (Doc G — Ichebo Media)
- `2026-05-24-ichebo-pilot-readiness-plan_v1.md`

---

## The Core Decision (Locked in Home Chat — 2026-06-25)

The Ichebo platform is infrastructure. It now serves two distinct surfaces with their own subdomains, their own design purpose, and their own users. These surfaces are the correct digital expression of the three-layer KGS order:

```
KGS Framework → Agency Surface (app.ichebo.org)
        ↓
Sceptre Community Programme → Community Surface (sceptre.ichebo.org)
        ↓
Ichebo Platform — backend infrastructure serving both
```

**`app.ichebo.org`** — the Agency / Architect surface. The current Apostolic Command Shell evolves into the operator domain. Constitutional governance, Handbook authorship, network oversight, licence issuance, formation pipeline oversight, platform administration. This is Chizola's domain and the steward's governance environment.

**`sceptre.ichebo.org`** — the Sceptre Community surface. A new surface designed from scratch for its actual users. Two sides: consumer (participant) and steward (community leadership). The pilot is being built here.

**The backend does not change.** Same Django backend, same database, same API, same data contract. Django serves both subdomains from one codebase — separate URL routing and templates per subdomain. One new Nginx server block for `sceptre.ichebo.org`.

---

## What This Session Must Design

Three interconnected problems that form one design. Do not treat them separately.

---

### 1. `sceptre.ichebo.org` — Surface Architecture

A new Django site surface serving the Sceptre Community Programme. Two sides within one subdomain:

**Consumer side (participant — Level 0b–2)**
Designed for someone going through the Sceptre Community Programme. Simple, focused, channel-first. They do not see governance tools, ministry campaigns, or platform administration.

**Steward side (Level 3+)**
Community leadership tools. Member management, gathering scheduling, formation pipeline, certification queue, announcement authorship, community support queue. Stewards access this from the same subdomain — a role-adaptive surface, not a separate URL.

This session must produce the information architecture, navigation model, and screen-level design for both sides of `sceptre.ichebo.org`.

---

### 2. Ichebo Channel

The continuous broadcast channel that is the primary surface of the participant consumer experience. The channel is the front door — not a feature you navigate to.

**What it does:**
- Runs continuously — 24/7
- Content plays in scheduled sequence from a programme grid
- Live service takes over the channel at its scheduled time, then returns to the playlist
- Fallback playlist rotates when no scheduled content is in the current slot
- Single loop default plays if the fallback playlist is empty or not configured

**The fallback hierarchy (locked):**
1. Scheduled content — plays at its designated time
2. Live override — takes over when a live service goes active
3. Fallback playlist — rotates when no scheduled content is in the current slot
4. Single loop default — plays if fallback playlist is empty or not configured

**The now-playing endpoint** — `sceptre.ichebo.org` and the mobile app ask the server "what is on right now?" and play that. Proposed: `GET /api/broadcast/now/` returning current content, stream URL if live, next scheduled item.

**Content library** — VODs in Ichebo Media are the programming source. Scheduler draws from the Media library.

**The scheduler is an Architect tool** — lives at `app.ichebo.org`, not visible to participants. Chizola programmes the channel. Participants watch.

**Participant Home screen** — channel video window is the first and dominant element. Compact quick-access tiles below for the four vital areas:
1. Community — announcements, gatherings, community info
2. Learning — active programme, next lesson, formation progress
3. Bible — always at hand
4. Support — community support channel

---

### 3. Three-Tier Access Model

A clean, explicit separation of what each user type sees across both surfaces.

| Tier | Surface | What they see |
|------|---------|--------------|
| Participant (Level 0b–2) | `sceptre.ichebo.org` consumer side | Channel, community area, learning, Bible, community support/chat |
| Community Steward (Level 3+) | `sceptre.ichebo.org` steward side | All participant access + member management, gathering scheduling, formation pipeline, certification queue, announcement authorship, community support queue |
| Architect (Level 5, Prime — Chizola) | `app.ichebo.org` | All steward access + channel scheduler, constitutional data, Handbook authorship, licence issuance, platform-wide oversight, network governance |

**What belongs exclusively to the Architect at `app.ichebo.org`:**
- Broadcast channel scheduler (programme grid, fallback playlist, loop default)
- Constitutional data management (Service Orders, Agency Tenants, qualification programmes)
- Prime Tenancy configuration
- Handbook foundational record authorship (Reference Library, Mandate branch)
- DesktopLicence issuance
- Competence level confirmation at Level 4–5
- Network-wide formation oversight
- Django admin and server (invisible to all users)

---

### 4. Community Communications (New Features to Scope)

Two new features that belong on `sceptre.ichebo.org`:

**Community Support**
A structured channel for members to raise something to leadership attention. Simple request/support ticket scoped to a community tenant. Member submits a support request. Steward sees it in their queue and responds. This is simpler to build and should be included in the pilot.

**Community Chat / Intranet**
A lightweight social layer. Community noticeboard where members interact. Not a full social network — closer to a community feed with responses. This needs scoping in this session — decide whether to build for pilot or defer with a full spec.

---

## What This Session Must Produce

In this order:

**Step 1 — Advisory**
Review the surface separation decision and all three design problems. Advise on:
- Django multi-site vs URL routing approach for subdomain separation
- Any conflicts with locked architecture decisions (ADR-001–021)
- Data contract amendments required (new models or fields)
- New ADRs needed (subdomain separation will require one)

**Step 2 — Lock decisions**
Confirm all decisions before any document is produced. Including: subdomain approach, navigation model for both sides, Community Chat scope decision.

**Step 3 — Amend if needed**
Note data contract changes required. Note new ADR numbers.

**Step 4 — Full system design document**
Produce a complete, canonical system design document covering:
- `sceptre.ichebo.org` surface architecture (consumer + steward sides)
- Ichebo Channel architecture (scheduler, now-playing endpoint, fallback logic, live override)
- Participant Home screen design (layout, video states, tile structure)
- Navigation model for `sceptre.ichebo.org` (web + mobile)
- Three-tier access model with explicit gating rules
- `app.ichebo.org` evolution — what moves there, what stays, what is new
- Community Support feature spec
- Community Chat — build or defer decision with spec either way
- Nginx configuration notes for subdomain separation
- Django routing approach

**Step 5 — Roadmap amendment notes**
What this adds to the master roadmap. Where it sits relative to the pilot readiness plan. What it displaces or supersedes.

---

## Key Constraints

- Django 4.2 + HTMX for web — no React, no vanilla JS app files
- Flutter for mobile — Android-first; the mobile app is the consumer-side companion to `sceptre.ichebo.org`
- Ichebo Media (Go + FFmpeg) is complete — channel scheduler draws from it
- No new parallel content models — content lives in records table via record_family/record_type discriminator
- DESIGN.md governs all visual decisions — no pink, no deviations
- Build complete, release selectively — features built in full, access governed by competence level
- Backend does not change — one Django codebase, one database, subdomain separation is routing and templates only

---

## What Chizola Confirmed in Home Chat (2026-06-25)

- The platform is infrastructure — it gives flexibility to tailor surfaces
- `sceptre.ichebo.org` is the community surface — consumer side and steward side
- `app.ichebo.org` evolves into the agency/architect domain
- The video window is the first thing a participant sees on Home
- True broadcast channel — continuous playlist, no gaps, live override
- Fallback: both fallback playlist and single loop default, with flexibility
- The scheduler is the Architect's tool — participants just watch
- Community Chat / Intranet is the right direction — needs scoping in this session
- Community Support (member-to-leadership) should be built for pilot
- Activity, Records & Journals, Governance Library do not belong in the participant front door
- iOS deferred to post-pilot — Android is the pilot mobile surface

---     
sceptre.ichebo.org frontend approach confirmed: static HTML/CSS for public-facing pages, Django templates + HTMX for authenticated participant and steward surfaces. Same architecture as app.ichebo.org. No vanilla JS application files. ADR amendment required to note the new subdomain follows the existing HTMX decision.
*Session prompt prepared by Home Chat — 2026-06-25 — Ichebo Christian Services*
