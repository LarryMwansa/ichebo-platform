**ICHEBO**

**Technical Architecture Document**

_DOC D - Version 1.0 - May 2026_

| **Field**      | **Value**                                                              |
| -------------- | ---------------------------------------------------------------------- |
| Document       | DOC D - Technical Architecture Document                                |
| Version        | 1.0 - May 2026                                                         |
| Status         | Approved - Canonical Reference                                         |
| ADR references | ADR-001 through ADR-021                                                |
| Depends on     | DOC A (Product Vision), DOC B (Desktop Spec), DOC C (Sync Engine Spec) |
| Feeds into     | DOC E (Engine Specifications)                                          |
| Authors        | Chizola (domain); Claude (technical)                                   |

**Purpose**

This document is the complete technical architecture reference for the Ichebo ecosystem. It defines every layer, every boundary, every technology choice, and the reasoning behind each. It is the document to read before making any infrastructure, language, or framework decision.

**-- OVERVIEW**

**The Ichebo Ecosystem Architecture**

Five layers. Three products. One design system. One data contract.

## **1.1 The Full Stack - One View**

The Ichebo ecosystem is five layers. Every component in the system belongs to exactly one layer. The arrows show data flow and dependency.

| **LAYER 1 - CLIENT SURFACES**                                                                                        |
| -------------------------------------------------------------------------------------------------------------------- |
| Ichebo Web (Django + HTMX, browser) \| Ichebo Desktop (Flutter, local-first) \| Ichebo Mobile (Flutter, Android/iOS) |

| **LAYER 2 - API GATEWAY (current: Nginx + DRF routing; future: dedicated Go gateway)**                           |
| ---------------------------------------------------------------------------------------------------------------- |
| Routes requests to services. Handles auth tokens, tenant context, rate limiting. All client traffic enters here. |

| **LAYER 3 - APPLICATION SERVICES**                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------- |
| Django Web App (auth, templates, HTMX) \| DRF API (mobile + Desktop sync) \| Paraclete Service \| Notification Service |

| **LAYER 4 - DOMAIN ENGINES (Go modules - portable, embeddable)**                                            |
| ----------------------------------------------------------------------------------------------------------- |
| Records Engine \| Activity Engine \| Relationships Engine \| Bible Engine \| Calendar Engine \| Sync Engine |

| **LAYER 5 - DATA STORES**                                                                             |
| ----------------------------------------------------------------------------------------------------- |
| PostgreSQL (cloud) \| SQLite (Desktop/Mobile local) \| MinIO / Hetzner Object Storage (files + media) |

## **1.2 The Core Architectural Principle**

**The separation of concerns**

Django is the web layer - not the domain logic owner. Go engines are the domain logic layer - portable, embeddable, independently testable. SQLite is the local data layer. PostgreSQL is the cloud data layer. The Sync Engine connects local to cloud. No layer reaches past its boundary into another.

## **1.3 Architecture Decisions - Full Reference**

All 21 ADRs govern this architecture. The table below maps each decision to the layer it affects.

| **ADR**           | **Decision**                                                              | **Layer affected**          |
| ----------------- | ------------------------------------------------------------------------- | --------------------------- |
| ADR-001 (amended) | Flutter for all client surfaces (Desktop + Mobile)                        | Layer 1                     |
| ADR-002           | Django 4.2 LTS - no upgrade to 5.x without ADR                            | Layer 3                     |
| ADR-003           | Single records table with record_family/record_type discriminator         | Layer 5                     |
| ADR-004           | DRF retained as service layer for mobile and Desktop sync                 | Layer 3                     |
| ADR-005           | Django templates + HTMX for web - no JS frameworks                        | Layer 1                     |
| ADR-006           | competence_level - one write path only                                    | Layer 3 + Layer 4           |
| ADR-007           | URL-based video in Version 2 - no self-hosted transcoding                 | Layer 3                     |
| ADR-008           | No Celery or Redis until Version 3                                        | Layer 3                     |
| ADR-009           | No Docker until Version 3 - Nginx + Gunicorn + systemd                    | Layer 2 + Layer 3           |
| ADR-010           | Paraclete is rule-based - no LLM in MVP                                   | Layer 3                     |
| ADR-011           | KGS programme and curriculum structure                                    | Layer 3 + Layer 4           |
| ADR-012           | Apostolic Command Shell - four-column desktop web interface               | Layer 1                     |
| ADR-013           | DESIGN.md + design-preview.html as locked design authority                | All layers                  |
| ADR-014           | The Desk as governance authorship surface                                 | Layer 1                     |
| ADR-015           | Dual-shell rendering - Stage Mode + Mobile Mode                           | Layer 1                     |
| ADR-016           | Local-first as Ichebo architectural philosophy                            | All layers                  |
| ADR-017           | Ichebo Desktop as primary product                                         | Layer 1 + Layer 4 + Layer 5 |
| ADR-018           | Sync Engine as standalone Go binary                                       | Layer 4                     |
| ADR-019           | Go as language for domain engines                                         | Layer 4                     |
| ADR-020           | Ichebo Handbook as standalone product (ADR supersedes Handbook-as-tenant) | Layer 3 + Layer 5           |
| ADR-021           | Ichebo Media as standalone product (Version 3+)                           | Layer 3 + Layer 4 + Layer 5 |

**-- LAYER 1**

**Client Surfaces**

Three products. One design system. Different canvases, same visual language.

## **2.1 Ichebo Web - Apostolic Command Shell**

| **Attribute** | **Value**                                                                          |
| ------------- | ---------------------------------------------------------------------------------- |
| URL           | app.ichebo.org                                                                     |
| Technology    | Django 4.2 templates + HTMX                                                        |
| Primary users | Level 3-5 stewards, coordinators, architects                                       |
| Rendering     | Server-side rendered HTML. HTMX handles dynamic interactions without page reloads. |
| Status        | Version 2 complete and in production                                               |
| ADR reference | ADR-005, ADR-012, ADR-014, ADR-015                                                 |

**The Apostolic Command Shell - Four-Column Architecture**

| **Zone**        | **Width**                  | **Function**                                                                                              |
| --------------- | -------------------------- | --------------------------------------------------------------------------------------------------------- |
| Primary Sidebar | 72px - Ink dark (#0E0E0E)  | Global app switcher. Icon + label. Active state: 3px red left rule. Tenancy Hub pinned to bottom.         |
| Context Bar     | 240px - Ink 2 (#1A1A1A)    | App-specific navigation, actions, editorial controls. Governance app button style is the standard.        |
| The Stage       | Flexible - Stone (#F5F3F0) | The sovereign canvas. Record rendering, markdown authorship, data display. Playfair Display for headings. |
| Options Bar     | 300px - Stone 2 (#ECE9E4)  | Tabbed sidecar. Record metadata, HRS relationships, Bible tool, quick-access forms.                       |

**Dual-Shell Architecture - Stage Mode and Mobile Mode**

Every template in the Django web app implements two rendering paths simultaneously from the same template inheritance tree:

- Stage Mode ({% block ws_content %}): Level 3+ users on viewport ≥1024px. The Apostolic Command Shell four-column grid.
- Mobile Mode: All users on mobile viewport. Standard pages use `{% block content %}`. Pages with full-screen mobile experiences (e.g. Bible reader) use the dedicated `/m/` URL pattern with a standalone minimal template. Both are Mobile Mode — the latter is purpose-built, not a workaround.

**Implementation status (2026-06-18 audit):** approved, not yet built. See roadmap Phase 5.1 amendment note.

**Activity Hub pattern:** On mobile, multi-tab app sections (Activity, Calendar) consolidate into a single shell URL with HTMX tab dispatch. Separate desktop URLs for sub-sections remain unchanged. This avoids re-rendering the hero and navigation on each tab.

**Implementation status (2026-06-18 audit):** approved, not yet confirmed built in current code.

Neither is a fallback or degradation of the other. Both are designed for their canvas. CSS switching via .ws-active class on the body element, toggled by inline JavaScript on base.html.

**The Desk - Governance Authorship Surface**

The Desk occupies The Stage when the user is in authorship mode. It is the editorial canvas for all governance record creation. Key properties:

- Markdown authorship canvas - the writing surface for governance records
- Record routing - record types selected in Context Bar open forms/views in The Stage
- Writing canvas max-width: 680px centred in The Stage
- Options Bar serves The Desk: record properties, HRS relationships, Bible tool
- All governance record creation and editing routes through The Desk - no full-page forms

**Amended by ADR-022 (2026-06-09):** The Desk is relocated into the Handbook surface. "The Desk is the canonical governance authorship surface" is superseded by "The Handbook is the canonical governance authorship surface; The Desk editor is embedded within it." Implemented in code as of the 2026-06-18 audit.

## **2.2 Ichebo Desktop**

| **Attribute**  | **Value**                                                         |
| -------------- | ----------------------------------------------------------------- |
| Technology     | Flutter (Dart) - Windows, macOS, Linux                            |
| Architecture   | Local-first. SQLite primary. Cloud sync via Go Sync Engine.       |
| Primary users  | Community steward - single Sceptre Community per installation     |
| Status         | Version 3+ - planned. Layer 6 of the roadmap.                     |
| Repository     | ichebo-desktop (separate from Django platform and Flutter mobile) |
| ADR references | ADR-001 (amended), ADR-016, ADR-017, ADR-018, ADR-019             |

**Flutter-Go Integration Boundary**

The boundary between Flutter (UI) and Go (Sync Engine) is strictly defined:

- FFI is for control only - six exported functions: SyncStart, SyncStop, SyncNow, SyncStatus, SyncConflictCount, SyncResolveConflict
- SQLite is for data - Flutter reads all display data directly from SQLite using sqflite package
- No data passes through the FFI boundary - FFI calls return control signals and status strings, not entity data
- The Go Sync Engine writes to SQLite. Flutter reads from SQLite. Clean separation.

## **2.3 Ichebo Mobile**

| **Attribute** | **Value**                                                              |
| ------------- | ---------------------------------------------------------------------- |
| Technology    | Flutter (Dart) - Android-first, iOS Version 3+                         |
| Primary users | All members, Level 0b through Level 5                                  |
| Backend       | DRF API - same endpoints as web. Delta sync via GET /api/sync/changes/ |
| Status        | In development - repository: ichebo-mobile                             |
| ADR reference | ADR-001 (amended), ADR-015                                             |

Ichebo Mobile is distinct from both Ichebo Desktop and the Django Mobile Mode web shell:

- Mobile Mode (Django): browser-based mobile rendering from Django templates - the web fallback when the Flutter app is unavailable
- Ichebo Mobile (Flutter): the native Flutter app - the primary long-term mobile surface
- Both exist simultaneously; Mobile Mode is the fallback; Flutter app is the destination
- The Flutter app and Mobile Mode share visual resemblance - the mobile UI in the browser informs the Flutter UI

**-- LAYER 2**

**API Gateway**

Current: Nginx + DRF routing. Future: dedicated Go gateway.

## **3.1 Current State - Nginx + DRF**

In Versions 1 and 2, the API gateway function is performed by Nginx + Gunicorn routing all traffic to the Django DRF API. There is no dedicated gateway process.

**Nginx configuration**

server {

listen 443 ssl;

server_name app.ichebo.org;

\# SSL certificates (Let's Encrypt via Certbot)

ssl_certificate /etc/letsencrypt/live/app.ichebo.org/fullchain.pem;

ssl_certificate_key /etc/letsencrypt/live/app.ichebo.org/privkey.pem;

\# Static files served by Nginx directly (not Django)

location /static/ {

alias /home/ics/ics/staticfiles/;

expires 30d;

add_header Cache-Control "public";

}

\# Media files via MinIO

location /media/ {

proxy_pass <http://localhost:9000/ics-media/>;

}

\# All other requests → Django via Gunicorn

location / {

proxy_pass <http://127.0.0.1:8001>;

proxy_set_header Host \$host;

proxy_set_header X-Real-IP \$remote_addr;

proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;

proxy_set_header X-Forwarded-Proto \$scheme;

}

}

**Gunicorn configuration**

\# gunicorn.conf.py

bind = "127.0.0.1:8001"

workers = 3 # CPU cores × 2 + 1 - for CX32 (4 vCPU): workers = 9

timeout = 120

accesslog = "/var/log/gunicorn/ics_access.log"

errorlog = "/var/log/gunicorn/ics_error.log"

**Systemd service**

\# /etc/systemd/system/ics.service

\[Unit\]

Description=Ichebo Gunicorn Service

After=network.target

\[Service\]

User=ics

WorkingDirectory=/home/ics/ics/backend

ExecStart=/home/ics/ics/venv/bin/gunicorn ics_project.wsgi:application -c gunicorn.conf.py

Restart=on-failure

Environment=DJANGO_SETTINGS_MODULE=ics_project.settings.production

\[Install\]

WantedBy=multi-user.target

## **3.2 Future State - Dedicated Go Gateway (Version 3+)**

When the Go engine layer matures and services are extracted, a dedicated API Gateway will be introduced. It will:

- Route requests to the correct service (Django web, Records Engine, Activity Engine, etc.)
- Handle auth token validation centrally - extracted from individual services
- Inject tenant context from the materialized path into every request
- Enforce rate limiting per tenant
- Provide a stable URL space while services evolve behind it

The client (Flutter, browser) never knows which service answers its request. The gateway owns the URL contract.

**-- LAYER 3**

**Application Services**

Django web layer, DRF API, Paraclete, Notifications. No domain logic lives here.

## **4.1 Django Web Application**

| **Attribute**   | **Value**                                                           |
| --------------- | ------------------------------------------------------------------- |
| Framework       | Django 4.2 LTS - do not upgrade to 5.x without ADR-002 amendment    |
| Role            | Web layer and API adapter. Not the domain logic owner.              |
| Template engine | Django templates + HTMX (no React, Vue, or JS frameworks)           |
| Auth            | Django session auth for web. DRF token auth for mobile and Desktop. |
| ORM             | Django ORM → PostgreSQL. Models map to the data contract schema.    |
| Static files    | Collected to /staticfiles/ and served by Nginx                      |
| Media files     | Django-storages → MinIO (S3-compatible). Bucket: ics-media.         |

**Django app structure (canonical)**

~/ics/backend/

ics_project/ ← Django project settings + root URLs

accounts/ ← User, UserProfile, UserPermission models + auth

tenants/ ← Tenant model + path resolution + ServiceOrder model

records/ ← Record + Relationship models (Records Engine Django layer)

activity/ ← Activity + ActivityLog models (Activity Engine Django layer)

learn/ ← CertificationConfirmation model + curriculum endpoint

bible/ ← BibleTranslation, BibleBook, BibleVerse models

community/ ← Community App (UI + coordination layer, no models)

governance/ ← Governance App (UI layer only, no models)

calendar_app/ ← Calendar aggregation service (no models)

paraclete/ ← Orchestration service (ParacletePrompt model only)

video_live/ ← Video / Live App (no models - uses Activity + records)
  [SUPERSEDED 2026-06-23, see video-direction-v2-plan.md — already stale before that
   document: BroadcastSchedule is a real model. video_live is now models/webhooks
   infrastructure only; its app templates/views/URLs and sidebar icon are retired.
   Consumed directly by community/ and learn/.]

notifications/ ← Notification model

frontend/ ← Static assets (CSS, storage.js, navbar.js)

**The separation of concerns rule**

**Rule - enforced**

No domain logic lives in Django apps. Business rules go into Python modules that Django calls (Phase 1) and eventually into Go engines (Phase 2+). Django views prepare context and call services - they do not contain decision logic. Community App and Governance App own no models - they are UI and coordination layers only.

## **4.2 DRF API Layer**

The Django REST Framework API is the service layer for Flutter Mobile and Ichebo Desktop sync. It is retained permanently - not replaced by the Go engine layer.

| **Endpoint group**                                                | **Consumers**                                        |
| ----------------------------------------------------------------- | ---------------------------------------------------- |
| POST /api/auth/login/ register/ logout/ + GET/PATCH /api/auth/me/ | Flutter Mobile, Ichebo Desktop (initial auth)        |
| GET/POST /api/records/ + GET/PATCH/DELETE /api/records/{id}/      | Flutter Mobile reads; Desktop sync via push/pull     |
| GET/POST /api/activities/ + /api/activities/{id}/                 | Flutter Mobile reads; Desktop sync                   |
| GET/POST /api/relationships/                                      | Flutter Mobile reads; Desktop sync                   |
| GET /api/bible/\* + /api/learn/\* + /api/community/health/        | Flutter Mobile only                                  |
| GET /api/paraclete/digest/ reminders/ prompt/                     | Flutter Mobile + Ichebo Web Dashboard                |
| GET /api/sync/changes/?since=                                     | Flutter Mobile delta sync (Part 17 of data contract) |
| POST /api/sync/push/ + GET /api/sync/pull/                        | Ichebo Desktop Sync Engine only                      |
| POST /api/sync/validate-licence/                                  | Ichebo Desktop first-run activation                  |
| GET /api/notifications/\* + POST /api/permissions/\*              | Flutter Mobile + Ichebo Web                          |

**API versioning strategy**

Current state: all endpoints at /api/ (unversioned) - acceptable during development. Before first mobile production release: all endpoints move to /api/v1/. The v1 prefix is then frozen - breaking changes require /api/v2/.

## **4.3 Paraclete Service**

| **Attribute**  | **Value**                                                          |
| -------------- | ------------------------------------------------------------------ |
| Location       | paraclete/ Django app                                              |
| Nature         | Standalone orchestration service - reads only, writes nothing      |
| Implementation | Pure Python - no LLM calls in MVP. Rule-based. No Celery.          |
| Cache          | Django filesystem cache (5-minute TTL) - no Redis in Version 2     |
| Output         | ParacleteDigest dataclass - consumed by Dashboard and Flutter Home |
| ADR            | ADR-010                                                            |

Paraclete reads from four data sources: Activity, ActivityLog, Record, UserProfile/UserPermission. It applies rule-based logic to generate a digest - discipline prompt, pending activities, habit streaks, active enrolments, suggestions. It never writes to any engine.

LLM integration (Layer 10): when Paraclete requires AI-generated insights rather than rule-based prompts, LLM integration becomes available. This requires significant architectural design - privacy implications, data boundaries, cost management. Not until Version 3 is complete.

## **4.4 Notification Service**

| **Attribute**      | **Value**                                                                   |
| ------------------ | --------------------------------------------------------------------------- |
| Location           | notifications/ Django app                                                   |
| Delivery - in-app  | HTMX polling at 60-second intervals on the web. No WebSockets in Version 2. |
| Delivery - email   | Brevo SMTP - certification confirmed, level advanced, tenant invitation.    |
| Delivery - push    | FCM via notifications/fcm.py - Flutter Mobile only                          |
| Real-time (future) | Django Channels + WebSockets - Layer 10 only                                |

**-- LAYER 4**

**Domain Engines**

Go modules. Portable. Embeddable. The domain logic layer that Django calls and Desktop embeds.

## **5.1 Why Go for the Engines**

The domain engines are built in Go for five specific reasons:

| **Property**   | **Go advantage for Ichebo**                                                                                                                                                 |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Single binary  | A Go binary has no runtime dependencies. Compile once, run anywhere. No virtualenv, no Node runtime, no installation process on the device.                                 |
| Cross-platform | One Go codebase compiles to Windows, macOS, Linux, and Android (via gomobile). The same Records Engine runs on a Windows Desktop and a cloud Linux server.                  |
| Concurrency    | Goroutines are lightweight and idiomatic. The Sync Engine runs in a background goroutine while the steward actively uses the UI - two lines of Go, no threading complexity. |
| Embeddability  | Go binaries embed cleanly into Flutter via dart:ffi. The engine runs inside the app, not as a separate server process. This is what makes offline-first possible.           |
| Performance    | Fast startup, low memory, efficient CPU use. Critical for Ichebo Desktop running on a 4GB RAM Windows PC from 2019 that is also running other software.                     |

## **5.2 The Six Engines**

| **Engine**           | **Language-agnostic specification**                                                                                                                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Records Engine       | Create, read, update, soft-delete records. Enforce record_class permission gate, record_family/record_type taxonomy, four mandatory fields. Works against SQLite (local) and PostgreSQL (cloud).     |
| Activity Engine      | Log participation events. Track ActivityLog entries (immutable). Calculate progress. Recurring activity logic. Status transition → ActivityLog entry written atomically in same transaction.         |
| Relationships Engine | Create, read, traverse relationships. Direction-aware (directed vs bidirectional). Enforce exactly one of to_record_id or bible_verse_id non-null. Controlled relationship type vocabulary.          |
| Bible Engine         | Scripture text, translation resolution, reference parsing. Returns text only - no HRS logic. KJV, ASV, WEB bundled in Desktop installer (30MB SQLite file). Read-only - never pushed to cloud.       |
| Calendar Engine      | Event aggregation from Activity table. KGS Annual Rhythm and governance cycle events. Returns CalendarEvent\[\] sorted by scheduled_at. Pull-only in Desktop MVP.                                    |
| Sync Engine          | ChangeLog management, Push/Pull/Resolve. Orchestrates the other five engines during sync. Standalone Go binary embedded in Desktop via FFI. The strategic secret sauce. Full specification in DOC C. |

## **5.3 Engine Interface - The Contract**

Every engine implements the Engine interface. The Sync Engine calls engines through the Registry - never directly. This decouples transport from domain logic.

// Engine is the interface every domain engine implements.

type Engine interface {

EntityType() string // "record" | "activity" | "relationship" | "bible_verse" | "calendar_event"

// Apply writes a cloud-sourced entity to the local store inside a transaction.

// Enforces all domain rules from the data contract.

Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error

// Extract reads a local entity and returns it as JSON for the push payload.

Extract(store store.Store, entityID uuid.UUID) (json.RawMessage, error)

// Validate checks a payload conforms to domain rules before Apply.

Validate(payload json.RawMessage) error

}

// Registry maps entity types to engines.

// Built once at startup. Immutable after construction.

type Registry struct { engines map\[string\]Engine }

func (r \*Registry) For(entityType string) Engine // panics if not found - programming error

func (r \*Registry) MustFor(entityType string) Engine

## **5.4 The Three-Phase Separation Plan**

Django does not become Go overnight. The separation is progressive and risk-managed.

| **Phase**                                         | **What changes**                                                                                                                                                                              | **When**                             |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| Phase 1 - Clean Boundaries (current)              | Stop adding domain logic to Django. Extract all business rules into Python modules that Django calls. Django becomes a thin HTTP layer that calls modules. No Go yet.                         | Now through Version 2 → 3 transition |
| Phase 2 - Extract Engines (Desktop build)         | Go engines built. Cloud Django begins calling engine specifications via internal API. Django becomes a thin adapter. Sync Engine embedded in Desktop, also run as cloud coordination service. | Layer 5 (E.1-E.4) of roadmap         |
| Phase 3 - Service Extraction (as products mature) | Community social graph extracted when it needs to scale. Video Engine built as Ichebo Media. Formation Engine extracted as Ichebo Formation service. API Gateway formalised.                  | Layer 8-10 of roadmap                |

**-- LAYER 5**

**Data Stores**

PostgreSQL for cloud. SQLite for local. MinIO for objects. One data contract governs all.

## **6.1 PostgreSQL - Cloud Database**

| **Attribute** | **Value**                                                      |
| ------------- | -------------------------------------------------------------- |
| Location      | Hetzner VPS - localhost:5432 (not exposed externally)          |
| Version       | PostgreSQL 14+ (Ubuntu 22.04 default package)                  |
| Database name | ics_db                                                         |
| Connection    | Django ORM via psycopg2. Not exposed directly to any client.   |
| Access        | Only via Django application layer. Never direct client access. |
| Backup        | Daily pg_dump to /home/ics/backups/ with 7-day retention       |

**Critical schema rules (data contract Part 1)**

- UUID primary keys on all entities (after Phase E.1 migration). No auto-increment integers.
- Four mandatory fields on every entity: id, tenant_id, created_by, created_at. No exceptions.
- Soft deletes only: deleted_at DateTimeField(null=True). No hard deletes.
- Single records table with record_family/record_type discriminator. No new content-type model tables.
- Materialised path for tenant hierarchy: path = "/global/africa/southafrica/gauteng/pretoria-north/sceptre-abc/"

**Key indexes**

\-- Records table

CREATE INDEX idx_records_tenant_id ON records(tenant_id);

CREATE INDEX idx_records_record_class ON records(record_class);

CREATE INDEX idx_records_record_family ON records(record_family);

CREATE INDEX idx_records_record_type ON records(record_type);

CREATE INDEX idx_records_deleted_at ON records(deleted_at);

CREATE INDEX idx_records_custom_fields ON records USING gin(custom_fields);

\-- Activity table

CREATE INDEX idx_activity_tenant_id ON activity(tenant_id);

CREATE INDEX idx_activity_assigned_to ON activity(assigned_to);

CREATE INDEX idx_activity_status ON activity(status);

CREATE INDEX idx_activity_due_at ON activity(due_at);

\-- UserPermission table (materialised path scoping)

CREATE INDEX idx_perm_tenant_path ON user_permission(tenant_path varchar_pattern_ops);

CREATE INDEX idx_perm_is_active ON user_permission(is_active);

## **6.2 SQLite - Local Database (Desktop + Mobile)**

| **Attribute**           | **Value**                                                                                     |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| Used by                 | Ichebo Desktop (full read/write), Ichebo Mobile (read cache + delta sync)                     |
| Mode                    | WAL (Write-Ahead Logging) - mandatory for concurrent read + write                             |
| Access pattern          | Go Sync Engine writes. Flutter reads via sqflite package.                                     |
| File location (Desktop) | OS-appropriate app data directory (AppData on Windows, ~/Library on macOS, ~/.local on Linux) |
| Backup (Desktop)        | User-initiated backup to USB or cloud folder. Automatic backup reminder on sync (future).     |

**SQLite configuration (mandatory pragmas)**

\-- Applied on every connection open:

PRAGMA journal_mode=WAL; -- concurrent reads + one writer

PRAGMA busy_timeout=5000; -- wait 5s before failing on lock contention

PRAGMA foreign_keys=ON; -- enforce FK constraints

PRAGMA synchronous=NORMAL; -- safe + fast in WAL mode

**Desktop SQLite schema scope**

- In scope: members (UserPermission rows), activities, records (limited - announcements and gatherings received via sync), ChangeLog, ConflictQueue, Settings, Bible verses (bundled, read-only)
- Out of scope in MVP: Handbook governance records (read-only snapshots), Learn programme content (synced on demand)

## **6.3 MinIO - Object Storage (Interim)**

| **Attribute** | **Value**                                                                             |
| ------------- | ------------------------------------------------------------------------------------- |
| Location      | Hetzner VPS - same machine as Django. Port 9000.                                      |
| Type          | S3-compatible object storage                                                          |
| Storage       | 80GB HDD - ample for current stage (user avatars, file attachments, document uploads) |
| Bucket        | ics-media                                                                             |
| Access        | Django-storages library. Private bucket - presigned URLs (1-hour expiry) for access.  |
| Nginx proxy   | location /media/ { proxy_pass <http://localhost:9000/ics-media/>; }                   |

**Migration path**

When Ichebo Media (ADR-021) requires CDN delivery for video content, MinIO migrates to Hetzner Object Storage (S3-compatible, same API). The migration is straightforward - same interface, different endpoint. No application code changes required beyond the endpoint URL in settings. 80GB HDD is ample until video hosting is needed.

**File storage pattern in data contract**

The attachment record type (record_family: "reference", record_type: "attachment") stores file metadata in the Record row. The file itself is in MinIO. custom_fields\["file_url"\] carries the presigned URL with 1-hour expiry. No separate Attachment model.

**-- INFRASTRUCTURE**

**Production Environment**

Hetzner VPS. Ubuntu 22.04. Nginx + Gunicorn + systemd. No Docker until Version 3.

## **7.1 Server Specification**

| **Attribute** | **Value**                                                                                 |
| ------------- | ----------------------------------------------------------------------------------------- |
| Provider      | Hetzner Cloud                                                                             |
| Instance type | CX32 recommended (4 vCPU, 8GB RAM, 80GB SSD) - start CX22, resize as needed               |
| OS            | Ubuntu 22.04 LTS                                                                          |
| Data centre   | Nuremberg or Falkenstein (Europe) - closest to primary African user base via good peering |
| IP            | Static IPv4 - mapped to app.ichebo.org via DNS A record                                   |
| SSH           | Key-based only. Password auth disabled. Non-root deploy user: ics                         |
| Firewall      | UFW - allows OpenSSH and Nginx Full only. All other ports closed.                         |

## **7.2 Process Architecture**

Internet

│

▼

Nginx (port 80/443)

├── /static/ → /home/ics/ics/staticfiles/ (served directly, no Django)

├── /media/ → MinIO on localhost:9000 (proxied)

└── / → Gunicorn on localhost:8001

Gunicorn (3-9 workers, depending on VPS size)

│

▼

Django WSGI Application

│

├── PostgreSQL on localhost:5432

└── MinIO on localhost:9000

Systemd manages:

├── ics.service → Gunicorn (auto-restart on failure)

└── nginx.service → Nginx (auto-restart on failure)

MinIO runs as a standalone process (not systemd-managed in MVP):

## **7.3 Key File Locations**

/home/ics/ics/backend/ ← App code (git repo)

/home/ics/ics/backend/.env ← Secrets (mode 600, never committed)

/home/ics/ics/venv/ ← Python virtual environment

/home/ics/ics/staticfiles/ ← Collected static files (Nginx serves)

/home/ics/backups/ ← PostgreSQL daily dumps

/var/log/ics/ ← Django error logs

/var/log/gunicorn/ ← Gunicorn access + error logs

/etc/nginx/sites-available/ics ← Nginx config

/etc/systemd/system/ics.service ← Gunicorn systemd unit

## **7.4 SSL and Security**

- SSL certificates via Let's Encrypt (Certbot) - auto-renew every 90 days
- HSTS enabled: Strict-Transport-Security with max-age=31536000
- HTTPS redirect: all HTTP traffic (port 80) redirected to HTTPS (port 443)
- Django security settings in production.py: SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE
- Secret key: generated with python3 -c "import secrets; print(secrets.token_urlsafe(50))" - stored in .env only
- id_number field (UserProfile): encrypted with django-encrypted-model-fields. FIELD_ENCRYPTION_KEY in .env. Never returned in any standard API response.

## **7.5 Backup Strategy**

| **What**            | **How often - How long retained**                                         |
| ------------------- | ------------------------------------------------------------------------- |
| PostgreSQL database | Daily pg_dump → /home/ics/backups/ - 7-day retention on VPS               |
| .env file           | Manual backup when changed - stored in secure personal password manager   |
| Nginx config        | In git (without secrets) - auto-backed up with code                       |
| Application code    | GitHub - no separate backup needed                                        |
| MinIO data          | Manual snapshot when significant files added - no automated backup in MVP |

\# Daily backup script (/home/ics/backup.sh)

# !/bin/bash

DATE=\$(date +%Y%m%d)

BACKUP_DIR=/home/ics/backups

pg*dump -U ics_user ics_db > \$BACKUP_DIR/ics_db*\$DATE.sql

\# Keep last 7 days

find \$BACKUP_DIR -name "\*.sql" -mtime +7 -delete

echo "Backup complete: ics*db*\$DATE.sql"

\# Run daily via cron (crontab -e):

\# 0 2 \* \* \* /home/ics/backup.sh >> /var/log/ics/backup.log 2>&1

## **7.6 Deployment Workflow**

Code moves from development laptop to production server via Git:

- Write and test code locally (python manage.py runserver on laptop)
- Commit: git add . && git commit -m "feat: description" (one logical unit per commit)
- Push: git push origin version-2 (or main for production)
- On server: git pull origin version-2
- Install any new dependencies: pip install -r requirements.txt
- Run migrations: python manage.py migrate
- Collect static files: python manage.py collectstatic --no-input
- Restart Gunicorn: sudo systemctl restart ics
- Verify: curl <https://app.ichebo.org/api/health/> → {"status": "ok"}

**No Docker until Version 3 (ADR-009)**

Nginx + Gunicorn + systemd is the production stack. It is battle-tested, well-documented, and understood. Docker adds complexity - container orchestration, image builds, networking - that is not needed until the platform has multiple services requiring independent scaling. That threshold is Version 3.

## **7.7 Email - Brevo SMTP**

| **Attribute**    | **Value**                                                                       |
| ---------------- | ------------------------------------------------------------------------------- |
| Provider         | Brevo (formerly Sendinblue)                                                     |
| Tier             | Free tier - 300 emails/day                                                      |
| Integration      | Django email backend (SMTP). django-anymail or direct SMTP settings.            |
| Events triggered | Certification confirmed, level advanced, tenant invitation, induction placement |
| Configuration    | EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD in .env                        |

**-- DATA ARCHITECTURE**

**The Data Contract**

One contract. Every entity. Every schema. Every rule. Canonical.

## **8.1 The Data Contract as the Source of Truth**

The data contract (data-contract-v11-canonical-2026-05-13.md) is the authoritative schema reference for the entire ecosystem. It governs:

- Every model schema - Django PostgreSQL and SQLite local
- Every API response shape - DRF serializers
- Every engine domain rule - Go and Python implementations
- Every permission algorithm - record_class, visibility, competence level gates

When the data contract and the code disagree, the data contract wins. Fix the code.

## **8.2 The Tenant Hierarchy - Materialised Path**

Every tenant has a path field. Scope queries use prefix matching - no recursive joins, no depth limit.

\# Tenant hierarchy example

/global/ ← Prime Tenancy

/global/africa/ ← Continental

/global/africa/southafrica/ ← National

/global/africa/southafrica/gauteng/ ← Provincial

/global/africa/southafrica/gauteng/pretoria-north/ ← District

/global/africa/southafrica/gauteng/pretoria-north/sceptre-abc/ ← Church Node

\# Scope query - find all records visible to a district steward:

WHERE tenant_path LIKE '/global/africa/southafrica/gauteng/%'

\# Agency tenants (6 KGS Service Domains) - constitutional, is_agency=True:

/global/apostolic-ministry/

/global/leadership-governance/

/global/formation-teaching/

/global/mission-outreach/

/global/community-life-care/

/global/operations-stewardship/

\# System singletons:

/global/handbook/ ← Handbook tenant (current production workaround - see ADR-020)

/global/induction/ ← Induction tenant (Level 0 entry point)

## **8.3 The Records Table - Single Table Pattern**

All content lives in one records table. record_class is the permission gate. record_family and record_type are the taxonomy. No new model tables for new content types.

| **record_family** | **record_type values**                                                                                                               | **record_class**          |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| journal           | prayer, spirit, dream, dar, note                                                                                                     | personal                  |
| governance        | class, principle, concept, divine_pattern, narrative, subject, entity, mandate, statement, programme, framework, protocol, procedure | governance                |
| activity          | event, campaign, project, habit, task, skill                                                                                         | organizational            |
| learning          | programme, course, lesson, assignment, quiz, certification                                                                           | organizational            |
| reference         | key, property, attachment                                                                                                            | personal / organizational |
| bible             | bible_note                                                                                                                           | personal                  |
| community         | announcement, gathering                                                                                                              | organizational            |

## **8.4 The Permission Algorithm**

def can_access(user, record):

\# 1. Handbook short-circuit (current production implementation)

if record.tenant and record.tenant.tier == 'handbook':

REFERENCE_LIBRARY_TYPES = \['class', 'principle', 'concept', 'divine_pattern'\]

if record.record_type in REFERENCE_LIBRARY_TYPES:

return user.competence_level >= 3 # Reference Library: Level 3+ read

else:

return user.competence_level >= 4 # Mandate branch: Level 4+ read

\# Write always requires competence_level >= 5

\# 2. record_class gate - check FIRST

if record.record_class == 'governance' and user.competence_level < 4:

return False

\# 3. Visibility scope

if record.permissions\['visibility'\] == 'private':

return record.created_by == user.id

if record.permissions\['visibility'\] == 'tenant':

return UserPermission.objects.filter(

user=user, tenant_path=record.tenant.path, is_active=True).exists()

if record.permissions\['visibility'\] == 'collective':

return UserPermission.objects.filter(

user=user,

tenant*path*\_startswith=record.tenant.collective_root_path,

is_active=True).exists()

if record.permissions\['visibility'\] == 'public':

return user.competence_level >= 1

\# 4. Level gate

return user.competence_level >= record.permissions\['required_level'\]

## **8.5 The competence_level Write Constraint**

**Absolute constraint - ADR-006**

competence_level may only be written by POST /api/learn/certifications/{id}/confirm/. No other code path, no other endpoint, no other method may write to this field. The constraint is enforced at the service layer in learn/services.py::confirm_certification_record(). This is the sole authorised write path. No exceptions.

**-- REPOSITORIES**

**Code Organisation**

Four repositories. Clean boundaries. Each with its own toolchain and deployment.

## **9.1 Repository Map**

| **Repository** | **Contents and role**                                                                                                                                                 |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ichebo         | Django web platform - Python, Django 4.2, DRF, PostgreSQL, HTMX templates. The cloud platform. One backend for web, mobile API, and Desktop sync. Active. Production. |
| ichebo-mobile  | Flutter mobile app - Dart, Flutter. Android-first. Consumes DRF API. Separate toolchain. Active development.                                                          |
| ichebo-desktop | Flutter Desktop app - Dart, Flutter, dart:ffi. Windows/macOS/Linux. Embeds ichebo-sync. Planned (Layer 6).                                                            |
| ichebo-sync    | Go Sync Engine - Go modules. Standalone binary and shared library. Shared between Desktop and future products. Planned (Layer 5 E.3-E.4).                             |

## **9.2 Branch Strategy - ichebo (Django)**

main ← production (always deployable)

├─ mvp ← MVP complete (6c43ce9) \[frozen\]

├─ version-2 ← Version 2 complete \[frozen\]

└─ version-3 ← active ecosystem development

├─ v3-uuid-migration ← E.1 UUID schema migration

├─ v3-soft-delete ← E.2 soft delete pattern

├─ v3-go-engines ← E.3 Go foundation engines

└─ v3-sync-engine ← E.4 Sync Engine cloud endpoints

## **9.3 Development Environment**

| **Tool**             | **Usage**                                                                                                             |
| -------------------- | --------------------------------------------------------------------------------------------------------------------- |
| VS Code + Remote-SSH | Primary development environment. SSH into Hetzner VPS directly. Edit files on server, run Django locally for testing. |
| Python 3.11+         | Django application runtime. Virtual environment at /home/ics/ics/venv/                                                |
| Go 1.22+             | Engine development. ichebo-sync repository. go build, go test.                                                        |
| Flutter 3.x (stable) | Mobile and Desktop development. Flutter SDK on development machine.                                                   |
| pgAdmin or psql      | PostgreSQL management. psql -U ics_user -d ics_db -h localhost                                                        |
| Postman or HTTPie    | API testing. DRF token auth headers required.                                                                         |

**-- ROADMAP**

**Architecture Evolution**

Version 1 and 2 complete. Version 3+ is the ecosystem.

## **10.1 Version 2 → Version 3 Transition Gates**

Before any Version 3 ecosystem work begins, two migrations must be complete:

**Gate E.1 - UUID Migration**

All Django model primary keys migrated to UUIDField. All existing records have UUID PKs. All API responses return UUID strings. No auto-increment IDs remain. This is the foundation for local-first data and the Sync Engine.

**Gate E.2 - Soft Delete Pattern**

deleted_at DateTimeField(null=True) added to all models. Default querysets filter deleted_at IS NULL. No hard deletes possible via any API endpoint. This is required for Sync Engine conflict resolution and audit trail integrity.

## **10.2 Version 3 Build Order**

- E.1 UUID migration - all Django models
- E.2 Soft delete pattern - all Django models
- E.3 Go foundation engines - Records, Activity, Relationships, Bible, Calendar (ichebo-sync repository)
- E.4 Sync Engine - ChangeLog, Push, Pull, Resolve, ConflictQueue, FFI bridge (ichebo-sync repository)
- D.1-D.10 Ichebo Desktop - Flutter, SQLite, FFI bridge to ichebo-sync (ichebo-desktop repository)
- H.2 Real-world use - get communities on Desktop, validate local-first in practice
- Layer 7 Flutter Mobile app - full native mobile (ichebo-mobile repository)
- Layer 8 Ichebo Media - Go + FFmpeg + Hetzner Object Storage
- Layer 9 Ichebo Handbook - standalone product, Handbook-as-tenant migration

## **10.3 Layer 10 - Scale (future, no timeline)**

Do not build any of these until Version 3 is complete and in real-world use:

- Docker Compose - containerisation for scaling and handoff
- Redis + Celery - background task processing at scale
- Django Channels + WebSockets - real-time notification delivery
- LLM integration for Paraclete - AI-generated insights with privacy architecture
- iOS - after Android stable in production (requires Apple Developer account, Mac build machine)
- API Gateway (Go) - formalised when services multiply

**Ichebo Christian Services**

_DOC D - Technical Architecture Document v1.0 - May 2026 - Canonical Reference_