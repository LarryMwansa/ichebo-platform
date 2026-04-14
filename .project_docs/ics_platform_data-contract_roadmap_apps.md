ICS Platform

**Data Contract & Architecture Document**

Version 9 Amendments

2026-04-10 · Governance App --- Pre-Build

**v9 Amendment Summary**

> *Previous version: v8 --- 2026-04-08. Everything in v8 is unchanged
> and remains locked unless explicitly amended below. Read this document
> against v8 before implementing the Governance App.*

  -----------------------------------------------------------------------------
  **\#**   **Amendment**                                   **Affects**
  -------- ----------------------------------------------- --------------------
  1        record_type enum extended: added \'article\' to Part 3.1
           journal family                                  

  2        journal family → type mapping updated to        Part 3.1
           include \'article\'                             

  3        Property Attributes custom_fields specification Part 15.3 (new)
           added for Reference Library types               

  4        Handbook read access amended: Level 3+ for      Part 2.5.2
           Reference Library, Level 4+ for Mandate branch  

  5        Governance record lifecycle defined: draft →    Part 15.4 (new)
           active → locked → superseded                    

  6        calendar record type deferred to Phase 2 of     Part 15.5 (new)
           Governance App                                  

  7        Part 15 (Governance App Engine) added in full   Part 15 (new)

  8        Part 12 updated: Task 5.5 Governance App marked Part 12
           as system design complete                       
  -----------------------------------------------------------------------------

**Amendment 1--2 --- Part 3.1: record_type enum + journal family
mapping**

**1. record_type enum --- addition**

The following type is added to the record_type enum in Part 3.1:

> record_type: \"\... \| article \| \...\"
>
> *\'article\' is added to the journal family. It represents a general
> written entry or essay --- structured writing that is more intentional
> than a note but not a sermon. It does not exist in the governance
> family. Governance uses \'narrative\' for written accounts carrying
> governance meaning.*

**2. journal family → type mapping --- updated**

The journal family → type mapping in Part 3.1 is amended as follows:

  -----------------------------------------------------------------------
  **Family**     **Types (updated)**
  -------------- --------------------------------------------------------
  journal        prayer \| dream \| note \| sermon \| article

  governance     (unchanged) class \| principle \| concept \|
                 divine_pattern \| narrative \| subject \| entity \|
                 mandate \| statement \| programme \| framework \|
                 protocol \| procedure \| calendar

  activity       (unchanged)

  learning       (unchanged)

  reference      (unchanged --- key \| property)

  bible          (unchanged)

  community      (unchanged)
  -----------------------------------------------------------------------

**3. article --- access and default permissions**

  -----------------------------------------------------------------------
  **Field**           **Value**
  ------------------- ---------------------------------------------------
  record_class        personal

  record_family       journal

  record_type         article

  Default visibility  private

  Who can create      Level 1+ (any active member)

  Who can read        created_by only (private default); can be changed
                      to tenant or public by author

  Governance linkage  A Level 5 operator may link a journal article into
                      a Mandate record via Relationship
                      (relationship_type: \'references\', direction:
                      \'directed\')
  -----------------------------------------------------------------------

**Amendment 3 --- Part 15.3: Property Attributes in custom_fields**

Reference Library governance records (record_type: class, principle,
concept, divine_pattern) carry six HRS Property Attributes as
custom_fields. These attributes characterise the nature and relational
position of each Property as produced by the Hierarchy and Relationship
System methodology.

**Property Attributes specification**

  ---------------------------------------------------------------------------------
  **Attribute**   **Field key**           **Type**     **Values / Notes**
  --------------- ----------------------- ------------ ----------------------------
  Complexity      complexity              string \|    free-text --- describes
                                          null         structural depth of the
                                                       property

  Relationship    relationship_polarity   enum \| null \'subjective\' (ruling) \|
                                                       \'objective\' (subservient)

  Position        position                enum \| null \'up\' \| \'down\' \|
                                                       \'left\' \| \'right\' \|
                                                       null

  Direction       direction               enum \| null \'forward\' \| \'backward\'
                                                       \| null

  Speed           speed                   enum \| null \'fast\' \| \'slow\' \| null

  Emotional Tone  emotional_tone          string \|    free-text --- e.g.
                                          null         \'fearful\', \'dread\',
                                                       \'vengeful\'
  ---------------------------------------------------------------------------------

**custom_fields schema for Reference Library record types**

> // Applies to: record_type IN (\'class\', \'principle\', \'concept\',
> \'divine_pattern\')
>
> // record_family: \'governance\', record_class: \'governance\'
>
> custom_fields: {
>
> complexity: \"string \| null\",
>
> relationship_polarity: \"subjective \| objective \| null\",
>
> position: \"up \| down \| left \| right \| null\",
>
> direction: \"forward \| backward \| null\",
>
> speed: \"fast \| slow \| null\",
>
> emotional_tone: \"string \| null\"
>
> }
>
> *All six fields are optional (null by default). The Governance App
> authorship form presents them as optional structured fields on the
> Reference Library entry form. They are not validated beyond enum
> membership where applicable. No new model or migration is required ---
> custom_fields is already a JSONField on the Record model.*

**Amendment 4 --- Part 2.5.2: Handbook Read Access**

**Amended rule**

Part 2.5.2 previously stated: \'Read: Level 5 only / Write: Level 5
only.\'

This is amended as follows:

  ------------------------------------------------------------------------
  **Action**            **Level       **Scope**
                        required**    
  --------------------- ------------- ------------------------------------
  Read --- Reference    Level 3+      record_type IN: class, principle,
  Library records                     concept, divine_pattern, subject,
                                      entity, narrative, framework

  Read --- Mandate      Level 4+      record_type IN: mandate, statement,
  branch records                      programme, protocol, procedure

  Write (create, edit,  Level 5 only  All Handbook record types
  lock)                               

  Supersede a locked    Level 5 only  All Handbook record types
  record                              

  Link to scripture     Level 5 only  Relationship creation on Handbook
  (bible_verse_id)                    records
  ------------------------------------------------------------------------

> *The permission check algorithm (Part 7) Handbook short-circuit is
> amended: \'if record.tenant.tier == handbook: return
> user.competence_level \>= 3 (for read) or \>= 5 (for write).\' The
> Governance App view layer enforces the read/write split by record_type
> group. The DRF endpoint enforces the Level 3+ floor.*

**Amendment 5 --- Part 15.4: Governance Record Lifecycle**

Governance records (record_class: \'governance\') follow a defined
lifecycle. The \'submitted\' status exists in the data model but has no
UI in MVP --- it is reserved for a future approval queue.

**Lifecycle states**

  -------------------------------------------------------------------------
  **Status**   **Meaning**         **Who sets it**    **Transitions to**
  ------------ ------------------- ------------------ ---------------------
  draft        Being authored; not Creator (Level 4+  active, archived
               yet visible to      or Level 5)        
               others within scope                    

  active       Published and       Creator            locked, archived
               readable within                        
               access rules; still                    
               editable                               

  locked       Approved and fixed; Creator (Level 5   superseded (via new
               no further edits    for Handbook;      version)
               permitted; can only Level 4+ for       
               be superseded       tenant scope)      

  superseded   A new version has   System (set when   --- (terminal)
               been created; this  new version is     
               record is archived  created)           
               but retained in the                    
               version chain;                         
               readable via                           
               version history                        

  archived     Withdrawn from      Creator or Level 5 --- (terminal)
               active use; not                        
               superseded;                            
               retained for record                    

  submitted    DEFERRED ---        ---                ---
               reserved for future                    
               approval queue; no                     
               MVP UI                                 
  -------------------------------------------------------------------------

**Versioning pattern**

> // Creating a new version of a locked record
>
> // 1. Create new Record with version = old.version + 1
>
> // previous_version_id = old.id
>
> // 2. PATCH old Record: superseded_by = new.id, status =
> \'superseded\'
>
> // Both in transaction.atomic()

**Locking rules**

  -----------------------------------------------------------------------
  **Record scope**                **Who can lock**
  ------------------------------- ---------------------------------------
  Handbook records (tenant_path:  Level 5 only
  /global/handbook/)              

  Tenant governance records       Level 4+ within their scope_path
  (tenant_path:                   
  /global/africa/\.../)           
  -----------------------------------------------------------------------

> *A locked record cannot be edited. The only mutation path is
> supersession: creating a new draft, authoring changes, locking the new
> version, and patching the old record to superseded. This preserves the
> full version chain via previous_version_id / superseded_by.*

**Amendment 6 --- Part 15.5: calendar Record Type --- Deferred**

The governance record_type \'calendar\' is registered in the data
contract and remains in the record_type enum. However, it is deferred to
Phase 2 of the Governance App.

> *Reason: A governance calendar (representing the Great Calendar,
> spiritual seasons, appointed times, and governance cycles) requires a
> structured custom_fields specification and integration with the
> Calendar App that is too complex to define well in MVP without a full
> Calendars & Programmes implementation. MVP includes all other 13
> governance record types. The \'calendar\' type will receive its
> custom_fields specification in the v10 amendment when Phase 2 of the
> Governance App is designed.*

**Amendment 7 --- Part 15: Governance App Engine (Data Patterns &
Contracts)**

Part 15 is added in full below. The Governance App owns no models. It is
a UI and transaction coordination layer over the Records Engine ---
identical pattern to the Community App.

**15.1 Purpose**

The Governance App is the digital expression of the Prophet\'s Handbook
--- the Apostolic Properties system. It is organised around three
branches, each with a distinct direction of flow:

  ------------------------------------------------------------------------
  **Branch**     **Also known  **Direction**         **record_types**
                 as**                                
  -------------- ------------- --------------------- ---------------------
  Reference      Prophet\'s    Flows inward ---      class, principle,
  Library        Library       compiled from         concept,
                               Scripture via HRS     divine_pattern,
                                                     subject, entity,
                                                     narrative, framework

  Keys Library   Dream Library Flows inward and      record_family:
                               outward --- personal  \'reference\',
                               symbol-to-meaning     record_type: \'key\'
                               mappings              (personal, not
                                                     governance)

  Mandate        Apostolic     Flows outward ---     mandate, statement,
                 Mandate       received directives   programme, protocol,
                               translated into work  procedure
                               and platform          
  ------------------------------------------------------------------------

> *The Keys Library is record_class: \'personal\', not governance. It
> surfaces in the Governance App as a personal sub-section but is not
> subject to the Level 4+ governance gate. Any Level 3+ operator may
> maintain their own Keys Library.*

**15.2 Three-Surface Model**

> Governance App
>
> │
>
> ├── \'Reference Library\' (read surface --- Level 3+)
>
> │ Scope: tenant_path = /global/handbook/
>
> │ Types: class, principle, concept, divine_pattern,
>
> │ subject, entity, narrative, framework
>
> │ Shows: Browse by record_type; Property Attributes;
>
> │ Linked Records panel (HRS); scripture links
>
> │
>
> ├── \'Mandate\' (read Level 4+, write Level 5 only)
>
> │ Scope: tenant_path = /global/handbook/
>
> │ Types: mandate, statement, programme, protocol, procedure
>
> │ Shows: Browse by type; version history chain;
>
> │ Linked Records panel; linked Reference Library entries
>
> │
>
> └── \'My Keys\' (personal --- Level 3+)
>
> Scope: record_family: \'reference\', record_type: \'key\',
>
> created_by = request.user
>
> Shows: Personal symbol-to-meaning mappings;
>
> source journal entries (dream, note, spirit)

**15.3 User Roles in the Governance App**

  -------------------------------------------------------------------------
  **Level**       **Reference    **Mandate      **My Keys**    **Handbook
                  Library**      branch**                      write**
  --------------- -------------- -------------- -------------- ------------
  Seeker (0b)     ✗              ✗              ✗              ✗

  Member (1)      ✗              ✗              ✗              ✗

  Disciple (2)    ✗              ✗              ✗              ✗

  Steward (3)     Read only      ✗              Full           ✗
                                                (personal)     

  Senior Steward  Read only      Read only      Full           ✗
  (4+)                                          (personal)     

  Architect (5)   Read + Write   Read + Write   Full           Full
                                                (personal)     
  -------------------------------------------------------------------------

**15.4 HRS Linked Records Panel**

Every governance record detail view includes a Linked Records panel.
This panel surfaces all Relationship objects where from_record_id or
to_record_id = record.id.

  ------------------------------------------------------------------------
  **Relationship     **From → To**      **Displayed as**
  type**                                
  ------------------ ------------------ ----------------------------------
  part_of            principle →        \'Part of: \[framework title\]\'
                     framework          

  derived_from       concept →          \'Derived from: \[pattern
                     divine_pattern     title\]\'

  aligns_with        programme →        \'Aligns with: \[mandate title\]\'
                     mandate            

  authorised_by      procedure →        \'Authorised by: \[mandate
                     mandate            title\]\'

  references         narrative →        \'References: \[subject title\]\'
                     subject            

  references         governance record  Verse text rendered inline;
  (scripture)        → BibleVerse       book/chapter/verse label

  has_subject        framework →        \'Has subject: \[subject title\]\'
                     subject            

  has_entity         mandate → entity   \'Has entity: \[entity title\]\'
  ------------------------------------------------------------------------

> *The Linked Records panel is read-only in MVP. Creating new
> Relationship links is done via the record authorship form (Level 5
> only for Handbook records). Full graph visualisation is deferred to
> Phase 2.*

**15.5 Version History Chain**

Each governance record detail view includes a Version History section
when version \> 1 or previous_version_id is set. The version chain is
traversed via the previous_version_id and superseded_by fields.

> // Version history query
>
> GET /api/records/{id}/ → read previous_version_id, superseded_by
>
> // Walk backward through previous_version_id chain
>
> // Walk forward through superseded_by chain
>
> // Display as ordered list: v1 → v2 → v3 (current)

**15.6 Journal → Governance Linkage Pattern**

A Level 5 operator may link a personal journal record (Spirit Journal
entry, Dream Journal entry, or Article) into a Mandate branch governance
record. This is the primary input pathway from divine reception to
written record.

> // Journal → Mandate linkage
>
> POST /api/relationships/ {
>
> from_record_id: journal_record.id, // spirit note, dream, article
>
> to_record_id: mandate_record.id,
>
> relationship_type: \'references\',
>
> direction: \'directed\',
>
> notes: \'Source journal entry for this mandate\'
>
> }
>
> *This pattern is not a dual-write --- it is a simple Relationship
> link. The journal record remains personal (record_class:
> \'personal\'); the governance record is governance-class. The
> Governance App Linked Records panel surfaces these source links on the
> mandate detail view.*

**15.7 Keys Library --- Personal Record Pattern**

The Keys Library surfaces as \'My Keys\' in the Governance App. Key
Records are personal records --- not governance-class --- and are scoped
to the operator who created them.

  -----------------------------------------------------------------------
  **Field**           **Value**
  ------------------- ---------------------------------------------------
  record_class        personal

  record_family       reference

  record_type         key

  visibility          private (always --- Keys are operator-specific)

  Who can create      Level 3+ (operator-level access)

  Source data         Dream Journal records, Spirit Journal (note)
                      records

  Linkage             Relationship: dream/note record → key record
                      (relationship_type: \'derived_from\')

  custom_fields       symbol: string, meaning: string, source_context:
                      string \| null
  -----------------------------------------------------------------------

**15.8 Governance App DRF Endpoints**

The Governance App uses existing platform endpoints. No new DRF ViewSets
are introduced in MVP.

> \# Reference Library browsing
>
> GET
> /api/records/?record_family=governance&record_type=class&tenant_id={handbook_id}
>
> GET
> /api/records/?record_family=governance&record_type=principle&tenant_id={handbook_id}
>
> GET
> /api/records/?record_family=governance&record_type=concept&tenant_id={handbook_id}
>
> GET
> /api/records/?record_family=governance&record_type=divine_pattern&tenant_id={handbook_id}
>
> GET /api/records/{id}/ record detail (any governance type)
>
> \# Mandate branch browsing
>
> GET
> /api/records/?record_family=governance&record_type=mandate&tenant_id={handbook_id}
>
> GET
> /api/records/?record_family=governance&record_type=statement&tenant_id={handbook_id}
>
> \# Governance record create / edit / lock
>
> POST /api/records/ create governance record (Level 5 for Handbook)
>
> PATCH /api/records/{id}/ edit, change status, set locked_by/locked_at
>
> \# Versioning
>
> POST /api/records/ create new version (previous_version_id set)
>
> PATCH /api/records/{old_id}/ set superseded_by = new.id, status =
> \'superseded\'
>
> \# HRS Relationships
>
> GET /api/relationships/?from_record_id={id}
>
> GET /api/relationships/?to_record_id={id}
>
> POST /api/relationships/ create link (Level 5 for Handbook records)
>
> \# Keys Library (personal)
>
> GET
> /api/records/?record_family=reference&record_type=key&created_by={user_id}
>
> POST /api/records/ create key record
>
> PATCH /api/records/{id}/ edit key record
>
> \# Django template views (Governance App)
>
> GET /governance/ Governance App home (branch selector)
>
> GET /governance/library/ Reference Library browser
>
> GET /governance/library/{type}/ Browse by record_type
> (class/principle/etc.)
>
> GET /governance/library/{id}/ Record detail + Linked Records + Version
> History
>
> GET /governance/mandate/ Mandate branch browser
>
> GET /governance/mandate/{type}/ Browse by record_type
> (mandate/statement/etc.)
>
> GET /governance/mandate/{id}/ Record detail
>
> GET /governance/keys/ My Keys (personal --- Level 3+)
>
> GET /governance/keys/{id}/ Key record detail
>
> \# HTMX partials
>
> POST /governance/htmx/record/create/ create governance or key record
>
> POST /governance/htmx/record/lock/ lock a record
>
> POST /governance/htmx/record/supersede/ create new version
>
> GET /governance/htmx/relationships/{id}/ Linked Records panel partial
>
> GET /governance/htmx/versions/{id}/ Version History panel partial
>
> POST /governance/htmx/relationship/create/ create HRS link
>
> GET /api/governance/health/ health check

**Amendment 8 --- Part 12: Build Sequence Update**

Task 5.5 Governance App is updated in Part 12 as follows:

  ------------------------------------------------------------------------------------
  **Task**         **Status**         **Reference document**
  ---------------- ------------------ ------------------------------------------------
  5.1 Bible App    System design      2026-04-08-ics-bible-app-system-design_v2.md
                   complete           

  5.2 Learn App    System design      2026-04-07-ics-learn-app-system-design_v2.md
                   complete           

  5.3 Activity App System design      2026-04-08-ics-activity-app-system-design.md
                   complete           

  5.4 Community    System design      2026-04-08-ics-community-app-system-design.md
  App              complete           

  5.5 Governance   System design      2026-04-10-ics-governance-app-system-design.md
  App              complete           

  5.6 Profile +    Not started        ---
  Settings                            

  5.7              Not started        ---
  Notifications                       
  stub                                
  ------------------------------------------------------------------------------------

**Governance App --- Deferred to Phase 2**

-   calendar record type --- governance calendar with custom_fields
    specification and Calendar App integration

-   Full graph visualisation of HRS Relationship network

-   Approval queue --- submitted status UI (Level 4 submits, Level 5
    approves)

-   Tenant-scoped governance records for Level 4 district/province
    stewards

-   Rich text editor for governance record content (markdown textarea in
    MVP)

-   Governance record search and full-text filter across Handbook

-   Paraclete integration --- governance digest, mandate alignment
    suggestions

ICS Platform · Data Contract v9 · 2026-04-10 · Governance App pre-build


---

# ICS Platform — Full Build Roadmap

> **Version:** v2 — 2026-04-07
> **Previous version:** v1 — 2026-04-02
>
> **v2 Amendments:**
> 1. Task 5.2 (Learn App) fully rewritten — now a structured summary referencing the Learn App system design document (`2026-04-07-ics-learn-app-system-design.md`) as the authoritative implementation detail
> 2. Dependency rules updated — `learn.service.js` dependency chain added
> 3. Deferred section extended — Learn App post-MVP items carried in from the system design doc
>
> **Everything else in v1 is unchanged.**

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the ICS platform (digital twin of the Kingdom Governance System) from a fresh Django project on a VPS to a fully operational multi-tenant platform with vanilla JS frontend.

**Architecture:** Django + DRF backend (single source of truth) + vanilla JS frontend (mobile-first UI layer making fetch calls to DRF endpoints). No localStorage as primary storage — localStorage is UI state only (theme, session token). All data lives in PostgreSQL via Django. Frontend engine services (`records.service.js` etc.) call DRF endpoints, not localStorage. The data contract document (`2026-03-30-ics-platform-data-contract.md`) is the canonical schema reference throughout.

**Tech Stack:** Python 3.11+, Django 4.2 LTS, Django REST Framework, PostgreSQL, Nginx, Gunicorn, HTML/CSS/Vanilla JS (IIFE modules), VPS (Ubuntu).

---

## Current State Audit

### What exists and is COMPLETE (keep, wire to Django)

- Navigation system: navbar, app drawer, bottom nav, overlay, theme system
- Mobile-first shell: index.html, responsive layout, CSS variables
- `storage.js` — localStorage abstraction (repurpose for UI state only)
- `router.js` — auth guards and navigation (update fetch targets)
- `auth.js` — register/login/logout flows (point to DRF auth endpoints)
- `main.js` — boot and component loader
- Records app UI — forms, list views, detail views (wire to DRF)

### What exists and needs REFACTORING

- `auth.js` — currently reads/writes localStorage users; must call DRF
- `router.js` — auth guard reads localStorage session; must read JWT token
- `storage.js` — remove data persistence role; keep only UI state helpers
- Records app JS — direct localStorage calls must become service calls

### What does NOT exist yet (build in order)

- Django project, apps, models, serializers, views, URLs
- All engine service JS files (`records.service.js`, `activity.service.js` etc.)
- All remaining app JS files (activity, learn, community, governance, dashboard)

---

## Dependency Rules (Non-Negotiable)

These rules govern build order. Violating them causes rework.

```
Django auth → Django tenant → Django records → Django activity
Django models → DRF serializers → DRF views → DRF URLs
DRF endpoints live → JS engine services → JS app files
Engine files complete → App files begin (never in parallel)
Records engine complete → Activity engine begin
Activity engine complete → Paraclete service begin
Activity engine complete → learn.service.js begin (learn.service.js depends on activity.service.js)
learn.service.js complete → learn-app.js begin
All engines complete → Dashboard begin
```

---

## Phase 0 — VPS + Django Project Setup

**Exit criteria:** `https://your-domain.com/api/health/` returns `{"status": "ok"}`. Nothing else. Do not proceed to Phase 1 until this passes.

### Task 0.1 — VPS baseline

**Files:** none (server commands only)

1. SSH into VPS
2. Update packages: `sudo apt update && sudo apt upgrade -y`
3. Install dependencies:

   ```bash
   sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx git
   ```

4. Create deploy user: `sudo adduser ics && sudo usermod -aG sudo ics`
5. Switch to deploy user: `su - ics`
6. Commit: n/a (server setup)

### Task 0.2 — PostgreSQL database

**Files:** none (DB commands only)

1. Start PostgreSQL: `sudo systemctl start postgresql && sudo systemctl enable postgresql`
2. Create DB and user:

   ```bash
   sudo -u postgres psql
   CREATE DATABASE ics_db;
   CREATE USER ics_user WITH PASSWORD 'your-strong-password';
   ALTER ROLE ics_user SET client_encoding TO 'utf8';
   ALTER ROLE ics_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE ics_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE ics_db TO ics_user;
   \q
   ```

3. Test connection: `psql -U ics_user -d ics_db -h localhost`

### Task 0.3 — Django project scaffold

**Files:**

- Create: `~/ics/` (project root)
- Create: `~/ics/requirements.txt`
- Create: `~/ics/ics_project/settings/base.py`
- Create: `~/ics/ics_project/settings/production.py`
- Create: `~/ics/ics_project/settings/local.py`

1. Create project directory and virtualenv:

   ```bash
   mkdir ~/ics && cd ~/ics
   python3.11 -m venv venv
   source venv/bin/activate
   ```

2. Install packages:

   ```bash
   pip install django==4.2 djangorestframework django-cors-headers psycopg2-binary python-decouple gunicorn
   pip freeze > requirements.txt
   ```

3. Create Django project:

   ```bash
   django-admin startproject ics_project .
   ```

4. Create settings split:

   ```bash
   mkdir ics_project/settings
   mv ics_project/settings.py ics_project/settings/base.py
   touch ics_project/settings/production.py
   touch ics_project/settings/local.py
   touch ics_project/settings/__init__.py
   ```

5. `ics_project/settings/base.py` — update DATABASE section:

   ```python
   from decouple import config

   SECRET_KEY = config('SECRET_KEY')
   DEBUG = config('DEBUG', default=False, cast=bool)
   ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

   INSTALLED_APPS = [
       'django.contrib.admin',
       'django.contrib.auth',
       'django.contrib.contenttypes',
       'django.contrib.sessions',
       'django.contrib.messages',
       'django.contrib.staticfiles',
       'rest_framework',
       'rest_framework.authtoken',
       'corsheaders',
   ]

   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       'django.middleware.security.SecurityMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'django.middleware.common.CommonMiddleware',
       'django.middleware.csrf.CsrfViewMiddleware',
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       'django.contrib.messages.middleware.MessageMiddleware',
       'django.middleware.clickjacking.XFrameOptionsMiddleware',
   ]

   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': config('DB_NAME'),
           'USER': config('DB_USER'),
           'PASSWORD': config('DB_PASSWORD'),
           'HOST': config('DB_HOST', default='localhost'),
           'PORT': config('DB_PORT', default='5432'),
       }
   }

   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework.authentication.TokenAuthentication',
       ],
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.IsAuthenticated',
       ],
       'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
       'PAGE_SIZE': 20,
   }

   CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=lambda v: [s.strip() for s in v.split(',')])
   ```

6. Create `.env` file in project root:

   ```
   SECRET_KEY=generate-a-long-random-string-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
   DB_NAME=ics_db
   DB_USER=ics_user
   DB_PASSWORD=your-strong-password
   DB_HOST=localhost
   DB_PORT=5432
   CORS_ALLOWED_ORIGINS=http://localhost:8000,https://your-domain.com
   ```

7. Run migrations: `python manage.py migrate`
8. Commit: `git init && git add . && git commit -m "chore: django project scaffold"`

### Task 0.4 — Health check endpoint

**Files:**

- Create: `~/ics/core/` (Django app)
- Create: `~/ics/core/views.py`
- Create: `~/ics/core/urls.py`
- Modify: `~/ics/ics_project/urls.py`

1. Create core app: `python manage.py startapp core`
2. Add to `INSTALLED_APPS`: `'core',`
3. `core/views.py`:

   ```python
   from rest_framework.decorators import api_view, permission_classes
   from rest_framework.permissions import AllowAny
   from rest_framework.response import Response

   @api_view(['GET'])
   @permission_classes([AllowAny])
   def health_check(request):
       return Response({'status': 'ok'})
   ```

4. `core/urls.py`:

   ```python
   from django.urls import path
   from . import views

   urlpatterns = [
       path('health/', views.health_check, name='health-check'),
   ]
   ```

5. `ics_project/urls.py`:

   ```python
   from django.contrib import admin
   from django.urls import path, include

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('api/', include('core.urls')),
   ]
   ```

6. Run server: `python manage.py runserver`
7. Test: `curl http://localhost:8000/api/health/`
   Expected: `{"status": "ok"}`
8. Commit: `git add . && git commit -m "feat: health check endpoint"`

### Task 0.5 — Nginx + Gunicorn (production)

**Files:**

- Create: `/etc/nginx/sites-available/ics`
- Create: `~/ics/gunicorn.conf.py`

1. `gunicorn.conf.py`:

   ```python
   bind = "127.0.0.1:8001"
   workers = 3
   timeout = 120
   accesslog = "/var/log/gunicorn/ics_access.log"
   errorlog = "/var/log/gunicorn/ics_error.log"
   ```

2. Nginx config `/etc/nginx/sites-available/ics`:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location /api/ {
           proxy_pass http://127.0.0.1:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static/ {
           alias /home/ics/ics/staticfiles/;
       }

       location / {
           root /home/ics/ics/frontend/;
           try_files $uri $uri/ /index.html;
       }
   }
   ```

3. Enable site: `sudo ln -s /etc/nginx/sites-available/ics /etc/nginx/sites-enabled/`
4. Test config: `sudo nginx -t`
5. Start Nginx: `sudo systemctl restart nginx`
6. Start Gunicorn: `gunicorn ics_project.wsgi:application -c gunicorn.conf.py`
7. Test: `curl https://your-domain.com/api/health/`
   Expected: `{"status": "ok"}`
8. Commit: `git add . && git commit -m "chore: nginx + gunicorn production config"`

---

## Phase 1 — Django Foundation (Auth + Tenant + Identity)

**Exit criteria:** Can register a user, log in, receive a token, create a tenant with a materialized path, assign a UserPermission. All via DRF endpoints. No frontend yet.

### Task 1.1 — Accounts Django app

**Files:**

- Create: `~/ics/accounts/models.py`
- Create: `~/ics/accounts/serializers.py`
- Create: `~/ics/accounts/views.py`
- Create: `~/ics/accounts/urls.py`
- Create: `~/ics/accounts/permissions.py`

1. Create app: `python manage.py startapp accounts`
2. Add to `INSTALLED_APPS`: `'accounts',`
3. `accounts/models.py`:

   ```python
   import uuid
   from django.contrib.auth.models import AbstractUser
   from django.db import models

   class User(AbstractUser):
       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
       display_name = models.CharField(max_length=100, blank=True)
       avatar_url = models.URLField(blank=True, null=True)
       competence_level = models.IntegerField(default=0)
       # 0 = seeker, 1-5 = formation levels per KGS
       status = models.CharField(
           max_length=30,
           choices=[
               ('seeker', 'Seeker'),
               ('active', 'Active'),
               ('suspended', 'Suspended'),
               ('pending_verification', 'Pending Verification'),
           ],
           default='seeker'
       )
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       class Meta:
           db_table = 'accounts_user'

       def __str__(self):
           return self.email
   ```

4. Add to `settings/base.py`: `AUTH_USER_MODEL = 'accounts.User'`
5. `accounts/serializers.py`:

   ```python
   from rest_framework import serializers
   from django.contrib.auth import authenticate
   from .models import User

   class RegisterSerializer(serializers.ModelSerializer):
       password = serializers.CharField(write_only=True, min_length=8)

       class Meta:
           model = User
           fields = ['id', 'email', 'display_name', 'password']

       def create(self, validated_data):
           user = User.objects.create_user(
               username=validated_data['email'],
               email=validated_data['email'],
               display_name=validated_data.get('display_name', ''),
               password=validated_data['password'],
               status='seeker',
               competence_level=0
           )
           return user

   class LoginSerializer(serializers.Serializer):
       email = serializers.EmailField()
       password = serializers.CharField(write_only=True)

       def validate(self, data):
           user = authenticate(username=data['email'], password=data['password'])
           if not user:
               raise serializers.ValidationError('Invalid credentials')
           if user.status == 'suspended':
               raise serializers.ValidationError('Account suspended')
           data['user'] = user
           return data

   class UserSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ['id', 'email', 'display_name', 'avatar_url',
                     'competence_level', 'status', 'created_at']
           read_only_fields = ['id', 'created_at', 'competence_level']
   ```

6. `accounts/views.py`:

   ```python
   from rest_framework import status
   from rest_framework.decorators import api_view, permission_classes
   from rest_framework.permissions import AllowAny, IsAuthenticated
   from rest_framework.response import Response
   from rest_framework.authtoken.models import Token
   from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

   @api_view(['POST'])
   @permission_classes([AllowAny])
   def register(request):
       serializer = RegisterSerializer(data=request.data)
       if serializer.is_valid():
           user = serializer.save()
           token, _ = Token.objects.get_or_create(user=user)
           return Response({
               'token': token.key,
               'user': UserSerializer(user).data
           }, status=status.HTTP_201_CREATED)
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   @api_view(['POST'])
   @permission_classes([AllowAny])
   def login(request):
       serializer = LoginSerializer(data=request.data)
       if serializer.is_valid():
           user = serializer.validated_data['user']
           token, _ = Token.objects.get_or_create(user=user)
           return Response({
               'token': token.key,
               'user': UserSerializer(user).data
           })
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   @api_view(['POST'])
   @permission_classes([IsAuthenticated])
   def logout(request):
       request.user.auth_token.delete()
       return Response({'detail': 'Logged out'})

   @api_view(['GET', 'PATCH'])
   @permission_classes([IsAuthenticated])
   def me(request):
       if request.method == 'GET':
           return Response(UserSerializer(request.user).data)
       serializer = UserSerializer(request.user, data=request.data, partial=True)
       if serializer.is_valid():
           serializer.save()
           return Response(serializer.data)
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   ```

7. `accounts/urls.py`:

   ```python
   from django.urls import path
   from . import views

   urlpatterns = [
       path('auth/register/', views.register, name='register'),
       path('auth/login/', views.login, name='login'),
       path('auth/logout/', views.logout, name='logout'),
       path('auth/me/', views.me, name='me'),
   ]
   ```

8. Add to `ics_project/urls.py`: `path('api/', include('accounts.urls')),`
9. Run: `python manage.py makemigrations accounts && python manage.py migrate`
10. Test register:

    ```bash
    curl -X POST http://localhost:8000/api/auth/register/ \
      -H "Content-Type: application/json" \
      -d '{"email":"test@test.com","display_name":"Test","password":"testpass123"}'
    ```

    Expected: `{"token": "...", "user": {...}}`
11. Commit: `git add . && git commit -m "feat: accounts app — register, login, logout, me"`

### Task 1.2 — Tenants Django app

**Files:**

- Create: `~/ics/tenants/models.py`
- Create: `~/ics/tenants/serializers.py`
- Create: `~/ics/tenants/views.py`
- Create: `~/ics/tenants/urls.py`

1. Create app: `python manage.py startapp tenants`
2. Add to `INSTALLED_APPS`: `'tenants',`
3. `tenants/models.py`:

   ```python
   import uuid
   from django.db import models
   from django.conf import settings

   class Tenant(models.Model):
       TIER_CHOICES = [
           ('handbook', 'Handbook'),
           ('church_node', 'Church Node'),
           ('church_collective', 'Church Collective'),
           ('district', 'District'),
           ('provincial', 'Provincial'),
           ('national', 'National'),
           ('regional', 'Regional'),
           ('continental', 'Continental'),
           ('global', 'Global'),
       ]
       AFFILIATION_CHOICES = [
           ('ichebo', 'Ichebo'),
           ('independent', 'Independent'),
           ('affiliate', 'Affiliate'),
       ]
       STATUS_CHOICES = [
           ('active', 'Active'),
           ('pending', 'Pending'),
           ('suspended', 'Suspended'),
       ]

       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
       parent = models.ForeignKey(
           'self', null=True, blank=True,
           on_delete=models.PROTECT, related_name='children'
       )
       created_by = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
           related_name='created_tenants'
       )
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       name = models.CharField(max_length=200)
       slug = models.SlugField(max_length=200, unique=True)
       # Materialized path — e.g. /global/africa/southafrica/gauteng/pretoria/
       path = models.CharField(max_length=500, db_index=True)

       tier = models.CharField(max_length=30, choices=TIER_CHOICES)
       affiliation = models.CharField(max_length=20, choices=AFFILIATION_CHOICES, default='independent')
       status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
       is_collective = models.BooleanField(default=False)

       description = models.TextField(blank=True, null=True)
       logo_url = models.URLField(blank=True, null=True)

       # Location (JSON field — PostgreSQL)
       location = models.JSONField(default=dict, blank=True)
       settings_data = models.JSONField(default=dict, blank=True)

       class Meta:
           db_table = 'tenants_tenant'
           indexes = [
               models.Index(fields=['path']),
               models.Index(fields=['tier']),
               models.Index(fields=['status']),
           ]

       def get_descendants(self):
           return Tenant.objects.filter(
               path__startswith=self.path
           ).exclude(pk=self.pk)

       def get_ancestors(self):
           parts = self.path.strip('/').split('/')
           ancestor_paths = [
               '/' + '/'.join(parts[:i+1]) + '/'
               for i in range(len(parts) - 1)
           ]
           return Tenant.objects.filter(path__in=ancestor_paths)

       def __str__(self):
           return f"{self.name} ({self.path})"


   class UserPermission(models.Model):
       ROLE_CHOICES = [
           ('seeker', 'Seeker'),
           ('disciple', 'Disciple'),
           ('branch-steward', 'Branch Steward'),
           ('district-steward', 'District Steward'),
           ('provincial-steward', 'Provincial Steward'),
           ('national-steward', 'National Steward'),
           ('regional-steward', 'Regional Steward'),
           ('continental-steward', 'Continental Steward'),
           ('global-steward', 'Global Steward'),
           ('admin', 'Admin'),
       ]

       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
       tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='permissions')
       user = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
           related_name='tenant_permissions'
       )
       created_by = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
           related_name='granted_permissions'
       )
       created_at = models.DateTimeField(auto_now_add=True)

       tenant_path = models.CharField(max_length=500, db_index=True)
       role = models.CharField(max_length=30, choices=ROLE_CHOICES)
       level = models.IntegerField(default=1)
       is_active = models.BooleanField(default=True)
       granted_at = models.DateTimeField(auto_now_add=True)
       granted_by = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
           related_name='permissions_granted', null=True
       )

       class Meta:
           db_table = 'tenants_userpermission'
           unique_together = [['tenant', 'user', 'role']]
   ```

4. Write serializers and views following the same pattern as Task 1.1 — CRUD for Tenant and UserPermission, all authenticated.
5. Run: `python manage.py makemigrations tenants && python manage.py migrate`
6. Test: create a tenant via POST, verify path is stored correctly.
7. Commit: `git add . && git commit -m "feat: tenants app — tenant model + user permissions"`

### Task 1.3 — accounts/permissions.py (KGS permission helper)

**Files:**

- Create: `~/ics/accounts/permissions.py`

This is the Python implementation of the permission check algorithm from Part 7 of the data contract. Implement once, import everywhere.

```python
# accounts/permissions.py
from rest_framework.permissions import BasePermission
from tenants.models import UserPermission

class IsLevel1OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 1

class IsLevel2OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 2

class IsLevel4OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 4

class IsLevel5OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 5

def check_record_permission(user, record):
    """
    Full permission check per data contract Part 7.
    Returns True if user may read this record, False otherwise.
    """
    if not user or not user.is_authenticated:
        return record.visibility == 'public'

    if user.status == 'seeker':
        return (record.created_by == user) or record.visibility == 'public'

    # Handbook short-circuit
    if record.tenant and record.tenant.path.startswith('/global/handbook/'):
        return user.competence_level >= 5

    visibility = record.permissions_data.get('visibility', 'private')
    required_level = record.permissions_data.get('required_level', 1)
    roles_allowed = record.permissions_data.get('roles_allowed', [])

    if visibility == 'private':
        return record.created_by == user

    if user.competence_level < required_level:
        return False

    if visibility == 'public':
        return True

    user_permissions = UserPermission.objects.filter(
        user=user, is_active=True
    ).values_list('tenant_path', 'role')

    tenant_path = record.tenant.path if record.tenant else ''

    if visibility == 'tenant':
        has_access = any(tp == tenant_path for tp, _ in user_permissions)
    elif visibility == 'collective':
        has_access = any(
            tenant_path.startswith(tp) or tp.startswith(tenant_path)
            for tp, _ in user_permissions
        )
    else:
        has_access = False

    if not has_access:
        return False

    if roles_allowed:
        return any(role in roles_allowed for _, role in user_permissions)

    return True
```

Commit: `git add . && git commit -m "feat: KGS permission helper — check_record_permission"`

---

## Phase 2 — Records Engine (Django + DRF + JS Service)

**Exit criteria:** Can create, read, update, soft-delete a Record via DRF. Can create a Relationship between two Records. JS `records.service.js` calls these endpoints. Records app UI works against real data.

### Task 2.1 — Records Django app (models)

**Files:**

- Create: `~/ics/records/models.py`

```python
import uuid
from django.db import models
from django.conf import settings

class Record(models.Model):
    RECORD_CLASS_CHOICES = [
        ('personal', 'Personal'),
        ('organizational', 'Organizational'),
        ('governance', 'Governance'),
    ]
    RECORD_FAMILY_CHOICES = [
        ('journal', 'Journal'),
        ('governance', 'Governance'),
        ('activity', 'Activity'),
        ('learning', 'Learning'),
        ('reference', 'Reference'),
        ('bible', 'Bible'),
        ('community', 'Community'),
    ]
    ORIGIN_CHOICES = [
        ('user', 'User'),
        ('system', 'System'),
        ('paraclete', 'Paraclete'),
        ('import', 'Import'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
        ('locked', 'Locked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT, related_name='records'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    record_class = models.CharField(max_length=20, choices=RECORD_CLASS_CHOICES)
    record_family = models.CharField(max_length=20, choices=RECORD_FAMILY_CHOICES)
    record_type = models.CharField(max_length=50)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default='user')

    title = models.CharField(max_length=500)
    content = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='locked_records'
    )
    locked_at = models.DateTimeField(null=True, blank=True)

    # Governance versioning
    version = models.IntegerField(null=True, blank=True)
    previous_version = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='next_versions'
    )
    superseded_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='supersedes'
    )

    tags = models.JSONField(default=list, blank=True)
    categories = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    permissions_data = models.JSONField(default=dict, blank=True)
    # permissions_data structure: {visibility, required_level, roles_allowed, can_edit}

    class Meta:
        db_table = 'records_record'
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['record_family']),
            models.Index(fields=['record_type']),
            models.Index(fields=['record_class']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['tenant', 'record_family']),
            models.Index(fields=['tenant', 'record_class']),
        ]

    def __str__(self):
        return f"{self.record_type}: {self.title}"


class Relationship(models.Model):
    DIRECTION_CHOICES = [
        ('directed', 'Directed'),
        ('bidirectional', 'Bidirectional'),
    ]
    RELATIONSHIP_TYPE_CHOICES = [
        ('relates_to', 'Relates To'),
        ('derived_from', 'Derived From'),
        ('references', 'References'),
        ('answers', 'Answers'),
        ('fulfills', 'Fulfills'),
        ('requests', 'Requests'),
        ('has_symbol', 'Has Symbol'),
        ('matches_pattern', 'Matches Pattern'),
        ('assigned_to', 'Assigned To'),
        ('tracks', 'Tracks'),
        ('completes', 'Completes'),
        ('part_of', 'Part Of'),
        ('aligns_with', 'Aligns With'),
        ('authorised_by', 'Authorised By'),
        ('has_subject', 'Has Subject'),
        ('has_entity', 'Has Entity'),
        ('tagged_in', 'Tagged In'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    from_record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name='outgoing_relationships'
    )
    to_record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name='incoming_relationships'
    )

    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    relationship_type = models.CharField(max_length=30, choices=RELATIONSHIP_TYPE_CHOICES)
    notes = models.TextField(blank=True, null=True)
    strength = models.CharField(
        max_length=10,
        choices=[('weak','Weak'),('medium','Medium'),('strong','Strong')],
        null=True, blank=True
    )

    class Meta:
        db_table = 'records_relationship'
        indexes = [
            models.Index(fields=['from_record']),
            models.Index(fields=['to_record']),
            models.Index(fields=['relationship_type']),
        ]
```

Run: `python manage.py makemigrations records && python manage.py migrate`
Commit: `git add . && git commit -m "feat: records models — Record + Relationship"`

### Task 2.2 — Records serializers + views + URLs

**Files:**

- Create: `~/ics/records/serializers.py`
- Create: `~/ics/records/views.py`
- Create: `~/ics/records/urls.py`

Endpoints to implement:

```
GET    /api/records/              list (filtered by tenant, family, type, class)
POST   /api/records/              create
GET    /api/records/{id}/         retrieve
PATCH  /api/records/{id}/         update
DELETE /api/records/{id}/         soft delete (set deleted_at)
GET    /api/records/{id}/relationships/   list related records
POST   /api/relationships/        create relationship
DELETE /api/relationships/{id}/   soft delete relationship
```

All list endpoints filter out soft-deleted records (`deleted_at=None`) by default.
All write endpoints enforce `check_record_permission` from `accounts/permissions.py`.

Commit: `git add . && git commit -m "feat: records DRF endpoints — CRUD + relationships"`

### Task 2.3 — records.service.js (JS engine)

**Files:**

- Create: `~/ics/frontend/assets/js/engines/records.service.js`
- Create: `~/ics/frontend/assets/js/engines/relationships.service.js`
- Create: `~/ics/frontend/assets/js/engines/records.store.js`

```js
// records.service.js — IIFE module, calls DRF endpoints
const ICSRecords = (() => {
  const BASE = '/api/records/'

  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    }
  }

  async function list(filters = {}) {
    const params = new URLSearchParams(filters)
    const res = await fetch(`${BASE}?${params}`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Records list failed: ${res.status}`)
    return res.json()
  }

  async function get(id) {
    const res = await fetch(`${BASE}${id}/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Record get failed: ${res.status}`)
    return res.json()
  }

  async function create(data) {
    const res = await fetch(BASE, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Record create failed: ${res.status}`)
    return res.json()
  }

  async function update(id, data) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Record update failed: ${res.status}`)
    return res.json()
  }

  async function remove(id) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (!res.ok) throw new Error(`Record delete failed: ${res.status}`)
    return true
  }

  return { list, get, create, update, remove }
})()
```

Commit: `git add . && git commit -m "feat: records.service.js + relationships.service.js"`

### Task 2.4 — Wire Records app UI to DRF

**Files:**

- Modify: `~/ics/frontend/assets/js/apps/records-app.js`
- Modify: `~/ics/frontend/assets/js/core/auth.js`
- Modify: `~/ics/frontend/assets/js/core/router.js`

1. Update `auth.js` — replace localStorage user creation with fetch to `/api/auth/register/` and `/api/auth/login/`. Store returned token in `localStorage.setItem('ics_token', token)`.
2. Update `router.js` — auth guard checks `localStorage.getItem('ics_token')` (not a user object). On protected route access without token, redirect to login.
3. Update `records-app.js` — replace all direct storage calls with `ICSRecords.list()`, `ICSRecords.create()` etc.
4. Test: register a user via the UI, create a record, confirm it appears in Django admin.
5. Commit: `git add . && git commit -m "feat: wire records UI to DRF — auth + records CRUD"`

---

## Phase 3 — Activity Engine (Django + DRF + JS Service)

**Exit criteria:** Can create, read, update, soft-delete an Activity. ActivityLog is written on every status change. Activity → Record linking works via Relationships (no `linked_record_ids`). JS `activity.service.js` calls DRF endpoints.

### Task 3.1 — Activity Django app (models)

**Files:**

- Create: `~/ics/activity/models.py`

Model fields per data contract Part 4. Key points:

- `activity_type`: task | habit | goal | event | campaign | project | programme | reminder | skill
- `parent_activity_id` for nesting: programme → project → campaign → task
- `kgs_pillar` and `kgs_pathway` fields from data contract
- No `linked_record_ids` — linking is via `records.Relationship` only
- `ActivityLog` model for every status/progress change

Run migrations. Commit: `git add . && git commit -m "feat: activity models — Activity + ActivityLog"`

### Task 3.2 — Activity serializers + views + URLs

Endpoints:

```
GET    /api/activities/           list
POST   /api/activities/           create
GET    /api/activities/{id}/      retrieve
PATCH  /api/activities/{id}/      update (auto-writes ActivityLog entry)
DELETE /api/activities/{id}/      soft delete
GET    /api/activities/{id}/log/  activity history
```

Commit: `git add . && git commit -m "feat: activity DRF endpoints"`

### Task 3.3 — activity.service.js + activity.store.js

Same pattern as `records.service.js`. Calls DRF activity endpoints.
Commit: `git add . && git commit -m "feat: activity.service.js + activity.store.js"`

### Task 3.4 — Build activity-app.js UI

Mobile-first. Displays tasks, habits, goals. Links to records via `ICSRelationships.create()`.
Commit: `git add . && git commit -m "feat: activity app UI"`

---

## Phase 4 — Identity + Tenant Service Layer (JS)

**Exit criteria:** `identity.service.js` and `tenant.service.js` exist and call DRF. `router.js` uses `identity.service.js` for competence-level-aware route guarding.

### Task 4.1 — identity.service.js

**Files:**

- Create: `~/ics/frontend/assets/js/engines/identity.service.js`

```js
const ICSIdentity = (() => {
  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return { 'Authorization': `Token ${token}`, 'Content-Type': 'application/json' }
  }

  async function getCurrentUser() {
    const res = await fetch('/api/auth/me/', { headers: authHeaders() })
    if (!res.ok) return null
    return res.json()
  }

  async function getPermissions() {
    const res = await fetch('/api/auth/me/permissions/', { headers: authHeaders() })
    if (!res.ok) return []
    return res.json()
  }

  function isAuthenticated() {
    return !!localStorage.getItem('ics_token')
  }

  function getToken() {
    return localStorage.getItem('ics_token')
  }

  return { getCurrentUser, getPermissions, isAuthenticated, getToken }
})()
```

Commit: `git add . && git commit -m "feat: identity.service.js"`

### Task 4.2 — tenant.service.js

Calls `/api/tenants/` endpoints. Handles path resolution and membership queries.
Commit: `git add . && git commit -m "feat: tenant.service.js"`

---

## Phase 5 — App Layer (one app per task)

**Exit criteria per app:** App renders real data from DRF. Mobile-first layout. Passes manual smoke test on phone.

Build order is fixed — do not reorder:

### Task 5.1 — Bible app (bible.js + Django bible endpoints)

- Store Bible data as `Record` objects with `record_family: "bible"`, `record_type: "bible_note"`
- Bible reader reads from a static JSON file (no DB needed for scripture text itself)
- Notes and annotations write to Records via `ICSRecords.create()`
- Commit: `git add . && git commit -m "feat: bible app"`

### Task 5.2 — Learn app (learn-app.js + Django learning endpoints)

> **Full implementation detail:** `2026-04-07-ics-learn-app-system-design.md`
> This task is a summary only. All phase-level tasks, code, endpoints, and file paths
> are defined in the system design document. Build from that document, not this entry.

**What this task builds:**
The Learn App is the digital expression of the Sceptre Qualification Programmes
Framework. It enables learners to browse programmes, enrol, track progress through
courses and lessons, complete assessments, and earn certifications that advance
their competence level. Content is authored by Level 4+ users and reviewed by
Level 5 (Handbook) before publishing.

**New Django app:**
- `~/ics/learn/` — dedicated Django app with one model (`CertificationConfirmation`),
  curriculum endpoint, certification queue endpoint, and certification confirm endpoint

**Modified Django apps:**
- `~/ics/activity/signals.py` — auto-creates draft Certification Record when a
  programme Activity reaches `progress: 100` and `status: "completed"`
- `~/ics/accounts/serializers.py` — `competence_level` remains `read_only` everywhere
  except `POST /api/learn/certifications/{id}/confirm/` (sole authorised write path)

**New frontend files:**
- `~/ics/frontend/learn.html` — page shell with all view sections
- `~/ics/frontend/assets/js/engines/learn.service.js` — Learn engine (after `activity.service.js` in load order)
- `~/ics/frontend/assets/js/apps/learn-app.js` — Learn App UI (IIFE module)
- `~/ics/frontend/assets/css/learn.css` — mobile-first Learn App styles

**New endpoints:**
```
GET  /api/learn/health/
GET  /api/learn/programmes/{id}/curriculum/
GET  /api/learn/certifications/queue/
POST /api/learn/certifications/{id}/confirm/
```

**Data model summary:**
- All learning content = `Record` objects (`record_family: "learning"`, types:
  `programme | course | lesson | assignment | quiz | certification`)
- Curriculum = `Relationship` objects (`relationship_type: "part_of"`) traversed
  by the curriculum endpoint — no separate curriculum table
- Learner progress = `Activity` hierarchy (`programme → project → task`) linked to
  content Records via `Relationship (tracks)`
- Competence advancement = steward confirms draft Certification Record via confirm
  endpoint → `user.competence_level` incremented

**Build phases (A–G) — see system design doc for full task breakdown:**

| Phase | What it builds |
|-------|----------------|
| A | Django `learn` app, `CertificationConfirmation` model, confirm + queue endpoints |
| B | Records endpoint filter verification, curriculum endpoint, `learn.service.js` |
| C | `learn.html`, `learn-app.js` (My Learning, Catalogue, Enrolment, Lesson Viewer), `learn.css` |
| D | Quiz renderer, Assignment submission |
| E | Auto-certification signal, steward certification queue UI, competence level advancement |
| F | Content authorship UI (Level 4+), Handbook review queue UI (Level 5) |
| G | Role-aware navigation, Pathway banner, mobile smoke test |

**Exit criteria:** All seven phases (A–G) pass. Mobile smoke test checklist in Phase G
passes in full. `POST /api/learn/certifications/{id}/confirm/` correctly increments
`competence_level` in the DB and is verifiable in Django admin.

Commit per phase: see system design doc for per-phase commit messages.

### Task 5.3 — Community app (community-app.js + Django community endpoints)

- Tenant membership views
- Member directory (filtered by user's tenant scope)
- Commit: `git add . && git commit -m "feat: community app"`

### Task 5.4 — Governance app (governance-app.js + Django governance endpoints)

- Reads `record_class: "governance"` records only
- Write access gated to Level 4+ (Level 5 for Handbook records)
- Version history view using `previous_version_id` / `superseded_by` chain
- Commit: `git add . && git commit -m "feat: governance app"`

### Task 5.5 — Profile + Settings apps

- Profile: reads/writes `/api/auth/me/`
- Settings: theme, language, timezone — stored in `localStorage` (UI state only, not persisted to DB at this phase)
- Commit: `git add . && git commit -m "feat: profile + settings apps"`

### Task 5.6 — Notifications app (stub)

- Endpoint: `GET /api/notifications/` — returns empty list for now
- UI renders list, marks as read
- Full implementation deferred to Phase 7
- Commit: `git add . && git commit -m "feat: notifications app stub"`

---

## Phase 6 — Paraclete Service

**Exit criteria:** `paraclete.service.js` calls DRF and returns a real `ParacleteDigest` for the logged-in user. Dashboard renders digest data.

### Task 6.1 — Paraclete Django app

**Files:**

- Create: `~/ics/paraclete/` Django app
- Create: `~/ics/paraclete/service.py` — orchestration logic (reads from records + activity, writes nothing)
- Create: `~/ics/paraclete/views.py` — DRF endpoints

Endpoints:

```
GET  /api/paraclete/digest/              daily digest
GET  /api/paraclete/reminders/           pending reminders
GET  /api/paraclete/suggest/{record_id}/ link suggestions
GET  /api/paraclete/prompt/              discipline prompt
POST /api/paraclete/respond/             accept/dismiss suggestion
```

`paraclete/service.py` calls Django ORM directly (not other DRF endpoints). It is a Python orchestration module, not a web service calling itself.

Commit: `git add . && git commit -m "feat: paraclete Django service + endpoints"`

### Task 6.2 — paraclete.service.js

Calls Paraclete DRF endpoints. Returns `ParacleteDigest` for dashboard consumption.
Commit: `git add . && git commit -m "feat: paraclete.service.js"`

---

## Phase 7 — Dashboard

**Exit criteria:** Dashboard renders a real `ParacleteDigest`. Shows pending activities, recent records, active prayer count, discipline prompt. Role-aware and tenant-aware.

### Task 7.1 — dashboard-app.js

- Calls `ICSParaclete.getDailyDigest()`
- Renders widgets: today's focus, pending activities, recent records, prayer count
- Competence level determines which widgets are visible
- Commit: `git add . && git commit -m "feat: dashboard app"`

---

## Phase 8 — Production Hardening

**Exit criteria:** Platform runs stably on VPS. SSL active. Static files served by Nginx. Error logging in place.

### Task 8.1 — SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Commit: `git add . && git commit -m "chore: SSL via Let's Encrypt"`

### Task 8.2 — Static files

```bash
python manage.py collectstatic
```

Nginx serves `/static/` from `staticfiles/`. Frontend assets served from `frontend/`.
Commit: `git add . && git commit -m "chore: static files config"`

### Task 8.3 — Error logging + Django admin

- Configure `LOGGING` in Django settings to write errors to file
- Create superuser: `python manage.py createsuperuser`
- Verify Django admin accessible at `/admin/`
- Commit: `git add . && git commit -m "chore: logging + admin setup"`

### Task 8.4 — Systemd service for Gunicorn

Create `/etc/systemd/system/ics.service` so Gunicorn restarts on reboot:

```ini
[Unit]
Description=ICS Gunicorn Service
After=network.target

[Service]
User=ics
WorkingDirectory=/home/ics/ics
ExecStart=/home/ics/ics/venv/bin/gunicorn ics_project.wsgi:application -c gunicorn.conf.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ics
sudo systemctl start ics
```

Commit: `git add . && git commit -m "chore: systemd gunicorn service"`

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|-------|---------------|-------------------|---------------|
| 0 | VPS + Django scaffold + health check | VPS access | `/api/health/` returns 200 |
| 1 | Auth + Tenant + Identity + Permissions | Phase 0 done | Register, login, create tenant, assign permission |
| 2 | Records Engine (Django + JS) | Phase 1 done | Full Record + Relationship CRUD, UI wired |
| 3 | Activity Engine (Django + JS) | Phase 2 done | Full Activity CRUD, ActivityLog, linked to Records |
| 4 | Identity + Tenant JS services | Phase 1 done | identity.service.js + tenant.service.js call DRF |
| 5 | All apps (Bible, Learn, Community, Governance, Profile) | Phases 2–4 done | Each app renders real data |
| 6 | Paraclete service | Phase 3 done | DailyDigest returns real data |
| 7 | Dashboard | Phase 6 done | Dashboard renders digest, role-aware |
| 8 | Production hardening | Phase 7 done | SSL, static files, logging, systemd |

## Deferred (post-MVP)

**Platform-wide:**
- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Video/Live streaming app
- In-service Display app
- Donations feature
- Advanced Paraclete AI features (pattern detection, auto-linking)
- Push notifications (mobile)

**Learn App specific** *(carried from `2026-04-07-ics-learn-app-system-design.md`)*:
- Rich text editor (TipTap or similar) for lesson authorship — markdown textarea suffices for MVP
- Quiz auto-grading with score display
- Assignment peer review
- Paraclete "continue your lesson" integration (Phase 6 of this roadmap)
- Learning analytics dashboard (completion rates per programme)
- Offline lesson caching (service worker)
- Video lessons (`record_type: "video_lesson"` — deferred with Video/Live app)
- Programme ordering / sequencing UI (drag-and-drop curriculum builder)


---

# ICS Activity App — System Design & Build Roadmap

> **UI Architecture:** Django templates + HTMX throughout. No `activity-app.js`.
> All UI is server-rendered. HTMX handles status updates, form submissions, and
> partial refreshes. `storage.js` is retained for UI state (theme, session token) only.

> **Data Contract reference:** `2026-04-08-ics-platform-data-contract_v5.md` —
> all schemas and patterns in this document originate from Parts 4, 10, and 11
> of that contract. Read the contract before implementing.

**Goal:** Build the ICS Activity App — the operational execution layer of the Kingdom
Governance System — enabling members to manage personal disciplines, stewards to
coordinate team campaigns, and the platform to feed Paraclete and the Dashboard with
rich activity data.

**Architecture:** Django + DRF backend with a dedicated `activity` Django app (already
scaffolded from Phase 3 of the main roadmap). The Activity App adds Django template
views, HTMX interactions, and the Calendar aggregation service on top of the existing
Activity Engine. No new models beyond the existing data contract — the Activity App is a
pattern and UI layer over the Activity Engine.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX,
`activity.css` (mobile-first, CSS variables).

---

## System Overview

### The Activity Stack

```
KGS Layer          Great Calendar → Seven-Year Programme → Harvest Campaign Cycle
                   ↓ generates
Operational Layer  Campaign (activity_type: "campaign")
                   ↓ contains
                   Project (activity_type: "project")
                   ↓ contains
                   Task (activity_type: "task") — assigned to a user
                   ↓ also parallel to
Personal Layer     Habit / Goal / Reminder (personal, tenant_id: null)
                   ↓ alongside
Gifts Layer        Skill register (activity_type: "skill") — gifts & competence
                   ↓ all feed into
Aggregation        Calendar App (GET /api/calendar/events/) — reads Activity table
                   ↓ consumed by
Intelligence       Paraclete digest — pending activities, habits, reminders
                   ↓ surfaces on
Dashboard          Pending activities widget, today's focus, habit streaks
```

### Two-surface model

```
Activity App
  │
  ├── "My Activities"  (personal surface)
  │     Scope:  tenant_id: null, created_by = request.user
  │     Types:  task, habit, goal, skill, reminder
  │     Also:   read-only programme cards (Learn enrolments)
  │     Nesting: flat only
  │
  └── "Ministry"  (organisational surface)
        Scope:  tenant_id in user's tenants
        Types:  task, habit, event, campaign, project, reminder
        Includes: "Assigned to me" queue — first-class tab
        Nesting: two-level (campaign/project → task)
        Create: campaign/project = Level 3+; task = Level 1+
```

### User roles in the Activity App

| Role | What they can do |
|---|---|
| Seeker (0b) | Personal tasks and habits only (limited) |
| Member (Level 1) | Full personal activities; see assigned ministry tasks |
| Disciple (Level 2) | All personal + team tasks; instantiate templates |
| Branch-Steward (Level 3+) | Create campaigns, projects, events; assign tasks to team members; view team gifts register |
| Senior Steward (Level 4+) | All above + create activity templates |
| Architect (Level 5) | All above + cross-tenant visibility |

---

## Feature List (All Features — Unphased)

### F1 — My Activities (Personal Surface)

- Personal task list: create, edit, complete, defer, cancel
- Habit tracker: create recurring disciplines (daily/weekly/monthly)
- Goal register: personal goals with progress tracking (0–100%)
- Gifts register: skills/gifts inventory (`activity_type: "skill"`)
  - Add a gift: title, description, self-assessed competence, KGS pathway, service order
  - View gifts list; update competence level; archive
- Reminder: create time-based reminders (Paraclete surfaces these; no dedicated view)
- Read-only Learn programme cards: active enrolments with progress bar
- Empty state for new members

### F2 — Ministry Surface

- Ministry activity list: all team activities visible to the user
  - Grouped view: campaign/project headers with nested tasks
  - Flat assigned-tasks view (no campaign parent)
- "Assigned to me" queue: primary tab — tasks where `assigned_to = request.user`
  - Grouped by parent campaign/project
  - Due today / overdue highlighted
  - HTMX status toggle (pending → in_progress → completed)
- Ministry events list: upcoming events with `scheduled_at` as dated list

### F3 — Create / Edit Activity

- Unified create form for all user-accessible types
- Fields: title, description, type selector (filtered by competence level),
  KGS pillar selector, KGS pathway selector, due_at, scheduled_at,
  recurrence (daily/weekly/monthly radio — custom RRULE deferred),
  assigned_to (steward only, scoped to their tenant), tenant selector
- "Start from template" affordance: HTMX-powered typeahead to select a template
  and pre-fill the form
- "Link to record" affordance: HTMX typeahead calls `GET /api/records/?search={q}`
  and creates a Relationship on save (per Part 3.3 rules in v5 contract)
- Edit: same form, pre-filled; access controlled by `created_by` or Level 3+ steward

### F4 — Campaign / Project Management (Level 3+)

- Create campaign: title, description, KGS pillar, pathway, date range, assigned team
- Create project nested under a campaign
- Create task nested under a campaign or project, with `assigned_to` selection
- Campaign detail view: progress overview (% tasks completed), task list, team members
- Task status managed by either the assigned user or the creating steward

### F5 — Template Management (Level 4+)

- Create activity template (`metadata.is_template: true`): any activity type
- Template list view (separate from main activity list)
- Template detail: view/edit template fields
- Instantiate template: creates a new activity with fields pre-filled from template
  (`metadata.template_id` set to source); all Level 2+ users can instantiate

### F6 — Gifts Register (Personal + Team View)

- Personal: add, edit, archive skill/gift entries
- Team view (steward, Level 3+): read-only list of team gifts within their tenant scope
  - Grouped by KGS service order
  - Competence distribution at a glance

### F7 — Dated Activity List (Events)

- Ministry surface events tab: activities with `scheduled_at` or `due_at` set
- Grouped by date (today, tomorrow, this week, later)
- Event cards: title, type badge, time, tenant context
- No calendar grid in MVP — dated grouped list only

### F8 — Paraclete Filter Endpoints (Backend)

All six Paraclete-required filters on `GET /api/activities/`:

```
?assigned_to={user_id}
?due_today=true
?overdue=true
?activity_type=habit&status=in_progress
?tenant_id={id}&status=pending
?parent_activity_id={id}
?metadata__source_app=learn
```

These are built as part of the Activity App work and consumed by Paraclete in Phase 6.

### F9 — Calendar App Backend

- `GET /api/calendar/events/?from=&to=&tenant_id=` aggregation endpoint
- Queries Activity table for activities with `scheduled_at` or `due_at` in range
- Returns `CalendarEvent[]` sorted chronologically
- Scope: requesting user's tenant membership + personal activities
- No calendar UI in this phase — backend only

### F10 — ActivityLog Signals

- Every status change writes an `ActivityLog` entry
- Every `assigned_to` change writes an `ActivityLog` entry (`event_type: "assigned"`)
- Every record link creation writes an `ActivityLog` entry (`event_type: "linked"`)
- Signals wired in `activity/signals.py`

---

## Build Phases

### Phase A — Activity App Backend (Filters + Signals)
*Entry requirement: Phases 0–4 of main roadmap complete. `activity` Django app exists with basic CRUD.*

### Phase B — Django Views + URL Routing
*Entry requirement: Phase A complete.*

### Phase C — My Activities Surface (UI)
*Entry requirement: Phase B complete.*

### Phase D — Ministry Surface + Assigned-to-Me Queue (UI)
*Entry requirement: Phase C complete.*

### Phase E — Campaign / Project Management + Record Linking (UI)
*Entry requirement: Phase D complete.*

### Phase F — Templates + Gifts Register + Calendar Backend
*Entry requirement: Phase E complete.*

---

## Phase A — Activity App Backend

**Exit criteria:** `GET /api/activities/health/` returns `{"status": "ok"}`. All
six Paraclete filter parameters work on `GET /api/activities/`. `ActivityLog` signal
fires on status change. Calendar app scaffolded with aggregation endpoint returning
valid JSON.

---

### Task A.1 — Verify and extend ActivityViewSet filters

**Files:**
- Modify: `~/ics/activity/views.py` (or `api_views.py` if already split)
- Modify: `~/ics/activity/urls.py`

The `activity` Django app was scaffolded in Phase 3 of the main roadmap. This task
verifies its DRF `ActivityViewSet` exists and adds all required filter backends.

**Step 1:** Confirm `activity/models.py` matches the v5 data contract schema.
The `Activity` model must include all fields from Part 4.1 of the contract.
Key fields to verify:

```python
# activity/models.py — confirm these exist
class Activity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='activities')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.PROTECT,
                                   related_name='created_activities')
    created_at = models.DateTimeField(auto_now_add=True)

    ACTIVITY_TYPES = [
        ('task', 'Task'), ('habit', 'Habit'), ('goal', 'Goal'),
        ('event', 'Event'), ('campaign', 'Campaign'), ('project', 'Project'),
        ('programme', 'Programme'), ('reminder', 'Reminder'), ('skill', 'Skill'),
    ]
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    recurrence = models.CharField(
        max_length=10,
        choices=[('none','None'),('daily','Daily'),('weekly','Weekly'),
                 ('monthly','Monthly'),('custom','Custom')],
        default='none'
    )
    recurrence_rule = models.CharField(max_length=500, blank=True, null=True)

    parent_activity = models.ForeignKey('self', null=True, blank=True,
                                        on_delete=models.SET_NULL,
                                        related_name='child_activities',
                                        db_index=True)

    STATUS_CHOICES = [
        ('pending','Pending'), ('in_progress','In Progress'),
        ('completed','Completed'), ('cancelled','Cancelled'), ('deferred','Deferred'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)

    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='assigned_activities',
                                    db_index=True)

    KGS_PILLARS = [
        ('apostolic','Apostolic'), ('strategy','Strategy'),
        ('formation','Formation'), ('programmes','Programmes'),
        ('mission','Mission'), ('communities','Communities'),
        ('stewardship','Stewardship'),
    ]
    KGS_PATHWAYS = [
        ('new_life','New Life'), ('spiritual_formation','Spiritual Formation'),
        ('community_life','Community Life'), ('service','Service'),
        ('leadership','Leadership'), ('learning','Learning'),
        ('mission','Mission'), ('apostolic_stewardship','Apostolic Stewardship'),
    ]
    kgs_pillar = models.CharField(max_length=30, choices=KGS_PILLARS,
                                  blank=True, null=True)
    kgs_pathway = models.CharField(max_length=30, choices=KGS_PATHWAYS,
                                   blank=True, null=True)

    metadata = models.JSONField(default=dict, blank=True)
    # metadata keys: source_app, icon, color, is_template, template_id, service_order

    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['status']),
            models.Index(fields=['due_at']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['parent_activity']),
            models.Index(fields=['created_by']),
            models.Index(fields=['tenant', 'activity_type']),
            models.Index(fields=['tenant', 'assigned_to']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['assigned_to', 'due_at']),
        ]
```

**Step 2:** Add `django-filter` to requirements if not present:

```bash
pip install django-filter
pip freeze > requirements.txt
```

Add to `INSTALLED_APPS` in `base.py`:
```python
'django_filters',
```

Add to `REST_FRAMEWORK` in `base.py`:
```python
'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
```

**Step 3:** Create `activity/filters.py`:

```python
# activity/filters.py
import django_filters
from django.utils import timezone
from .models import Activity


class ActivityFilter(django_filters.FilterSet):
    # Standard field filters
    activity_type = django_filters.CharFilter(field_name='activity_type')
    status = django_filters.CharFilter(field_name='status')
    assigned_to = django_filters.UUIDFilter(field_name='assigned_to__id')
    tenant_id = django_filters.UUIDFilter(field_name='tenant__id')
    parent_activity_id = django_filters.UUIDFilter(field_name='parent_activity__id')
    source_app = django_filters.CharFilter(
        field_name='metadata__source_app', lookup_expr='exact'
    )

    # Surface filter: personal (tenant null, created_by=user) or
    # ministry (tenant in user's tenants) — handled in ViewSet, not here

    # Computed filters
    due_today = django_filters.BooleanFilter(method='filter_due_today')
    overdue = django_filters.BooleanFilter(method='filter_overdue')

    def filter_due_today(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(
                due_at__date=today,
                status__in=['pending', 'in_progress']
            )
        return queryset

    def filter_overdue(self, queryset, name, value):
        if value:
            now = timezone.now()
            return queryset.filter(
                due_at__lt=now,
                status__in=['pending', 'in_progress']
            )
        return queryset

    class Meta:
        model = Activity
        fields = ['activity_type', 'status', 'assigned_to', 'tenant_id',
                  'parent_activity_id', 'due_today', 'overdue', 'source_app']
```

**Step 4:** Create or update `activity/api_views.py`:

```python
# activity/api_views.py
import uuid
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Activity, ActivityLog
from .serializers import ActivitySerializer, ActivityLogSerializer
from .filters import ActivityFilter


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "activity"})


class ActivityViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Activity objects.
    Scoping: results filtered to activities the requesting user may see.
    Filters: see ActivityFilter for all supported query parameters.
    """
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ActivityFilter

    def get_queryset(self):
        user = self.request.user
        surface = self.request.query_params.get('surface')

        # Soft-delete: never return deleted activities
        qs = Activity.objects.filter(deleted_at__isnull=True)

        if surface == 'personal':
            # Personal: created by this user, no tenant
            return qs.filter(
                created_by=user,
                tenant__isnull=True
            )

        if surface == 'ministry':
            # Ministry: any activity in a tenant the user belongs to
            user_tenant_ids = user.userpermission_set.filter(
                is_active=True
            ).values_list('tenant_id', flat=True)
            return qs.filter(
                tenant_id__in=user_tenant_ids
            )

        # Default: personal + assigned-to-user ministry activities
        user_tenant_ids = user.userpermission_set.filter(
            is_active=True
        ).values_list('tenant_id', flat=True)

        personal = qs.filter(created_by=user, tenant__isnull=True)
        assigned = qs.filter(assigned_to=user, tenant_id__in=user_tenant_ids)

        return (personal | assigned).distinct()

    def perform_create(self, serializer):
        """
        Assignment permission gate: only Level 3+ may set assigned_to to another user.
        Template creation: only Level 4+ may set is_template: true.
        """
        user = self.request.user
        user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

        assigned_to = serializer.validated_data.get('assigned_to')
        if assigned_to and assigned_to != user and user_level < 3:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Only stewards (Level 3+) may assign activities to other users."
            )

        metadata = serializer.validated_data.get('metadata', {})
        if metadata.get('is_template') and user_level < 4:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Only Senior Stewards (Level 4+) may create activity templates."
            )

        serializer.save(created_by=user)

    def perform_update(self, serializer):
        """Log status changes via ActivityLog."""
        instance = self.get_object()
        old_status = instance.status
        old_assigned = instance.assigned_to_id

        updated = serializer.save()

        # Log status change
        if updated.status != old_status:
            ActivityLog.objects.create(
                activity=updated,
                tenant=updated.tenant,
                created_by=self.request.user,
                event_type='status_changed',
                previous_value=old_status,
                new_value=updated.status
            )

        # Log assignment change
        if updated.assigned_to_id != old_assigned:
            ActivityLog.objects.create(
                activity=updated,
                tenant=updated.tenant,
                created_by=self.request.user,
                event_type='assigned',
                previous_value=str(old_assigned),
                new_value=str(updated.assigned_to_id)
            )

    def perform_destroy(self, instance):
        """Soft delete — never hard delete."""
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])

    @action(detail=True, methods=['post'], url_path='instantiate')
    def instantiate(self, request, pk=None):
        """
        Create a new Activity from a template.
        Requires: activity.metadata.is_template = true
        Level 2+ may instantiate.
        """
        user = request.user
        user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)
        if user_level < 2:
            return Response(
                {"detail": "Level 2 or above required to instantiate templates."},
                status=status.HTTP_403_FORBIDDEN
            )

        template = self.get_object()
        if not template.metadata.get('is_template'):
            return Response(
                {"detail": "This activity is not a template."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Copy template fields; override per instantiation rules
        new_activity = Activity.objects.create(
            tenant=template.tenant,
            created_by=user,
            activity_type=template.activity_type,
            title=template.title,
            description=template.description,
            recurrence=template.recurrence,
            recurrence_rule=template.recurrence_rule,
            kgs_pillar=template.kgs_pillar,
            kgs_pathway=template.kgs_pathway,
            status='pending',
            progress=0,
            assigned_to=user,
            metadata={
                **template.metadata,
                'is_template': False,
                'template_id': str(template.id),
                'source_app': 'activity',
            }
        )

        ActivityLog.objects.create(
            activity=new_activity,
            tenant=new_activity.tenant,
            created_by=user,
            event_type='created',
            new_value=f'Instantiated from template {template.id}'
        )

        serializer = self.get_serializer(new_activity)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

**Step 5:** Create `activity/serializers.py` if not already complete:

```python
# activity/serializers.py
from rest_framework import serializers
from .models import Activity, ActivityLog


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
```

**Step 6:** Update `activity/urls.py`:

```python
# activity/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'activities', api_views.ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', api_views.health, name='activity-health'),
]
```

**Step 7:** Include in main `urls.py`:

```python
path('api/', include('activity.urls')),
```

**Step 8:** Run migrations and verify:

```bash
python manage.py makemigrations activity
python manage.py migrate
curl https://your-domain.com/api/activity/health/
# Expected: {"status": "ok", "app": "activity"}

# Test filters
curl "https://your-domain.com/api/activities/?activity_type=task" -H "Authorization: Token {token}"
curl "https://your-domain.com/api/activities/?due_today=true&assigned_to={uuid}" -H "Authorization: Token {token}"
curl "https://your-domain.com/api/activities/?overdue=true" -H "Authorization: Token {token}"
```

Commit: `git add . && git commit -m "feat: activity app — ViewSet, filters, soft delete, instantiate endpoint"`

---

### Task A.2 — ActivityLog signal

**Files:**
- Create/modify: `~/ics/activity/signals.py`
- Modify: `~/ics/activity/apps.py`

```python
# activity/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Activity, ActivityLog


@receiver(post_save, sender=Activity)
def log_activity_creation(sender, instance, created, **kwargs):
    """Log Activity creation event."""
    if created:
        ActivityLog.objects.create(
            activity=instance,
            tenant=instance.tenant,
            created_by=instance.created_by,
            event_type='created',
            new_value=instance.title
        )
```

```python
# activity/apps.py
from django.apps import AppConfig


class ActivityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity'

    def ready(self):
        import activity.signals  # noqa: F401
```

Commit: `git add . && git commit -m "feat: activity signals — log creation on save"`

---

### Task A.3 — Calendar app scaffold + aggregation endpoint

**Files:**
- Create: `~/ics/calendar_app/` (Django app — named `calendar_app` to avoid
  collision with Python's built-in `calendar` module)
- Modify: `~/ics/ics_project/settings/base.py`
- Modify: `~/ics/ics_project/urls.py`

**Step 1:** Scaffold the app:

```bash
cd ~/ics && python manage.py startapp calendar_app
```

**Step 2:** Add to `INSTALLED_APPS`:

```python
'calendar_app',
```

**Step 3:** Create `calendar_app/service.py` — aggregation logic:

```python
# calendar_app/service.py
from django.utils.dateparse import parse_datetime
from activity.models import Activity


def get_calendar_events(user, from_date, to_date, tenant_id=None,
                        activity_type=None, source_app=None):
    """
    Aggregate Activity objects with scheduled_at or due_at in range.
    Scoped to the requesting user's tenant memberships + personal activities.
    Returns a list of CalendarEvent dicts sorted by scheduled_at / due_at.
    """
    user_tenant_ids = list(
        user.userpermission_set.filter(is_active=True).values_list('tenant_id', flat=True)
    )

    qs = Activity.objects.filter(deleted_at__isnull=True).filter(
        # Personal activities
        models_Q(created_by=user, tenant__isnull=True) |
        # Tenant activities the user can see
        models_Q(tenant_id__in=user_tenant_ids)
    )

    # Date range filter — match either scheduled_at OR due_at in range
    qs = qs.filter(
        models_Q(scheduled_at__date__gte=from_date, scheduled_at__date__lte=to_date) |
        models_Q(due_at__date__gte=from_date, due_at__date__lte=to_date)
    )

    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if activity_type:
        qs = qs.filter(activity_type=activity_type)
    if source_app:
        qs = qs.filter(metadata__source_app=source_app)

    events = []
    for activity in qs.order_by('scheduled_at', 'due_at'):
        events.append({
            'id': str(activity.id),
            'source_type': 'activity',
            'source_app': activity.metadata.get('source_app', 'activity'),
            'title': activity.title,
            'scheduled_at': activity.scheduled_at.isoformat() if activity.scheduled_at else None,
            'due_at': activity.due_at.isoformat() if activity.due_at else None,
            'activity_type': activity.activity_type,
            'record_type': None,
            'tenant_id': str(activity.tenant_id) if activity.tenant_id else None,
            'status': activity.status,
            'kgs_pillar': activity.kgs_pillar,
            'kgs_pathway': activity.kgs_pathway,
        })

    return events


# Import Q here to avoid naming collision
from django.db.models import Q as models_Q
```

**Step 4:** Create `calendar_app/views.py`:

```python
# calendar_app/views.py
from datetime import date, timedelta
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status
from .service import get_calendar_events


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_events(request):
    """
    GET /api/calendar/events/
    Query params:
      from        ISO date (default: today)
      to          ISO date (default: today + 30 days)
      tenant_id   UUID (optional)
      activity_type (optional)
      source_app  (optional)
    """
    from_str = request.query_params.get('from')
    to_str = request.query_params.get('to')
    tenant_id = request.query_params.get('tenant_id')
    activity_type = request.query_params.get('activity_type')
    source_app = request.query_params.get('source_app')

    from_date = parse_date(from_str) if from_str else date.today()
    to_date = parse_date(to_str) if to_str else from_date + timedelta(days=30)

    if from_date > to_date:
        return Response(
            {"detail": "'from' must be before or equal to 'to'."},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    events = get_calendar_events(
        user=request.user,
        from_date=from_date,
        to_date=to_date,
        tenant_id=tenant_id,
        activity_type=activity_type,
        source_app=source_app,
    )

    return Response({'events': events, 'count': len(events)})
```

**Step 5:** Create `calendar_app/urls.py`:

```python
# calendar_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.calendar_events, name='calendar-events'),
]
```

**Step 6:** Include in main `urls.py`:

```python
path('api/calendar/', include('calendar_app.urls')),
```

**Step 7:** Verify:

```bash
curl "https://your-domain.com/api/calendar/events/?from=2026-04-08&to=2026-04-30" \
  -H "Authorization: Token {token}"
# Expected: {"events": [...], "count": N}
```

Commit: `git add . && git commit -m "feat: calendar app — aggregation endpoint (Activity table, MVP scope)"`

---

## Phase B — Django Views + URL Routing

**Exit criteria:** All Activity App URL routes resolve. `views.py` and `api_views.py`
are split. `base_activity.html` loads HTMX and `activity.css`. No template content
yet — 200 responses with empty base template suffice.

---

### Task B.1 — URL structure + views/api_views split

**Files:**
- Create: `~/ics/activity/views.py` (Django template views)
- Rename existing DRF views to: `~/ics/activity/api_views.py`
- Modify: `~/ics/activity/urls.py`

```python
# activity/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views, views

router = DefaultRouter()
router.register(r'activities', api_views.ActivityViewSet, basename='activity')

urlpatterns = [
    # API (DRF — consumed by HTMX + Paraclete)
    path('api/', include(router.urls)),
    path('api/activity/health/', api_views.health, name='activity-health'),

    # Django template views (UI)
    path('activity/', views.my_activities, name='activity-home'),
    path('activity/ministry/', views.ministry, name='activity-ministry'),
    path('activity/ministry/assigned/', views.assigned_to_me, name='activity-assigned'),
    path('activity/ministry/events/', views.ministry_events, name='activity-events'),
    path('activity/create/', views.activity_create, name='activity-create'),
    path('activity/<uuid:activity_id>/', views.activity_detail, name='activity-detail'),
    path('activity/<uuid:activity_id>/edit/', views.activity_edit, name='activity-edit'),
    path('activity/templates/', views.template_list, name='activity-templates'),
    path('activity/gifts/', views.gifts_register, name='activity-gifts'),
    path('activity/team-gifts/', views.team_gifts, name='activity-team-gifts'),

    # HTMX partial endpoints (return HTML fragments)
    path('activity/htmx/status/<uuid:activity_id>/', views.htmx_status_update, name='htmx-activity-status'),
    path('activity/htmx/progress/<uuid:activity_id>/', views.htmx_progress_update, name='htmx-activity-progress'),
    path('activity/htmx/create/', views.htmx_create_activity, name='htmx-activity-create'),
    path('activity/htmx/link-record/<uuid:activity_id>/', views.htmx_link_record, name='htmx-link-record'),
    path('activity/htmx/record-search/', views.htmx_record_search, name='htmx-record-search'),
    path('activity/htmx/template-search/', views.htmx_template_search, name='htmx-template-search'),
    path('activity/htmx/instantiate/<uuid:template_id>/', views.htmx_instantiate_template, name='htmx-instantiate'),
    path('activity/htmx/gift/add/', views.htmx_add_gift, name='htmx-add-gift'),
    path('activity/htmx/gift/<uuid:gift_id>/archive/', views.htmx_archive_gift, name='htmx-archive-gift'),
]
```

**Step 2:** Create stub `activity/views.py` with all view functions returning a
simple render to confirm routing:

```python
# activity/views.py — stubs (content added in Phases C–F)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST


@login_required
def my_activities(request):
    return render(request, 'activity/my_activities.html', {})

@login_required
def ministry(request):
    return render(request, 'activity/ministry.html', {})

@login_required
def assigned_to_me(request):
    return render(request, 'activity/assigned_to_me.html', {})

@login_required
def ministry_events(request):
    return render(request, 'activity/ministry_events.html', {})

@login_required
def activity_create(request):
    return render(request, 'activity/activity_form.html', {})

@login_required
def activity_detail(request, activity_id):
    return render(request, 'activity/activity_detail.html', {})

@login_required
def activity_edit(request, activity_id):
    return render(request, 'activity/activity_form.html', {})

@login_required
def template_list(request):
    return render(request, 'activity/template_list.html', {})

@login_required
def gifts_register(request):
    return render(request, 'activity/gifts_register.html', {})

@login_required
def team_gifts(request):
    return render(request, 'activity/team_gifts.html', {})

# HTMX stubs
@login_required
def htmx_status_update(request, activity_id):
    return HttpResponse('')

@login_required
def htmx_progress_update(request, activity_id):
    return HttpResponse('')

@login_required
def htmx_create_activity(request):
    return HttpResponse('')

@login_required
def htmx_link_record(request, activity_id):
    return HttpResponse('')

@login_required
def htmx_record_search(request):
    return HttpResponse('')

@login_required
def htmx_template_search(request):
    return HttpResponse('')

@login_required
def htmx_instantiate_template(request, template_id):
    return HttpResponse('')

@login_required
def htmx_add_gift(request):
    return HttpResponse('')

@login_required
def htmx_archive_gift(request, gift_id):
    return HttpResponse('')
```

Commit: `git add . && git commit -m "feat: activity app — URL structure, views/api_views split, all routes resolve"`

---

### Task B.2 — Base activity template + CSS

**Files:**
- Create: `~/ics/activity/templates/activity/base_activity.html`
- Create: `~/ics/frontend/assets/css/activity.css`

```html
<!-- activity/templates/activity/base_activity.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/activity.css' %}">
{% endblock %}

{% block extra_scripts %}
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
{% endblock %}

{% block content %}
<div class="activity-shell">

  <!-- Surface tab row -->
  <nav class="activity-tab-row">
    <a href="{% url 'activity-home' %}"
       class="activity-tab {% if request.resolver_match.url_name == 'activity-home' %}active{% endif %}">
      My Activities
    </a>
    <a href="{% url 'activity-ministry' %}"
       class="activity-tab {% if 'ministry' in request.resolver_match.url_name %}active{% endif %}">
      Ministry
    </a>
  </nav>

  <!-- Page content injected here by child templates -->
  {% block activity_content %}{% endblock %}

</div>
{% endblock %}
```

**`activity.css`** — mobile-first styles using platform CSS variables:

```css
/* activity.css — Activity App styles */

/* ── Shell ──────────────────────────────────────────────── */
.activity-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--color-bg);
}

/* ── Tab row ─────────────────────────────────────────────── */
.activity-tab-row {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  position: sticky;
  top: var(--navbar-height, 56px);
  z-index: 10;
}
.activity-tab {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.activity-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* ── Activity cards ──────────────────────────────────────── */
.activity-card {
  background: var(--color-surface);
  border-radius: var(--radius-md, 12px);
  padding: 16px;
  margin: 12px 16px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.activity-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.activity-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}
.activity-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

/* ── Type badge ───────────────────────────────────────────── */
.type-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.type-badge.task     { background: var(--color-blue-tint); color: var(--color-blue); }
.type-badge.habit    { background: var(--color-green-tint); color: var(--color-green); }
.type-badge.goal     { background: var(--color-purple-tint); color: var(--color-purple); }
.type-badge.event    { background: var(--color-orange-tint); color: var(--color-orange); }
.type-badge.campaign { background: var(--color-red-tint); color: var(--color-red); }
.type-badge.project  { background: var(--color-teal-tint); color: var(--color-teal); }
.type-badge.skill    { background: var(--color-yellow-tint); color: var(--color-yellow-dark); }

/* ── Status controls ─────────────────────────────────────── */
.status-controls {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.btn-status {
  padding: 6px 14px;
  border-radius: 100px;
  border: 1px solid var(--color-border);
  background: transparent;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}
.btn-status:hover,
.btn-status.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

/* ── Progress bar ────────────────────────────────────────── */
.progress-bar-wrap {
  background: var(--color-border);
  border-radius: 100px;
  height: 6px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: var(--color-primary);
  border-radius: 100px;
  transition: width 0.3s ease;
}

/* ── Campaign / project group ────────────────────────────── */
.campaign-group {
  margin: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
}
.campaign-group-header {
  background: var(--color-surface-alt, var(--color-surface));
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-border);
}
.campaign-group-header h3 {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}
.campaign-tasks {
  display: flex;
  flex-direction: column;
}
.campaign-tasks .activity-card {
  margin: 0;
  border-radius: 0;
  border-bottom: 1px solid var(--color-border);
  box-shadow: none;
}
.campaign-tasks .activity-card:last-child {
  border-bottom: none;
}

/* ── Due date indicators ─────────────────────────────────── */
.due-label {
  font-size: 12px;
  font-weight: 600;
}
.due-label.overdue  { color: var(--color-red, #d93025); }
.due-label.due-today { color: var(--color-orange, #f29900); }

/* ── Empty states ────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--color-text-secondary);
}
.empty-state p { font-size: 15px; margin-bottom: 16px; }

/* ── Activity form ───────────────────────────────────────── */
.activity-form {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}
.form-control {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm, 8px);
  padding: 10px 12px;
  font-size: 15px;
  background: var(--color-surface);
  color: var(--color-text);
  width: 100%;
  box-sizing: border-box;
}
.form-control:focus {
  border-color: var(--color-primary);
  outline: none;
}

/* ── Recurrence radio group ──────────────────────────────── */
.recurrence-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.recurrence-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: 100px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text);
}
.recurrence-group input[type="radio"]:checked + span,
.recurrence-group label:has(input:checked) {
  background: var(--color-primary-tint, #e8f0fe);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* ── Record link typeahead ───────────────────────────────── */
.record-search-wrap {
  position: relative;
}
.record-search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-top: none;
  border-radius: 0 0 var(--radius-sm, 8px) var(--radius-sm, 8px);
  max-height: 200px;
  overflow-y: auto;
  z-index: 50;
}
.record-search-results .record-option {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 1px solid var(--color-border);
}
.record-search-results .record-option:last-child { border-bottom: none; }
.record-search-results .record-option:hover {
  background: var(--color-bg);
}

/* ── Gifts register ──────────────────────────────────────── */
.gift-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 12px);
  padding: 14px 16px;
  margin: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.gift-card-body { flex: 1; }
.gift-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}
.gift-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 3px;
}
.gift-competence {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}

/* ── Desktop breakpoint ──────────────────────────────────── */
@media (min-width: 768px) {
  .activity-card { margin: 12px 24px; }
  .campaign-group { margin: 16px 24px; }
  .activity-form { max-width: 640px; margin: 0 auto; padding: 32px 24px; }
}
```

Commit: `git add . && git commit -m "feat: activity base template + activity.css"`

---

## Phase C — My Activities Surface (UI)

**Exit criteria:** A member can view their personal activities (tasks, habits, goals),
create new ones, mark complete via HTMX, and see their Learn enrolments as read-only
progress cards.

---

### Task C.1 — My Activities view + template

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/my_activities.html`

```python
# activity/views.py — my_activities
from django.utils import timezone

@login_required
def my_activities(request):
    user = request.user
    now = timezone.now()

    # Personal activities (no tenant) — exclude templates and programme types
    personal_qs = Activity.objects.filter(
        created_by=user,
        tenant__isnull=True,
        deleted_at__isnull=True,
        metadata__is_template=False,
    ).exclude(activity_type='programme').order_by('due_at', '-created_at')

    tasks  = personal_qs.filter(activity_type='task',
                                status__in=['pending', 'in_progress'])
    habits = personal_qs.filter(activity_type='habit',
                                status__in=['pending', 'in_progress'])
    goals  = personal_qs.filter(activity_type='goal',
                                status__in=['pending', 'in_progress'])

    # Learn enrolments — read-only programme activities
    learn_enrolments = Activity.objects.filter(
        assigned_to=user,
        activity_type='programme',
        status='in_progress',
        metadata__source_app='learn',
        deleted_at__isnull=True,
    ).order_by('-created_at')

    completed = personal_qs.filter(status='completed').order_by('-updated_at')[:5]

    return render(request, 'activity/my_activities.html', {
        'tasks': tasks,
        'habits': habits,
        'goals': goals,
        'learn_enrolments': learn_enrolments,
        'completed': completed,
        'now': now,
    })
```

```html
<!-- activity/templates/activity/my_activities.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>My Activities</h1>
  <a href="{% url 'activity-create' %}" class="btn-primary">+ New</a>
</div>

<!-- Learn enrolments (read-only) -->
{% if learn_enrolments %}
<section class="activity-section">
  <h2 class="section-title">Learning</h2>
  {% for enrolment in learn_enrolments %}
  <div class="activity-card">
    <div class="activity-card-header">
      <span class="activity-title">{{ enrolment.title }}</span>
      <span class="type-badge" style="background:var(--color-blue-tint);color:var(--color-blue)">
        Programme
      </span>
    </div>
    <div class="progress-bar-wrap">
      <div class="progress-bar" style="width:{{ enrolment.progress }}%"></div>
    </div>
    <span class="activity-meta">{{ enrolment.progress }}% complete</span>
  </div>
  {% endfor %}
</section>
{% endif %}

<!-- Tasks -->
{% if tasks %}
<section class="activity-section">
  <h2 class="section-title">Tasks</h2>
  {% for activity in tasks %}
    {% include "activity/partials/activity_card.html" with activity=activity %}
  {% endfor %}
</section>
{% endif %}

<!-- Habits -->
{% if habits %}
<section class="activity-section">
  <h2 class="section-title">Habits</h2>
  {% for activity in habits %}
    {% include "activity/partials/activity_card.html" with activity=activity show_recurrence=True %}
  {% endfor %}
</section>
{% endif %}

<!-- Goals -->
{% if goals %}
<section class="activity-section">
  <h2 class="section-title">Goals</h2>
  {% for activity in goals %}
    {% include "activity/partials/activity_card.html" with activity=activity show_progress=True %}
  {% endfor %}
</section>
{% endif %}

<!-- Gifts register link -->
<div style="margin: 8px 16px 24px;">
  <a href="{% url 'activity-gifts' %}" class="btn-secondary" style="width:100%;display:block;text-align:center;">
    My Gifts & Skills Register
  </a>
</div>

{% if not tasks and not habits and not goals and not learn_enrolments %}
<div class="empty-state">
  <p>Nothing here yet. Start by adding a task, habit, or goal.</p>
  <a href="{% url 'activity-create' %}" class="btn-primary">Add your first activity</a>
</div>
{% endif %}

{% endblock %}
```

---

### Task C.2 — Activity card partial + HTMX status update

**Files:**
- Create: `~/ics/activity/templates/activity/partials/activity_card.html`
- Modify: `~/ics/activity/views.py` (htmx_status_update)

```html
<!-- activity/templates/activity/partials/activity_card.html -->
<div class="activity-card" id="activity-{{ activity.id }}">
  <div class="activity-card-header">
    <span class="activity-title">{{ activity.title }}</span>
    <span class="type-badge {{ activity.activity_type }}">{{ activity.activity_type }}</span>
  </div>

  {% if activity.description %}
  <p class="activity-meta">{{ activity.description|truncatechars:100 }}</p>
  {% endif %}

  <div class="activity-meta">
    {% if activity.due_at %}
      {% if activity.due_at < now %}
        <span class="due-label overdue">Overdue · {{ activity.due_at|date:"d M" }}</span>
      {% elif activity.due_at|date:"Y-m-d" == now|date:"Y-m-d" %}
        <span class="due-label due-today">Due today</span>
      {% else %}
        <span>Due {{ activity.due_at|date:"d M" }}</span>
      {% endif %}
    {% endif %}
    {% if show_recurrence and activity.recurrence != 'none' %}
      <span>{{ activity.get_recurrence_display }}</span>
    {% endif %}
    {% if activity.kgs_pathway %}
      <span>{{ activity.get_kgs_pathway_display }}</span>
    {% endif %}
  </div>

  {% if show_progress %}
  <div class="progress-bar-wrap" style="margin-top:4px">
    <div class="progress-bar" style="width:{{ activity.progress }}%"></div>
  </div>
  <span class="activity-meta">{{ activity.progress }}%</span>
  {% endif %}

  <!-- HTMX status controls -->
  <div class="status-controls"
       hx-target="#activity-{{ activity.id }}"
       hx-swap="outerHTML">
    {% if activity.status == 'pending' %}
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "in_progress"}'>
        Start
      </button>
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "deferred"}'>
        Defer
      </button>
    {% elif activity.status == 'in_progress' %}
      <button class="btn-status active"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "completed"}'>
        ✓ Mark Complete
      </button>
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "deferred"}'>
        Defer
      </button>
    {% elif activity.status == 'deferred' %}
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "pending"}'>
        Restore
      </button>
    {% endif %}
    <a href="{% url 'activity-detail' activity.id %}" class="btn-status">View</a>
  </div>
</div>
```

```python
# activity/views.py — htmx_status_update
from django.views.decorators.http import require_POST
from django.utils import timezone

@login_required
@require_POST
def htmx_status_update(request, activity_id):
    """
    HTMX endpoint: update activity status.
    Returns updated activity card HTML fragment.
    """
    activity = get_object_or_404(
        Activity,
        id=activity_id,
        deleted_at__isnull=True
    )

    # Permission: owner or Level 3+ steward in the same tenant
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)
    is_owner = activity.created_by == user
    is_assignee = activity.assigned_to == user
    is_steward = user_level >= 3

    if not (is_owner or is_assignee or is_steward):
        return HttpResponse(status=403)

    new_status = request.POST.get('status')
    allowed = ['pending', 'in_progress', 'completed', 'deferred', 'cancelled']
    if new_status not in allowed:
        return HttpResponse(status=400)

    old_status = activity.status
    activity.status = new_status
    if new_status == 'completed':
        activity.progress = 100
    activity.save(update_fields=['status', 'progress', 'updated_at'])

    ActivityLog.objects.create(
        activity=activity,
        tenant=activity.tenant,
        created_by=user,
        event_type='status_changed',
        previous_value=old_status,
        new_value=new_status
    )

    now = timezone.now()
    return render(request, 'activity/partials/activity_card.html', {
        'activity': activity,
        'now': now,
    })
```

Commit: `git add . && git commit -m "feat: my activities view — personal tasks, habits, goals, learn cards, HTMX status"`

---

### Task C.3 — Activity create form

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/activity_form.html`
- Create: `~/ics/activity/templates/activity/partials/record_search_results.html`
- Create: `~/ics/activity/templates/activity/partials/template_search_results.html`

```python
# activity/views.py — activity_create
@login_required
def activity_create(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    if request.method == 'POST':
        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        activity_type = request.POST.get('activity_type', 'task')
        kgs_pillar   = request.POST.get('kgs_pillar') or None
        kgs_pathway  = request.POST.get('kgs_pathway') or None
        due_at_str   = request.POST.get('due_at') or None
        scheduled_at_str = request.POST.get('scheduled_at') or None
        recurrence   = request.POST.get('recurrence', 'none')
        assigned_to_id = request.POST.get('assigned_to') or None
        tenant_id    = request.POST.get('tenant_id') or None
        linked_record_id = request.POST.get('linked_record_id') or None

        if not title:
            return render(request, 'activity/activity_form.html', {
                'error': 'Title is required.',
                'user_level': user_level,
                'post': request.POST,
            })

        # Resolve tenant
        tenant = None
        if tenant_id:
            from tenants.models import Tenant
            tenant = Tenant.objects.filter(id=tenant_id).first()

        # Resolve assigned_to
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assigned_to = None
        if assigned_to_id:
            if user_level < 3:
                return render(request, 'activity/activity_form.html', {
                    'error': 'Only stewards (Level 3+) may assign activities.',
                    'user_level': user_level,
                    'post': request.POST,
                })
            assigned_to = User.objects.filter(id=assigned_to_id).first()

        # Parse dates
        from django.utils.dateparse import parse_datetime, parse_date
        due_at = parse_datetime(due_at_str) if due_at_str else None
        scheduled_at = parse_datetime(scheduled_at_str) if scheduled_at_str else None

        activity = Activity.objects.create(
            created_by=user,
            tenant=tenant,
            activity_type=activity_type,
            title=title,
            description=description or None,
            kgs_pillar=kgs_pillar,
            kgs_pathway=kgs_pathway,
            due_at=due_at,
            scheduled_at=scheduled_at,
            recurrence=recurrence,
            assigned_to=assigned_to,
            status='pending',
            metadata={'source_app': 'activity', 'is_template': False},
        )

        # Create record link if provided
        if linked_record_id:
            _create_activity_record_link(activity, linked_record_id, user)

        return redirect('activity-detail', activity_id=activity.id)

    # GET — determine available type options by level
    available_types = ['task', 'habit', 'goal', 'reminder']
    if user_level >= 1:
        available_types.append('skill')
    if user_level >= 3:
        available_types.extend(['event', 'campaign', 'project'])

    # User's tenants for tenant selector
    user_tenants = user.userpermission_set.filter(
        is_active=True
    ).select_related('tenant')

    return render(request, 'activity/activity_form.html', {
        'available_types': available_types,
        'user_tenants': user_tenants,
        'user_level': user_level,
    })


def _create_activity_record_link(activity, record_id, user):
    """
    Create a Relationship between this Activity (via its Record representation)
    and the target Record, per Part 3.3 of v5 data contract.
    """
    from records.models import Relationship, Record
    import uuid

    # Determine relationship_type by activity_type (v5 Part 3.3 rules)
    tracks_types = {'task', 'habit', 'goal', 'reminder'}
    aligns_types = {'campaign', 'event', 'project', 'skill'}

    rel_type = 'tracks' if activity.activity_type in tracks_types else 'aligns_with'

    target_record = Record.objects.filter(id=record_id).first()
    if not target_record:
        return

    # Find or create a Record representation for this Activity
    # (using activity family, matching activity_type)
    activity_record = Record.objects.filter(
        metadata__activity_id=str(activity.id)
    ).first()

    if not activity_record:
        activity_record = Record.objects.create(
            tenant=activity.tenant,
            created_by=user,
            record_class='personal' if not activity.tenant else 'organizational',
            record_family='activity',
            record_type=activity.activity_type,
            title=activity.title,
            status='active',
            origin='user',
            metadata={
                'source_app': 'activity',
                'activity_id': str(activity.id),
            },
        )

    Relationship.objects.create(
        tenant=activity.tenant,
        created_by=user,
        from_record_id=activity_record.id,
        to_record_id=target_record.id,
        relationship_type=rel_type,
        direction='directed',
    )
```

```html
<!-- activity/templates/activity/activity_form.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-form">
  <h1 style="font-size:20px;font-weight:700;margin-bottom:4px;">
    {% if activity %}Edit Activity{% else %}New Activity{% endif %}
  </h1>

  {% if error %}
  <div class="form-error" style="color:var(--color-red);font-size:14px;padding:10px;
    border:1px solid var(--color-red);border-radius:8px;background:var(--color-red-tint)">
    {{ error }}
  </div>
  {% endif %}

  <form method="post" action="{% if activity %}{% url 'activity-edit' activity.id %}{% else %}{% url 'activity-create' %}{% endif %}">
    {% csrf_token %}

    <!-- Start from template -->
    <div class="form-group">
      <label>Start from a template (optional)</label>
      <input type="text" id="template-search-input" class="form-control"
             placeholder="Search templates…"
             hx-get="{% url 'htmx-template-search' %}"
             hx-trigger="keyup changed delay:300ms"
             hx-target="#template-search-results"
             hx-include="[name='template_q']"
             name="template_q"
             autocomplete="off">
      <div id="template-search-results" class="record-search-results" style="display:none"></div>
      <input type="hidden" name="template_id" id="template-id-input">
    </div>

    <!-- Title -->
    <div class="form-group">
      <label for="title">Title <span style="color:var(--color-red)">*</span></label>
      <input type="text" name="title" id="title" class="form-control"
             value="{{ post.title|default:activity.title|default:'' }}"
             placeholder="What do you need to do?" required>
    </div>

    <!-- Description -->
    <div class="form-group">
      <label for="description">Description</label>
      <textarea name="description" id="description" class="form-control"
                rows="3" placeholder="Optional details…">{{ post.description|default:activity.description|default:'' }}</textarea>
    </div>

    <!-- Type -->
    <div class="form-group">
      <label for="activity_type">Type</label>
      <select name="activity_type" id="activity_type" class="form-control">
        {% for t in available_types %}
        <option value="{{ t }}"
          {% if post.activity_type == t or activity.activity_type == t %}selected{% endif %}>
          {{ t|capfirst }}
        </option>
        {% endfor %}
      </select>
    </div>

    <!-- Recurrence -->
    <div class="form-group">
      <label>Recurrence</label>
      <div class="recurrence-group">
        {% for val, label in recurrence_options %}
        <label>
          <input type="radio" name="recurrence" value="{{ val }}"
            {% if post.recurrence == val or activity.recurrence == val %}checked{% endif %}
            {% if not post and not activity and val == 'none' %}checked{% endif %}>
          <span>{{ label }}</span>
        </label>
        {% endfor %}
      </div>
    </div>

    <!-- KGS alignment -->
    <div class="form-group">
      <label for="kgs_pathway">KGS Pathway</label>
      <select name="kgs_pathway" id="kgs_pathway" class="form-control">
        <option value="">— None —</option>
        <option value="new_life">New Life</option>
        <option value="spiritual_formation">Spiritual Formation</option>
        <option value="community_life">Community Life</option>
        <option value="service">Service</option>
        <option value="leadership">Leadership</option>
        <option value="learning">Learning</option>
        <option value="mission">Mission</option>
        <option value="apostolic_stewardship">Apostolic Stewardship</option>
      </select>
    </div>

    <!-- Due date -->
    <div class="form-group">
      <label for="due_at">Due date</label>
      <input type="datetime-local" name="due_at" id="due_at" class="form-control"
             value="{{ post.due_at|default:'' }}">
    </div>

    <!-- Scheduled at (for events) -->
    <div class="form-group" id="scheduled-at-group" style="display:none">
      <label for="scheduled_at">Scheduled date &amp; time</label>
      <input type="datetime-local" name="scheduled_at" id="scheduled_at" class="form-control"
             value="{{ post.scheduled_at|default:'' }}">
    </div>

    <!-- Tenant (ministry activities) -->
    {% if user_tenants %}
    <div class="form-group">
      <label for="tenant_id">Ministry context (optional)</label>
      <select name="tenant_id" id="tenant_id" class="form-control">
        <option value="">Personal (no team)</option>
        {% for up in user_tenants %}
        <option value="{{ up.tenant.id }}"
          {% if post.tenant_id == up.tenant.id|stringformat:"s" %}selected{% endif %}>
          {{ up.tenant.name }}
        </option>
        {% endfor %}
      </select>
    </div>
    {% endif %}

    <!-- Assign to (Level 3+ only) -->
    {% if user_level >= 3 %}
    <div class="form-group">
      <label for="assigned_to">Assign to</label>
      <input type="text" class="form-control" placeholder="Search team members…"
             autocomplete="off">
      <input type="hidden" name="assigned_to" id="assigned_to_input"
             value="{{ post.assigned_to|default:'' }}">
      <small style="color:var(--color-text-secondary);font-size:12px">
        Leave blank to assign to yourself or leave unassigned (team-visible)
      </small>
    </div>
    {% endif %}

    <!-- Link to Record -->
    <div class="form-group">
      <label>Link to a record (optional)</label>
      <div class="record-search-wrap">
        <input type="text" class="form-control" id="record-search-input"
               placeholder="Search records…"
               hx-get="{% url 'htmx-record-search' %}"
               hx-trigger="keyup changed delay:300ms"
               hx-target="#record-search-results"
               hx-include="[name='record_q']"
               name="record_q"
               autocomplete="off">
        <div id="record-search-results" class="record-search-results"></div>
      </div>
      <input type="hidden" name="linked_record_id" id="linked-record-id">
      <div id="linked-record-display" style="font-size:13px;color:var(--color-primary);margin-top:4px"></div>
    </div>

    <button type="submit" class="btn-primary" style="width:100%">
      {% if activity %}Save Changes{% else %}Create Activity{% endif %}
    </button>
  </form>
</div>

<script>
// Show scheduled_at field for event type
document.getElementById('activity_type').addEventListener('change', function() {
  const group = document.getElementById('scheduled-at-group');
  group.style.display = this.value === 'event' ? 'block' : 'none';
});
</script>
{% endblock %}
```

```python
# activity/views.py — add to create view's GET context
# (pass recurrence options)
'recurrence_options': [
    ('none', 'Once'), ('daily', 'Daily'),
    ('weekly', 'Weekly'), ('monthly', 'Monthly')
],
```

```python
# activity/views.py — htmx_record_search
@login_required
def htmx_record_search(request):
    """HTMX typeahead: search records for linking."""
    from records.models import Record
    query = request.GET.get('record_q', '').strip()
    if len(query) < 2:
        return HttpResponse('')

    user = request.user
    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    records = Record.objects.filter(
        deleted_at__isnull=True,
        status='active',
    ).filter(
        models_Q(created_by=user) |
        models_Q(tenant_id__in=user_tenant_ids)
    ).filter(
        title__icontains=query
    )[:8]

    return render(request, 'activity/partials/record_search_results.html', {
        'records': records
    })
```

```python
# Import needed
from django.db.models import Q as models_Q
```

```html
<!-- activity/templates/activity/partials/record_search_results.html -->
{% if records %}
<div class="record-search-results" style="display:block">
  {% for record in records %}
  <div class="record-option"
       onclick="selectRecord('{{ record.id }}', '{{ record.title|escapejs }}')">
    {{ record.title }}
    <span style="color:var(--color-text-secondary);font-size:11px;margin-left:6px">
      {{ record.record_type }}
    </span>
  </div>
  {% endfor %}
</div>
<script>
function selectRecord(id, title) {
  document.getElementById('linked-record-id').value = id;
  document.getElementById('record-search-input').value = title;
  document.getElementById('linked-record-display').textContent = '✓ Linked: ' + title;
  document.getElementById('record-search-results').innerHTML = '';
}
</script>
{% endif %}
```

Commit: `git add . && git commit -m "feat: activity create form — all types, recurrence, record link typeahead"`

---

## Phase D — Ministry Surface + Assigned-to-Me Queue (UI)

**Exit criteria:** A disciple can see all tasks assigned to them. A steward can see
their team's campaign/project/task hierarchy. HTMX status updates work on the Ministry
surface identically to My Activities.

---

### Task D.1 — Ministry view + Assigned-to-me queue

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/ministry.html`
- Create: `~/ics/activity/templates/activity/assigned_to_me.html`
- Create: `~/ics/activity/templates/activity/ministry_events.html`

```python
# activity/views.py — ministry
@login_required
def ministry(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)
    now = timezone.now()

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    # Top-level campaigns and projects (no parent)
    campaigns = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        activity_type__in=['campaign', 'project'],
        parent_activity__isnull=True,
        deleted_at__isnull=True,
        metadata__is_template=False,
        status__in=['pending', 'in_progress'],
    ).order_by('due_at', '-created_at')

    # Annotate child tasks on each campaign
    campaign_data = []
    for campaign in campaigns:
        tasks = Activity.objects.filter(
            parent_activity=campaign,
            activity_type='task',
            deleted_at__isnull=True,
            status__in=['pending', 'in_progress'],
        ).order_by('due_at')
        campaign_data.append({'campaign': campaign, 'tasks': tasks})

    # Unparented team tasks (no campaign/project parent)
    loose_tasks = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        activity_type='task',
        parent_activity__isnull=True,
        deleted_at__isnull=True,
        status__in=['pending', 'in_progress'],
    ).order_by('due_at', '-created_at')

    return render(request, 'activity/ministry.html', {
        'campaign_data': campaign_data,
        'loose_tasks': loose_tasks,
        'user_level': user_level,
        'now': now,
    })


@login_required
def assigned_to_me(request):
    user = request.user
    now = timezone.now()

    assigned = Activity.objects.filter(
        assigned_to=user,
        tenant__isnull=False,
        deleted_at__isnull=True,
        status__in=['pending', 'in_progress'],
    ).select_related('parent_activity').order_by('due_at', '-created_at')

    # Group by parent (campaign/project) or no parent
    grouped = {}
    ungrouped = []
    for task in assigned:
        if task.parent_activity_id:
            key = task.parent_activity_id
            if key not in grouped:
                grouped[key] = {
                    'parent': task.parent_activity,
                    'tasks': []
                }
            grouped[key]['tasks'].append(task)
        else:
            ungrouped.append(task)

    return render(request, 'activity/assigned_to_me.html', {
        'grouped': grouped.values(),
        'ungrouped': ungrouped,
        'now': now,
    })


@login_required
def ministry_events(request):
    user = request.user
    now = timezone.now()

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    events = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        activity_type='event',
        deleted_at__isnull=True,
        scheduled_at__gte=now,
    ).order_by('scheduled_at')

    return render(request, 'activity/ministry_events.html', {
        'events': events,
        'now': now,
    })
```

```html
<!-- activity/templates/activity/ministry.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Ministry</h1>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}?type=campaign" class="btn-primary">+ Campaign</a>
  {% endif %}
</div>

<!-- Ministry sub-tabs -->
<div class="ministry-subtabs">
  <a href="{% url 'activity-assigned' %}"
     class="subtab">Assigned to Me</a>
  <a href="{% url 'activity-ministry' %}"
     class="subtab active">Team</a>
  <a href="{% url 'activity-events' %}"
     class="subtab">Events</a>
</div>

<!-- Campaign / project groups -->
{% for group in campaign_data %}
<div class="campaign-group">
  <div class="campaign-group-header">
    <h3>{{ group.campaign.title }}</h3>
    <div style="display:flex;align-items:center;gap:8px">
      <span class="type-badge {{ group.campaign.activity_type }}">
        {{ group.campaign.activity_type }}
      </span>
      {% if group.campaign.due_at %}
      <span class="due-label {% if group.campaign.due_at < now %}overdue{% endif %}">
        {{ group.campaign.due_at|date:"d M" }}
      </span>
      {% endif %}
    </div>
  </div>
  <div class="campaign-tasks">
    {% for task in group.tasks %}
      {% include "activity/partials/activity_card.html" with activity=task %}
    {% empty %}
    <div style="padding:14px 16px;color:var(--color-text-secondary);font-size:14px">
      No tasks yet.
      {% if user_level >= 3 %}
      <a href="{% url 'activity-create' %}?parent={{ group.campaign.id }}&type=task"
         style="color:var(--color-primary)">Add task</a>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</div>
{% endfor %}

<!-- Loose tasks -->
{% if loose_tasks %}
<section class="activity-section" style="margin-top:8px">
  <h2 class="section-title">Unassigned Tasks</h2>
  {% for task in loose_tasks %}
    {% include "activity/partials/activity_card.html" with activity=task %}
  {% endfor %}
</section>
{% endif %}

{% if not campaign_data and not loose_tasks %}
<div class="empty-state">
  <p>No team activities yet.</p>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}" class="btn-primary">Create a campaign</a>
  {% endif %}
</div>
{% endif %}
{% endblock %}
```

```html
<!-- activity/templates/activity/assigned_to_me.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Assigned to Me</h1>
</div>

<div class="ministry-subtabs">
  <a href="{% url 'activity-assigned' %}" class="subtab active">Assigned to Me</a>
  <a href="{% url 'activity-ministry' %}" class="subtab">Team</a>
  <a href="{% url 'activity-events' %}" class="subtab">Events</a>
</div>

{% for group in grouped %}
<div class="campaign-group">
  <div class="campaign-group-header">
    <h3>{{ group.parent.title }}</h3>
    <span class="type-badge {{ group.parent.activity_type }}">
      {{ group.parent.activity_type }}
    </span>
  </div>
  <div class="campaign-tasks">
    {% for task in group.tasks %}
      {% include "activity/partials/activity_card.html" with activity=task %}
    {% endfor %}
  </div>
</div>
{% endfor %}

{% if ungrouped %}
<section class="activity-section">
  <h2 class="section-title">Direct Assignments</h2>
  {% for task in ungrouped %}
    {% include "activity/partials/activity_card.html" with activity=task %}
  {% endfor %}
</section>
{% endif %}

{% if not grouped and not ungrouped %}
<div class="empty-state">
  <p>Nothing assigned to you right now.</p>
</div>
{% endif %}
{% endblock %}
```

```html
<!-- activity/templates/activity/ministry_events.html -->
{% extends "activity/base_activity.html" %}
{% load tz %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Events</h1>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}?type=event" class="btn-primary">+ Event</a>
  {% endif %}
</div>

<div class="ministry-subtabs">
  <a href="{% url 'activity-assigned' %}" class="subtab">Assigned to Me</a>
  <a href="{% url 'activity-ministry' %}" class="subtab">Team</a>
  <a href="{% url 'activity-events' %}" class="subtab active">Events</a>
</div>

{% if events %}
  {% regroup events by scheduled_at|date:"Y-m-d" as events_by_date %}
  {% for date_group in events_by_date %}
  <div class="date-group-header">{{ date_group.grouper|date:"l, d F Y" }}</div>
  {% for event in date_group.list %}
  <div class="activity-card">
    <div class="activity-card-header">
      <span class="activity-title">{{ event.title }}</span>
      <span class="activity-meta">{{ event.scheduled_at|time:"H:i" }}</span>
    </div>
    {% if event.description %}
    <p class="activity-meta">{{ event.description|truncatechars:120 }}</p>
    {% endif %}
    {% if event.kgs_pathway %}
    <span class="activity-meta">{{ event.get_kgs_pathway_display }}</span>
    {% endif %}
    <div class="status-controls">
      <a href="{% url 'activity-detail' event.id %}" class="btn-status">View</a>
    </div>
  </div>
  {% endfor %}
  {% endfor %}
{% else %}
<div class="empty-state">
  <p>No upcoming events.</p>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}" class="btn-primary">Create an event</a>
  {% endif %}
</div>
{% endif %}
{% endblock %}
```

Commit: `git add . && git commit -m "feat: ministry surface — team view, assigned-to-me queue, events dated list"`

---

## Phase E — Campaign Management + Activity Detail

**Exit criteria:** A steward can create a campaign, add nested tasks, assign to
team members. Any user can view an activity detail page. Completed activities
shown in a "Done" section.

---

### Task E.1 — Activity detail view

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/activity_detail.html`

```python
# activity/views.py — activity_detail
@login_required
def activity_detail(request, activity_id):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    activity = get_object_or_404(Activity, id=activity_id, deleted_at__isnull=True)

    # Permission check
    user_tenant_ids = list(user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True))

    is_owner = activity.created_by == user
    is_assignee = activity.assigned_to == user
    is_team_member = activity.tenant_id in user_tenant_ids if activity.tenant_id else False
    is_personal_visible = not activity.tenant_id and is_owner

    if not (is_owner or is_assignee or is_team_member or is_personal_visible):
        return render(request, 'activity/locked.html', status=403)

    # Child tasks
    child_tasks = Activity.objects.filter(
        parent_activity=activity,
        deleted_at__isnull=True,
    ).order_by('due_at', '-created_at')

    # Activity log
    logs = ActivityLog.objects.filter(
        activity=activity
    ).order_by('-created_at')[:10]

    # Linked records
    from records.models import Relationship, Record
    linked_relationships = Relationship.objects.filter(
        from_record__metadata__activity_id=str(activity_id),
        deleted_at__isnull=True,
    ).select_related('to_record')

    can_edit = is_owner or user_level >= 3

    return render(request, 'activity/activity_detail.html', {
        'activity': activity,
        'child_tasks': child_tasks,
        'logs': logs,
        'linked_relationships': linked_relationships,
        'can_edit': can_edit,
        'user_level': user_level,
        'now': timezone.now(),
    })
```

```html
<!-- activity/templates/activity/activity_detail.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div style="padding:16px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div>
      <span class="type-badge {{ activity.activity_type }}">{{ activity.activity_type }}</span>
      <h1 style="font-size:20px;font-weight:700;margin-top:6px">{{ activity.title }}</h1>
    </div>
    {% if can_edit %}
    <a href="{% url 'activity-edit' activity.id %}" class="btn-secondary" style="white-space:nowrap">
      Edit
    </a>
    {% endif %}
  </div>

  {% if activity.description %}
  <p style="font-size:15px;color:var(--color-text);margin-bottom:12px">
    {{ activity.description }}
  </p>
  {% endif %}

  <!-- Meta row -->
  <div class="activity-meta" style="margin-bottom:16px">
    <span>Status: <strong>{{ activity.get_status_display }}</strong></span>
    {% if activity.due_at %}
      <span>Due: {{ activity.due_at|date:"d M Y" }}</span>
    {% endif %}
    {% if activity.scheduled_at %}
      <span>Scheduled: {{ activity.scheduled_at|date:"d M Y, H:i" }}</span>
    {% endif %}
    {% if activity.assigned_to %}
      <span>Assigned to: {{ activity.assigned_to.get_full_name|default:activity.assigned_to.email }}</span>
    {% endif %}
    {% if activity.kgs_pathway %}
      <span>Pathway: {{ activity.get_kgs_pathway_display }}</span>
    {% endif %}
    {% if activity.recurrence != 'none' %}
      <span>Repeats: {{ activity.get_recurrence_display }}</span>
    {% endif %}
  </div>

  <!-- Progress bar (goals and programmes) -->
  {% if activity.activity_type in 'goal,programme' %}
  <div class="progress-bar-wrap" style="margin-bottom:12px">
    <div class="progress-bar" style="width:{{ activity.progress }}%"></div>
  </div>
  <span class="activity-meta">{{ activity.progress }}% complete</span>
  {% endif %}

  <!-- HTMX status controls -->
  <div class="status-controls"
       id="activity-status-{{ activity.id }}"
       hx-target="#activity-status-{{ activity.id }}"
       hx-swap="outerHTML">
    {% if activity.status == 'pending' %}
    <button class="btn-status"
            hx-post="{% url 'htmx-activity-status' activity.id %}"
            hx-vals='{"status":"in_progress"}'>
      Start
    </button>
    {% elif activity.status == 'in_progress' %}
    <button class="btn-status active"
            hx-post="{% url 'htmx-activity-status' activity.id %}"
            hx-vals='{"status":"completed"}'>
      ✓ Mark Complete
    </button>
    {% endif %}
  </div>

  <!-- Linked records -->
  {% if linked_relationships %}
  <section style="margin-top:24px">
    <h2 style="font-size:15px;font-weight:700;margin-bottom:8px">Linked Records</h2>
    {% for rel in linked_relationships %}
    <div style="padding:10px 12px;border:1px solid var(--color-border);border-radius:8px;
         margin-bottom:8px;font-size:14px">
      <span style="font-weight:600">{{ rel.to_record.title }}</span>
      <span style="color:var(--color-text-secondary);margin-left:8px;font-size:12px">
        {{ rel.to_record.record_type }} · {{ rel.relationship_type }}
      </span>
    </div>
    {% endfor %}
  </section>
  {% endif %}

  <!-- Child tasks -->
  {% if child_tasks %}
  <section style="margin-top:24px">
    <h2 style="font-size:15px;font-weight:700;margin-bottom:8px">Tasks</h2>
    {% for task in child_tasks %}
      {% include "activity/partials/activity_card.html" with activity=task %}
    {% endfor %}
  </section>
  {% endif %}
  {% if can_edit and activity.activity_type in 'campaign,project' %}
  <div style="margin-top:8px">
    <a href="{% url 'activity-create' %}?parent={{ activity.id }}&type=task"
       class="btn-secondary" style="width:100%;display:block;text-align:center">
      + Add Task
    </a>
  </div>
  {% endif %}

  <!-- Activity log -->
  {% if logs %}
  <section style="margin-top:24px">
    <h2 style="font-size:15px;font-weight:700;margin-bottom:8px">History</h2>
    {% for log in logs %}
    <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--color-border);
         font-size:13px;color:var(--color-text-secondary)">
      <span style="white-space:nowrap">{{ log.created_at|date:"d M, H:i" }}</span>
      <span>{{ log.event_type|capfirst }}
        {% if log.previous_value and log.new_value %}
          · {{ log.previous_value }} → {{ log.new_value }}
        {% elif log.new_value %}
          · {{ log.new_value }}
        {% endif %}
      </span>
    </div>
    {% endfor %}
  </section>
  {% endif %}
</div>
{% endblock %}
```

Commit: `git add . && git commit -m "feat: activity detail — meta, status HTMX, child tasks, linked records, log"`

---

## Phase F — Templates + Gifts Register + Calendar UI Stub

**Exit criteria:** Level 4+ can create activity templates. Level 2+ can instantiate
them. Personal gifts register is functional. Team gifts view works for stewards.
Calendar backend passes smoke test.

---

### Task F.1 — Template list + HTMX instantiate

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/template_list.html`
- Create: `~/ics/activity/templates/activity/partials/template_search_results.html`

```python
# activity/views.py — template_list
@login_required
def template_list(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    templates = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        metadata__is_template=True,
        deleted_at__isnull=True,
    ).order_by('activity_type', 'title')

    return render(request, 'activity/template_list.html', {
        'templates': templates,
        'user_level': user_level,
    })


@login_required
def htmx_template_search(request):
    """HTMX: search templates for 'start from template' affordance."""
    query = request.GET.get('template_q', '').strip()
    if len(query) < 2:
        return HttpResponse('')

    user_tenant_ids = request.user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    templates = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        metadata__is_template=True,
        title__icontains=query,
        deleted_at__isnull=True,
    )[:6]

    return render(request, 'activity/partials/template_search_results.html', {
        'templates': templates,
    })


@login_required
@require_POST
def htmx_instantiate_template(request, template_id):
    """HTMX: instantiate a template and redirect to the new activity's edit form."""
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    if user_level < 2:
        return HttpResponse('Level 2 required to use templates.', status=403)

    template = get_object_or_404(
        Activity,
        id=template_id,
        deleted_at__isnull=True,
    )
    if not template.metadata.get('is_template'):
        return HttpResponse('Not a template.', status=400)

    new_activity = Activity.objects.create(
        tenant=template.tenant,
        created_by=user,
        activity_type=template.activity_type,
        title=template.title,
        description=template.description,
        recurrence=template.recurrence,
        kgs_pillar=template.kgs_pillar,
        kgs_pathway=template.kgs_pathway,
        status='pending',
        progress=0,
        assigned_to=user,
        metadata={
            **template.metadata,
            'is_template': False,
            'template_id': str(template.id),
            'source_app': 'activity',
        },
    )

    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(f'/activity/{new_activity.id}/edit/')
```

```html
<!-- activity/templates/activity/partials/template_search_results.html -->
{% if templates %}
<div style="display:block">
  {% for t in templates %}
  <div class="record-option"
       hx-post="{% url 'htmx-instantiate' t.id %}"
       hx-target="body"
       hx-push-url="true"
       style="cursor:pointer">
    {{ t.title }}
    <span style="color:var(--color-text-secondary);font-size:11px;margin-left:6px">
      {{ t.activity_type }}
    </span>
  </div>
  {% endfor %}
</div>
{% endif %}
```

---

### Task F.2 — Gifts register (personal + team)

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/gifts_register.html`
- Create: `~/ics/activity/templates/activity/team_gifts.html`
- Create: `~/ics/activity/templates/activity/partials/gift_card.html`

```python
# activity/views.py — gifts_register + team_gifts
@login_required
def gifts_register(request):
    user = request.user
    gifts = Activity.objects.filter(
        created_by=user,
        activity_type='skill',
        tenant__isnull=True,
        deleted_at__isnull=True,
    ).order_by('status', '-created_at')

    return render(request, 'activity/gifts_register.html', {'gifts': gifts})


@login_required
def team_gifts(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    if user_level < 3:
        return render(request, 'activity/locked.html', {
            'message': 'The team gifts register requires Steward level (Level 3+).'
        })

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    # Tenant-scoped skill activities
    team_gifts_qs = Activity.objects.filter(
        activity_type='skill',
        tenant_id__in=user_tenant_ids,
        deleted_at__isnull=True,
        status='active',
    ).select_related('created_by').order_by('metadata__service_order', 'title')

    return render(request, 'activity/team_gifts.html', {
        'team_gifts': team_gifts_qs,
    })


@login_required
@require_POST
def htmx_add_gift(request):
    """HTMX: add a new skill/gift entry. Returns updated gift list fragment."""
    user = request.user
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    kgs_pathway = request.POST.get('kgs_pathway') or None
    service_order = request.POST.get('service_order', '').strip()
    competence = int(request.POST.get('competence', 20))

    if not title:
        return HttpResponse('<p style="color:red">Title is required.</p>')

    Activity.objects.create(
        created_by=user,
        tenant=None,
        activity_type='skill',
        title=title,
        description=description or None,
        kgs_pathway=kgs_pathway,
        progress=competence,
        status='active',
        metadata={
            'source_app': 'activity',
            'is_template': False,
            'service_order': service_order or None,
        },
    )

    gifts = Activity.objects.filter(
        created_by=user,
        activity_type='skill',
        tenant__isnull=True,
        deleted_at__isnull=True,
    ).order_by('status', '-created_at')

    return render(request, 'activity/partials/gifts_list.html', {'gifts': gifts})


@login_required
@require_POST
def htmx_archive_gift(request, gift_id):
    """HTMX: archive a skill/gift entry."""
    user = request.user
    gift = get_object_or_404(Activity, id=gift_id, created_by=user, activity_type='skill')
    gift.status = 'cancelled'
    gift.save(update_fields=['status', 'updated_at'])

    return HttpResponse(status=200)
```

```html
<!-- activity/templates/activity/gifts_register.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Gifts & Skills</h1>
</div>

<!-- Add gift form -->
<div style="padding:16px;background:var(--color-surface);border-bottom:1px solid var(--color-border)">
  <form hx-post="{% url 'htmx-add-gift' %}"
        hx-target="#gifts-list"
        hx-swap="innerHTML"
        hx-on::after-request="this.reset()">
    {% csrf_token %}
    <div class="form-group">
      <input type="text" name="title" class="form-control"
             placeholder="Gift or skill name (e.g. Teaching, Administration)" required>
    </div>
    <div class="form-group">
      <textarea name="description" class="form-control" rows="2"
                placeholder="How does this gift manifest in your life?"></textarea>
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <div class="form-group" style="flex:1;min-width:140px">
        <label style="font-size:12px;font-weight:600;color:var(--color-text-secondary)">
          KGS Pathway
        </label>
        <select name="kgs_pathway" class="form-control" style="font-size:14px">
          <option value="">— None —</option>
          <option value="service">Service</option>
          <option value="leadership">Leadership</option>
          <option value="mission">Mission</option>
          <option value="spiritual_formation">Spiritual Formation</option>
          <option value="community_life">Community Life</option>
          <option value="learning">Learning</option>
          <option value="apostolic_stewardship">Apostolic Stewardship</option>
        </select>
      </div>
      <div class="form-group" style="flex:1;min-width:140px">
        <label style="font-size:12px;font-weight:600;color:var(--color-text-secondary)">
          Competence (1–100)
        </label>
        <input type="number" name="competence" class="form-control"
               min="1" max="100" value="20" style="font-size:14px">
      </div>
    </div>
    <div class="form-group">
      <input type="text" name="service_order" class="form-control"
             placeholder="Service order (optional, e.g. Order of Teaching and Doctrine)">
    </div>
    <button type="submit" class="btn-primary" style="width:100%">Add Gift</button>
  </form>
</div>

<!-- Gifts list -->
<div id="gifts-list" style="padding:8px 0">
  {% include "activity/partials/gifts_list.html" %}
</div>

{% if request.user.userprofile.competence_level >= 3 %}
<div style="margin:8px 16px 24px">
  <a href="{% url 'activity-team-gifts' %}" class="btn-secondary"
     style="width:100%;display:block;text-align:center">
    View Team Gifts Register
  </a>
</div>
{% endif %}
{% endblock %}
```

```html
<!-- activity/templates/activity/partials/gifts_list.html -->
{% for gift in gifts %}
{% if gift.status != 'cancelled' %}
<div class="gift-card" id="gift-{{ gift.id }}">
  <div class="gift-card-body">
    <div class="gift-title">{{ gift.title }}</div>
    {% if gift.description %}
    <div class="gift-meta">{{ gift.description|truncatechars:100 }}</div>
    {% endif %}
    <div class="gift-meta" style="margin-top:4px">
      {% if gift.kgs_pathway %}<span>{{ gift.get_kgs_pathway_display }}</span>{% endif %}
      {% if gift.metadata.service_order %}<span>{{ gift.metadata.service_order }}</span>{% endif %}
    </div>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px">
    <span class="gift-competence">{{ gift.progress }}%</span>
    <button class="btn-status"
            hx-post="{% url 'htmx-archive-gift' gift.id %}"
            hx-target="#gift-{{ gift.id }}"
            hx-swap="outerHTML"
            style="font-size:11px">
      Archive
    </button>
  </div>
</div>
{% endif %}
{% empty %}
<div class="empty-state">
  <p>No gifts or skills recorded yet.</p>
</div>
{% endfor %}
```

Commit: `git add . && git commit -m "feat: gifts register — add, view, archive; team gifts view for stewards"`

---

### Task F.3 — Smoke test checklist

Before closing Phase F, verify manually on mobile:

- [ ] Member creates a personal task; marks complete via HTMX — card updates without page reload
- [ ] Member creates a habit (weekly); sees recurrence label on card
- [ ] Member creates a goal; sees progress bar
- [ ] Member adds a gift to gifts register; archives one
- [ ] Member views their Learn enrolment as a read-only card on My Activities
- [ ] Disciple sees "Assigned to me" tab; HTMX status update works
- [ ] Steward creates a campaign with two nested tasks; both appear in campaign group
- [ ] Steward assigns a task to another team member; task appears in their "Assigned to me" queue
- [ ] Steward views team gifts register; sees correct tenant scope
- [ ] Level 4 user creates an activity template; Level 2 user instantiates it and gets pre-filled form
- [ ] Record link typeahead returns results; linking creates a Relationship (verify in Django admin)
- [ ] `GET /api/calendar/events/?from=2026-04-08&to=2026-04-30` returns events JSON
- [ ] `GET /api/activities/?due_today=true` returns today's due activities
- [ ] `GET /api/activities/?overdue=true` returns overdue activities
- [ ] `GET /api/activities/?metadata__source_app=learn` returns learn enrolments
- [ ] `ActivityLog` entries exist in Django admin after status changes

Commit: `git add . && git commit -m "feat: activity app — smoke test pass, all phases complete"`

---

## Django Endpoint Summary

```
# Activity CRUD (core engine)
GET    /api/activities/                  list with all filters
POST   /api/activities/                  create
GET    /api/activities/{id}/             retrieve
PATCH  /api/activities/{id}/             update
DELETE /api/activities/{id}/             soft delete

# Activity template
POST   /api/activities/{id}/instantiate/ create Activity from template

# Paraclete-required filters (all on GET /api/activities/)
?assigned_to={user_id}
?due_today=true
?overdue=true
?activity_type={type}
?status={status}
?tenant_id={tenant_id}
?parent_activity_id={id}
?metadata__source_app={app}
?surface=personal
?surface=ministry

# Calendar aggregation
GET    /api/calendar/events/             date-range event feed

# Activity App health
GET    /api/activity/health/
```

---

## File Map (Activity App additions)

```
~/ics/
  activity/
    __init__.py
    apps.py                    ← MODIFIED: ready() imports signals
    models.py                  ← VERIFIED: all v5 fields present + indexes
    filters.py                 ← NEW: ActivityFilter (django-filter)
    serializers.py             ← VERIFIED: ActivitySerializer, ActivityLogSerializer
    api_views.py               ← NEW/MODIFIED: ActivityViewSet, health, instantiate action
    views.py                   ← NEW: all Django template views + HTMX partials
    signals.py                 ← NEW: log creation on save
    urls.py                    ← MODIFIED: full URL structure
    templates/
      activity/
        base_activity.html     ← NEW
        my_activities.html     ← NEW
        ministry.html          ← NEW
        assigned_to_me.html    ← NEW
        ministry_events.html   ← NEW
        activity_form.html     ← NEW (create + edit)
        activity_detail.html   ← NEW
        template_list.html     ← NEW
        gifts_register.html    ← NEW
        team_gifts.html        ← NEW
        locked.html            ← NEW (competence gate + 403)
        partials/
          activity_card.html   ← NEW (HTMX status controls)
          gifts_list.html      ← NEW (HTMX target for add/archive)
          record_search_results.html  ← NEW
          template_search_results.html ← NEW

  calendar_app/
    __init__.py
    apps.py
    service.py                 ← NEW: aggregation logic
    views.py                   ← NEW: calendar_events DRF view
    urls.py                    ← NEW
    templates/
      calendar/
        (empty — Phase 2 adds grid view)

  frontend/assets/css/
    activity.css               ← NEW
```

**Note:** There is no `activity-app.js`. The UI is entirely served by Django views
and templates. HTMX replaces the JS interaction layer. `storage.js` is retained
for theme/UI state only.

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|-------|----------------|-------------------|---------------|
| A | ActivityViewSet filters, soft delete, instantiate endpoint, ActivityLog signal, Calendar app scaffold + endpoint | Phases 0–4 done; `activity` app exists | All filters work; health 200; calendar endpoint returns JSON |
| B | Django URL structure, views/api_views split, base template, `activity.css` | Phase A done | All URLs resolve; base template loads HTMX and CSS |
| C | My Activities surface: tasks, habits, goals, Learn cards, HTMX status, create form, record link typeahead | Phase B done | Member can create, view, and complete personal activities via HTMX |
| D | Ministry surface: team view, assigned-to-me queue, events dated list | Phase C done | Disciple sees assigned queue; steward sees team hierarchy |
| E | Activity detail, campaign/project management, activity edit | Phase D done | Steward creates campaign with nested tasks; detail page shows log |
| F | Templates (Level 4+ create, Level 2+ instantiate), gifts register, team gifts, smoke test | Phase E done | Full smoke test checklist passes |

---

## Deferred (Post-MVP)

- Full RRULE custom recurrence builder (UI for `recurrence: 'custom'`)
- Activity analytics dashboard (completion rates, habit streaks, team performance)
- Bulk task assignment (multiple tasks → multiple users in one action)
- Cross-tenant campaign templates (visible across Church Collective network)
- `assigned_to_tenant_id` field (collective/network-level assignment — see v5 contract note)
- Calendar App Phase 2: full month/week grid UI in Django templates + HTMX
- Calendar App Phase 2: Records engine events (programme milestones, governance calendars)
- Progress update HTMX widget (slider or input for goals — currently manual via edit form)
- iCal export from Calendar app
- Notifications on task assignment (wired to Notifications app stub in Phase 5.7)
- Paraclete "next suggested activity" integration (Phase 6 of main roadmap)


---

# ICS Learn App — System Design & Build Roadmap

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **UI Architecture amendment — 2026-04-07:**
> The original design specified vanilla JS (IIFE modules + `learn.service.js`) for the UI layer.
> This has been superseded by the platform-wide decision to build all app UIs in
> **Django templates + HTMX**. The backend (Django `learn` app, DRF endpoints, signals,
> models) is unchanged. Phases A and B are unchanged. Phases C–G are amended:
> all `learn-app.js`, `learn.service.js`, and `learn.html` references are replaced
> by Django views, URL patterns, and templates. `learn.css` is unchanged — the
> design system carries forward identically. Vanilla JS is retained only for
> theme/UI state (`storage.js`) and minor interactions HTMX cannot handle.

**Goal:** Build the ICS Learn App — the digital expression of the Sceptre Qualification Programmes Framework — enabling learners to browse courses, enrol in programmes, track progress, and earn certifications that advance their competence level within the Kingdom Governance System.

**Architecture:** Django + DRF backend with a dedicated `learn` app. UI rendered via Django templates with HTMX for dynamic interactions (progress updates, enrolment, lesson completion, queue refreshes). All learning content is Record objects (`record_family: "learning"`). All learner progress is Activity objects. The two are linked via the Relationship engine. No new tables beyond the existing data contract — the Learning Engine is a pattern layer over Records + Activities.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX, `learn.css` (mobile-first, existing CSS variables).

**Data Contract reference:** `2026-04-07-ics-platform-data-contract_v4.md` — all schemas and patterns in this document originate from Part 9 of that contract.

---

## System Overview

### The Learning Stack

```
KGS Layer          Apostles Programme (7-year mission container)
                   ↓ contextualises
Content Layer      Qualification Programmes (Certificate → Doctorate)
                   ↓ contains
                   Courses → Lessons → Assignments / Quizzes
                   (all Record objects, record_family: "learning")
                   ↓ structured by
                   Relationships (part_of — curriculum graph)

Learner Layer      Enrolment Activity (activity_type: "programme")
                   ↓ nests
                   Course Activity (activity_type: "project")
                   ↓ nests
                   Lesson/Assessment Activities (activity_type: "task")
                   ↓ completes to produce
                   Certification Record (record_type: "certification")
                   ↓ confirmed by steward via
                   POST /api/learn/certifications/{id}/confirm/
                   ↓ advances
                   user.competence_level
```

### User roles in the Learn App

| Role | What they do |
|---|---|
| Seeker (0b) | Browse published programmes. Cannot enrol. |
| Member (Level 1+) | Enrol, track progress, complete lessons |
| Disciple/Operator (Level 2+) | All above + submit assignments |
| Branch-Steward (Level 3+) | Confirm certifications for their tenant's learners |
| District-Steward / Senior Steward (Level 4+) | Author and submit Programmes and Courses for review |
| Architect (Level 5) | Review submitted content, approve (status → active), lock |

---

## The Five Qualification Programmes

These are the five content containers of the Apostles Programme. Each is a
Record (`record_class: "organizational"`, `record_family: "learning"`,
`record_type: "programme"`). Courses are authored within them.

| Programme | Competence Level | Duration | KGS Pathways | Prerequisites |
|---|---|---|---|---|
| Certificate | Level 1 | 1 year | New Life; Community Life; Learning | None |
| Diploma | Level 2 | 3 years | Spiritual Formation; Service; Mission; Learning | Certificate |
| Degree | Level 3 | 4 years | Leadership; Learning | Diploma + Certificate |
| Masters | Level 4 | 4–5 years | Leadership; Apostolic Stewardship | Degree + prior |
| Doctorate | Level 5 | 7 years total | Leadership; Apostolic Stewardship | Masters + all prior |

---

## Feature List (All Features — Unphased)

This is the complete Learn App feature inventory. Phasing follows below.

### F1 — Programme Catalogue
- Browse all published Qualification Programmes
- Pathway View: grouped by KGS pathway (default for enrolled learners)
- Catalogue View: flat list filtered by competence level
- Locked indicator for programmes above learner's current level
- Programme detail: title, description, pathways, duration, prerequisites, course list

### F2 — Course Browser
- Browse courses within a programme
- Course detail: title, description, lesson list, assignments, quizzes
- Competence gate: courses requiring a higher level show locked state

### F3 — Enrolment
- Enrol in a programme (creates enrolment Activity of type "programme")
- Prerequisite check before enrolment is permitted
- One active enrolment per programme per user
- Enrolment confirmation screen

### F4 — Progress Tracking
- Lesson completion (marks task Activity as completed)
- Course progress bar (% lessons/assessments completed)
- Programme progress bar (% courses completed)
- Progress persists via ActivityLog
- Resume where left off (last incomplete lesson)

### F5 — Lesson Viewer
- Read lesson content (Record.content rendered as rich text / markdown)
- Mark lesson complete button
- Navigate previous / next lesson
- Back to course breadcrumb

### F6 — Assessments (Assignments & Quizzes)
- Quiz: inline multiple-choice or short answer (stored in Record.custom_fields)
- Assignment: text submission by learner (stored as child Record linked to assignment)
- Submission marks assessment Activity as completed
- Steward can view submitted assignments within their tenant scope

### F7 — Certification & Competence Advancement
- Auto-create draft Certification Record when programme Activity hits 100%
- Learner sees "Awaiting certification" status
- Steward review queue: list of draft certifications for their tenant's learners
- Steward confirms → certification status → active → competence_level incremented
- Learner notification on certification confirmed (via Notifications app stub)

### F8 — Content Authorship (Level 4+)
- Create Programme record (draft)
- Create Course record (linked to programme via part_of Relationship)
- Create Lesson record (linked to course via part_of Relationship)
- Create Assignment / Quiz record (linked to course or lesson via part_of)
- Rich text / markdown content editor for lesson body
- Submit Programme or Course for Handbook review (status → submitted)

### F9 — Handbook Review Queue (Level 5)
- List submitted learning records (status: "submitted", record_family: "learning")
- Review programme / course detail
- Approve (status → active) or return to draft with a note
- Lock approved content (status → locked)

### F10 — Pathway View (Dashboard integration)
- "You are enrolled in [Programme] — [Primary Pathway]" banner
- Active enrolment widget surfaced on Learn App home
- Paraclete integration: "Continue your lesson: [lesson title]" (Phase 6)

### F11 — My Learning Dashboard (Learn App home)
- Active enrolments with progress
- Completed programmes and certifications
- Recommended next programme (based on competence level)
- Quick-access: resume last lesson

---

## Build Phases

### Phase A — Django Learn App (backend foundation)
*Entry requirement: Phases 0–4 of main roadmap complete (Django project, Records, Activity, Identity engines all live).*

### Phase B — Content Engine (read-only)
*Entry requirement: Phase A complete.*

### Phase C — Enrolment + Progress Tracking
*Entry requirement: Phase B complete.*

### Phase D — Assessments
*Entry requirement: Phase C complete.*

### Phase E — Certification + Competence Advancement
*Entry requirement: Phase D complete.*

### Phase F — Content Authorship + Handbook Review
*Entry requirement: Phase E complete.*

### Phase G — UI Polish + Pathway View + My Learning Dashboard
*Entry requirement: Phase F complete.*

---

## Phase A — Django Learn App (Backend Foundation)

**Exit criteria:** `GET /api/learn/health/` returns `{"status": "ok"}`. Django `learn` app exists with models, serializers, basic endpoints. No UI yet.

### Task A.1 — Create Django `learn` app

**Files:**
- Create: `~/ics/learn/__init__.py`
- Create: `~/ics/learn/apps.py`
- Create: `~/ics/learn/models.py`
- Create: `~/ics/learn/serializers.py`
- Create: `~/ics/learn/views.py`
- Create: `~/ics/learn/urls.py`
- Modify: `~/ics/ics_project/settings/base.py` (add `learn` to INSTALLED_APPS)
- Modify: `~/ics/ics_project/urls.py` (include learn.urls)

**Step 1:** Create the app scaffold

```bash
cd ~/ics && python manage.py startapp learn
```

**Step 2:** Add to INSTALLED_APPS in `base.py`

```python
INSTALLED_APPS = [
    ...
    'learn',
]
```

**Step 3:** Create `learn/models.py`

The Learn App does not define its own content models — all content is stored
in `records.Record`. The only Learn-specific model is `CertificationConfirmation`
which records the steward action (audit trail separate from the Record status change).

```python
# learn/models.py
import uuid
from django.db import models
from django.conf import settings


class CertificationConfirmation(models.Model):
    """
    Audit record of a steward confirming a learner's certification.
    The certification itself is a records.Record with record_type='certification'.
    This model records WHO confirmed it and WHEN, separately from the Record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certification_record_id = models.UUIDField(db_index=True)  # FK → records.Record
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='certifications_confirmed'
    )
    learner_id = models.UUIDField(db_index=True)               # FK → User (the learner)
    previous_competence_level = models.IntegerField()
    new_competence_level = models.IntegerField()
    confirmed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-confirmed_at']
        indexes = [
            models.Index(fields=['certification_record_id']),
            models.Index(fields=['learner_id']),
            models.Index(fields=['confirmed_by']),
        ]
```

**Step 4:** Run migrations

```bash
python manage.py makemigrations learn
python manage.py migrate
```

**Step 5:** Create health endpoint in `learn/views.py`

```python
# learn/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "learn"})
```

**Step 6:** Create `learn/urls.py`

```python
# learn/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='learn-health'),
]
```

**Step 7:** Include in main `urls.py`

```python
path('api/learn/', include('learn.urls')),
```

**Step 8:** Test

```bash
curl https://your-domain.com/api/learn/health/
# Expected: {"status": "ok", "app": "learn"}
```

Commit: `git add . && git commit -m "feat: learn app scaffold + health endpoint"`

---

### Task A.2 — Certification confirmation endpoint

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`
- Modify: `~/ics/learn/serializers.py`
- Modify: `~/ics/accounts/serializers.py` (competence_level write rule)

This is the most critical backend endpoint in the Learn App. It is the ONLY
place in the system that may increment `user.competence_level`.

**Step 1:** Add `CertificationConfirmSerializer` to `learn/serializers.py`

```python
# learn/serializers.py
from rest_framework import serializers
from .models import CertificationConfirmation


class CertificationConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificationConfirmation
        fields = [
            'id', 'certification_record_id', 'confirmed_by',
            'learner_id', 'previous_competence_level',
            'new_competence_level', 'confirmed_at', 'notes'
        ]
        read_only_fields = [
            'id', 'confirmed_by', 'previous_competence_level',
            'new_competence_level', 'confirmed_at'
        ]
```

**Step 2:** Add the confirm view to `learn/views.py`

```python
# learn/views.py (additions)
import uuid
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from records.models import Record          # adjust import path to your project
from django.contrib.auth import get_user_model
from .models import CertificationConfirmation
from .serializers import CertificationConfirmSerializer

User = get_user_model()


def is_level_3_or_above(user):
    """Check if user has competence_level >= 3 (branch-steward or above)."""
    return hasattr(user, 'userprofile') and user.userprofile.competence_level >= 3


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_certification(request, certification_id):
    """
    Steward confirms a learner's certification.
    - Gated to competence_level >= 3
    - Sets certification Record status to 'active'
    - Increments learner's competence_level by 1 (up to target_level)
    - Creates CertificationConfirmation audit record
    - This endpoint is the SOLE authorised writer of competence_level
    """
    if not is_level_3_or_above(request.user):
        return Response(
            {"detail": "Certification confirmation requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    certification_record = get_object_or_404(
        Record,
        id=certification_id,
        record_type='certification',
        status='draft'
    )

    # Retrieve metadata from the certification record
    metadata = certification_record.metadata or {}
    learner_id = metadata.get('learner_id') or str(certification_record.created_by_id)
    target_level = metadata.get('target_level', 1)

    learner = get_object_or_404(User, id=learner_id)
    learner_profile = learner.userprofile
    previous_level = learner_profile.competence_level

    # Only advance if not already at or above target level
    if previous_level >= target_level:
        return Response(
            {"detail": "Learner is already at or above the target competence level."},
            status=status.HTTP_400_BAD_REQUEST
        )

    new_level = min(previous_level + 1, target_level)

    # Update certification record status
    certification_record.status = 'active'
    certification_record.save(update_fields=['status', 'updated_at'])

    # Advance learner competence level — only write path in the system
    learner_profile.competence_level = new_level
    learner_profile.save(update_fields=['competence_level'])

    # Create audit record
    confirmation = CertificationConfirmation.objects.create(
        certification_record_id=certification_record.id,
        confirmed_by=request.user,
        learner_id=learner.id,
        previous_competence_level=previous_level,
        new_competence_level=new_level,
        notes=request.data.get('notes', '')
    )

    serializer = CertificationConfirmSerializer(confirmation)
    return Response(serializer.data, status=status.HTTP_200_OK)
```

**Step 3:** Add to `learn/urls.py`

```python
path('certifications/<uuid:certification_id>/confirm/', views.confirm_certification, name='certification-confirm'),
```

**Step 4:** Verify `competence_level` is read-only in `accounts/serializers.py`
everywhere EXCEPT this endpoint. Add a comment:

```python
# accounts/serializers.py — UserProfileSerializer
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['competence_level', 'status', ...]
        read_only_fields = ['competence_level']
        # NOTE: competence_level is intentionally read-only here.
        # The ONLY authorised write path is POST /api/learn/certifications/{id}/confirm/
        # See learn/views.py::confirm_certification
```

Commit: `git add . && git commit -m "feat: certification confirm endpoint — sole writer of competence_level"`

---

### Task A.3 — Certification review queue endpoint

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`

Stewards need a list of draft certifications pending their review.

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def certification_queue(request):
    """
    Returns draft certification records visible to the requesting steward.
    Filtered to certifications created by learners within the steward's tenant scope.
    Requires competence_level >= 3.
    """
    if not is_level_3_or_above(request.user):
        return Response(
            {"detail": "Certification queue requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Fetch draft certifications scoped to steward's tenant path
    # The steward's tenant_path comes from their active UserPermission row
    steward_tenant_path = request.user.userprofile.active_tenant_path  # adjust to your model

    certifications = Record.objects.filter(
        record_type='certification',
        status='draft',
        tenant__path__startswith=steward_tenant_path  # adjust to your tenant FK structure
    ).order_by('created_at')

    # Use existing RecordSerializer from records app
    from records.serializers import RecordSerializer
    serializer = RecordSerializer(certifications, many=True)
    return Response(serializer.data)
```

Add to `learn/urls.py`:

```python
path('certifications/queue/', views.certification_queue, name='certification-queue'),
```

Commit: `git add . && git commit -m "feat: certification queue endpoint for stewards"`

---

## Phase B — Content Engine (Read-Only)

**Exit criteria:** Published programmes, courses, lessons are retrievable via DRF. Django learn views call the ORM directly (not via a JS service layer). Competence gating works server-side.

### Task B.1 — Verify Records engine serves learning content

The Records engine (`GET /api/records/`) already exists from Phase 2 of the main roadmap. This task confirms the filtering params needed by the Learn App work correctly.

**Required queries — verify each returns correct results:**

```bash
# All published programmes
GET /api/records/?record_family=learning&record_type=programme&status=active

# Programmes visible to a specific learner level
GET /api/records/?record_family=learning&record_type=programme&status=active&required_level_lte=2

# Courses in a programme (via relationship traversal — see Task B.2)
GET /api/records/?record_family=learning&record_type=course&status=active

# Submitted content (Level 5 review queue)
GET /api/records/?record_family=learning&status=submitted

# Lessons in a course
GET /api/records/?record_family=learning&record_type=lesson&status=active
```

If the Records DRF view does not support `required_level_lte` filtering, add it:

```python
# records/views.py — add to filter_queryset or filterset_fields
required_level_lte = request.query_params.get('required_level_lte')
if required_level_lte:
    queryset = queryset.filter(permissions__required_level__lte=required_level_lte)
```

Commit: `git add . && git commit -m "feat: records endpoint — required_level_lte filter for learn app"`

---

### Task B.2 — Curriculum endpoint (course list for a programme)

The curriculum is the set of `part_of` Relationships from courses to a programme.
Rather than forcing the JS client to traverse relationships manually, expose a
dedicated curriculum endpoint.

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programme_curriculum(request, programme_id):
    """
    Returns the ordered list of courses (and their lessons) for a programme.
    Traverses part_of Relationships: course → part_of → programme.
    Then for each course: lesson → part_of → course.
    """
    from records.models import Record, Relationship

    programme = get_object_or_404(
        Record,
        id=programme_id,
        record_family='learning',
        record_type='programme',
        status__in=['active', 'locked']
    )

    # Check learner competence gate
    required_level = programme.permissions.get('required_level', 1)
    user_level = request.user.userprofile.competence_level
    if user_level < required_level:
        return Response(
            {"detail": "Insufficient competence level to access this programme."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get all courses part_of this programme
    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids,
        record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id,
            relationship_type='part_of'
        ).values_list('from_record_id', flat=True)

        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked']
        ).order_by('created_at')

        from records.serializers import RecordSerializer
        curriculum.append({
            'course': RecordSerializer(course).data,
            'lessons': RecordSerializer(lessons, many=True).data
        })

    return Response({
        'programme': RecordSerializer(programme).data,
        'curriculum': curriculum
    })
```

Add to `learn/urls.py`:

```python
path('programmes/<uuid:programme_id>/curriculum/', views.programme_curriculum, name='programme-curriculum'),
```

Commit: `git add . && git commit -m "feat: curriculum endpoint — traverses part_of relationships"`

---

### Task B.3 — Django learn views + URL routing

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`
- Create: `~/ics/learn/templates/learn/` (template directory)

The Learn App UI is served by Django views that query the ORM directly and
pass context to templates. HTMX handles partial updates. No JS service layer.

**URL structure:**

```python
# learn/urls.py
from django.urls import path
from . import views, api_views

urlpatterns = [
    # API endpoints (DRF — consumed by HTMX and future mobile clients)
    path('health/', api_views.health, name='learn-health'),
    path('programmes/<uuid:programme_id>/curriculum/', api_views.programme_curriculum, name='programme-curriculum'),
    path('certifications/queue/', api_views.certification_queue, name='certification-queue'),
    path('certifications/<uuid:certification_id>/confirm/', api_views.confirm_certification, name='certification-confirm'),

    # Django template views (UI)
    path('', views.my_learning, name='learn-home'),
    path('programmes/', views.catalogue, name='learn-catalogue'),
    path('programmes/<uuid:programme_id>/', views.programme_detail, name='learn-programme'),
    path('lessons/<uuid:lesson_id>/', views.lesson_viewer, name='learn-lesson'),
    path('certifications/', views.certification_queue_view, name='learn-cert-queue'),
    path('author/', views.authorship, name='learn-author'),
    path('review/', views.review_queue, name='learn-review'),

    # HTMX partial endpoints (return HTML fragments, not full pages)
    path('htmx/enrol/<uuid:programme_id>/', views.htmx_enrol, name='htmx-enrol'),
    path('htmx/complete-lesson/<uuid:lesson_id>/', views.htmx_complete_lesson, name='htmx-complete-lesson'),
    path('htmx/confirm-cert/<uuid:cert_id>/', views.htmx_confirm_cert, name='htmx-confirm-cert'),
    path('htmx/approve-content/<uuid:record_id>/', views.htmx_approve_content, name='htmx-approve-content'),
]
```

**Rename existing DRF views file for clarity:**
- Rename: `learn/views.py` → `learn/api_views.py` (holds all DRF `@api_view` functions)
- Create: `learn/views.py` (holds all Django template views)

This keeps the API layer and the template layer cleanly separated in the same app.

Commit: `git add . && git commit -m "feat: learn app — Django URL structure, views/api_views split"`

---

## Phase C — Enrolment + Progress Tracking (UI)

**Exit criteria:** A learner can browse programmes, enrol, view their curriculum, mark lessons complete, and see progress bars update — all via Django templates and HTMX. No JS app file required.

### Task C.1 — Django template views (My Learning + Catalogue)

**Files:**
- Create: `~/ics/learn/views.py`
- Create: `~/ics/learn/templates/learn/base_learn.html`
- Create: `~/ics/learn/templates/learn/my_learning.html`
- Create: `~/ics/learn/templates/learn/catalogue.html`
- Create: `~/ics/learn/templates/learn/programme_detail.html`

**`learn/views.py` — core template views:**

```python
# learn/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from records.models import Record, Relationship
from activity.models import Activity


@login_required
def my_learning(request):
    """My Learning home — active enrolments and completed certifications."""
    user = request.user
    enrolments = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        status='in_progress',
        metadata__source_app='learn'
    ).order_by('-created_at')

    certifications = Record.objects.filter(
        record_type='certification',
        created_by=user,
        status='active'
    ).order_by('-updated_at')

    return render(request, 'learn/my_learning.html', {
        'enrolments': enrolments,
        'certifications': certifications,
    })


@login_required
def catalogue(request):
    """Programme catalogue — filtered by user competence level."""
    user_level = request.user.userprofile.competence_level
    programmes = Record.objects.filter(
        record_family='learning',
        record_type='programme',
        status='active'
    ).order_by('created_at')

    # Annotate each programme with locked status for the template
    for p in programmes:
        p.is_locked = user_level < (p.permissions.get('required_level', 1))

    return render(request, 'learn/catalogue.html', {
        'programmes': programmes,
        'user_level': user_level,
    })


@login_required
def programme_detail(request, programme_id):
    """Programme detail with curriculum and enrolment status."""
    user = request.user
    user_level = user.userprofile.competence_level

    programme = get_object_or_404(
        Record, id=programme_id,
        record_family='learning', record_type='programme',
        status__in=['active', 'locked']
    )

    required_level = programme.permissions.get('required_level', 1)
    if user_level < required_level:
        return render(request, 'learn/locked.html', {'programme': programme})

    # Build curriculum via part_of relationships
    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids, record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id, relationship_type='part_of'
        ).values_list('from_record_id', flat=True)
        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked']
        ).order_by('created_at')
        curriculum.append({'course': course, 'lessons': lessons})

    already_enrolled = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        metadata__programme_record_id=str(programme_id)
    ).exists()

    return render(request, 'learn/programme_detail.html', {
        'programme': programme,
        'curriculum': curriculum,
        'already_enrolled': already_enrolled,
    })


@login_required
def lesson_viewer(request, lesson_id):
    """Lesson viewer — renders lesson content with prev/next navigation."""
    lesson = get_object_or_404(
        Record, id=lesson_id,
        record_type__in=['lesson', 'assignment', 'quiz'],
        status__in=['active', 'locked']
    )

    # Find parent course via part_of relationship
    parent_rel = Relationship.objects.filter(
        from_record_id=lesson_id, relationship_type='part_of'
    ).first()
    course = None
    siblings = []
    if parent_rel:
        course = Record.objects.filter(id=parent_rel.to_record_id).first()
        if course:
            sibling_ids = Relationship.objects.filter(
                to_record_id=course.id, relationship_type='part_of'
            ).values_list('from_record_id', flat=True)
            siblings = list(Record.objects.filter(
                id__in=sibling_ids, status__in=['active', 'locked']
            ).order_by('created_at'))

    current_index = next((i for i, s in enumerate(siblings) if s.id == lesson.id), 0)
    prev_lesson = siblings[current_index - 1] if current_index > 0 else None
    next_lesson = siblings[current_index + 1] if current_index < len(siblings) - 1 else None

    return render(request, 'learn/lesson_viewer.html', {
        'lesson': lesson,
        'course': course,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    })
```

Commit: `git add . && git commit -m "feat: learn views — my_learning, catalogue, programme_detail, lesson_viewer"`

---

### Task C.2 — Base learn template + CSS

**Files:**
- Create: `~/ics/learn/templates/learn/base_learn.html`
- Create: `~/ics/frontend/assets/css/learn.css`

**`base_learn.html`** — extends the platform base template, adds HTMX and learn-specific structure:

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/learn.css' %}">
{% endblock %}

{% block extra_scripts %}
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
{% endblock %}
```

**`learn.css`** — identical to the original design. No changes to the design system. All CSS variables, mobile-first breakpoints, programme cards, progress bars, lesson viewer styles, and certification styles carry forward unchanged.

Commit: `git add . && git commit -m "feat: learn base template + learn.css"`

---

### Task C.3 — My Learning template

**Files:**
- Create: `~/ics/learn/templates/learn/my_learning.html`

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="learn-header">
  <h1>Learn</h1>
  <a href="{% url 'learn-catalogue' %}" class="btn-secondary">Browse Programmes</a>
</div>

{% if enrolments %}
  {% for enrolment in enrolments %}
  <div class="enrolment-card">
    <div class="enrolment-title">{{ enrolment.title }}</div>
    <div class="progress-bar-wrap">
      <div class="progress-bar" style="width:{{ enrolment.progress }}%"></div>
    </div>
    <span class="progress-label">{{ enrolment.progress }}% complete</span>
    <a href="{% url 'learn-programme' enrolment.metadata.programme_record_id %}"
       class="btn-primary">Continue</a>
  </div>
  {% endfor %}
{% else %}
  <div class="empty-state">
    <p>You are not enrolled in any programme yet.</p>
    <a href="{% url 'learn-catalogue' %}" class="btn-primary">Browse Programmes</a>
  </div>
{% endif %}

{% if certifications %}
  <h2>Completed</h2>
  {% for cert in certifications %}
  <div class="enrolment-card">
    <div class="enrolment-title">{{ cert.title }}</div>
    <span class="enrolled-badge">Certified</span>
  </div>
  {% endfor %}
{% endif %}
{% endblock %}
```

Commit: `git add . && git commit -m "feat: my_learning.html template"`

---

### Task C.4 — Catalogue + Programme detail templates

**Files:**
- Create: `~/ics/learn/templates/learn/catalogue.html`
- Create: `~/ics/learn/templates/learn/programme_detail.html`
- Create: `~/ics/learn/templates/learn/locked.html`

**`catalogue.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="learn-header">
  <a href="{% url 'learn-home' %}" class="btn-back">← My Learning</a>
  <h2>Programmes</h2>
</div>

<div class="programme-grid">
  {% for programme in programmes %}
  <div class="programme-card {% if programme.is_locked %}locked{% endif %}">
    <div class="programme-badge">
      {{ programme.metadata.qualification|default:"Programme" }}
    </div>
    <h3 class="programme-title">{{ programme.title }}</h3>
    <p class="programme-meta">
      {{ programme.metadata.duration_years|default:"?" }} year{{ programme.metadata.duration_years|pluralize }}
    </p>
    {% if programme.is_locked %}
      <span class="lock-indicator">
        Level {{ programme.permissions.required_level }} required
      </span>
    {% else %}
      <a href="{% url 'learn-programme' programme.id %}" class="btn-primary">View</a>
    {% endif %}
  </div>
  {% endfor %}
</div>
{% endblock %}
```

**`programme_detail.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="programme-detail">
  <a href="{% url 'learn-catalogue' %}" class="btn-back">← Programmes</a>
  <div class="programme-badge">{{ programme.metadata.qualification|default:"Programme" }}</div>
  <h2>{{ programme.title }}</h2>
  <p class="programme-description">{{ programme.content|default:programme.summary }}</p>
  <div class="programme-meta-row">
    <span>{{ programme.metadata.duration_years|default:"?" }} years</span>
    <span>Level {{ programme.permissions.required_level|default:1 }}</span>
  </div>

  {% if already_enrolled %}
    <span class="enrolled-badge">Enrolled</span>
  {% else %}
    <!-- HTMX enrolment — swaps button with confirmation in-place -->
    <button class="btn-primary enrol-btn"
            hx-post="{% url 'htmx-enrol' programme.id %}"
            hx-target="#enrol-section"
            hx-swap="outerHTML">
      Enrol in this Programme
    </button>
    <div id="enrol-section"></div>
  {% endif %}

  <div class="curriculum-list">
    <h3>Curriculum</h3>
    {% for item in curriculum %}
    <div class="course-block">
      <h4>{{ forloop.counter }}. {{ item.course.title }}</h4>
      <ul class="lesson-list">
        {% for lesson in item.lessons %}
        <li class="lesson-item">
          <span class="lesson-type-tag">{{ lesson.record_type }}</span>
          <a href="{% url 'learn-lesson' lesson.id %}">{{ lesson.title }}</a>
        </li>
        {% endfor %}
      </ul>
    </div>
    {% endfor %}
  </div>
</div>
{% endblock %}
```

Commit: `git add . && git commit -m "feat: catalogue.html + programme_detail.html templates"`

---

### Task C.5 — Lesson viewer template + HTMX complete button

**Files:**
- Create: `~/ics/learn/templates/learn/lesson_viewer.html`
- Create: `~/ics/learn/templates/learn/partials/lesson_complete_btn.html`
- Add HTMX view to `learn/views.py`

**`lesson_viewer.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="lesson-viewer">
  {% if course %}
    <a href="{% url 'learn-programme' course.id %}" class="btn-back">← Back to Course</a>
  {% endif %}
  <span class="lesson-type-tag">{{ lesson.record_type }}</span>
  <h2 class="lesson-title">{{ lesson.title }}</h2>

  <div class="lesson-content">
    {{ lesson.content|linebreaks }}
  </div>

  <div class="lesson-nav">
    {% if prev_lesson %}
      <a href="{% url 'learn-lesson' prev_lesson.id %}" class="btn-secondary">← Previous</a>
    {% else %}
      <span></span>
    {% endif %}

    <!-- HTMX complete button — replaces itself with a ✓ confirmation -->
    <div id="complete-section">
      {% include "learn/partials/lesson_complete_btn.html" %}
    </div>

    {% if next_lesson %}
      <a href="{% url 'learn-lesson' next_lesson.id %}" class="btn-secondary">Next →</a>
    {% else %}
      <span></span>
    {% endif %}
  </div>
</div>
{% endblock %}
```

**`partials/lesson_complete_btn.html`:**

```html
<button class="btn-primary complete-btn"
        hx-post="{% url 'htmx-complete-lesson' lesson.id %}"
        hx-target="#complete-section"
        hx-swap="outerHTML">
  Mark Complete
</button>
```

**HTMX views — add to `learn/views.py`:**

```python
@login_required
def htmx_enrol(request, programme_id):
    """HTMX: creates enrolment Activity, returns confirmation fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    user = request.user
    programme = get_object_or_404(Record, id=programme_id, record_type='programme')

    Activity.objects.create(
        activity_type='programme',
        title=f'Enrolment — {programme.title}',
        assigned_to=user,
        status='in_progress',
        progress=0,
        kgs_pathway='learning',
        metadata={
            'source_app': 'learn',
            'programme_record_id': str(programme_id)
        }
    )

    # Return a small HTML fragment — HTMX swaps it in place of the button
    return HttpResponse('<span class="enrolled-badge">Enrolled ✓</span>')


@login_required
def htmx_complete_lesson(request, lesson_id):
    """HTMX: marks lesson Activity complete, returns updated button fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    Activity.objects.filter(
        metadata__lesson_record_id=str(lesson_id),
        assigned_to=request.user
    ).update(status='completed', progress=100)

    # Return completed state fragment
    return HttpResponse(
        '<button class="btn-primary complete-btn completed" disabled>✓ Completed</button>'
    )
```

Commit: `git add . && git commit -m "feat: lesson_viewer.html + HTMX complete lesson + enrol views"`

---

## Phase D — Assessments

**Exit criteria:** Quiz and Assignment records render correctly in the lesson viewer. Submission marks the assessment activity complete via HTMX.

### Task D.1 — Quiz template + HTMX submission

Quiz questions live in `Record.custom_fields`. The lesson viewer template detects
`lesson.record_type == 'quiz'` and renders a form. Submission is an HTMX POST.

**Files:**
- Create: `~/ics/learn/templates/learn/partials/quiz.html`
- Add HTMX quiz submit view to `learn/views.py`

**`partials/quiz.html`:**

```html
<form hx-post="{% url 'htmx-submit-quiz' lesson.id %}"
      hx-target="#complete-section"
      hx-swap="outerHTML">
  {% csrf_token %}
  {% for q in lesson.custom_fields.questions %}
  <div class="quiz-question">
    <p>{{ q.text }}</p>
    {% if q.type == 'multiple_choice' %}
      {% for option in q.options %}
      <label class="quiz-option">
        <input type="radio" name="q_{{ q.id }}" value="{{ forloop.counter0 }}">
        {{ option }}
      </label>
      {% endfor %}
    {% else %}
      <textarea name="q_{{ q.id }}" class="quiz-text-answer" rows="3"></textarea>
    {% endif %}
  </div>
  {% endfor %}
  <button type="submit" class="btn-primary">Submit Quiz</button>
</form>
```

Add `htmx-submit-quiz` view to `learn/views.py` — marks assessment Activity
as completed and returns the completed state fragment.

### Task D.2 — Assignment submission template

Same HTMX pattern. Assignment form submits text via POST. The view creates a
child Record (`record_type: "note"`) linked to the assignment via a `references`
Relationship, then marks the task Activity complete.

Commit: `git add . && git commit -m "feat: learn app — quiz + assignment templates with HTMX submission"`

---

## Phase E — Certification + Competence Advancement (UI)

**Exit criteria:** Learner sees "Awaiting certification" when programme is 100% complete. Steward sees certification queue as a Django-rendered page. Steward confirms via HTMX. Learner's competence level advances.

### Task E.1 — Awaiting certification view

The Django signal (Task E.1 backend — unchanged) auto-creates the draft
Certification Record. The learner's My Learning page detects a draft certification
linked to their completed enrolment and shows an "Awaiting certification" banner.

Add to `my_learning.html`:

```html
{% if pending_certifications %}
  {% for cert in pending_certifications %}
  <div class="enrolment-card awaiting-cert">
    <div class="enrolment-title">{{ cert.title }}</div>
    <span class="cert-pending-badge">Awaiting Steward Confirmation</span>
  </div>
  {% endfor %}
{% endif %}
```

Update `my_learning` view to pass `pending_certifications` (draft certification
Records created by the current user).

### Task E.2 — Steward certification queue template + HTMX confirm

**Files:**
- Create: `~/ics/learn/templates/learn/certification_queue.html`
- Add `htmx_confirm_cert` view to `learn/views.py`

**`certification_queue.html`:**

```html
{% extends "learn/base_learn.html" %}
{% block content %}
<div class="learn-header"><h2>Certifications Pending</h2></div>

{% if certifications %}
  {% for cert in certifications %}
  <div class="cert-card" id="cert-{{ cert.id }}">
    <h4>{{ cert.title }}</h4>
    <p class="cert-meta">Submitted: {{ cert.created_at|date:"d M Y" }}</p>
    <textarea name="notes" placeholder="Notes (optional)"
              id="notes-{{ cert.id }}"></textarea>
    <button class="btn-primary"
            hx-post="{% url 'htmx-confirm-cert' cert.id %}"
            hx-target="#cert-{{ cert.id }}"
            hx-swap="outerHTML"
            hx-include="#notes-{{ cert.id }}">
      Confirm &amp; Advance Level
    </button>
  </div>
  {% endfor %}
{% else %}
  <p class="empty-state">No certifications pending.</p>
{% endif %}
{% endblock %}
```

**`htmx_confirm_cert` view** calls the existing `confirm_certification` logic
from `api_views.py` and returns a small HTML fragment confirming the action:

```python
@login_required
def htmx_confirm_cert(request, cert_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    # Reuse confirm_certification logic (extracted to a service function)
    # Returns fragment replacing the cert card with a confirmed state
    return HttpResponse(
        f'<div class="cert-card confirmed">'
        f'<span class="enrolled-badge">✓ Certification Confirmed</span>'
        f'</div>'
    )
```

Commit: `git add . && git commit -m "feat: learn app — certification queue template + HTMX confirm"`

---

## Phase F — Content Authorship + Handbook Review (UI)

**Exit criteria:** Level 4+ users can create and submit Programmes, Courses, and Lessons via Django forms. Level 5 users see a review queue and can approve content via HTMX.

### Task F.1 — Authorship views + templates (Level 4+)

**Files:**
- Create: `~/ics/learn/templates/learn/authorship.html`
- Create: `~/ics/learn/templates/learn/author_programme_form.html`
- Create: `~/ics/learn/templates/learn/author_course_form.html`
- Create: `~/ics/learn/templates/learn/author_lesson_form.html`
- Add authorship views to `learn/views.py`

Django `CreateView` or function-based views gated to `competence_level >= 4`.
Each form creates a Record with the appropriate `record_family`, `record_type`,
and `status: "draft"`. A "Submit for Review" button PATCHes the record status
to `"submitted"` — this can be a standard Django form POST (no HTMX needed here
as it's a full-page action).

Core form fields per content type are unchanged from the original design spec
(Programme: title, qualification, description, duration, pathways; Course: title,
description, parent programme; Lesson: title, content textarea, type, parent course).

### Task F.2 — Handbook review queue template + HTMX approve (Level 5)

**Files:**
- Create: `~/ics/learn/templates/learn/review_queue.html`
- Add `htmx_approve_content` view to `learn/views.py`

**`review_queue.html`:**

```html
{% extends "learn/base_learn.html" %}
{% block content %}
<div class="learn-header"><h2>Review Queue</h2></div>

{% if items %}
  {% for item in items %}
  <div class="review-card" id="review-{{ item.id }}">
    <span class="lesson-type-tag">{{ item.record_type }}</span>
    <h4>{{ item.title }}</h4>
    <p class="cert-meta">Submitted: {{ item.updated_at|date:"d M Y" }}</p>
    <div class="review-actions">
      <button class="btn-primary"
              hx-post="{% url 'htmx-approve-content' item.id %}"
              hx-target="#review-{{ item.id }}"
              hx-swap="outerHTML">
        Approve
      </button>
      <button class="btn-secondary"
              hx-post="{% url 'htmx-return-content' item.id %}"
              hx-target="#review-{{ item.id }}"
              hx-swap="outerHTML">
        Return to Draft
      </button>
    </div>
  </div>
  {% endfor %}
{% else %}
  <p class="empty-state">No items pending review.</p>
{% endif %}
{% endblock %}
```

`htmx_approve_content` view sets `record.status = 'active'`, gated to Level 5.
Returns a small confirmation fragment replacing the review card.

Commit: `git add . && git commit -m "feat: learn app — authorship forms + handbook review queue templates"`

---

## Phase G — UI Polish + Role-Aware Navigation

**Exit criteria:** Learn App navigation adapts to user role server-side. Pathway banner shows for enrolled learners. Smoke test on mobile passes.

### Task G.1 — Role-aware navigation (server-side)

Role-aware tabs are rendered in `base_learn.html` using the Django request context.
No JS required — the template checks `request.user.userprofile.competence_level`
and shows the appropriate navigation items:

```html
<!-- In base_learn.html nav section -->
<nav class="learn-tab-row">
  <a href="{% url 'learn-home' %}">My Learning</a>
  <a href="{% url 'learn-catalogue' %}">Browse</a>
  {% if request.user.userprofile.competence_level >= 3 %}
    <a href="{% url 'learn-cert-queue' %}">Certifications</a>
  {% endif %}
  {% if request.user.userprofile.competence_level >= 4 %}
    <a href="{% url 'learn-author' %}">Author</a>
  {% endif %}
  {% if request.user.userprofile.competence_level >= 5 %}
    <a href="{% url 'learn-review' %}">Review Queue</a>
  {% endif %}
</nav>
```

| Level | Visible tabs |
|---|---|
| 0b (Seeker) | Browse only |
| 1–2 (Member/Disciple) | My Learning, Browse |
| 3 (Branch-Steward) | My Learning, Browse, Certifications |
| 4 (Senior Steward) | My Learning, Browse, Certifications, Author |
| 5 (Architect) | All above + Review Queue |

### Task G.2 — Pathway banner

Add to `my_learning.html` above the enrolment list, populated from the active
enrolment Activity's `kgs_pathway` and the linked Programme Record's metadata:

```html
{% if active_pathway %}
<div class="pathway-banner">
  <span class="pathway-label">{{ active_pathway }}</span>
  <span class="pathway-programme">{{ active_qualification }} · Year {{ active_year }}</span>
</div>
{% endif %}
```

The `my_learning` view resolves these values from the user's active enrolment
Activity before passing them to the template as context.

### Task G.3 — Smoke test checklist

Before closing Phase G, verify manually on mobile:

- [ ] Seeker can browse programmes, sees lock on locked programmes
- [ ] Member can enrol, see progress bar, mark a lesson complete
- [ ] Progress bar updates after lesson completion (HTMX swap visible)
- [ ] Programme at 100% shows "Awaiting certification" state on My Learning page
- [ ] Branch-Steward sees certification queue with pending item
- [ ] Steward confirms via HTMX → learner's competence level increments in DB
- [ ] Level 4 user can create a Programme and submit for review
- [ ] Level 5 user sees submitted Programme in review queue and can approve
- [ ] Approved Programme appears in public catalogue
- [ ] Role-aware nav tabs show/hide correctly for each level
- [ ] Pathway banner displays for enrolled learner

Commit: `git add . && git commit -m "feat: learn app — role-aware nav, pathway banner, smoke test pass"`

---

## Django Endpoint Summary

All endpoints required by the Learn App, in one place:

```
# Existing Records endpoints (already built — verify filters work)
GET  /api/records/?record_family=learning&record_type=programme&status=active
GET  /api/records/?record_family=learning&status=submitted
GET  /api/records/{id}/
PATCH /api/records/{id}/     (status changes — gated by role)

# Existing Activity endpoints (already built)
POST  /api/activities/
PATCH /api/activities/{id}/
GET   /api/activities/?activity_type=programme&assigned_to={id}

# New Learn endpoints (built in Phase A)
GET   /api/learn/health/
GET   /api/learn/programmes/{id}/curriculum/
GET   /api/learn/certifications/queue/
POST  /api/learn/certifications/{id}/confirm/
```

---

## File Map (Learn App additions)

```
/learn/                              ← NEW Django app
  __init__.py
  apps.py
  models.py                          ← CertificationConfirmation only
  serializers.py
  api_views.py                       ← DRF endpoints (health, curriculum, cert queue, cert confirm)
  views.py                           ← Django template views + HTMX partial views
  urls.py                            ← API routes + template view routes + HTMX routes
  signals.py                         ← auto-create certification on programme complete
  templates/
    learn/
      base_learn.html                ← extends base.html, loads HTMX, learn.css
      my_learning.html               ← My Learning home
      catalogue.html                 ← Programme catalogue
      programme_detail.html          ← Programme detail + curriculum
      lesson_viewer.html             ← Lesson content + nav
      certification_queue.html       ← Steward cert queue
      authorship.html                ← Level 4 authorship home
      author_programme_form.html     ← Create programme form
      author_course_form.html        ← Create course form
      author_lesson_form.html        ← Create lesson form
      review_queue.html              ← Level 5 Handbook review queue
      locked.html                    ← Competence gate placeholder
      partials/
        lesson_complete_btn.html     ← HTMX complete button fragment
        quiz.html                    ← Quiz form fragment

/activity/
  signals.py                         ← MODIFIED: add programme completion handler

/accounts/serializers.py             ← MODIFIED: competence_level read-only note

/frontend/assets/css/
  learn.css                          ← NEW — unchanged from original design spec
```

**Note:** `learn.html`, `learn-app.js`, and `learn.service.js` are **not created**.
The UI is fully served by Django views and templates. HTMX replaces the JS
interaction layer. `storage.js` is retained for theme/UI state only.

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|---|---|---|---|
| A | Django `learn` app, `CertificationConfirmation` model, DRF endpoints | Phases 0–4 done | `/api/learn/health/` 200. Confirm endpoint works. |
| B | Records endpoint filters verified, curriculum endpoint, URL structure, views/api_views split | Phase A done | All DRF queries return correct data. URL routing confirmed. |
| C | Django template views, base template, My Learning, Catalogue, Programme detail, Lesson viewer, `learn.css` | Phase B done | Learner can enrol (HTMX) and mark lessons complete (HTMX) |
| D | Quiz template + HTMX submission, Assignment submission template | Phase C done | Assessments render and submit via HTMX |
| E | Certification auto-creation signal, steward queue template, HTMX confirm | Phase D done | Steward confirms via HTMX; `competence_level` increments in DB |
| F | Authorship forms (Level 4+), Handbook review queue template, HTMX approve (Level 5) | Phase E done | Content can be authored, submitted, approved |
| G | Role-aware nav (server-side), pathway banner, mobile smoke test | Phase F done | Full smoke test checklist passes on mobile |

---

## Deferred (Post-MVP)

- Rich text editor (TipTap or similar) for lesson authorship — markdown textarea suffices for MVP
- Quiz auto-grading with score display
- Assignment peer review
- Paraclete "continue your lesson" integration (Phase 6 of main roadmap)
- Learning analytics dashboard (completion rates per programme)
- Offline lesson caching (service worker)
- Video lessons (`record_type: "video_lesson"` — deferred with Video/Live app)
- Programme ordering / sequencing UI (drag-and-drop curriculum builder)


---


# ICS Bible App — System Design & Build Roadmap

> **Version:** v2 — 2026-04-08
> **Previous version:** v1 — 2026-04-08
>
> **v2 Amendments (source data structure confirmed):**
> 1. `BibleTranslation` model expanded — five fields added from `metadata` object:
>    `language_full`, `year`, `description`, `copyright_statement`, `is_copyright`.
>    `is_public` mapping clarified: derived from `metadata.restrict == 0`.
> 2. Task A.2 (management command) fully rewritten — source JSON is a flat
>    `metadata` + `verses` structure, not nested books → chapters → verses.
>    Command now parses flat `verses` array. `TESTAMENT_MAP` and `BOOK_CODE_MAP`
>    hardcoded (JSON does not carry testament or short book code).
>    Load is idempotent. Bulk insert in batches of 1000.
>    `--file` argument added for specifying alternate file path.
> 3. Part 0.1 `BibleTranslation` schema updated to match expanded model.
> 4. Phase summary verse count note updated: ~31,102 per translation (WEB confirmed).
>    Total at setup ~93,306 rows (3 translations). Exact counts vary by translation.
> 5. Data files note updated: all three translations share identical flat JSON structure.
>    Single command handles all three without modification.
>
> **Everything else in v1 is unchanged.**
>
> **Status:** LOCKED
> **UI Architecture:** Django templates + HTMX (per HTMX ADR — 2026-04-07)
> **Data Contract reference:** `2026-04-08-ics-platform-data-contract_v7.md`
> **Format standard:** Matches `2026-04-07-ics-learn-app-system-design_v2.md`

**Goal:** Build the ICS Bible App — the scripture reading and personal formation layer of
the platform — enabling members to read scripture, write personal and community annotations,
connect governance records to their scriptural basis, and surface Learn App lesson
cross-references in context. The Bible App is the primary digital expression of the
**Spiritual Formation Pathway** (Prayer, Word, and spiritual disciplines) within the KGS.

**Architecture:** Django `bible` app with its own models (`BibleTranslation`, `BibleBook`,
`BibleVerse`) loaded at setup via management commands. Annotations and notes are
`Record` objects (`record_family: "bible"`) stored in the standard records table.
Handbook linkages use a `data contract amendment` to `Relationship` allowing
`bible_verse_id` as an alternative target. UI rendered via Django templates + HTMX.
No `bible-app.js` or `bible.service.js` are built. `bible.css` carries forward from
prior design work, amended as needed.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX,
`bible.css` (mobile-first, existing CSS variables).

---

## Data Contract Amendment Required (Part 0)

> **This amendment must be applied to the data contract before Phase A begins.**
> The system design depends on it. Do not build until it is incorporated into v6.

### 0.1 New Bible models (not Record objects)

The Bible App introduces three new Django models that sit outside the Records Engine.
They are not `Record` objects — making `BibleVerse` a Record would pollute the records
table with ~95,000 rows per translation (31,000 verses × 3 translations at setup).
These models are read-only after loading.

```python
BibleTranslation = {
  id:                  "uuid",
  code:                "string",          # 'KJV', 'ASV', 'WEB' ← metadata.shortname
  name:                "string",          # 'World English Bible' ← metadata.name
  language:            "string",          # 'en' ← metadata.lang_short
  language_full:       "string",          # 'English' ← metadata.lang
  year:                "string | null",   # '2006' ← metadata.year
  description:         "text | null",     # HTML string ← metadata.description
  copyright_statement: "text | null",     # 'This Bible is in the Public Domain.' ← metadata.copyright_statement
  is_copyright:        "boolean",         # False = public domain ← metadata.copyright == 0
  is_public:           "boolean",         # True = unrestricted ← metadata.restrict == 0
  is_default:          "boolean",         # exactly one row is True — KJV at setup
  created_at:          "ISO-8601"
}

BibleBook = {
  id:        "integer",           # auto PK
  code:      "string",            # 'GEN', 'MAT', 'REV' — canonical, translation-independent
  name:      "string",            # 'Genesis', 'Matthew'
  testament: "OT | NT",
  order:     "integer"            # canonical book order 1–66
}

BibleVerse = {
  id:          "uuid",
  translation: "FK → BibleTranslation",
  book:        "FK → BibleBook",
  chapter:     "integer",
  verse:       "integer",
  text:        "string"
  # unique_together: (translation, book, chapter, verse)
}
```

### 0.2 `Relationship` schema amendment

The `Relationship` object gains one optional FK field to allow governance records
(and any Record) to reference a specific Bible verse directly:

```js
Relationship = {
  // ... all existing fields unchanged ...

  // NEW — Bible verse target (alternative to to_record_id)
  // Exactly one of to_record_id or bible_verse_id must be set.
  // When bible_verse_id is set, to_record_id is null, and vice versa.
  bible_verse_id: "uuid | null",    // FK → bible.BibleVerse

  // Amended constraint (was: to_record_id required):
  // to_record_id: "uuid | null"    — null when bible_verse_id is set
}
```

**When used:** A Handbook governance record (principle, mandate, divine_pattern,
narrative, framework) may reference the specific `BibleVerse` row(s) from which it
derives its authority. The `relationship_type` is `"references"`, direction
`"directed"` (governance_record → verse).

**Enforcement:** The service layer must validate that at least one of `to_record_id`
or `bible_verse_id` is non-null on every Relationship row. Both null is invalid.
Both non-null is invalid.

### 0.3 `UserProfile` amendment

`UserProfile` gains a preferred translation field:

```python
preferred_bible_translation = models.ForeignKey(
    'bible.BibleTranslation',
    null=True, blank=True,
    on_delete=models.SET_NULL,
    related_name='preferred_by_users'
)
# null = use system default (BibleTranslation.is_default=True)
```

### 0.4 `Record.custom_fields` convention for Learn App cross-references

Lesson Records (`record_family: "learning"`, `record_type: "lesson"`) MAY carry
a `scripture_reference` key in `custom_fields`:

```js
custom_fields: {
  scripture_reference: "GEN 1:1"   // format: "{BOOK_CODE} {chapter}:{verse}"
  // or range: "ROM 8:1-4"         // format: "{BOOK_CODE} {chapter}:{start}-{end}"
}
```

This is a convention enforced by the Learn App authorship form, not a DB constraint.
The Bible App queries `Record.objects.filter(custom_fields__scripture_reference__startswith="GEN 1")`.

---

## System Overview

### The Bible App Stack

```
Scripture Layer    BibleTranslation (KJV | ASV | WEB — loaded at setup)
                   ↓ contains
                   BibleBook × BibleVerse (read-only after load)
                   ↓ displayed by
                   Django template reader view (chapter by chapter)

Annotation Layer   Personal Note — Record (record_class:'personal',
                                           record_family:'bible',
                                           record_type:'bible_note')
                                   → visible to created_by only
                   Tenant Note   — Record (record_class:'organizational',
                                           record_family:'bible',
                                           record_type:'bible_note')
                                   → visible to all tenant members
                                   → Level 3+ to create

Governance Layer   Handbook Record (record_class:'governance')
                   → Relationship (references, directed)
                   → BibleVerse (via bible_verse_id FK — Amendment 0.2)
                   → surfaced read-only in reader at Level 5 only

Cross-Reference    Lesson Record (record_family:'learning', record_type:'lesson')
Layer              → custom_fields.scripture_reference (string convention)
                   → surfaced in reader for all authenticated users
                   → link to lesson gated to enrolment
```

### User roles in the Bible App

| Role | What they can do |
|---|---|
| Seeker (Level 0b) | Read scripture. Create personal notes (10-record platform limit applies). No tenant notes visible. No Handbook references visible. |
| Member (Level 1+) | Read scripture. Full personal notes (no limit). See tenant notes for their branch. See Learn cross-references. |
| Disciple (Level 2+) | All above. |
| Branch-Steward (Level 3+) | All above. Publish tenant notes visible to branch members. |
| Senior Steward (Level 4+) | All above. |
| Architect (Level 5) | All above. See Handbook governance records linked to verses. |

---

## Feature List (All Features — Unphased)

### F1 — Scripture Reader
- Chapter-by-chapter reading view, all 66 books
- Book → Chapter navigation via slide-up navigator panel
- Previous / Next chapter navigation
- Reading position restored on return (stored in `localStorage` as UI state)
- Three translations available: KJV (default), ASV, WEB
- Inline translation switcher — HTMX swap of chapter content, updates `UserProfile.preferred_bible_translation`
- Whole app requires login (`@login_required` on all views)

### F2 — Personal Annotations (Bible Notes)
- Tap any verse to open annotation panel
- Create, edit, delete personal notes per verse
- Stored as `Record` (`record_class:'personal'`, `record_family:'bible'`, `record_type:'bible_note'`)
- Verse reference auto-populated from context (`custom_fields.book_code`, `custom_fields.chapter`, `custom_fields.verse`)
- Personal note indicator: blue dot on annotated verses
- Seeker 10-record limit enforced server-side before save

### F3 — Tenant Notes (Level 3+ publish)
- Branch-Steward (Level 3+) can publish a note on any verse to their tenant
- Stored as `Record` (`record_class:'organizational'`, `record_family:'bible'`, `record_type:'bible_note'`, `permissions.visibility:'tenant'`)
- Tenant notes pre-fetched at chapter level for all branch members
- Tenant note indicator: amber dot, visually distinct from personal notes
- In annotation panel: tenant note shown as read-only attributed block above personal note area
- Steward can edit or retract their own tenant note (status → archived)

### F4 — Learn App Cross-References
- For each verse, query active lesson Records with matching `custom_fields.scripture_reference`
- Surface as "Referenced in [Lesson Title] · [Course Name]" indicator in annotation panel
- Visible to all authenticated users
- Link to lesson detail gated to enrolment — non-enrolled users see lesson title + "Enrol to access"
- Fetched on verse tap (not pre-fetched at chapter level — low frequency, not worth the query cost)

### F5 — Handbook Scripture Linkages (Level 5 only)
- Governance records linked to a verse via `Relationship.bible_verse_id` surface in the annotation panel
- Shown as "Handbook references" section — read-only, attributed to record title
- Visible only when `request.user.userprofile.competence_level >= 5`
- Fetched on verse tap (same request as F4, different permission gate)
- Link navigates to Governance App record detail

### F6 — Translation Management (Setup + Admin)
- Three translations loaded at setup via management commands: KJV, ASV, WEB
- `BibleTranslation.is_default = True` set on KJV
- Django admin exposes `BibleTranslation` for future additions
- No UI for loading new translations — admin-only operation

---

## Deferred (Post-MVP)

- Reading plans (personal Activity-based schedule — defer until Activity App is mature)
- Verse highlights (colour-coded, no text — notes cover MVP use case)
- Scripture search (full-text `SearchVectorField` on `BibleVerse` — defer)
- Licensed translations (NIV, ESV, NLT — requires publisher licensing agreement)
- African language translations (Zulu, Xhosa, Afrikaans — same loading mechanism, content TBD)
- Paraclete integration ("You haven't read today" prompt based on habit Activity)
- Cross-reference chains (verse-to-verse canonical cross-references)
- Audio Bible (deferred with Video/Live app)
- Community sharing of notes (beyond tenant scope — deferred)

---

## Build Phases

### Phase A — Django `bible` App + Models + Data Load
*Entry requirement: Phases 0–2 of main roadmap complete (Django project live, Records Engine built, Relationship model live with `bible_verse_id` amendment applied).*

### Phase B — DRF Endpoints + Annotation CRUD
*Entry requirement: Phase A complete — BibleVerse rows exist in DB.*

### Phase C — Django Template Views + Reader UI
*Entry requirement: Phase B complete.*

### Phase D — Tenant Notes + Learn Cross-References
*Entry requirement: Phase C complete — reader is live and personal notes work.*

### Phase E — Handbook Linkages (Level 5)
*Entry requirement: Phase D complete. Governance App models must exist (Relationship rows with `bible_verse_id` must be creatable — even if Governance App UI is not complete, the data must be writable).*

### Phase F — Translation Switcher + UI Polish
*Entry requirement: Phase E complete.*

---

## Phase A — Django `bible` App + Models + Data Load

**Exit criteria:** `GET /api/bible/health/` returns `{"status": "ok"}`. `BibleVerse` rows
exist in DB for KJV, ASV, WEB. `BibleTranslation.objects.get(is_default=True)` returns KJV.
`UserProfile` has `preferred_bible_translation` field. `Relationship` model has
`bible_verse_id` field (migration applied).

### Task A.1 — Create Django `bible` app

**Files:**
- Create: `~/ics/bible/__init__.py`
- Create: `~/ics/bible/apps.py`
- Create: `~/ics/bible/models.py`
- Create: `~/ics/bible/serializers.py`
- Create: `~/ics/bible/api_views.py`
- Create: `~/ics/bible/views.py`
- Create: `~/ics/bible/urls.py`
- Modify: `~/ics/ics_project/settings/base.py` (add `bible` to INSTALLED_APPS)
- Modify: `~/ics/ics_project/urls.py` (include bible.urls)

**Step 1:** Create the app scaffold

```bash
cd ~/ics && python manage.py startapp bible
```

**Step 2:** Add to INSTALLED_APPS in `base.py`

```python
INSTALLED_APPS = [
    ...
    'bible',
]
```

**Step 3:** Create `bible/models.py`

```python
# bible/models.py
import uuid
from django.db import models


class BibleTranslation(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code                = models.CharField(max_length=10, unique=True)
    name                = models.CharField(max_length=100)
    language            = models.CharField(max_length=10, default='en')       # from metadata.lang_short
    language_full       = models.CharField(max_length=50, default='English')  # from metadata.lang
    year                = models.CharField(max_length=10, null=True, blank=True)  # from metadata.year
    description         = models.TextField(null=True, blank=True)             # from metadata.description
    copyright_statement = models.TextField(null=True, blank=True)             # from metadata.copyright_statement
    is_copyright        = models.BooleanField(default=False)                  # metadata.copyright == 0 → False
    is_public           = models.BooleanField(default=True)                   # metadata.restrict == 0 → True
    is_default          = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        # Enforce singleton is_default — only one translation may be default
        if self.is_default:
            BibleTranslation.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class BibleBook(models.Model):
    OT = 'OT'
    NT = 'NT'
    TESTAMENT_CHOICES = [(OT, 'Old Testament'), (NT, 'New Testament')]

    code = models.CharField(max_length=10, unique=True)   # 'GEN', 'MAT'
    name = models.CharField(max_length=50)                # 'Genesis'
    testament = models.CharField(max_length=2, choices=TESTAMENT_CHOICES)
    order = models.PositiveSmallIntegerField(unique=True)  # 1–66

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class BibleVerse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    translation = models.ForeignKey(
        BibleTranslation,
        on_delete=models.CASCADE,
        related_name='verses'
    )
    book = models.ForeignKey(
        BibleBook,
        on_delete=models.CASCADE,
        related_name='verses'
    )
    chapter = models.PositiveSmallIntegerField()
    verse = models.PositiveSmallIntegerField()
    text = models.TextField()

    class Meta:
        unique_together = [('translation', 'book', 'chapter', 'verse')]
        indexes = [
            models.Index(fields=['translation', 'book', 'chapter']),
            models.Index(fields=['book', 'chapter', 'verse']),
        ]

    def __str__(self):
        return f"{self.translation.code} {self.book.code} {self.chapter}:{self.verse}"
```

**Step 4:** Apply `Relationship` amendment — add `bible_verse_id` to the existing
Relationship model in `records/models.py`:

```python
# records/models.py — Relationship model amendment
class Relationship(models.Model):
    # ... all existing fields ...

    # Amendment — Bible verse target (alternative to to_record)
    # Exactly one of to_record or bible_verse must be non-null.
    to_record = models.ForeignKey(
        'Record',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='targeted_by_relationships'
    )
    bible_verse = models.ForeignKey(
        'bible.BibleVerse',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='governance_references'
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.to_record is None and self.bible_verse is None:
            raise ValidationError("A Relationship must target either a Record or a BibleVerse.")
        if self.to_record is not None and self.bible_verse is not None:
            raise ValidationError("A Relationship cannot target both a Record and a BibleVerse.")
```

**Step 5:** Apply `UserProfile` amendment — add preferred translation field:

```python
# accounts/models.py — UserProfile amendment
class UserProfile(models.Model):
    # ... existing fields ...
    preferred_bible_translation = models.ForeignKey(
        'bible.BibleTranslation',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='preferred_by_users'
    )
    # null = use BibleTranslation.objects.get(is_default=True)
```

**Step 6:** Run migrations

```bash
python manage.py makemigrations bible
python manage.py makemigrations records   # Relationship amendment
python manage.py makemigrations accounts  # UserProfile amendment
python manage.py migrate
```

**Step 7:** Health endpoint in `bible/api_views.py`

```python
# bible/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "bible"})
```

**Step 8:** Create `bible/urls.py`

```python
# bible/urls.py
from django.urls import path
from . import api_views, views

app_name = 'bible'

# API routes
api_urlpatterns = [
    path('health/', api_views.health, name='api-health'),
    path('translations/', api_views.TranslationListView.as_view(), name='api-translations'),
    path('books/', api_views.BookListView.as_view(), name='api-books'),
    path('verses/', api_views.VerseListView.as_view(), name='api-verses'),
    path('verse-context/<uuid:verse_id>/', api_views.VerseContextView.as_view(), name='api-verse-context'),
]

# Template view routes
urlpatterns = [
    path('', views.BibleReaderView.as_view(), name='reader'),
    path('<str:book_code>/<int:chapter>/', views.BibleReaderView.as_view(), name='reader-chapter'),
    # HTMX partials
    path('htmx/chapter/', views.htmx_chapter, name='htmx-chapter'),
    path('htmx/annotation/<uuid:verse_id>/', views.htmx_annotation_panel, name='htmx-annotation-panel'),
    path('htmx/note/save/', views.htmx_save_note, name='htmx-save-note'),
    path('htmx/note/<uuid:note_id>/delete/', views.htmx_delete_note, name='htmx-delete-note'),
    path('htmx/translation/set/', views.htmx_set_translation, name='htmx-set-translation'),
]
```

**Step 9:** Include in main `urls.py`

```python
# ics_project/urls.py
path('api/bible/', include('bible.urls', namespace='bible')),
path('bible/', include('bible.urls', namespace='bible')),
```

**Step 10:** Test

```bash
curl https://your-domain.com/api/bible/health/
# Expected: {"status": "ok", "app": "bible"}
```

Commit: `git add . && git commit -m "feat: bible app scaffold + models + migrations + health endpoint"`

---

### Task A.2 — Management commands to load scripture data

**Files:**
- Create: `~/ics/bible/management/__init__.py`
- Create: `~/ics/bible/management/commands/__init__.py`
- Create: `~/ics/bible/management/commands/load_bible.py`
- Create: `~/ics/bible/data/` (directory for source JSON files)

**Source data format — confirmed flat structure (all three translations):**

All three translation files (KJV, ASV, WEB) share the same structure: a top-level
`metadata` object containing translation details, and a flat `verses` array where
every verse in the entire Bible is a single entry. There is no nested book →
chapter hierarchy. The management command derives book structure from the `book`
integer (1–66) on each verse row using hardcoded `TESTAMENT_MAP` and `BOOK_CODE_MAP`
lookups, since the JSON does not carry testament or canonical short book code.

```json
{
    "metadata": {
        "name": "World English Bible",
        "shortname": "WEB",
        "module": "web",
        "year": "2006",
        "publisher": null,
        "lang": "English",
        "lang_short": "en",
        "copyright": 0,
        "copyright_statement": "This Bible is in the Public Domain.",
        "restrict": 0
    },
    "verses": [
        {
            "book_name": "Genesis",
            "book": 1,
            "chapter": 1,
            "verse": 1,
            "text": "In the beginning God created the heavens and the earth."
        },
        {
            "book_name": "Genesis",
            "book": 1,
            "chapter": 1,
            "verse": 2,
            "text": "..."
        }
    ]
}
```

**`metadata` field mapping to `BibleTranslation` model:**

| JSON field | Model field | Notes |
|---|---|---|
| `name` | `name` | Full translation name |
| `shortname` | `code` | Used as the load command argument |
| `lang_short` | `language` | ISO language code |
| `lang` | `language_full` | Human-readable language name |
| `year` | `year` | Publication year (string) |
| `description` | `description` | HTML string — may be long |
| `copyright_statement` | `copyright_statement` | Short plain-text statement |
| `copyright` | `is_copyright` | `0` → `False` (public domain) |
| `restrict` | `is_public` | `0` → `True` (unrestricted) |

```python
# bible/management/commands/load_bible.py
import json
import os
from django.core.management.base import BaseCommand
from bible.models import BibleTranslation, BibleBook, BibleVerse

# Static OT/NT lookup — 66 canonical books
# book integer (1–66) → testament
TESTAMENT_MAP = {
    **{i: 'OT' for i in range(1, 40)},   # Genesis (1) through Malachi (39)
    **{i: 'NT' for i in range(40, 67)},  # Matthew (40) through Revelation (66)
}

# Static book integer → canonical short code
# Needed because the flat JSON only gives book_name (full name) not a short code
BOOK_CODE_MAP = {
    1: 'GEN',  2: 'EXO',  3: 'LEV',  4: 'NUM',  5: 'DEU',
    6: 'JOS',  7: 'JDG',  8: 'RUT',  9: '1SA',  10: '2SA',
    11: '1KI', 12: '2KI', 13: '1CH', 14: '2CH', 15: 'EZR',
    16: 'NEH', 17: 'EST', 18: 'JOB', 19: 'PSA', 20: 'PRO',
    21: 'ECC', 22: 'SNG', 23: 'ISA', 24: 'JER', 25: 'LAM',
    26: 'EZK', 27: 'DAN', 28: 'HOS', 29: 'JOL', 30: 'AMO',
    31: 'OBA', 32: 'JON', 33: 'MIC', 34: 'NAH', 35: 'HAB',
    36: 'ZEP', 37: 'HAG', 38: 'ZEC', 39: 'MAL',
    40: 'MAT', 41: 'MRK', 42: 'LUK', 43: 'JHN', 44: 'ACT',
    45: 'ROM', 46: '1CO', 47: '2CO', 48: 'GAL', 49: 'EPH',
    50: 'PHP', 51: 'COL', 52: '1TH', 53: '2TH', 54: '1TI',
    55: '2TI', 56: 'TIT', 57: 'PHM', 58: 'HEB', 59: 'JAS',
    60: '1PE', 61: '2PE', 62: '1JN', 63: '2JN', 64: '3JN',
    65: 'JUD', 66: 'REV',
}


class Command(BaseCommand):
    help = 'Load a Bible translation from a flat JSON source file'

    def add_arguments(self, parser):
        parser.add_argument('translation_code', type=str,
                            help='Translation code: KJV | ASV | WEB')
        parser.add_argument('--set-default', action='store_true',
                            help='Set this translation as the platform default')
        parser.add_argument('--file', type=str, default=None,
                            help='Path to JSON file (optional — defaults to bible/data/{code}.json)')

    def handle(self, *args, **options):
        code = options['translation_code'].upper()

        # Resolve file path
        if options['file']:
            data_path = options['file']
        else:
            data_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', f'{code.lower()}.json'
            )

        if not os.path.exists(data_path):
            self.stderr.write(f"Data file not found: {data_path}")
            return

        self.stdout.write(f"Loading {code} from {data_path}…")

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # --- Parse metadata ---
        meta = data.get('metadata', {})
        restrict = meta.get('restrict', 0)
        is_copyright_val = bool(meta.get('copyright', 0))

        translation, created = BibleTranslation.objects.update_or_create(
            code=code,
            defaults={
                'name':                meta.get('name', code),
                'language':            meta.get('lang_short', 'en'),
                'language_full':       meta.get('lang', 'English'),
                'year':                meta.get('year'),
                'description':         meta.get('description'),
                'copyright_statement': meta.get('copyright_statement'),
                'is_copyright':        is_copyright_val,
                'is_public':           restrict == 0,
                'is_default':          options['set_default'],
            }
        )

        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} translation: {translation.name} ({code})")

        # --- Clear existing verses for this translation (re-load idempotent) ---
        if not created:
            deleted_count, _ = BibleVerse.objects.filter(translation=translation).delete()
            self.stdout.write(f"Cleared {deleted_count} existing verses.")

        # --- Parse flat verses array ---
        verses_data = data.get('verses', [])
        if not verses_data:
            self.stderr.write("No verses found in file. Check JSON structure.")
            return

        # Resolve or create BibleBook rows on first occurrence of each book integer
        book_cache = {}   # book_int → BibleBook instance

        verses_to_create = []
        skipped = 0

        for row in verses_data:
            book_int  = row.get('book')
            chapter   = row.get('chapter')
            verse     = row.get('verse')
            text      = row.get('text', '')
            book_name = row.get('book_name', '')

            if not all([book_int, chapter, verse, text]):
                skipped += 1
                continue

            # Resolve BibleBook — create once per book_int per run
            if book_int not in book_cache:
                book_code = BOOK_CODE_MAP.get(book_int)
                testament = TESTAMENT_MAP.get(book_int, 'OT')

                if not book_code:
                    self.stderr.write(
                        f"Unknown book integer {book_int} ({book_name}) — skipping."
                    )
                    skipped += 1
                    continue

                book_obj, _ = BibleBook.objects.get_or_create(
                    code=book_code,
                    defaults={
                        'name':      book_name,
                        'testament': testament,
                        'order':     book_int,
                    }
                )
                book_cache[book_int] = book_obj

            verses_to_create.append(BibleVerse(
                translation=translation,
                book=book_cache[book_int],
                chapter=chapter,
                verse=verse,
                text=text,
            ))

        # Bulk insert in batches of 1000
        batch_size = 1000
        total = len(verses_to_create)
        for i in range(0, total, batch_size):
            BibleVerse.objects.bulk_create(
                verses_to_create[i:i + batch_size],
                batch_size=batch_size
            )
            self.stdout.write(f"  Inserted {min(i + batch_size, total)}/{total} verses…")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Loaded {total} verses for {code}. Skipped: {skipped}."
        ))
```

**Step to run at setup — load all three translations:**

```bash
python manage.py load_bible KJV --set-default
python manage.py load_bible ASV
python manage.py load_bible WEB
```

**Verify:**

```bash
python manage.py shell -c "
from bible.models import BibleVerse, BibleTranslation
print(BibleVerse.objects.count(), 'total verses')
print(BibleTranslation.objects.get(is_default=True).code, 'is default')
"
# Expected: ~93,306 total verses (~31,102 per translation × 3), KJV is default
# Exact counts vary by translation — WEB confirmed ~31,102
```

Commit: `git add . && git commit -m "feat: bible load management command + data setup for KJV, ASV, WEB"`

---

## Phase B — DRF Endpoints

**Exit criteria:** All Bible DRF endpoints return correct data. Verse query returns the
correct translation for the requesting user. Annotation CRUD via Records endpoint
confirmed working with `record_family=bible` filter.

### Task B.1 — Bible serializers

**Files:**
- Modify: `~/ics/bible/serializers.py`

```python
# bible/serializers.py
from rest_framework import serializers
from .models import BibleTranslation, BibleBook, BibleVerse


class BibleTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleTranslation
        fields = [
            'id', 'code', 'name', 'language', 'language_full',
            'year', 'copyright_statement', 'is_copyright',
            'is_default', 'is_public'
        ]
        # description excluded from list response — too large for list views
        # Expose via a separate detail endpoint if needed


class BibleBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleBook
        fields = ['id', 'code', 'name', 'testament', 'order']


class BibleVerseSerializer(serializers.ModelSerializer):
    book_code = serializers.CharField(source='book.code', read_only=True)
    book_name = serializers.CharField(source='book.name', read_only=True)
    translation_code = serializers.CharField(source='translation.code', read_only=True)

    class Meta:
        model = BibleVerse
        fields = [
            'id', 'translation_code', 'book_code', 'book_name',
            'chapter', 'verse', 'text'
        ]
```

### Task B.2 — DRF API views

**Files:**
- Modify: `~/ics/bible/api_views.py`

```python
# bible/api_views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import BibleTranslation, BibleBook, BibleVerse
from .serializers import BibleTranslationSerializer, BibleBookSerializer, BibleVerseSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "bible"})


class TranslationListView(generics.ListAPIView):
    """List all public translations."""
    permission_classes = [IsAuthenticated]
    serializer_class = BibleTranslationSerializer
    queryset = BibleTranslation.objects.filter(is_public=True)


class BookListView(generics.ListAPIView):
    """List all books (translation-independent)."""
    permission_classes = [IsAuthenticated]
    serializer_class = BibleBookSerializer
    queryset = BibleBook.objects.all()


class VerseListView(generics.ListAPIView):
    """
    List verses for a book/chapter in the user's preferred translation.
    Required query params: ?book_code=GEN&chapter=1
    Optional: ?translation_code=ASV (overrides user preference)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BibleVerseSerializer

    def get_queryset(self):
        book_code = self.request.query_params.get('book_code')
        chapter = self.request.query_params.get('chapter')
        translation_code = self.request.query_params.get('translation_code')

        if not book_code or not chapter:
            return BibleVerse.objects.none()

        # Resolve translation: explicit param > user preference > system default
        if translation_code:
            translation = BibleTranslation.objects.filter(
                code=translation_code, is_public=True
            ).first()
        elif (
            hasattr(self.request.user, 'userprofile') and
            self.request.user.userprofile.preferred_bible_translation
        ):
            translation = self.request.user.userprofile.preferred_bible_translation
        else:
            translation = BibleTranslation.objects.filter(is_default=True).first()

        if not translation:
            return BibleVerse.objects.none()

        return BibleVerse.objects.filter(
            translation=translation,
            book__code=book_code,
            chapter=chapter
        ).select_related('book', 'translation').order_by('verse')


class VerseContextView(generics.RetrieveAPIView):
    """
    Return a single verse by ID, plus its translation and book context.
    Used by the annotation panel when resolving governance Relationship targets.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BibleVerseSerializer
    queryset = BibleVerse.objects.select_related('book', 'translation')
```

Commit: `git add . && git commit -m "feat: bible DRF endpoints — translations, books, verses"`

---

## Phase C — Django Template Views + Reader UI

**Exit criteria:** A logged-in user can navigate to `/bible/`, select a book and chapter,
read scripture in their preferred translation, and see verse indicators for their existing
notes. HTMX chapter swap works without full page reload. Mobile smoke test passes.

### Task C.1 — `bible/views.py` — Reader and navigator views

**Files:**
- Modify: `~/ics/bible/views.py`
- Create: `~/ics/bible/services.py`

```python
# bible/services.py
"""
Bible App service layer — ORM queries for template views.
Template views call these functions; they do not call DRF endpoints internally.
"""
from .models import BibleTranslation, BibleBook, BibleVerse


def get_user_translation(user):
    """Return the user's preferred translation, falling back to system default."""
    if (
        hasattr(user, 'userprofile') and
        user.userprofile.preferred_bible_translation
    ):
        return user.userprofile.preferred_bible_translation
    return BibleTranslation.objects.filter(is_default=True).first()


def get_chapter_verses(translation, book_code, chapter):
    """Return all verses for a chapter in a given translation."""
    return BibleVerse.objects.filter(
        translation=translation,
        book__code=book_code,
        chapter=chapter
    ).select_related('book').order_by('verse')


def get_all_books():
    """Return all BibleBooks ordered canonically."""
    return BibleBook.objects.all()


def get_book_chapters(book_code):
    """Return distinct chapter numbers for a book (translation-independent)."""
    return (
        BibleVerse.objects
        .filter(book__code=book_code, translation__is_default=True)
        .values_list('chapter', flat=True)
        .distinct()
        .order_by('chapter')
    )


def get_chapter_note_verse_numbers(user, translation, book_code, chapter):
    """
    Return two sets of verse numbers for a chapter:
    - personal_noted: verses where the user has a personal note
    - tenant_noted:   verses where a tenant note exists for the user's tenant(s)
    Used to render verse indicators in the reader without loading full note content.
    """
    from records.models import Record

    personal_noted = set(
        Record.objects.filter(
            record_family='bible',
            record_type='bible_note',
            record_class='personal',
            created_by=user,
            custom_fields__book_code=book_code,
            custom_fields__chapter=chapter,
            deleted_at__isnull=True,
        ).values_list('custom_fields__verse', flat=True)
    )

    # Tenant notes: visible to all members of the user's active tenants
    user_tenant_ids = (
        user.userpermission_set
        .filter(is_active=True)
        .values_list('tenant_id', flat=True)
    )

    tenant_noted = set(
        Record.objects.filter(
            record_family='bible',
            record_type='bible_note',
            record_class='organizational',
            permissions__visibility='tenant',
            tenant_id__in=user_tenant_ids,
            custom_fields__book_code=book_code,
            custom_fields__chapter=chapter,
            status='active',
            deleted_at__isnull=True,
        ).values_list('custom_fields__verse', flat=True)
    )

    return personal_noted, tenant_noted
```

```python
# bible/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .services import (
    get_user_translation, get_chapter_verses, get_all_books,
    get_book_chapters, get_chapter_note_verse_numbers
)
from .models import BibleBook, BibleTranslation


DEFAULT_BOOK = 'GEN'
DEFAULT_CHAPTER = 1


class BibleReaderView(LoginRequiredMixin, View):
    """
    Main reader view. Serves the full page shell.
    Book and chapter default to GEN 1 or the user's last position
    (last position is localStorage UI state — not server state).
    """

    def get(self, request, book_code=DEFAULT_BOOK, chapter=DEFAULT_CHAPTER):
        translation = get_user_translation(request.user)
        books = get_all_books()
        book = BibleBook.objects.filter(code=book_code).first()
        if not book:
            return redirect('bible:reader')

        chapters = get_book_chapters(book_code)
        verses = get_chapter_verses(translation, book_code, chapter)
        personal_noted, tenant_noted = get_chapter_note_verse_numbers(
            request.user, translation, book_code, chapter
        )
        translations = BibleTranslation.objects.filter(is_public=True)

        context = {
            'translation': translation,
            'translations': translations,
            'books': books,
            'book': book,
            'chapters': list(chapters),
            'chapter': chapter,
            'verses': verses,
            'personal_noted': personal_noted,
            'tenant_noted': tenant_noted,
        }
        return render(request, 'bible/reader.html', context)


@login_required
def htmx_chapter(request):
    """
    HTMX: swap chapter content when user navigates to a new book/chapter.
    Called by the navigator panel and prev/next buttons.
    """
    book_code = request.GET.get('book_code', DEFAULT_BOOK)
    chapter = int(request.GET.get('chapter', DEFAULT_CHAPTER))
    translation = get_user_translation(request.user)

    verses = get_chapter_verses(translation, book_code, chapter)
    personal_noted, tenant_noted = get_chapter_note_verse_numbers(
        request.user, translation, book_code, chapter
    )
    book = BibleBook.objects.filter(code=book_code).first()

    context = {
        'translation': translation,
        'book': book,
        'chapter': chapter,
        'verses': verses,
        'personal_noted': personal_noted,
        'tenant_noted': tenant_noted,
    }
    return render(request, 'bible/_chapter.html', context)


@login_required
def htmx_annotation_panel(request, verse_id):
    """
    HTMX: load annotation panel for a tapped verse.
    Returns personal note, tenant note, Learn cross-references,
    and Handbook references (Level 5 only) for the verse.
    """
    from .models import BibleVerse
    from records.models import Record, Relationship

    verse = BibleVerse.objects.select_related('book', 'translation').get(id=verse_id)
    user = request.user
    competence_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    # Personal note
    personal_note = Record.objects.filter(
        record_family='bible',
        record_type='bible_note',
        record_class='personal',
        created_by=user,
        custom_fields__book_code=verse.book.code,
        custom_fields__chapter=verse.chapter,
        custom_fields__verse=verse.verse,
        deleted_at__isnull=True,
    ).first()

    # Tenant notes
    user_tenant_ids = (
        user.userpermission_set
        .filter(is_active=True)
        .values_list('tenant_id', flat=True)
    )
    tenant_notes = Record.objects.filter(
        record_family='bible',
        record_type='bible_note',
        record_class='organizational',
        permissions__visibility='tenant',
        tenant_id__in=user_tenant_ids,
        custom_fields__book_code=verse.book.code,
        custom_fields__chapter=verse.chapter,
        custom_fields__verse=verse.verse,
        status='active',
        deleted_at__isnull=True,
    ).select_related('created_by__userprofile')

    # Learn cross-references
    verse_ref = f"{verse.book.code} {verse.chapter}:{verse.verse}"
    learn_references = Record.objects.filter(
        record_family='learning',
        record_type='lesson',
        status='active',
        custom_fields__scripture_reference__icontains=f"{verse.book.code} {verse.chapter}:{verse.verse}",
    ).values('id', 'title', 'metadata')[:5]

    # Check enrolment for each referenced lesson (for link gating)
    enrolled_programme_ids = set()
    if competence_level >= 1:
        enrolled_programme_ids = set(
            user.activity_set
            .filter(activity_type='programme', status__in=['pending', 'in_progress'])
            .values_list('id', flat=True)
        )

    # Handbook references (Level 5 only)
    handbook_references = []
    if competence_level >= 5:
        handbook_references = Relationship.objects.filter(
            bible_verse=verse,
            relationship_type='references',
            deleted_at__isnull=True,
        ).select_related('from_record')[:10]

    context = {
        'verse': verse,
        'verse_ref': verse_ref,
        'personal_note': personal_note,
        'tenant_notes': tenant_notes,
        'learn_references': learn_references,
        'enrolled_programme_ids': enrolled_programme_ids,
        'handbook_references': handbook_references,
        'competence_level': competence_level,
        'can_publish_tenant_note': competence_level >= 3,
    }
    return render(request, 'bible/_annotation_panel.html', context)


@login_required
def htmx_save_note(request):
    """
    HTMX: create or update a personal or tenant bible note.
    POST params: verse_id, content, note_id (optional — if updating),
                 note_class ('personal' | 'organizational')
    Returns updated verse indicators row for the verse.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    from .models import BibleVerse
    from records.models import Record
    import uuid as uuid_lib

    verse_id = request.POST.get('verse_id')
    content = request.POST.get('content', '').strip()
    note_id = request.POST.get('note_id', '')
    note_class = request.POST.get('note_class', 'personal')
    user = request.user
    competence_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    # Permission gate for tenant notes
    if note_class == 'organizational' and competence_level < 3:
        return HttpResponse("Permission denied.", status=403)

    verse = BibleVerse.objects.select_related('book').get(id=verse_id)
    verse_ref = f"{verse.book.name} {verse.chapter}:{verse.verse}"

    if note_id:
        note = Record.objects.get(id=note_id, created_by=user)
        note.content = content
        note.save(update_fields=['content', 'updated_at'])
    else:
        # Seeker 10-record limit check (personal notes only)
        if note_class == 'personal':
            if competence_level == 0:
                personal_count = Record.objects.filter(
                    record_class='personal',
                    created_by=user,
                    deleted_at__isnull=True
                ).count()
                if personal_count >= 10:
                    return render(request, 'bible/_note_limit_reached.html', {})

        active_tenant = getattr(getattr(user, 'userprofile', None), 'active_tenant', None)

        note = Record.objects.create(
            id=uuid_lib.uuid4(),
            tenant_id=active_tenant.id if active_tenant and note_class == 'organizational' else None,
            created_by=user,
            record_class=note_class,
            record_family='bible',
            record_type='bible_note',
            title=verse_ref,
            content=content,
            status='active' if note_class == 'organizational' else 'active',
            metadata={'source_app': 'bible'},
            custom_fields={
                'book_code': verse.book.code,
                'chapter': verse.chapter,
                'verse': verse.verse,
            },
            permissions={
                'visibility': 'tenant' if note_class == 'organizational' else 'private',
                'required_level': 1,
                'roles_allowed': [],
                'can_edit': [],
            }
        )

    return render(request, 'bible/_verse_indicators.html', {
        'verse': verse,
        'has_personal_note': note_class == 'personal',
        'has_tenant_note': note_class == 'organizational',
    })


@login_required
def htmx_delete_note(request, note_id):
    """HTMX: soft-delete a note. Returns empty response to remove element."""
    if request.method != 'DELETE':
        return HttpResponse(status=405)

    from records.models import Record
    from django.utils import timezone

    note = Record.objects.get(id=note_id, created_by=request.user)
    note.deleted_at = timezone.now()
    note.save(update_fields=['deleted_at'])
    return HttpResponse('')


@login_required
def htmx_set_translation(request):
    """
    HTMX: update user's preferred translation.
    POST params: translation_code, book_code, chapter
    Returns updated chapter content in the new translation.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    translation_code = request.POST.get('translation_code')
    book_code = request.POST.get('book_code', DEFAULT_BOOK)
    chapter = int(request.POST.get('chapter', DEFAULT_CHAPTER))

    translation = BibleTranslation.objects.filter(
        code=translation_code, is_public=True
    ).first()

    if translation and hasattr(request.user, 'userprofile'):
        request.user.userprofile.preferred_bible_translation = translation
        request.user.userprofile.save(update_fields=['preferred_bible_translation'])

    verses = get_chapter_verses(translation, book_code, chapter)
    personal_noted, tenant_noted = get_chapter_note_verse_numbers(
        request.user, translation, book_code, chapter
    )
    book = BibleBook.objects.filter(code=book_code).first()

    context = {
        'translation': translation,
        'book': book,
        'chapter': chapter,
        'verses': verses,
        'personal_noted': personal_noted,
        'tenant_noted': tenant_noted,
    }
    return render(request, 'bible/_chapter.html', context)
```

Commit: `git add . && git commit -m "feat: bible template views + HTMX partial views"`

---

### Task C.2 — Templates

**Files:**
- Create: `~/ics/templates/bible/base_bible.html`
- Create: `~/ics/templates/bible/reader.html`
- Create: `~/ics/templates/bible/_chapter.html`
- Create: `~/ics/templates/bible/_annotation_panel.html`
- Create: `~/ics/templates/bible/_verse_indicators.html`
- Create: `~/ics/templates/bible/_note_limit_reached.html`
- Create: `~/ics/static/css/bible.css`

**`templates/bible/base_bible.html`:**

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/bible.css' %}">
{% endblock %}

{% block extra_js %}
  <script>
    /* Restore last reading position from localStorage on page load */
    document.addEventListener('DOMContentLoaded', () => {
      const pos = localStorage.getItem('ics_ui.bible_last_position')
      if (pos && !window.location.pathname.includes('/bible/')) {
        try {
          const { bookCode, chapter } = JSON.parse(pos)
          if (bookCode && chapter) {
            htmx.ajax('GET', `/bible/htmx/chapter/?book_code=${bookCode}&chapter=${chapter}`,
              { target: '#bible-chapter', swap: 'innerHTML' })
          }
        } catch (_) {}
      }
    })

    /* Save reading position to localStorage after each chapter load */
    document.body.addEventListener('htmx:afterSwap', (e) => {
      if (e.detail.target.id === 'bible-chapter') {
        const bookCode = e.detail.target.dataset.bookCode
        const chapter = e.detail.target.dataset.chapter
        if (bookCode && chapter) {
          localStorage.setItem('ics_ui.bible_last_position',
            JSON.stringify({ bookCode, chapter }))
        }
      }
    })
  </script>
{% endblock %}
```

**`templates/bible/reader.html`:**

```html
{% extends "bible/base_bible.html" %}

{% block title %}Bible · {{ book.name }} {{ chapter }}{% endblock %}

{% block content %}
<div class="bible-reader-shell">

  <!-- Top bar: book/chapter heading + translation selector -->
  <div class="bible-topbar">
    <button class="bible-topbar__nav-btn"
            hx-get="{% url 'bible:htmx-chapter' %}?book_code={{ book.code }}&chapter={{ chapter|add:'-1' }}"
            hx-target="#bible-chapter"
            hx-swap="innerHTML"
            aria-label="Previous chapter">&#8592;</button>

    <button class="bible-topbar__title-btn"
            aria-haspopup="dialog"
            aria-controls="bible-navigator"
            onclick="document.getElementById('bible-navigator').classList.add('bible-navigator--open')">
      {{ book.name }} {{ chapter }}
    </button>

    <button class="bible-topbar__nav-btn"
            hx-get="{% url 'bible:htmx-chapter' %}?book_code={{ book.code }}&chapter={{ chapter|add:'1' }}"
            hx-target="#bible-chapter"
            hx-swap="innerHTML"
            aria-label="Next chapter">&#8594;</button>
  </div>

  <!-- Translation selector -->
  <div class="bible-translation-row">
    {% for t in translations %}
    <button class="bible-translation-btn {% if t.id == translation.id %}bible-translation-btn--active{% endif %}"
            hx-post="{% url 'bible:htmx-set-translation' %}"
            hx-vals='{"translation_code": "{{ t.code }}", "book_code": "{{ book.code }}", "chapter": "{{ chapter }}"}'
            hx-target="#bible-chapter"
            hx-swap="innerHTML"
            {% csrf_token %}>
      {{ t.code }}
    </button>
    {% endfor %}
  </div>

  <!-- Chapter content (swapped by HTMX on navigation) -->
  <div id="bible-chapter"
       data-book-code="{{ book.code }}"
       data-chapter="{{ chapter }}">
    {% include "bible/_chapter.html" %}
  </div>

  <!-- Annotation panel (slide-up sheet — hidden by default) -->
  <div id="bible-annotation-overlay" class="sheet-overlay" hidden></div>
  <div id="bible-annotation-panel" class="sheet bible-annotation-panel"
       role="dialog" aria-modal="true" aria-label="Verse note">
    {# Populated by HTMX on verse tap #}
  </div>

  <!-- Book/Chapter navigator (slide-up sheet) -->
  <div id="bible-navigator" class="sheet bible-navigator"
       role="dialog" aria-modal="true" aria-label="Book and chapter navigator">
    <div class="sheet__header">
      <span class="sheet__title">Select Passage</span>
      <button class="sheet__close-btn"
              onclick="document.getElementById('bible-navigator').classList.remove('bible-navigator--open')"
              aria-label="Close">✕</button>
    </div>
    <div class="bible-navigator__body">
      <div class="bible-navigator__books-col">
        <p class="bible-navigator__col-label">Book</p>
        <ul class="bible-nav__book-list" role="list">
          {% for b in books %}
          <li>
            <button class="bible-nav__book-btn {% if b.code == book.code %}bible-nav__book-btn--active{% endif %}"
                    hx-get="{% url 'bible:htmx-chapter' %}?book_code={{ b.code }}&chapter=1"
                    hx-target="#bible-chapter"
                    hx-swap="innerHTML"
                    onclick="document.getElementById('bible-navigator').classList.remove('bible-navigator--open')">
              {{ b.name }}
            </button>
          </li>
          {% endfor %}
        </ul>
      </div>
      <div class="bible-navigator__chapters-col">
        <p class="bible-navigator__col-label">Chapter</p>
        <div class="bible-nav__chapter-grid">
          {% for ch in chapters %}
          <button class="bible-nav__chapter-btn {% if ch == chapter %}bible-nav__chapter-btn--active{% endif %}"
                  hx-get="{% url 'bible:htmx-chapter' %}?book_code={{ book.code }}&chapter={{ ch }}"
                  hx-target="#bible-chapter"
                  hx-swap="innerHTML"
                  onclick="document.getElementById('bible-navigator').classList.remove('bible-navigator--open')">
            {{ ch }}
          </button>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>

</div>
{% endblock %}
```

**`templates/bible/_chapter.html`** (HTMX partial):

```html
<div data-book-code="{{ book.code }}" data-chapter="{{ chapter }}">
  {% for verse in verses %}
  <div class="bible-verse {% if verse.verse in personal_noted %}bible-verse--personal{% endif %} {% if verse.verse in tenant_noted %}bible-verse--tenant{% endif %}"
       hx-get="{% url 'bible:htmx-annotation-panel' verse.id %}"
       hx-target="#bible-annotation-panel"
       hx-swap="innerHTML"
       hx-on::after-request="document.getElementById('bible-annotation-panel').classList.add('bible-annotation-panel--open'); document.getElementById('bible-annotation-overlay').removeAttribute('hidden')"
       role="button"
       tabindex="0"
       aria-label="Verse {{ verse.verse }}">
    <span class="bible-verse__num">{{ verse.verse }}</span>
    <span class="bible-verse__text">{{ verse.text }}</span>
    <span class="bible-verse__indicators">
      {% if verse.verse in personal_noted %}<span class="dot dot--personal" title="Your note"></span>{% endif %}
      {% if verse.verse in tenant_noted %}<span class="dot dot--tenant" title="Community note"></span>{% endif %}
    </span>
  </div>
  {% endfor %}
</div>
```

**`templates/bible/_annotation_panel.html`** (HTMX partial):

```html
<div class="sheet__header">
  <span class="sheet__title">{{ verse_ref }}</span>
  <button class="sheet__close-btn"
          onclick="document.getElementById('bible-annotation-panel').classList.remove('bible-annotation-panel--open'); document.getElementById('bible-annotation-overlay').setAttribute('hidden','')"
          aria-label="Close">✕</button>
</div>

<div class="bible-annotation-panel__body">

  <!-- Selected verse text -->
  <blockquote class="bible-annotation-panel__verse">{{ verse.text }}</blockquote>

  <!-- Tenant notes (read-only, attributed) -->
  {% for note in tenant_notes %}
  <div class="bible-annotation-panel__tenant-note">
    <span class="bible-annotation-panel__tenant-badge">Community Note</span>
    <p>{{ note.content }}</p>
    <span class="bible-annotation-panel__tenant-attr">— {{ note.created_by.userprofile.display_name }}</span>
  </div>
  {% endfor %}

  <!-- Learn cross-references -->
  {% if learn_references %}
  <div class="bible-annotation-panel__learn-refs">
    <p class="bible-annotation-panel__section-label">Referenced in Learn</p>
    {% for lesson in learn_references %}
    <div class="bible-annotation-panel__learn-ref">
      <span class="bible-annotation-panel__learn-title">{{ lesson.title }}</span>
      {% if lesson.id|stringformat:"s" in enrolled_programme_ids|join:"," %}
        <a href="{% url 'learn:lesson-detail' lesson.id %}" class="btn btn--sm btn--secondary">Open Lesson</a>
      {% else %}
        <span class="bible-annotation-panel__enrol-prompt">Enrol to access</span>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Handbook references (Level 5 only) -->
  {% if competence_level >= 5 and handbook_references %}
  <div class="bible-annotation-panel__handbook-refs">
    <p class="bible-annotation-panel__section-label">Handbook References</p>
    {% for rel in handbook_references %}
    <a href="{% url 'governance:record-detail' rel.from_record.id %}"
       class="bible-annotation-panel__handbook-ref">
      {{ rel.from_record.title }}
      <span class="badge badge--governance">{{ rel.from_record.record_type }}</span>
    </a>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Personal note area -->
  <p class="bible-annotation-panel__section-label">Your Note</p>
  <form hx-post="{% url 'bible:htmx-save-note' %}"
        hx-target="#bible-annotation-panel"
        hx-swap="none"
        hx-on::after-request="document.getElementById('bible-annotation-panel').classList.remove('bible-annotation-panel--open')">
    {% csrf_token %}
    <input type="hidden" name="verse_id" value="{{ verse.id }}">
    <input type="hidden" name="note_class" value="personal">
    {% if personal_note %}
    <input type="hidden" name="note_id" value="{{ personal_note.id }}">
    {% endif %}
    <textarea name="content"
              class="bible-annotation-panel__textarea"
              placeholder="Write a reflection, cross-reference, or personal note…"
              rows="4"
              maxlength="2000">{{ personal_note.content|default:'' }}</textarea>
    <button type="submit" class="btn btn--primary bible-annotation-panel__save-btn">
      {% if personal_note %}Update Note{% else %}Save Note{% endif %}
    </button>
  </form>

  <!-- Delete personal note -->
  {% if personal_note %}
  <button hx-delete="{% url 'bible:htmx-delete-note' personal_note.id %}"
          hx-target="#bible-annotation-panel"
          hx-swap="none"
          hx-confirm="Delete this note?"
          hx-on::after-request="document.getElementById('bible-annotation-panel').classList.remove('bible-annotation-panel--open')"
          class="btn btn--danger btn--sm bible-annotation-panel__delete-btn">
    Delete Note
  </button>
  {% endif %}

  <!-- Publish tenant note (Level 3+) -->
  {% if can_publish_tenant_note %}
  <details class="bible-annotation-panel__tenant-publish">
    <summary>Publish community note…</summary>
    <form hx-post="{% url 'bible:htmx-save-note' %}"
          hx-target="#bible-annotation-panel"
          hx-swap="none"
          hx-on::after-request="document.getElementById('bible-annotation-panel').classList.remove('bible-annotation-panel--open')">
      {% csrf_token %}
      <input type="hidden" name="verse_id" value="{{ verse.id }}">
      <input type="hidden" name="note_class" value="organizational">
      <textarea name="content"
                class="bible-annotation-panel__textarea"
                placeholder="Publish a teaching note visible to your branch…"
                rows="4"
                maxlength="2000"></textarea>
      <button type="submit" class="btn btn--secondary bible-annotation-panel__save-btn">
        Publish to Branch
      </button>
    </form>
  </details>
  {% endif %}

</div>
```

**`templates/bible/_note_limit_reached.html`:**

```html
<div class="bible-annotation-panel__limit-msg" role="alert">
  <p>You have reached the 10-record limit for Seekers.</p>
  <p>Complete your formation requirements to unlock full access.</p>
</div>
```

Commit: `git add . && git commit -m "feat: bible reader templates + HTMX annotation panel"`

---

## Phase D — Smoke Test + CSS

**Exit criteria:** Full smoke test checklist passes on mobile. `bible.css` finalised.

### Task D.1 — `bible.css`

Place at `~/ics/static/css/bible.css`. This carries forward the styles established in
the prior design work with the following additions: tenant note amber dot, tenant note
read-only block styling, Learn reference chip, Handbook reference chip, translation
button row.

Core additions to the prior CSS:

```css
/* Tenant note indicator */
.dot--tenant {
  background: var(--color-amber, #f59e0b);
}

/* Tenant note block in annotation panel */
.bible-annotation-panel__tenant-note {
  background: var(--color-amber-light, #fef3c7);
  border-left: 3px solid var(--color-amber, #f59e0b);
  border-radius: 0 0.375rem 0.375rem 0;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
}

.bible-annotation-panel__tenant-badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-amber-dark, #92400e);
}

.bible-annotation-panel__tenant-attr {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #666);
  display: block;
  margin-top: 0.25rem;
}

/* Section labels */
.bible-annotation-panel__section-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary, #666);
  margin: 0.75rem 0 0.375rem;
}

/* Learn cross-reference chip */
.bible-annotation-panel__learn-refs {
  margin-bottom: 0.5rem;
}
.bible-annotation-panel__learn-ref {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface-alt, #f8f9fa);
  border-radius: 0.375rem;
  margin-bottom: 0.25rem;
  gap: 0.5rem;
}
.bible-annotation-panel__learn-title {
  font-size: 0.875rem;
  font-weight: 500;
  flex: 1;
}
.bible-annotation-panel__enrol-prompt {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #888);
}

/* Handbook reference link */
.bible-annotation-panel__handbook-refs {
  margin-bottom: 0.5rem;
}
.bible-annotation-panel__handbook-ref {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-primary-light, #e8f0fe);
  border-radius: 0.375rem;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-primary, #1a73e8);
  text-decoration: none;
}

/* Tenant publish details */
.bible-annotation-panel__tenant-publish {
  margin-top: 0.75rem;
  border-top: 1px solid var(--color-divider, #e0e0e0);
  padding-top: 0.75rem;
}
.bible-annotation-panel__tenant-publish summary {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666);
  cursor: pointer;
  user-select: none;
}

/* Translation button row */
.bible-translation-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--color-divider, #e0e0e0);
}
.bible-translation-btn {
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--color-divider, #e0e0e0);
  border-radius: 1rem;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
}
.bible-translation-btn--active {
  background: var(--color-primary, #1a73e8);
  border-color: var(--color-primary, #1a73e8);
  color: #fff;
}
```

### Task D.2 — Smoke test checklist

Before closing Phase D, verify manually on mobile:

- [ ] Logged-out user navigating to `/bible/` is redirected to login
- [ ] Seeker (Level 0b) can read scripture — all books, all chapters
- [ ] Seeker can tap a verse and open the annotation panel
- [ ] Seeker can save a personal note (first note — no limit reached)
- [ ] Seeker at 10-record limit sees limit message, cannot save note
- [ ] Member (Level 1+) can save personal notes without limit
- [ ] Personal note indicator (blue dot) appears on verse after save
- [ ] Chapter navigation (prev/next) works via HTMX — no full page reload
- [ ] Book/chapter navigator opens, user can select any book and chapter
- [ ] Translation switcher (KJV/ASV/WEB) swaps chapter text via HTMX
- [ ] Translation preference persists after switching (HTMX post updates UserProfile)
- [ ] Branch-Steward (Level 3+) sees "Publish community note" option in annotation panel
- [ ] Steward publishes tenant note — amber dot appears on verse for branch members
- [ ] Branch member sees tenant note as read-only attributed block in annotation panel
- [ ] Verse referenced in an active lesson shows "Referenced in Learn" chip
- [ ] Non-enrolled user sees lesson title + "Enrol to access"
- [ ] Enrolled user sees "Open Lesson" link
- [ ] Level 5 user sees "Handbook References" section when Relationship rows exist
- [ ] Level 4 user does NOT see Handbook References section
- [ ] Delete note removes note and clears dot indicator

Commit: `git add . && git commit -m "feat: bible app — bible.css additions + smoke test pass"`

---

## Django Endpoint Summary

```
# Bible-specific DRF endpoints (new — Bible App)
GET  /api/bible/health/
GET  /api/bible/translations/
GET  /api/bible/books/
GET  /api/bible/verses/?book_code=GEN&chapter=1
GET  /api/bible/verses/?book_code=GEN&chapter=1&translation_code=ASV
GET  /api/bible/verse-context/{verse_id}/

# Bible template view routes
GET  /bible/                                    reader (default GEN 1)
GET  /bible/{book_code}/{chapter}/             reader (specific passage)

# HTMX partial routes
GET  /bible/htmx/chapter/                      chapter content swap
GET  /bible/htmx/annotation/{verse_id}/        annotation panel
POST /bible/htmx/note/save/                    create or update note
DELETE /bible/htmx/note/{note_id}/delete/      soft-delete note
POST /bible/htmx/translation/set/             update user translation preference

# Existing Records endpoints (verify filters work — no changes)
GET  /api/records/?record_family=bible&record_type=bible_note
GET  /api/records/?record_family=learning&record_type=lesson
     &custom_fields__scripture_reference__icontains=GEN 1:1

# Existing Relationship endpoint (amendment applied)
POST /api/relationships/                       create with bible_verse_id
GET  /api/relationships/?bible_verse_id={id}  fetch governance links for a verse
```

---

## File Map (Bible App additions)

```
~/ics/bible/                              ← NEW Django app
  __init__.py
  apps.py
  models.py                              ← BibleTranslation, BibleBook, BibleVerse
  serializers.py                         ← Translation, Book, Verse serializers
  api_views.py                           ← DRF endpoints (health, translations, books, verses)
  views.py                               ← Django template views + HTMX partial views
  services.py                            ← ORM query helpers for template views
  urls.py                                ← API routes + template routes + HTMX routes
  management/
    commands/
      load_bible.py                      ← Management command for loading translations
  data/
    kjv.json                             ← KJV source data (downloaded, not committed to git)
    asv.json                             ← ASV source data
    web.json                             ← WEB source data
  templates/
    bible/
      base_bible.html                    ← extends base.html, loads bible.css, position JS
      reader.html                        ← Full reader page
      _chapter.html                      ← HTMX: chapter content partial
      _annotation_panel.html            ← HTMX: annotation panel partial
      _verse_indicators.html            ← HTMX: verse dot indicator partial
      _note_limit_reached.html          ← Seeker limit reached message

~/ics/records/models.py                  ← MODIFIED: Relationship.bible_verse FK added
~/ics/accounts/models.py                 ← MODIFIED: UserProfile.preferred_bible_translation added
~/ics/static/css/bible.css               ← NEW/UPDATED: Bible App styles
```

**Note:** `bible-app.js`, `bible.html` (static file), and `bible.service.js` produced
in the prior design session are **not used**. The UI is fully served by Django views
and templates. HTMX replaces the JS interaction layer. `bible.css` from the prior
session is the starting point for the updated stylesheet.

**Data files note:** All three translation files share the same flat `metadata` +
`verses` JSON structure — the single management command handles all three without
modification. `bible/data/*.json` source files must be added to `.gitignore` if they
exceed GitHub's file size limits (~50MB per file uncompressed). The management command
is committed; data is loaded at deployment via `python manage.py load_bible`.

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|---|---|---|---|
| A | Django `bible` app, models, migrations, management command, data load | Phases 0–2 done + data contract amended | `/api/bible/health/` 200. ~93,306 verse rows in DB (3 translations). Relationship.bible_verse_id field exists. |
| B | DRF serializers + API views (translations, books, verses, verse-context) | Phase A done | All DRF endpoints return correct data. Verse query respects user translation preference. |
| C | Django template views, HTMX partial views, all templates | Phase B done | Reader renders scripture. Personal note CRUD works via HTMX. |
| D | `bible.css` additions, smoke test | Phase C done | Full smoke test checklist passes on mobile. Tenant notes, Learn refs, Handbook refs all working. |

---

## Deferred (Post-MVP)

- Reading plans (personal Activity `activity_type:'habit'` — defer until Activity App is complete)
- Verse highlights (colour-coded, no text)
- Scripture full-text search (`SearchVectorField` on `BibleVerse`)
- Licensed translations (NIV, ESV, NLT — licensing required)
- African language translations (Zulu, Xhosa, Afrikaans)
- Paraclete "You haven't read today" prompt (Phase 6)
- Cross-reference chains (canonical verse-to-verse references)
- Audio Bible (deferred with Video/Live app)
- Relationship-engine-based Learn cross-references (upgrade from `custom_fields` convention)


---


# ICS Learn App — System Design & Build Roadmap

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **UI Architecture amendment — 2026-04-07:**
> The original design specified vanilla JS (IIFE modules + `learn.service.js`) for the UI layer.
> This has been superseded by the platform-wide decision to build all app UIs in
> **Django templates + HTMX**. The backend (Django `learn` app, DRF endpoints, signals,
> models) is unchanged. Phases A and B are unchanged. Phases C–G are amended:
> all `learn-app.js`, `learn.service.js`, and `learn.html` references are replaced
> by Django views, URL patterns, and templates. `learn.css` is unchanged — the
> design system carries forward identically. Vanilla JS is retained only for
> theme/UI state (`storage.js`) and minor interactions HTMX cannot handle.

**Goal:** Build the ICS Learn App — the digital expression of the Sceptre Qualification Programmes Framework — enabling learners to browse courses, enrol in programmes, track progress, and earn certifications that advance their competence level within the Kingdom Governance System.

**Architecture:** Django + DRF backend with a dedicated `learn` app. UI rendered via Django templates with HTMX for dynamic interactions (progress updates, enrolment, lesson completion, queue refreshes). All learning content is Record objects (`record_family: "learning"`). All learner progress is Activity objects. The two are linked via the Relationship engine. No new tables beyond the existing data contract — the Learning Engine is a pattern layer over Records + Activities.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX, `learn.css` (mobile-first, existing CSS variables).

**Data Contract reference:** `2026-04-07-ics-platform-data-contract_v4.md` — all schemas and patterns in this document originate from Part 9 of that contract.

---

## System Overview

### The Learning Stack

```
KGS Layer          Apostles Programme (7-year mission container)
                   ↓ contextualises
Content Layer      Qualification Programmes (Certificate → Doctorate)
                   ↓ contains
                   Courses → Lessons → Assignments / Quizzes
                   (all Record objects, record_family: "learning")
                   ↓ structured by
                   Relationships (part_of — curriculum graph)

Learner Layer      Enrolment Activity (activity_type: "programme")
                   ↓ nests
                   Course Activity (activity_type: "project")
                   ↓ nests
                   Lesson/Assessment Activities (activity_type: "task")
                   ↓ completes to produce
                   Certification Record (record_type: "certification")
                   ↓ confirmed by steward via
                   POST /api/learn/certifications/{id}/confirm/
                   ↓ advances
                   user.competence_level
```

### User roles in the Learn App

| Role | What they do |
|---|---|
| Seeker (0b) | Browse published programmes. Cannot enrol. |
| Member (Level 1+) | Enrol, track progress, complete lessons |
| Disciple/Operator (Level 2+) | All above + submit assignments |
| Branch-Steward (Level 3+) | Confirm certifications for their tenant's learners |
| District-Steward / Senior Steward (Level 4+) | Author and submit Programmes and Courses for review |
| Architect (Level 5) | Review submitted content, approve (status → active), lock |

---

## The Five Qualification Programmes

These are the five content containers of the Apostles Programme. Each is a
Record (`record_class: "organizational"`, `record_family: "learning"`,
`record_type: "programme"`). Courses are authored within them.

| Programme | Competence Level | Duration | KGS Pathways | Prerequisites |
|---|---|---|---|---|
| Certificate | Level 1 | 1 year | New Life; Community Life; Learning | None |
| Diploma | Level 2 | 3 years | Spiritual Formation; Service; Mission; Learning | Certificate |
| Degree | Level 3 | 4 years | Leadership; Learning | Diploma + Certificate |
| Masters | Level 4 | 4–5 years | Leadership; Apostolic Stewardship | Degree + prior |
| Doctorate | Level 5 | 7 years total | Leadership; Apostolic Stewardship | Masters + all prior |

---

## Feature List (All Features — Unphased)

This is the complete Learn App feature inventory. Phasing follows below.

### F1 — Programme Catalogue
- Browse all published Qualification Programmes
- Pathway View: grouped by KGS pathway (default for enrolled learners)
- Catalogue View: flat list filtered by competence level
- Locked indicator for programmes above learner's current level
- Programme detail: title, description, pathways, duration, prerequisites, course list

### F2 — Course Browser
- Browse courses within a programme
- Course detail: title, description, lesson list, assignments, quizzes
- Competence gate: courses requiring a higher level show locked state

### F3 — Enrolment
- Enrol in a programme (creates enrolment Activity of type "programme")
- Prerequisite check before enrolment is permitted
- One active enrolment per programme per user
- Enrolment confirmation screen

### F4 — Progress Tracking
- Lesson completion (marks task Activity as completed)
- Course progress bar (% lessons/assessments completed)
- Programme progress bar (% courses completed)
- Progress persists via ActivityLog
- Resume where left off (last incomplete lesson)

### F5 — Lesson Viewer
- Read lesson content (Record.content rendered as rich text / markdown)
- Mark lesson complete button
- Navigate previous / next lesson
- Back to course breadcrumb

### F6 — Assessments (Assignments & Quizzes)
- Quiz: inline multiple-choice or short answer (stored in Record.custom_fields)
- Assignment: text submission by learner (stored as child Record linked to assignment)
- Submission marks assessment Activity as completed
- Steward can view submitted assignments within their tenant scope

### F7 — Certification & Competence Advancement
- Auto-create draft Certification Record when programme Activity hits 100%
- Learner sees "Awaiting certification" status
- Steward review queue: list of draft certifications for their tenant's learners
- Steward confirms → certification status → active → competence_level incremented
- Learner notification on certification confirmed (via Notifications app stub)

### F8 — Content Authorship (Level 4+)
- Create Programme record (draft)
- Create Course record (linked to programme via part_of Relationship)
- Create Lesson record (linked to course via part_of Relationship)
- Create Assignment / Quiz record (linked to course or lesson via part_of)
- Rich text / markdown content editor for lesson body
- Submit Programme or Course for Handbook review (status → submitted)

### F9 — Handbook Review Queue (Level 5)
- List submitted learning records (status: "submitted", record_family: "learning")
- Review programme / course detail
- Approve (status → active) or return to draft with a note
- Lock approved content (status → locked)

### F10 — Pathway View (Dashboard integration)
- "You are enrolled in [Programme] — [Primary Pathway]" banner
- Active enrolment widget surfaced on Learn App home
- Paraclete integration: "Continue your lesson: [lesson title]" (Phase 6)

### F11 — My Learning Dashboard (Learn App home)
- Active enrolments with progress
- Completed programmes and certifications
- Recommended next programme (based on competence level)
- Quick-access: resume last lesson

---

## Build Phases

### Phase A — Django Learn App (backend foundation)
*Entry requirement: Phases 0–4 of main roadmap complete (Django project, Records, Activity, Identity engines all live).*

### Phase B — Content Engine (read-only)
*Entry requirement: Phase A complete.*

### Phase C — Enrolment + Progress Tracking
*Entry requirement: Phase B complete.*

### Phase D — Assessments
*Entry requirement: Phase C complete.*

### Phase E — Certification + Competence Advancement
*Entry requirement: Phase D complete.*

### Phase F — Content Authorship + Handbook Review
*Entry requirement: Phase E complete.*

### Phase G — UI Polish + Pathway View + My Learning Dashboard
*Entry requirement: Phase F complete.*

---

## Phase A — Django Learn App (Backend Foundation)

**Exit criteria:** `GET /api/learn/health/` returns `{"status": "ok"}`. Django `learn` app exists with models, serializers, basic endpoints. No UI yet.

### Task A.1 — Create Django `learn` app

**Files:**
- Create: `~/ics/learn/__init__.py`
- Create: `~/ics/learn/apps.py`
- Create: `~/ics/learn/models.py`
- Create: `~/ics/learn/serializers.py`
- Create: `~/ics/learn/views.py`
- Create: `~/ics/learn/urls.py`
- Modify: `~/ics/ics_project/settings/base.py` (add `learn` to INSTALLED_APPS)
- Modify: `~/ics/ics_project/urls.py` (include learn.urls)

**Step 1:** Create the app scaffold

```bash
cd ~/ics && python manage.py startapp learn
```

**Step 2:** Add to INSTALLED_APPS in `base.py`

```python
INSTALLED_APPS = [
    ...
    'learn',
]
```

**Step 3:** Create `learn/models.py`

The Learn App does not define its own content models — all content is stored
in `records.Record`. The only Learn-specific model is `CertificationConfirmation`
which records the steward action (audit trail separate from the Record status change).

```python
# learn/models.py
import uuid
from django.db import models
from django.conf import settings


class CertificationConfirmation(models.Model):
    """
    Audit record of a steward confirming a learner's certification.
    The certification itself is a records.Record with record_type='certification'.
    This model records WHO confirmed it and WHEN, separately from the Record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certification_record_id = models.UUIDField(db_index=True)  # FK → records.Record
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='certifications_confirmed'
    )
    learner_id = models.UUIDField(db_index=True)               # FK → User (the learner)
    previous_competence_level = models.IntegerField()
    new_competence_level = models.IntegerField()
    confirmed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-confirmed_at']
        indexes = [
            models.Index(fields=['certification_record_id']),
            models.Index(fields=['learner_id']),
            models.Index(fields=['confirmed_by']),
        ]
```

**Step 4:** Run migrations

```bash
python manage.py makemigrations learn
python manage.py migrate
```

**Step 5:** Create health endpoint in `learn/views.py`

```python
# learn/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "learn"})
```

**Step 6:** Create `learn/urls.py`

```python
# learn/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='learn-health'),
]
```

**Step 7:** Include in main `urls.py`

```python
path('api/learn/', include('learn.urls')),
```

**Step 8:** Test

```bash
curl https://your-domain.com/api/learn/health/
# Expected: {"status": "ok", "app": "learn"}
```

Commit: `git add . && git commit -m "feat: learn app scaffold + health endpoint"`

---

### Task A.2 — Certification confirmation endpoint

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`
- Modify: `~/ics/learn/serializers.py`
- Modify: `~/ics/accounts/serializers.py` (competence_level write rule)

This is the most critical backend endpoint in the Learn App. It is the ONLY
place in the system that may increment `user.competence_level`.

**Step 1:** Add `CertificationConfirmSerializer` to `learn/serializers.py`

```python
# learn/serializers.py
from rest_framework import serializers
from .models import CertificationConfirmation


class CertificationConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificationConfirmation
        fields = [
            'id', 'certification_record_id', 'confirmed_by',
            'learner_id', 'previous_competence_level',
            'new_competence_level', 'confirmed_at', 'notes'
        ]
        read_only_fields = [
            'id', 'confirmed_by', 'previous_competence_level',
            'new_competence_level', 'confirmed_at'
        ]
```

**Step 2:** Add the confirm view to `learn/views.py`

```python
# learn/views.py (additions)
import uuid
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from records.models import Record          # adjust import path to your project
from django.contrib.auth import get_user_model
from .models import CertificationConfirmation
from .serializers import CertificationConfirmSerializer

User = get_user_model()


def is_level_3_or_above(user):
    """Check if user has competence_level >= 3 (branch-steward or above)."""
    return hasattr(user, 'userprofile') and user.userprofile.competence_level >= 3


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_certification(request, certification_id):
    """
    Steward confirms a learner's certification.
    - Gated to competence_level >= 3
    - Sets certification Record status to 'active'
    - Increments learner's competence_level by 1 (up to target_level)
    - Creates CertificationConfirmation audit record
    - This endpoint is the SOLE authorised writer of competence_level
    """
    if not is_level_3_or_above(request.user):
        return Response(
            {"detail": "Certification confirmation requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    certification_record = get_object_or_404(
        Record,
        id=certification_id,
        record_type='certification',
        status='draft'
    )

    # Retrieve metadata from the certification record
    metadata = certification_record.metadata or {}
    learner_id = metadata.get('learner_id') or str(certification_record.created_by_id)
    target_level = metadata.get('target_level', 1)

    learner = get_object_or_404(User, id=learner_id)
    learner_profile = learner.userprofile
    previous_level = learner_profile.competence_level

    # Only advance if not already at or above target level
    if previous_level >= target_level:
        return Response(
            {"detail": "Learner is already at or above the target competence level."},
            status=status.HTTP_400_BAD_REQUEST
        )

    new_level = min(previous_level + 1, target_level)

    # Update certification record status
    certification_record.status = 'active'
    certification_record.save(update_fields=['status', 'updated_at'])

    # Advance learner competence level — only write path in the system
    learner_profile.competence_level = new_level
    learner_profile.save(update_fields=['competence_level'])

    # Create audit record
    confirmation = CertificationConfirmation.objects.create(
        certification_record_id=certification_record.id,
        confirmed_by=request.user,
        learner_id=learner.id,
        previous_competence_level=previous_level,
        new_competence_level=new_level,
        notes=request.data.get('notes', '')
    )

    serializer = CertificationConfirmSerializer(confirmation)
    return Response(serializer.data, status=status.HTTP_200_OK)
```

**Step 3:** Add to `learn/urls.py`

```python
path('certifications/<uuid:certification_id>/confirm/', views.confirm_certification, name='certification-confirm'),
```

**Step 4:** Verify `competence_level` is read-only in `accounts/serializers.py`
everywhere EXCEPT this endpoint. Add a comment:

```python
# accounts/serializers.py — UserProfileSerializer
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['competence_level', 'status', ...]
        read_only_fields = ['competence_level']
        # NOTE: competence_level is intentionally read-only here.
        # The ONLY authorised write path is POST /api/learn/certifications/{id}/confirm/
        # See learn/views.py::confirm_certification
```

Commit: `git add . && git commit -m "feat: certification confirm endpoint — sole writer of competence_level"`

---

### Task A.3 — Certification review queue endpoint

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`

Stewards need a list of draft certifications pending their review.

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def certification_queue(request):
    """
    Returns draft certification records visible to the requesting steward.
    Filtered to certifications created by learners within the steward's tenant scope.
    Requires competence_level >= 3.
    """
    if not is_level_3_or_above(request.user):
        return Response(
            {"detail": "Certification queue requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Fetch draft certifications scoped to steward's tenant path
    # The steward's tenant_path comes from their active UserPermission row
    steward_tenant_path = request.user.userprofile.active_tenant_path  # adjust to your model

    certifications = Record.objects.filter(
        record_type='certification',
        status='draft',
        tenant__path__startswith=steward_tenant_path  # adjust to your tenant FK structure
    ).order_by('created_at')

    # Use existing RecordSerializer from records app
    from records.serializers import RecordSerializer
    serializer = RecordSerializer(certifications, many=True)
    return Response(serializer.data)
```

Add to `learn/urls.py`:

```python
path('certifications/queue/', views.certification_queue, name='certification-queue'),
```

Commit: `git add . && git commit -m "feat: certification queue endpoint for stewards"`

---

## Phase B — Content Engine (Read-Only)

**Exit criteria:** Published programmes, courses, lessons are retrievable via DRF. Django learn views call the ORM directly (not via a JS service layer). Competence gating works server-side.

### Task B.1 — Verify Records engine serves learning content

The Records engine (`GET /api/records/`) already exists from Phase 2 of the main roadmap. This task confirms the filtering params needed by the Learn App work correctly.

**Required queries — verify each returns correct results:**

```bash
# All published programmes
GET /api/records/?record_family=learning&record_type=programme&status=active

# Programmes visible to a specific learner level
GET /api/records/?record_family=learning&record_type=programme&status=active&required_level_lte=2

# Courses in a programme (via relationship traversal — see Task B.2)
GET /api/records/?record_family=learning&record_type=course&status=active

# Submitted content (Level 5 review queue)
GET /api/records/?record_family=learning&status=submitted

# Lessons in a course
GET /api/records/?record_family=learning&record_type=lesson&status=active
```

If the Records DRF view does not support `required_level_lte` filtering, add it:

```python
# records/views.py — add to filter_queryset or filterset_fields
required_level_lte = request.query_params.get('required_level_lte')
if required_level_lte:
    queryset = queryset.filter(permissions__required_level__lte=required_level_lte)
```

Commit: `git add . && git commit -m "feat: records endpoint — required_level_lte filter for learn app"`

---

### Task B.2 — Curriculum endpoint (course list for a programme)

The curriculum is the set of `part_of` Relationships from courses to a programme.
Rather than forcing the JS client to traverse relationships manually, expose a
dedicated curriculum endpoint.

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programme_curriculum(request, programme_id):
    """
    Returns the ordered list of courses (and their lessons) for a programme.
    Traverses part_of Relationships: course → part_of → programme.
    Then for each course: lesson → part_of → course.
    """
    from records.models import Record, Relationship

    programme = get_object_or_404(
        Record,
        id=programme_id,
        record_family='learning',
        record_type='programme',
        status__in=['active', 'locked']
    )

    # Check learner competence gate
    required_level = programme.permissions.get('required_level', 1)
    user_level = request.user.userprofile.competence_level
    if user_level < required_level:
        return Response(
            {"detail": "Insufficient competence level to access this programme."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get all courses part_of this programme
    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids,
        record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id,
            relationship_type='part_of'
        ).values_list('from_record_id', flat=True)

        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked']
        ).order_by('created_at')

        from records.serializers import RecordSerializer
        curriculum.append({
            'course': RecordSerializer(course).data,
            'lessons': RecordSerializer(lessons, many=True).data
        })

    return Response({
        'programme': RecordSerializer(programme).data,
        'curriculum': curriculum
    })
```

Add to `learn/urls.py`:

```python
path('programmes/<uuid:programme_id>/curriculum/', views.programme_curriculum, name='programme-curriculum'),
```

Commit: `git add . && git commit -m "feat: curriculum endpoint — traverses part_of relationships"`

---

### Task B.3 — Django learn views + URL routing

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`
- Create: `~/ics/learn/templates/learn/` (template directory)

The Learn App UI is served by Django views that query the ORM directly and
pass context to templates. HTMX handles partial updates. No JS service layer.

**URL structure:**

```python
# learn/urls.py
from django.urls import path
from . import views, api_views

urlpatterns = [
    # API endpoints (DRF — consumed by HTMX and future mobile clients)
    path('health/', api_views.health, name='learn-health'),
    path('programmes/<uuid:programme_id>/curriculum/', api_views.programme_curriculum, name='programme-curriculum'),
    path('certifications/queue/', api_views.certification_queue, name='certification-queue'),
    path('certifications/<uuid:certification_id>/confirm/', api_views.confirm_certification, name='certification-confirm'),

    # Django template views (UI)
    path('', views.my_learning, name='learn-home'),
    path('programmes/', views.catalogue, name='learn-catalogue'),
    path('programmes/<uuid:programme_id>/', views.programme_detail, name='learn-programme'),
    path('lessons/<uuid:lesson_id>/', views.lesson_viewer, name='learn-lesson'),
    path('certifications/', views.certification_queue_view, name='learn-cert-queue'),
    path('author/', views.authorship, name='learn-author'),
    path('review/', views.review_queue, name='learn-review'),

    # HTMX partial endpoints (return HTML fragments, not full pages)
    path('htmx/enrol/<uuid:programme_id>/', views.htmx_enrol, name='htmx-enrol'),
    path('htmx/complete-lesson/<uuid:lesson_id>/', views.htmx_complete_lesson, name='htmx-complete-lesson'),
    path('htmx/confirm-cert/<uuid:cert_id>/', views.htmx_confirm_cert, name='htmx-confirm-cert'),
    path('htmx/approve-content/<uuid:record_id>/', views.htmx_approve_content, name='htmx-approve-content'),
]
```

**Rename existing DRF views file for clarity:**
- Rename: `learn/views.py` → `learn/api_views.py` (holds all DRF `@api_view` functions)
- Create: `learn/views.py` (holds all Django template views)

This keeps the API layer and the template layer cleanly separated in the same app.

Commit: `git add . && git commit -m "feat: learn app — Django URL structure, views/api_views split"`

---

## Phase C — Enrolment + Progress Tracking (UI)

**Exit criteria:** A learner can browse programmes, enrol, view their curriculum, mark lessons complete, and see progress bars update — all via Django templates and HTMX. No JS app file required.

### Task C.1 — Django template views (My Learning + Catalogue)

**Files:**
- Create: `~/ics/learn/views.py`
- Create: `~/ics/learn/templates/learn/base_learn.html`
- Create: `~/ics/learn/templates/learn/my_learning.html`
- Create: `~/ics/learn/templates/learn/catalogue.html`
- Create: `~/ics/learn/templates/learn/programme_detail.html`

**`learn/views.py` — core template views:**

```python
# learn/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from records.models import Record, Relationship
from activity.models import Activity


@login_required
def my_learning(request):
    """My Learning home — active enrolments and completed certifications."""
    user = request.user
    enrolments = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        status='in_progress',
        metadata__source_app='learn'
    ).order_by('-created_at')

    certifications = Record.objects.filter(
        record_type='certification',
        created_by=user,
        status='active'
    ).order_by('-updated_at')

    return render(request, 'learn/my_learning.html', {
        'enrolments': enrolments,
        'certifications': certifications,
    })


@login_required
def catalogue(request):
    """Programme catalogue — filtered by user competence level."""
    user_level = request.user.userprofile.competence_level
    programmes = Record.objects.filter(
        record_family='learning',
        record_type='programme',
        status='active'
    ).order_by('created_at')

    # Annotate each programme with locked status for the template
    for p in programmes:
        p.is_locked = user_level < (p.permissions.get('required_level', 1))

    return render(request, 'learn/catalogue.html', {
        'programmes': programmes,
        'user_level': user_level,
    })


@login_required
def programme_detail(request, programme_id):
    """Programme detail with curriculum and enrolment status."""
    user = request.user
    user_level = user.userprofile.competence_level

    programme = get_object_or_404(
        Record, id=programme_id,
        record_family='learning', record_type='programme',
        status__in=['active', 'locked']
    )

    required_level = programme.permissions.get('required_level', 1)
    if user_level < required_level:
        return render(request, 'learn/locked.html', {'programme': programme})

    # Build curriculum via part_of relationships
    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids, record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id, relationship_type='part_of'
        ).values_list('from_record_id', flat=True)
        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked']
        ).order_by('created_at')
        curriculum.append({'course': course, 'lessons': lessons})

    already_enrolled = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        metadata__programme_record_id=str(programme_id)
    ).exists()

    return render(request, 'learn/programme_detail.html', {
        'programme': programme,
        'curriculum': curriculum,
        'already_enrolled': already_enrolled,
    })


@login_required
def lesson_viewer(request, lesson_id):
    """Lesson viewer — renders lesson content with prev/next navigation."""
    lesson = get_object_or_404(
        Record, id=lesson_id,
        record_type__in=['lesson', 'assignment', 'quiz'],
        status__in=['active', 'locked']
    )

    # Find parent course via part_of relationship
    parent_rel = Relationship.objects.filter(
        from_record_id=lesson_id, relationship_type='part_of'
    ).first()
    course = None
    siblings = []
    if parent_rel:
        course = Record.objects.filter(id=parent_rel.to_record_id).first()
        if course:
            sibling_ids = Relationship.objects.filter(
                to_record_id=course.id, relationship_type='part_of'
            ).values_list('from_record_id', flat=True)
            siblings = list(Record.objects.filter(
                id__in=sibling_ids, status__in=['active', 'locked']
            ).order_by('created_at'))

    current_index = next((i for i, s in enumerate(siblings) if s.id == lesson.id), 0)
    prev_lesson = siblings[current_index - 1] if current_index > 0 else None
    next_lesson = siblings[current_index + 1] if current_index < len(siblings) - 1 else None

    return render(request, 'learn/lesson_viewer.html', {
        'lesson': lesson,
        'course': course,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    })
```

Commit: `git add . && git commit -m "feat: learn views — my_learning, catalogue, programme_detail, lesson_viewer"`

---

### Task C.2 — Base learn template + CSS

**Files:**
- Create: `~/ics/learn/templates/learn/base_learn.html`
- Create: `~/ics/frontend/assets/css/learn.css`

**`base_learn.html`** — extends the platform base template, adds HTMX and learn-specific structure:

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/learn.css' %}">
{% endblock %}

{% block extra_scripts %}
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
{% endblock %}
```

**`learn.css`** — identical to the original design. No changes to the design system. All CSS variables, mobile-first breakpoints, programme cards, progress bars, lesson viewer styles, and certification styles carry forward unchanged.

Commit: `git add . && git commit -m "feat: learn base template + learn.css"`

---

### Task C.3 — My Learning template

**Files:**
- Create: `~/ics/learn/templates/learn/my_learning.html`

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="learn-header">
  <h1>Learn</h1>
  <a href="{% url 'learn-catalogue' %}" class="btn-secondary">Browse Programmes</a>
</div>

{% if enrolments %}
  {% for enrolment in enrolments %}
  <div class="enrolment-card">
    <div class="enrolment-title">{{ enrolment.title }}</div>
    <div class="progress-bar-wrap">
      <div class="progress-bar" style="width:{{ enrolment.progress }}%"></div>
    </div>
    <span class="progress-label">{{ enrolment.progress }}% complete</span>
    <a href="{% url 'learn-programme' enrolment.metadata.programme_record_id %}"
       class="btn-primary">Continue</a>
  </div>
  {% endfor %}
{% else %}
  <div class="empty-state">
    <p>You are not enrolled in any programme yet.</p>
    <a href="{% url 'learn-catalogue' %}" class="btn-primary">Browse Programmes</a>
  </div>
{% endif %}

{% if certifications %}
  <h2>Completed</h2>
  {% for cert in certifications %}
  <div class="enrolment-card">
    <div class="enrolment-title">{{ cert.title }}</div>
    <span class="enrolled-badge">Certified</span>
  </div>
  {% endfor %}
{% endif %}
{% endblock %}
```

Commit: `git add . && git commit -m "feat: my_learning.html template"`

---

### Task C.4 — Catalogue + Programme detail templates

**Files:**
- Create: `~/ics/learn/templates/learn/catalogue.html`
- Create: `~/ics/learn/templates/learn/programme_detail.html`
- Create: `~/ics/learn/templates/learn/locked.html`

**`catalogue.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="learn-header">
  <a href="{% url 'learn-home' %}" class="btn-back">← My Learning</a>
  <h2>Programmes</h2>
</div>

<div class="programme-grid">
  {% for programme in programmes %}
  <div class="programme-card {% if programme.is_locked %}locked{% endif %}">
    <div class="programme-badge">
      {{ programme.metadata.qualification|default:"Programme" }}
    </div>
    <h3 class="programme-title">{{ programme.title }}</h3>
    <p class="programme-meta">
      {{ programme.metadata.duration_years|default:"?" }} year{{ programme.metadata.duration_years|pluralize }}
    </p>
    {% if programme.is_locked %}
      <span class="lock-indicator">
        Level {{ programme.permissions.required_level }} required
      </span>
    {% else %}
      <a href="{% url 'learn-programme' programme.id %}" class="btn-primary">View</a>
    {% endif %}
  </div>
  {% endfor %}
</div>
{% endblock %}
```

**`programme_detail.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="programme-detail">
  <a href="{% url 'learn-catalogue' %}" class="btn-back">← Programmes</a>
  <div class="programme-badge">{{ programme.metadata.qualification|default:"Programme" }}</div>
  <h2>{{ programme.title }}</h2>
  <p class="programme-description">{{ programme.content|default:programme.summary }}</p>
  <div class="programme-meta-row">
    <span>{{ programme.metadata.duration_years|default:"?" }} years</span>
    <span>Level {{ programme.permissions.required_level|default:1 }}</span>
  </div>

  {% if already_enrolled %}
    <span class="enrolled-badge">Enrolled</span>
  {% else %}
    <!-- HTMX enrolment — swaps button with confirmation in-place -->
    <button class="btn-primary enrol-btn"
            hx-post="{% url 'htmx-enrol' programme.id %}"
            hx-target="#enrol-section"
            hx-swap="outerHTML">
      Enrol in this Programme
    </button>
    <div id="enrol-section"></div>
  {% endif %}

  <div class="curriculum-list">
    <h3>Curriculum</h3>
    {% for item in curriculum %}
    <div class="course-block">
      <h4>{{ forloop.counter }}. {{ item.course.title }}</h4>
      <ul class="lesson-list">
        {% for lesson in item.lessons %}
        <li class="lesson-item">
          <span class="lesson-type-tag">{{ lesson.record_type }}</span>
          <a href="{% url 'learn-lesson' lesson.id %}">{{ lesson.title }}</a>
        </li>
        {% endfor %}
      </ul>
    </div>
    {% endfor %}
  </div>
</div>
{% endblock %}
```

Commit: `git add . && git commit -m "feat: catalogue.html + programme_detail.html templates"`

---

### Task C.5 — Lesson viewer template + HTMX complete button

**Files:**
- Create: `~/ics/learn/templates/learn/lesson_viewer.html`
- Create: `~/ics/learn/templates/learn/partials/lesson_complete_btn.html`
- Add HTMX view to `learn/views.py`

**`lesson_viewer.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="lesson-viewer">
  {% if course %}
    <a href="{% url 'learn-programme' course.id %}" class="btn-back">← Back to Course</a>
  {% endif %}
  <span class="lesson-type-tag">{{ lesson.record_type }}</span>
  <h2 class="lesson-title">{{ lesson.title }}</h2>

  <div class="lesson-content">
    {{ lesson.content|linebreaks }}
  </div>

  <div class="lesson-nav">
    {% if prev_lesson %}
      <a href="{% url 'learn-lesson' prev_lesson.id %}" class="btn-secondary">← Previous</a>
    {% else %}
      <span></span>
    {% endif %}

    <!-- HTMX complete button — replaces itself with a ✓ confirmation -->
    <div id="complete-section">
      {% include "learn/partials/lesson_complete_btn.html" %}
    </div>

    {% if next_lesson %}
      <a href="{% url 'learn-lesson' next_lesson.id %}" class="btn-secondary">Next →</a>
    {% else %}
      <span></span>
    {% endif %}
  </div>
</div>
{% endblock %}
```

**`partials/lesson_complete_btn.html`:**

```html
<button class="btn-primary complete-btn"
        hx-post="{% url 'htmx-complete-lesson' lesson.id %}"
        hx-target="#complete-section"
        hx-swap="outerHTML">
  Mark Complete
</button>
```

**HTMX views — add to `learn/views.py`:**

```python
@login_required
def htmx_enrol(request, programme_id):
    """HTMX: creates enrolment Activity, returns confirmation fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    user = request.user
    programme = get_object_or_404(Record, id=programme_id, record_type='programme')

    Activity.objects.create(
        activity_type='programme',
        title=f'Enrolment — {programme.title}',
        assigned_to=user,
        status='in_progress',
        progress=0,
        kgs_pathway='learning',
        metadata={
            'source_app': 'learn',
            'programme_record_id': str(programme_id)
        }
    )

    # Return a small HTML fragment — HTMX swaps it in place of the button
    return HttpResponse('<span class="enrolled-badge">Enrolled ✓</span>')


@login_required
def htmx_complete_lesson(request, lesson_id):
    """HTMX: marks lesson Activity complete, returns updated button fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    Activity.objects.filter(
        metadata__lesson_record_id=str(lesson_id),
        assigned_to=request.user
    ).update(status='completed', progress=100)

    # Return completed state fragment
    return HttpResponse(
        '<button class="btn-primary complete-btn completed" disabled>✓ Completed</button>'
    )
```

Commit: `git add . && git commit -m "feat: lesson_viewer.html + HTMX complete lesson + enrol views"`

---

## Phase D — Assessments

**Exit criteria:** Quiz and Assignment records render correctly in the lesson viewer. Submission marks the assessment activity complete via HTMX.

### Task D.1 — Quiz template + HTMX submission

Quiz questions live in `Record.custom_fields`. The lesson viewer template detects
`lesson.record_type == 'quiz'` and renders a form. Submission is an HTMX POST.

**Files:**
- Create: `~/ics/learn/templates/learn/partials/quiz.html`
- Add HTMX quiz submit view to `learn/views.py`

**`partials/quiz.html`:**

```html
<form hx-post="{% url 'htmx-submit-quiz' lesson.id %}"
      hx-target="#complete-section"
      hx-swap="outerHTML">
  {% csrf_token %}
  {% for q in lesson.custom_fields.questions %}
  <div class="quiz-question">
    <p>{{ q.text }}</p>
    {% if q.type == 'multiple_choice' %}
      {% for option in q.options %}
      <label class="quiz-option">
        <input type="radio" name="q_{{ q.id }}" value="{{ forloop.counter0 }}">
        {{ option }}
      </label>
      {% endfor %}
    {% else %}
      <textarea name="q_{{ q.id }}" class="quiz-text-answer" rows="3"></textarea>
    {% endif %}
  </div>
  {% endfor %}
  <button type="submit" class="btn-primary">Submit Quiz</button>
</form>
```

Add `htmx-submit-quiz` view to `learn/views.py` — marks assessment Activity
as completed and returns the completed state fragment.

### Task D.2 — Assignment submission template

Same HTMX pattern. Assignment form submits text via POST. The view creates a
child Record (`record_type: "note"`) linked to the assignment via a `references`
Relationship, then marks the task Activity complete.

Commit: `git add . && git commit -m "feat: learn app — quiz + assignment templates with HTMX submission"`

---

## Phase E — Certification + Competence Advancement (UI)

**Exit criteria:** Learner sees "Awaiting certification" when programme is 100% complete. Steward sees certification queue as a Django-rendered page. Steward confirms via HTMX. Learner's competence level advances.

### Task E.1 — Awaiting certification view

The Django signal (Task E.1 backend — unchanged) auto-creates the draft
Certification Record. The learner's My Learning page detects a draft certification
linked to their completed enrolment and shows an "Awaiting certification" banner.

Add to `my_learning.html`:

```html
{% if pending_certifications %}
  {% for cert in pending_certifications %}
  <div class="enrolment-card awaiting-cert">
    <div class="enrolment-title">{{ cert.title }}</div>
    <span class="cert-pending-badge">Awaiting Steward Confirmation</span>
  </div>
  {% endfor %}
{% endif %}
```

Update `my_learning` view to pass `pending_certifications` (draft certification
Records created by the current user).

### Task E.2 — Steward certification queue template + HTMX confirm

**Files:**
- Create: `~/ics/learn/templates/learn/certification_queue.html`
- Add `htmx_confirm_cert` view to `learn/views.py`

**`certification_queue.html`:**

```html
{% extends "learn/base_learn.html" %}
{% block content %}
<div class="learn-header"><h2>Certifications Pending</h2></div>

{% if certifications %}
  {% for cert in certifications %}
  <div class="cert-card" id="cert-{{ cert.id }}">
    <h4>{{ cert.title }}</h4>
    <p class="cert-meta">Submitted: {{ cert.created_at|date:"d M Y" }}</p>
    <textarea name="notes" placeholder="Notes (optional)"
              id="notes-{{ cert.id }}"></textarea>
    <button class="btn-primary"
            hx-post="{% url 'htmx-confirm-cert' cert.id %}"
            hx-target="#cert-{{ cert.id }}"
            hx-swap="outerHTML"
            hx-include="#notes-{{ cert.id }}">
      Confirm &amp; Advance Level
    </button>
  </div>
  {% endfor %}
{% else %}
  <p class="empty-state">No certifications pending.</p>
{% endif %}
{% endblock %}
```

**`htmx_confirm_cert` view** calls the existing `confirm_certification` logic
from `api_views.py` and returns a small HTML fragment confirming the action:

```python
@login_required
def htmx_confirm_cert(request, cert_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    # Reuse confirm_certification logic (extracted to a service function)
    # Returns fragment replacing the cert card with a confirmed state
    return HttpResponse(
        f'<div class="cert-card confirmed">'
        f'<span class="enrolled-badge">✓ Certification Confirmed</span>'
        f'</div>'
    )
```

Commit: `git add . && git commit -m "feat: learn app — certification queue template + HTMX confirm"`

---

## Phase F — Content Authorship + Handbook Review (UI)

**Exit criteria:** Level 4+ users can create and submit Programmes, Courses, and Lessons via Django forms. Level 5 users see a review queue and can approve content via HTMX.

### Task F.1 — Authorship views + templates (Level 4+)

**Files:**
- Create: `~/ics/learn/templates/learn/authorship.html`
- Create: `~/ics/learn/templates/learn/author_programme_form.html`
- Create: `~/ics/learn/templates/learn/author_course_form.html`
- Create: `~/ics/learn/templates/learn/author_lesson_form.html`
- Add authorship views to `learn/views.py`

Django `CreateView` or function-based views gated to `competence_level >= 4`.
Each form creates a Record with the appropriate `record_family`, `record_type`,
and `status: "draft"`. A "Submit for Review" button PATCHes the record status
to `"submitted"` — this can be a standard Django form POST (no HTMX needed here
as it's a full-page action).

Core form fields per content type are unchanged from the original design spec
(Programme: title, qualification, description, duration, pathways; Course: title,
description, parent programme; Lesson: title, content textarea, type, parent course).

### Task F.2 — Handbook review queue template + HTMX approve (Level 5)

**Files:**
- Create: `~/ics/learn/templates/learn/review_queue.html`
- Add `htmx_approve_content` view to `learn/views.py`

**`review_queue.html`:**

```html
{% extends "learn/base_learn.html" %}
{% block content %}
<div class="learn-header"><h2>Review Queue</h2></div>

{% if items %}
  {% for item in items %}
  <div class="review-card" id="review-{{ item.id }}">
    <span class="lesson-type-tag">{{ item.record_type }}</span>
    <h4>{{ item.title }}</h4>
    <p class="cert-meta">Submitted: {{ item.updated_at|date:"d M Y" }}</p>
    <div class="review-actions">
      <button class="btn-primary"
              hx-post="{% url 'htmx-approve-content' item.id %}"
              hx-target="#review-{{ item.id }}"
              hx-swap="outerHTML">
        Approve
      </button>
      <button class="btn-secondary"
              hx-post="{% url 'htmx-return-content' item.id %}"
              hx-target="#review-{{ item.id }}"
              hx-swap="outerHTML">
        Return to Draft
      </button>
    </div>
  </div>
  {% endfor %}
{% else %}
  <p class="empty-state">No items pending review.</p>
{% endif %}
{% endblock %}
```

`htmx_approve_content` view sets `record.status = 'active'`, gated to Level 5.
Returns a small confirmation fragment replacing the review card.

Commit: `git add . && git commit -m "feat: learn app — authorship forms + handbook review queue templates"`

---

## Phase G — UI Polish + Role-Aware Navigation

**Exit criteria:** Learn App navigation adapts to user role server-side. Pathway banner shows for enrolled learners. Smoke test on mobile passes.

### Task G.1 — Role-aware navigation (server-side)

Role-aware tabs are rendered in `base_learn.html` using the Django request context.
No JS required — the template checks `request.user.userprofile.competence_level`
and shows the appropriate navigation items:

```html
<!-- In base_learn.html nav section -->
<nav class="learn-tab-row">
  <a href="{% url 'learn-home' %}">My Learning</a>
  <a href="{% url 'learn-catalogue' %}">Browse</a>
  {% if request.user.userprofile.competence_level >= 3 %}
    <a href="{% url 'learn-cert-queue' %}">Certifications</a>
  {% endif %}
  {% if request.user.userprofile.competence_level >= 4 %}
    <a href="{% url 'learn-author' %}">Author</a>
  {% endif %}
  {% if request.user.userprofile.competence_level >= 5 %}
    <a href="{% url 'learn-review' %}">Review Queue</a>
  {% endif %}
</nav>
```

| Level | Visible tabs |
|---|---|
| 0b (Seeker) | Browse only |
| 1–2 (Member/Disciple) | My Learning, Browse |
| 3 (Branch-Steward) | My Learning, Browse, Certifications |
| 4 (Senior Steward) | My Learning, Browse, Certifications, Author |
| 5 (Architect) | All above + Review Queue |

### Task G.2 — Pathway banner

Add to `my_learning.html` above the enrolment list, populated from the active
enrolment Activity's `kgs_pathway` and the linked Programme Record's metadata:

```html
{% if active_pathway %}
<div class="pathway-banner">
  <span class="pathway-label">{{ active_pathway }}</span>
  <span class="pathway-programme">{{ active_qualification }} · Year {{ active_year }}</span>
</div>
{% endif %}
```

The `my_learning` view resolves these values from the user's active enrolment
Activity before passing them to the template as context.

### Task G.3 — Smoke test checklist

Before closing Phase G, verify manually on mobile:

- [ ] Seeker can browse programmes, sees lock on locked programmes
- [ ] Member can enrol, see progress bar, mark a lesson complete
- [ ] Progress bar updates after lesson completion (HTMX swap visible)
- [ ] Programme at 100% shows "Awaiting certification" state on My Learning page
- [ ] Branch-Steward sees certification queue with pending item
- [ ] Steward confirms via HTMX → learner's competence level increments in DB
- [ ] Level 4 user can create a Programme and submit for review
- [ ] Level 5 user sees submitted Programme in review queue and can approve
- [ ] Approved Programme appears in public catalogue
- [ ] Role-aware nav tabs show/hide correctly for each level
- [ ] Pathway banner displays for enrolled learner

Commit: `git add . && git commit -m "feat: learn app — role-aware nav, pathway banner, smoke test pass"`

---

## Django Endpoint Summary

All endpoints required by the Learn App, in one place:

```
# Existing Records endpoints (already built — verify filters work)
GET  /api/records/?record_family=learning&record_type=programme&status=active
GET  /api/records/?record_family=learning&status=submitted
GET  /api/records/{id}/
PATCH /api/records/{id}/     (status changes — gated by role)

# Existing Activity endpoints (already built)
POST  /api/activities/
PATCH /api/activities/{id}/
GET   /api/activities/?activity_type=programme&assigned_to={id}

# New Learn endpoints (built in Phase A)
GET   /api/learn/health/
GET   /api/learn/programmes/{id}/curriculum/
GET   /api/learn/certifications/queue/
POST  /api/learn/certifications/{id}/confirm/
```

---

## File Map (Learn App additions)

```
/learn/                              ← NEW Django app
  __init__.py
  apps.py
  models.py                          ← CertificationConfirmation only
  serializers.py
  api_views.py                       ← DRF endpoints (health, curriculum, cert queue, cert confirm)
  views.py                           ← Django template views + HTMX partial views
  urls.py                            ← API routes + template view routes + HTMX routes
  signals.py                         ← auto-create certification on programme complete
  templates/
    learn/
      base_learn.html                ← extends base.html, loads HTMX, learn.css
      my_learning.html               ← My Learning home
      catalogue.html                 ← Programme catalogue
      programme_detail.html          ← Programme detail + curriculum
      lesson_viewer.html             ← Lesson content + nav
      certification_queue.html       ← Steward cert queue
      authorship.html                ← Level 4 authorship home
      author_programme_form.html     ← Create programme form
      author_course_form.html        ← Create course form
      author_lesson_form.html        ← Create lesson form
      review_queue.html              ← Level 5 Handbook review queue
      locked.html                    ← Competence gate placeholder
      partials/
        lesson_complete_btn.html     ← HTMX complete button fragment
        quiz.html                    ← Quiz form fragment

/activity/
  signals.py                         ← MODIFIED: add programme completion handler

/accounts/serializers.py             ← MODIFIED: competence_level read-only note

/frontend/assets/css/
  learn.css                          ← NEW — unchanged from original design spec
```

**Note:** `learn.html`, `learn-app.js`, and `learn.service.js` are **not created**.
The UI is fully served by Django views and templates. HTMX replaces the JS
interaction layer. `storage.js` is retained for theme/UI state only.

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|---|---|---|---|
| A | Django `learn` app, `CertificationConfirmation` model, DRF endpoints | Phases 0–4 done | `/api/learn/health/` 200. Confirm endpoint works. |
| B | Records endpoint filters verified, curriculum endpoint, URL structure, views/api_views split | Phase A done | All DRF queries return correct data. URL routing confirmed. |
| C | Django template views, base template, My Learning, Catalogue, Programme detail, Lesson viewer, `learn.css` | Phase B done | Learner can enrol (HTMX) and mark lessons complete (HTMX) |
| D | Quiz template + HTMX submission, Assignment submission template | Phase C done | Assessments render and submit via HTMX |
| E | Certification auto-creation signal, steward queue template, HTMX confirm | Phase D done | Steward confirms via HTMX; `competence_level` increments in DB |
| F | Authorship forms (Level 4+), Handbook review queue template, HTMX approve (Level 5) | Phase E done | Content can be authored, submitted, approved |
| G | Role-aware nav (server-side), pathway banner, mobile smoke test | Phase F done | Full smoke test checklist passes on mobile |

---

## Deferred (Post-MVP)

- Rich text editor (TipTap or similar) for lesson authorship — markdown textarea suffices for MVP
- Quiz auto-grading with score display
- Assignment peer review
- Paraclete "continue your lesson" integration (Phase 6 of main roadmap)
- Learning analytics dashboard (completion rates per programme)
- Offline lesson caching (service worker)
- Video lessons (`record_type: "video_lesson"` — deferred with Video/Live app)
- Programme ordering / sequencing UI (drag-and-drop curriculum builder)


---

# ICS Community App — System Design & Build Roadmap

> **UI Architecture:** Django templates + HTMX throughout.
> All UI is server-rendered. HTMX handles form submissions, member list updates,
> and partial refreshes. `storage.js` is retained for UI state (theme, session token) only.

> **Data Contract reference:** `2026-04-08-ics-platform-data-contract_v8.md` —
> all schemas and patterns in this document originate from Parts 2, 3, 4, 11, and 14
> of that contract. Read the contract before implementing.

**Goal:** Build the ICS Community App — the digital expression of KGS Pillar 6
(Communities & Networks) — enabling members to see and experience their community,
and stewards to manage membership, gatherings, and announcements within their tenant scope.

**Architecture:** Django + DRF backend with a dedicated `community` Django app (to be
scaffolded). The Community App adds Django template views and HTMX interactions on top
of the existing Records, Activity, and Identity engines. It owns **no models** of its
own in MVP — it is a UI and transaction coordination layer. One model is stubbed
(`MembershipRequest`) but not wired to UI until Phase 2.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX,
`community.css` (mobile-first, CSS variables).

---

## System Overview

### The Community Stack

```
KGS Layer          Pillar 6 — Communities & Networks
                   ↓ expressed as
Structural Layer   Sceptre Community (church_node Tenant)
                   ↓ populated by
Identity Layer     UserPermission (membership rows with metadata)
                   ↓ governed through
Content Layer      community/announcement Record — broadcasts to members
                   community/gathering Record — scheduled events
                   ↓ gathering also writes
Execution Layer    activity/event Activity (source_app:'community')
                   ↓ feeds into
Calendar App       GET /api/calendar/events/?source_app=community
                   ↓ and eventually
Dashboard          Upcoming gatherings widget, community pulse
```

### Two-surface model

```
Community App
  │
  ├── "My Community"  (member surface — Level 1+)
  │     Scope:  UserPermission rows where user_id = request.user, is_active = True
  │     Shows:  Active tenant(s), formation stage, service order, shepherd,
  │             upcoming gatherings (30 days), latest announcements, gifts summary
  │
  └── "Community Management"  (steward surface — Level 3+)
        Scope:  UserPermission.tenant_path LIKE '{steward.scope_path}%'
        Shows:  Member directory, formation pipeline, member profile,
                announcement management, gathering management,
                pastoral assignments, service order placement
```

### User roles in the Community App

| Role | What they can do |
|---|---|
| Seeker (0b) | No access — no tenant membership |
| Member (Level 1) | My Community: own tenant(s), gatherings, announcements |
| Disciple (Level 2) | My Community + limited directory (names and orders only) |
| Branch-Steward (Level 3) | Full My Community + full Management for their branch |
| Senior Steward (Level 4+) | All above + multi-branch directory across their scope |
| Architect (Level 5) | All above + cross-tenant visibility |

---

## Feature List (All Features — Unphased)

### F1 — My Community Surface

- Community header: tenant name, tier badge, description, logo
- Formation stage card:
  - Competence level label ("Foundational Disciple", "Active Contributor", etc.)
  - KGS Participation stage ("Formation", "Alignment", "Service", etc.)
  - Visual progress indicator (level 1–5 steps)
- Shepherd card: display_name of shepherd (if `UserPermission.metadata.shepherd_id` is set)
- Service order card: current service order placement (if `metadata.service_order` is set)
- Upcoming gatherings list (next 30 days via Calendar endpoint, source_app:'community')
  - Format badge: in_person / digital / hybrid
  - Stream link (if `custom_fields.stream_url` present)
  - Location (if `custom_fields.location` present)
- Latest announcements (most recent 5, record_type:'announcement', visibility:'tenant')
- Gifts register summary: count of active gifts with link to Activity App gifts register

### F2 — Member Directory (Level 3+ Management Surface)

- Searchable list: all active members within steward's scope_path
  - Search by display_name (HTMX typeahead)
  - Filter by: service order (dropdown), formation level (radio), shepherd (dropdown)
- Member card: avatar, display_name, competence level badge, service order label,
  tenant name (for multi-branch stewards)
- Tap/click → Member Profile detail
- Export: deferred (post-MVP)

### F3 — Formation Pipeline (Level 3+ Management Surface)

- Visual pipeline: members grouped by competence level
  - Columns: Seeker (0b) | Member (L1) | Disciple (L2) | Steward (L3) | Senior (L4) | Architect (L5)
  - Count per stage, member thumbnails/names within each column
- Pipeline shows who is "stuck" at each stage (no recent Learn activity or certification)
- Link to member profile for direct pastoral action

### F4 — Member Profile (Level 3+ Management Surface)

- Full member detail: avatar, display_name, email (Level 3+), competence level,
  join date, service order, shepherd assignment
- Formation history: competence level progression (read from Learn certifications
  via `GET /api/records/?record_family=learning&record_type=certification&created_by={id}`)
- Gifts summary: active gifts from Activity App gifts register
- Actions:
  - Assign/change shepherd (HTMX — PATCH UserPermission.metadata.shepherd_id)
  - Set/change service order (HTMX — PATCH UserPermission.metadata.service_order)
  - Deactivate membership (HTMX — PATCH UserPermission.is_active = false, with confirmation)

### F5 — Announcement Management (Level 3+)

- Announcement list: all active announcements for the steward's tenant
  - Sorted by created_at descending
  - Status badges: active / archived
- Create announcement: HTMX form
  - Fields: title, content (markdown textarea), tenant selector (if multi-branch steward)
  - Visibility is always 'tenant' (no choice — all member announcements are tenant-scoped)
  - On submit: POST /api/records/ with record_family:'community', record_type:'announcement'
- Archive announcement: HTMX toggle (PATCH status:'archived')
- Announcements appear on My Community surface for Level 1+ members

### F6 — Gathering Management (Level 3+)

- Gathering list: all active and upcoming gatherings for the steward's tenant
  - Sorted by custom_fields.scheduled_at ascending
  - Format badge: in_person / digital / hybrid
  - Status: upcoming / past / cancelled
- Create gathering: HTMX form (dual-write — see Part 14.4 of data contract)
  - Fields: title, description, format (in_person | digital | hybrid),
    scheduled_at (datetime picker), location (shown if format != digital),
    stream_url (shown if format != in_person), capacity (optional)
  - On submit: dual-write transaction (gathering Record + event Activity + Relationship)
  - On success: HTMX swaps gathering list with new card included
- Cancel gathering: HTMX confirmation → PATCH Record status:'cancelled' +
  PATCH Activity status:'cancelled' (transaction.atomic)
- Gatherings feed the Calendar App automatically via the event Activity

### F7 — Pastoral Assignment (Level 3+)

- Set shepherd on a member's profile: HTMX typeahead to select from Level 3+
  users within scope → PATCH UserPermission.metadata.shepherd_id
- Unset shepherd: clear button → PATCH shepherd_id: null
- Shepherd's flock view (optional — deferred if time): filtered member directory
  showing all members whose shepherd_id = request.user.id

### F8 — Service Order Placement (Level 3+)

- Set service order on a member's profile: dropdown of the 24 KGS Service Orders
  (hardcoded list — not a DB table in MVP) → PATCH UserPermission.metadata.service_order
- Clear placement: clear button → PATCH service_order: null
- The 24 Service Orders list is defined in community/constants.py and rendered
  as a select widget — consistent with the same free-text label used in the
  Activity App gifts register

### F9 — Gifts Register Cross-View (Level 3+)

- On the member profile, display a read-only summary of the member's gifts:
  `GET /api/activities/?activity_type=skill&created_by={member_id}&tenant_id={tenant_id}`
- Shows: gift title, KGS pathway, self-assessed competence %, service order label
- Link to Activity App team gifts register for full view
- No write access from Community App — gifts are owned by the Activity App

### F10 — Paraclete Integration Endpoint (Backend)

Community data available to Paraclete at Phase 6:

```
GET /api/calendar/events/?source_app=community&tenant_id={id}
    &from={today}&to={+7days}
    → upcoming gatherings for digest
```

Paraclete uses this to surface "Upcoming gathering: Sunday Service — in 2 days"
in the daily digest. No new endpoint required — Calendar endpoint already supports
this filter.

---

## Build Phases

### Phase A — Community App Scaffold + Health Check

*Entry requirement: Phases 0–4 of main roadmap complete. Records, Activity, and
Identity engines all have working DRF endpoints.*

#### Task A.1 — Django app scaffold

```bash
cd ~/ics
python manage.py startapp community
```

Register in `INSTALLED_APPS`:
```python
# ics_project/settings/base.py
INSTALLED_APPS = [
    ...
    'community',
]
```

#### Task A.2 — MembershipRequest model (stub — not wired to UI)

```python
# community/models.py
import uuid
from django.conf import settings
from django.db import models


class MembershipRequest(models.Model):
    """
    Deferred — Phase 2 of Community App.
    Stubbed here so migration exists and Phase 2 requires no schema change.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id   = models.UUIDField()
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='membership_requests_created'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='membership_requests_made'
    )
    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    status      = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')],
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='membership_requests_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note        = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'community_membership_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"MembershipRequest({self.user_id} → {self.tenant_id}, {self.status})"
```

```bash
python manage.py makemigrations community
python manage.py migrate
```

#### Task A.3 — Service order constants

```python
# community/constants.py
KGS_SERVICE_ORDERS = [
    # A — Apostolic & Spiritual Ministry
    ("Order of Apostolic Service",     "Apostolic & Spiritual Ministry"),
    ("Order of Prophetic Ministry",    "Apostolic & Spiritual Ministry"),
    ("Order of Teaching and Doctrine", "Apostolic & Spiritual Ministry"),
    ("Order of Prayer and Intercession","Apostolic & Spiritual Ministry"),
    # B — Leadership & Governance Support
    ("Order of Governance Support",    "Leadership & Governance Support"),
    ("Order of Strategic Coordination","Leadership & Governance Support"),
    ("Order of Leadership Assistance", "Leadership & Governance Support"),
    ("Order of Communication and Alignment","Leadership & Governance Support"),
    # C — Formation & Teaching
    ("Order of Discipleship Facilitation","Formation & Teaching"),
    ("Order of Training and Instruction",  "Formation & Teaching"),
    ("Order of Mentorship and Coaching",   "Formation & Teaching"),
    ("Order of Curriculum Development",    "Formation & Teaching"),
    # D — Mission & Outreach
    ("Order of Evangelism",            "Mission & Outreach"),
    ("Order of Mission Teams",         "Mission & Outreach"),
    ("Order of Community Outreach",    "Mission & Outreach"),
    ("Order of Expansion and Planting","Mission & Outreach"),
    # E — Community Life & Care
    ("Order of Pastoral Care",         "Community Life & Care"),
    ("Order of Community Building",    "Community Life & Care"),
    ("Order of Hospitality and Welcome","Community Life & Care"),
    ("Order of Welfare and Support",   "Community Life & Care"),
    # F — Operations & Stewardship
    ("Order of Administration",        "Operations & Stewardship"),
    ("Order of Resource Management",   "Operations & Stewardship"),
    ("Order of Logistics and Events",  "Operations & Stewardship"),
    ("Order of Media and Communication","Operations & Stewardship"),
]

KGS_SERVICE_ORDER_CHOICES = [(o[0], o[0]) for o in KGS_SERVICE_ORDERS]

KGS_PARTICIPATION_STAGES = {
    0: ("Seeker",      "Connection"),
    1: ("Member",      "Formation"),
    2: ("Disciple",    "Alignment"),
    3: ("Steward",     "Service"),
    4: ("Senior Steward", "Leadership"),
    5: ("Architect",   "Apostolic Stewardship"),
}

KGS_COMPETENCE_LABELS = {
    0: "Seeker",
    1: "Foundational Disciple",
    2: "Active Contributor",
    3: "Functional Minister",
    4: "Leader",
    5: "Apostolic Steward",
}
```

#### Task A.4 — URL structure and health endpoint

```python
# community/urls.py
from django.urls import path
from . import views, api_views

urlpatterns = [
    # Health
    path('api/community/health/', api_views.community_health, name='community-health'),

    # Template views — My Community surface
    path('community/', views.my_community, name='community-home'),

    # Template views — Management surface (Level 3+)
    path('community/management/', views.management_home, name='community-management'),
    path('community/management/members/', views.member_directory, name='community-members'),
    path('community/management/members/<uuid:member_id>/', views.member_profile, name='community-member-profile'),
    path('community/management/pipeline/', views.formation_pipeline, name='community-pipeline'),

    # HTMX partials
    path('community/htmx/announcement/create/', views.htmx_create_announcement, name='htmx-create-announcement'),
    path('community/htmx/announcement/<uuid:record_id>/archive/', views.htmx_archive_announcement, name='htmx-archive-announcement'),
    path('community/htmx/gathering/create/', views.htmx_create_gathering, name='htmx-create-gathering'),
    path('community/htmx/gathering/<uuid:record_id>/cancel/', views.htmx_cancel_gathering, name='htmx-cancel-gathering'),
    path('community/htmx/member/<uuid:permission_id>/shepherd/', views.htmx_set_shepherd, name='htmx-set-shepherd'),
    path('community/htmx/member/<uuid:permission_id>/order/', views.htmx_set_order, name='htmx-set-order'),
    path('community/htmx/member/<uuid:permission_id>/deactivate/', views.htmx_deactivate_member, name='htmx-deactivate-member'),
    path('community/htmx/members/search/', views.htmx_member_search, name='htmx-member-search'),
    path('community/htmx/announcements/', views.htmx_announcement_list, name='htmx-announcement-list'),
]
```

Wire into root URLs:

```python
# ics_project/urls.py
urlpatterns = [
    ...
    path('', include('community.urls')),
]
```

```python
# community/api_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def community_health(request):
    return Response({'status': 'ok', 'app': 'community'})
```

```bash
git add . && git commit -m "feat: community app scaffold — model stub, constants, URLs, health check"
```

---

### Phase B — Django Views + Base Template + CSS

*Entry requirement: Phase A complete.*

#### Task B.1 — community.css

```css
/* frontend/assets/css/community.css */

/* ── Community surface layout ─────────────────────────────────── */
.community-surface {
  padding: 16px;
  max-width: 600px;
  margin: 0 auto;
}

/* ── Community header card ────────────────────────────────────── */
.community-header {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.community-logo {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.community-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.community-tier { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* ── Formation stage card ─────────────────────────────────────── */
.formation-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}
.formation-stage-label {
  font-size: 13px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}
.formation-level-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}
.formation-participation {
  font-size: 13px;
  color: var(--primary);
  margin-top: 2px;
}
.formation-steps {
  display: flex;
  gap: 6px;
  margin-top: 12px;
}
.formation-step {
  height: 6px;
  flex: 1;
  border-radius: 3px;
  background: var(--border);
}
.formation-step.active { background: var(--primary); }

/* ── Info card (shepherd, service order) ──────────────────────── */
.info-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.info-card-icon { font-size: 20px; flex-shrink: 0; }
.info-card-label { font-size: 12px; color: var(--text-secondary); }
.info-card-value { font-size: 14px; font-weight: 500; color: var(--text-primary); }

/* ── Section heading ──────────────────────────────────────────── */
.section-heading {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 16px 0 8px;
}

/* ── Gathering card ───────────────────────────────────────────── */
.gathering-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.gathering-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.gathering-meta { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.gathering-format {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  margin-top: 6px;
}
.format-in_person  { background: var(--success-light); color: var(--success); }
.format-digital    { background: var(--primary-light); color: var(--primary); }
.format-hybrid     { background: var(--warning-light); color: var(--warning); }
.gathering-stream-link {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}

/* ── Announcement card ────────────────────────────────────────── */
.announcement-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.announcement-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.announcement-content { font-size: 13px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5; }
.announcement-date { font-size: 11px; color: var(--text-tertiary); margin-top: 6px; }

/* ── Member card (directory) ──────────────────────────────────── */
.member-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}
.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  flex-shrink: 0;
}
.member-name  { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.member-meta  { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* ── Formation pipeline ───────────────────────────────────────── */
.pipeline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.pipeline-col {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
}
.pipeline-col-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.pipeline-count {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
  line-height: 1;
}
.pipeline-names {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 6px;
  line-height: 1.5;
}

/* ── Form cards ───────────────────────────────────────────────── */
.community-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 16px;
  margin-bottom: 16px;
}
.form-field { margin-bottom: 14px; }
.form-field label { font-size: 13px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 4px; }
.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--background);
  color: var(--text-primary);
  font-size: 14px;
}
.format-conditional { display: none; }
.format-conditional.visible { display: block; }

/* ── Gifts summary (read-only cross-app) ──────────────────────── */
.gifts-summary {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.gifts-count { font-size: 22px; font-weight: 700; color: var(--primary); }
.gifts-label { font-size: 12px; color: var(--text-secondary); }

/* ── Buttons ──────────────────────────────────────────────────── */
.btn-primary {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
}
.btn-secondary {
  background: transparent;
  color: var(--primary);
  border: 1.5px solid var(--primary);
  border-radius: 8px;
  padding: 9px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
}
.btn-danger {
  background: var(--error-light);
  color: var(--error);
  border: none;
  border-radius: 8px;
  padding: 9px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn-sm { padding: 6px 12px; font-size: 12px; width: auto; }

/* ── Empty state ──────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* ── HTMX indicator ───────────────────────────────────────────── */
.htmx-indicator { opacity: 0; transition: opacity 0.2s; }
.htmx-request .htmx-indicator { opacity: 1; }

/* ── Desktop breakpoint ───────────────────────────────────────── */
@media (min-width: 768px) {
  .community-surface { padding: 24px; }
  .pipeline-grid { grid-template-columns: repeat(6, 1fr); }
}
```

#### Task B.2 — Base community template

```html
<!-- community/templates/community/base_community.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'assets/css/community.css' %}">
{% endblock %}

{% block content %}
<div class="community-surface">
  {% block community_content %}{% endblock %}
</div>
{% endblock %}
```

#### Task B.3 — Stub views file

```python
# community/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db import transaction
import requests

from .constants import (
    KGS_SERVICE_ORDERS, KGS_SERVICE_ORDER_CHOICES,
    KGS_PARTICIPATION_STAGES, KGS_COMPETENCE_LABELS
)


def _require_level(request, min_level):
    """Return True if the user meets the minimum competence level."""
    return request.user.userprofile.competence_level >= min_level


@login_required
def my_community(request):
    """My Community — member surface."""
    return render(request, 'community/my_community.html', {})


@login_required
def management_home(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/management.html', {})


@login_required
def member_directory(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/member_directory.html', {})


@login_required
def member_profile(request, member_id):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/member_profile.html',
                  {'member_id': member_id})


@login_required
def formation_pipeline(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/formation_pipeline.html', {})
```

```bash
git add . && git commit -m "feat: community app — base template, CSS, stub views, URL routing"
```

---

### Phase C — My Community Surface (UI)

*Entry requirement: Phase B complete.*

#### Task C.1 — My Community view (full implementation)

```python
# community/views.py — replace my_community stub

from django.utils import timezone
from datetime import timedelta


@login_required
def my_community(request):
    """My Community — member surface. Level 1+ only."""
    user = request.user
    level = user.userprofile.competence_level

    if level < 1:
        # Seekers have no tenant membership
        return render(request, 'community/seeker_gate.html')

    # 1 — Get all active UserPermission rows for this user
    base_url = request.build_absolute_uri('/')[:-1]
    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true'},
        headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
    )
    permissions = perms_resp.json().get('results', []) if perms_resp.ok else []

    # 2 — For the primary tenant (first active permission), load context
    primary_perm = permissions[0] if permissions else None
    shepherd = None
    service_order = None
    announcements = []
    upcoming_gatherings = []
    gifts_count = 0

    if primary_perm:
        tenant_id = primary_perm['tenant_id']
        meta = primary_perm.get('metadata', {})
        service_order = meta.get('service_order')

        # Shepherd
        shepherd_id = meta.get('shepherd_id')
        if shepherd_id:
            sh_resp = requests.get(
                f'{base_url}/api/auth/users/{shepherd_id}/',
                headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
            )
            shepherd = sh_resp.json() if sh_resp.ok else None

        # Announcements (latest 5)
        ann_resp = requests.get(
            f'{base_url}/api/records/',
            params={
                'record_family': 'community',
                'record_type': 'announcement',
                'tenant_id': tenant_id,
                'status': 'active',
                'ordering': '-created_at',
                'page_size': 5,
            },
            headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
        )
        announcements = ann_resp.json().get('results', []) if ann_resp.ok else []

        # Upcoming gatherings (next 30 days via Calendar endpoint)
        now = timezone.now()
        cal_resp = requests.get(
            f'{base_url}/api/calendar/events/',
            params={
                'source_app': 'community',
                'tenant_id': tenant_id,
                'from': now.date().isoformat(),
                'to': (now + timedelta(days=30)).date().isoformat(),
            },
            headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
        )
        upcoming_gatherings = cal_resp.json() if cal_resp.ok else []

        # Gifts count (Activity App cross-read)
        gifts_resp = requests.get(
            f'{base_url}/api/activities/',
            params={
                'activity_type': 'skill',
                'created_by': str(user.id),
                'tenant_id': tenant_id,
                'status': 'active',
            },
            headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
        )
        gifts_count = gifts_resp.json().get('count', 0) if gifts_resp.ok else 0

    stage_info = KGS_PARTICIPATION_STAGES.get(level, ('Member', 'Formation'))
    level_label = KGS_COMPETENCE_LABELS.get(level, 'Member')

    return render(request, 'community/my_community.html', {
        'permissions':          permissions,
        'primary_perm':         primary_perm,
        'shepherd':             shepherd,
        'service_order':        service_order,
        'announcements':        announcements,
        'upcoming_gatherings':  upcoming_gatherings,
        'gifts_count':          gifts_count,
        'level':                level,
        'level_label':          level_label,
        'stage_name':           stage_info[0],
        'participation_stage':  stage_info[1],
        'participation_steps':  range(1, 6),  # levels 1–5
    })
```

#### Task C.2 — My Community template

```html
<!-- community/templates/community/my_community.html -->
{% extends "community/base_community.html" %}

{% block community_content %}

{% if not primary_perm %}
<div class="empty-state">
  <p>You are not yet part of a community.</p>
  <p style="margin-top:8px;font-size:12px">
    Contact a steward to be added to your local Sceptre Community.
  </p>
</div>
{% else %}

<!-- Community header -->
{% with tenant=primary_perm.tenant %}
<div class="community-header">
  <div class="community-logo">🏛</div>
  <div>
    <div class="community-name">{{ primary_perm.tenant_name|default:"My Community" }}</div>
    <div class="community-tier">{{ primary_perm.tenant_tier|default:"Church Node"|title }}</div>
  </div>
</div>
{% endwith %}

<!-- Formation stage -->
<div class="formation-card">
  <div class="formation-stage-label">Formation Stage</div>
  <div class="formation-level-name">{{ level_label }}</div>
  <div class="formation-participation">{{ participation_stage }}</div>
  <div class="formation-steps">
    {% for step in participation_steps %}
    <div class="formation-step {% if step <= level %}active{% endif %}"></div>
    {% endfor %}
  </div>
</div>

<!-- Shepherd -->
{% if shepherd %}
<div class="info-card">
  <div class="info-card-icon">🤝</div>
  <div>
    <div class="info-card-label">Your Shepherd</div>
    <div class="info-card-value">{{ shepherd.display_name }}</div>
  </div>
</div>
{% endif %}

<!-- Service order -->
{% if service_order %}
<div class="info-card">
  <div class="info-card-icon">⚙️</div>
  <div>
    <div class="info-card-label">Service Placement</div>
    <div class="info-card-value">{{ service_order }}</div>
  </div>
</div>
{% endif %}

<!-- Gifts summary -->
<div class="gifts-summary">
  <div class="gifts-count">{{ gifts_count }}</div>
  <div class="gifts-label">
    Active gift{{ gifts_count|pluralize }} registered
    — <a href="/activity/gifts/" style="color:var(--primary)">View in Activity App</a>
  </div>
</div>

<!-- Upcoming gatherings -->
<div class="section-heading">Upcoming Gatherings</div>
{% if upcoming_gatherings %}
{% for gathering in upcoming_gatherings %}
<div class="gathering-card">
  <div class="gathering-title">{{ gathering.title }}</div>
  <div class="gathering-meta">{{ gathering.scheduled_at|slice:":16"|replace:"T":" " }}</div>
  {% with fmt=gathering.custom_fields.format|default:"in_person" %}
  <span class="gathering-format format-{{ fmt }}">
    {{ fmt|replace:"_":" "|title }}
  </span>
  {% endwith %}
  {% if gathering.custom_fields.location %}
  <div class="gathering-meta" style="margin-top:6px">📍 {{ gathering.custom_fields.location }}</div>
  {% endif %}
  {% if gathering.custom_fields.stream_url %}
  <a class="gathering-stream-link"
     href="{{ gathering.custom_fields.stream_url }}"
     target="_blank" rel="noopener">
    🔗 Join Online
  </a>
  {% endif %}
</div>
{% endfor %}
{% else %}
<div class="empty-state" style="padding:20px 0">No gatherings scheduled in the next 30 days.</div>
{% endif %}

<!-- Announcements -->
<div class="section-heading">Announcements</div>
{% if announcements %}
{% for ann in announcements %}
<div class="announcement-card">
  <div class="announcement-title">{{ ann.title }}</div>
  <div class="announcement-content">{{ ann.content|truncatechars:180 }}</div>
  <div class="announcement-date">{{ ann.created_at|slice:":10" }}</div>
</div>
{% endfor %}
{% else %}
<div class="empty-state" style="padding:20px 0">No announcements yet.</div>
{% endif %}

{% endif %}
{% endblock %}
```

#### Task C.3 — Seeker gate and locked templates

```html
<!-- community/templates/community/seeker_gate.html -->
{% extends "community/base_community.html" %}
{% block community_content %}
<div class="empty-state">
  <p style="font-size:32px;margin-bottom:12px">🌱</p>
  <p style="font-weight:600;color:var(--text-primary)">Community access requires membership.</p>
  <p style="margin-top:8px">
    Community features are available to Level 1 Members and above.
    Complete your formation journey to join a Sceptre Community.
  </p>
</div>
{% endblock %}
```

```html
<!-- community/templates/community/locked.html -->
{% extends "community/base_community.html" %}
{% block community_content %}
<div class="empty-state">
  <p style="font-size:32px;margin-bottom:12px">🔒</p>
  <p style="font-weight:600;color:var(--text-primary)">Level {{ min_level }}+ required.</p>
  <p style="margin-top:8px">This section is available to stewards and above.</p>
</div>
{% endblock %}
```

```bash
git add . && git commit -m "feat: community — My Community surface complete"
```

---

### Phase D — Member Directory + Formation Pipeline (Management Surface)

*Entry requirement: Phase C complete.*

#### Task D.1 — Management home view

```python
# community/views.py — replace management_home stub

@login_required
def management_home(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    # Get steward's scope_path from their highest-level UserPermission
    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    permissions = perms_resp.json().get('results', []) if perms_resp.ok else []
    primary_perm = permissions[0] if permissions else None
    scope_path = primary_perm['tenant_path'] if primary_perm else None

    # Member count
    member_count = 0
    if scope_path:
        mc_resp = requests.get(
            f'{base_url}/api/permissions/',
            params={'tenant_path__startswith': scope_path, 'is_active': 'true', 'page_size': 1},
            headers=auth_header,
        )
        member_count = mc_resp.json().get('count', 0) if mc_resp.ok else 0

    # Recent announcements (last 3)
    announcements = []
    if primary_perm:
        ann_resp = requests.get(
            f'{base_url}/api/records/',
            params={
                'record_family': 'community', 'record_type': 'announcement',
                'tenant_id': primary_perm['tenant_id'],
                'ordering': '-created_at', 'page_size': 3,
            },
            headers=auth_header,
        )
        announcements = ann_resp.json().get('results', []) if ann_resp.ok else []

    # Upcoming gatherings (next 7 days)
    now = timezone.now()
    gatherings = []
    if primary_perm:
        cal_resp = requests.get(
            f'{base_url}/api/calendar/events/',
            params={
                'source_app': 'community',
                'tenant_id': primary_perm['tenant_id'],
                'from': now.date().isoformat(),
                'to': (now + timedelta(days=7)).date().isoformat(),
            },
            headers=auth_header,
        )
        gatherings = cal_resp.json() if cal_resp.ok else []

    return render(request, 'community/management.html', {
        'primary_perm':  primary_perm,
        'scope_path':    scope_path,
        'member_count':  member_count,
        'announcements': announcements,
        'gatherings':    gatherings,
    })
```

#### Task D.2 — Member directory view

```python
# community/views.py — replace member_directory stub

@login_required
def member_directory(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    primary_perm = my_perms[0] if my_perms else None
    scope_path = primary_perm['tenant_path'] if primary_perm else None

    # Filters from GET params
    filter_order = request.GET.get('order', '')
    filter_level = request.GET.get('level', '')
    search_q     = request.GET.get('q', '')

    params = {
        'tenant_path__startswith': scope_path,
        'is_active': 'true',
        'ordering': 'user__display_name',
        'page_size': 50,
    }
    if filter_order:
        params['metadata__service_order'] = filter_order
    if filter_level:
        params['level'] = filter_level
    if search_q:
        params['search'] = search_q

    members_resp = requests.get(
        f'{base_url}/api/permissions/',
        params=params,
        headers=auth_header,
    )
    members = members_resp.json().get('results', []) if members_resp.ok else []

    return render(request, 'community/member_directory.html', {
        'members':       members,
        'scope_path':    scope_path,
        'filter_order':  filter_order,
        'filter_level':  filter_level,
        'search_q':      search_q,
        'order_choices': KGS_SERVICE_ORDER_CHOICES,
        'level_choices': [(0,'Seeker'),(1,'Member'),(2,'Disciple'),(3,'Steward'),(4,'Senior Steward'),(5,'Architect')],
    })
```

#### Task D.3 — Formation pipeline view

```python
# community/views.py — replace formation_pipeline stub

@login_required
def formation_pipeline(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    primary_perm = my_perms[0] if my_perms else None
    scope_path = primary_perm['tenant_path'] if primary_perm else None

    members_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'tenant_path__startswith': scope_path, 'is_active': 'true', 'page_size': 200},
        headers=auth_header,
    )
    all_members = members_resp.json().get('results', []) if members_resp.ok else []

    # Group by competence level
    pipeline = {lvl: [] for lvl in range(6)}
    for m in all_members:
        lvl = m.get('level', 0)
        pipeline[lvl].append(m)

    pipeline_display = [
        {
            'level': lvl,
            'label': KGS_COMPETENCE_LABELS.get(lvl, f'Level {lvl}'),
            'stage': KGS_PARTICIPATION_STAGES.get(lvl, ('',''))[1],
            'members': pipeline[lvl],
            'count': len(pipeline[lvl]),
        }
        for lvl in range(6)
    ]

    return render(request, 'community/formation_pipeline.html', {
        'pipeline_display': pipeline_display,
        'total': len(all_members),
    })
```

#### Task D.4 — Management, directory, and pipeline templates

```html
<!-- community/templates/community/management.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<div class="community-header">
  <div class="community-logo">⚙️</div>
  <div>
    <div class="community-name">Community Management</div>
    <div class="community-tier">{{ primary_perm.tenant_name|default:"Your Branch" }}</div>
  </div>
</div>

<!-- Nav tiles -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
  <a href="{% url 'community-members' %}" class="info-card" style="text-decoration:none">
    <div class="info-card-icon">👥</div>
    <div>
      <div class="info-card-label">Members</div>
      <div class="info-card-value">{{ member_count }}</div>
    </div>
  </a>
  <a href="{% url 'community-pipeline' %}" class="info-card" style="text-decoration:none">
    <div class="info-card-icon">📊</div>
    <div>
      <div class="info-card-label">Pipeline</div>
      <div class="info-card-value">Formation Stages</div>
    </div>
  </a>
</div>

<!-- Announcements -->
<div class="section-heading" style="display:flex;justify-content:space-between;align-items:center">
  <span>Announcements</span>
  <button class="btn-secondary btn-sm"
          hx-get="{% url 'htmx-create-announcement' %}"
          hx-target="#announcement-form-slot"
          hx-swap="innerHTML">+ New</button>
</div>
<div id="announcement-form-slot"></div>
<div id="announcement-list"
     hx-get="{% url 'htmx-announcement-list' %}"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="htmx-indicator">Loading…</div>
</div>

<!-- Gatherings -->
<div class="section-heading" style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
  <span>Gatherings</span>
  <button class="btn-secondary btn-sm"
          hx-get="{% url 'htmx-create-gathering' %}"
          hx-target="#gathering-form-slot"
          hx-swap="innerHTML">+ Schedule</button>
</div>
<div id="gathering-form-slot"></div>
{% if gatherings %}
{% for g in gatherings %}
<div class="gathering-card" id="gathering-{{ g.id }}">
  <div class="gathering-title">{{ g.title }}</div>
  <div class="gathering-meta">{{ g.scheduled_at|slice:":16"|replace:"T":" " }}</div>
  {% with fmt=g.custom_fields.format|default:"in_person" %}
  <span class="gathering-format format-{{ fmt }}">{{ fmt|replace:"_":" "|title }}</span>
  {% endwith %}
</div>
{% endfor %}
{% else %}
<div class="empty-state" style="padding:20px 0">No gatherings in the next 7 days.</div>
{% endif %}

{% endblock %}
```

```html
<!-- community/templates/community/member_directory.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<div style="margin-bottom:16px">
  <input type="search" placeholder="Search members…"
         name="q" value="{{ search_q }}"
         hx-get="{% url 'htmx-member-search' %}"
         hx-trigger="keyup changed delay:400ms"
         hx-target="#member-list"
         hx-swap="innerHTML"
         style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;
                background:var(--background);color:var(--text-primary);font-size:14px">
</div>

<!-- Filters -->
<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
  <select name="level"
          hx-get="{% url 'htmx-member-search' %}"
          hx-trigger="change"
          hx-target="#member-list"
          hx-swap="innerHTML"
          hx-include="[name='q'],[name='order']"
          style="flex:1;padding:8px;border:1px solid var(--border);border-radius:8px;
                 background:var(--background);color:var(--text-primary);font-size:13px">
    <option value="">All levels</option>
    {% for val, label in level_choices %}
    <option value="{{ val }}" {% if filter_level == val|stringformat:"s" %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>

  <select name="order"
          hx-get="{% url 'htmx-member-search' %}"
          hx-trigger="change"
          hx-target="#member-list"
          hx-swap="innerHTML"
          hx-include="[name='q'],[name='level']"
          style="flex:1;padding:8px;border:1px solid var(--border);border-radius:8px;
                 background:var(--background);color:var(--text-primary);font-size:13px">
    <option value="">All service orders</option>
    {% for val, label in order_choices %}
    <option value="{{ val }}" {% if filter_order == val %}selected{% endif %}>{{ val }}</option>
    {% endfor %}
  </select>
</div>

<div id="member-list">
  {% include "community/partials/member_list.html" %}
</div>
{% endblock %}
```

```html
<!-- community/templates/community/partials/member_list.html -->
{% for m in members %}
<a href="{% url 'community-member-profile' m.user_id %}" class="member-card">
  <div class="member-avatar">{{ m.display_name|first|upper }}</div>
  <div>
    <div class="member-name">{{ m.display_name }}</div>
    <div class="member-meta">
      Level {{ m.level }}
      {% if m.metadata.service_order %} · {{ m.metadata.service_order }}{% endif %}
    </div>
  </div>
</a>
{% empty %}
<div class="empty-state">No members found.</div>
{% endfor %}
```

```html
<!-- community/templates/community/formation_pipeline.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">
  {{ total }} total active member{{ total|pluralize }}
</div>

<div class="pipeline-grid">
{% for col in pipeline_display %}
<div class="pipeline-col">
  <div class="pipeline-col-label">{{ col.label }}</div>
  <div class="pipeline-count">{{ col.count }}</div>
  <div class="pipeline-names">
    {% for m in col.members|slice:":5" %}{{ m.display_name }}{% if not forloop.last %}, {% endif %}{% endfor %}
    {% if col.count > 5 %} +{{ col.count|add:"-5" }} more{% endif %}
  </div>
</div>
{% endfor %}
</div>

{% endblock %}
```

```bash
git add . && git commit -m "feat: community — member directory, formation pipeline, management surface"
```

---

### Phase E — Announcement + Gathering Management (HTMX)

*Entry requirement: Phase D complete.*

#### Task E.1 — HTMX views: announcements

```python
# community/views.py — HTMX announcement handlers

@login_required
def htmx_announcement_list(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    tenant_id = my_perms[0]['tenant_id'] if my_perms else None

    if not tenant_id:
        return HttpResponse('<div class="empty-state">No tenant context.</div>')

    ann_resp = requests.get(
        f'{base_url}/api/records/',
        params={
            'record_family': 'community', 'record_type': 'announcement',
            'tenant_id': tenant_id, 'ordering': '-created_at', 'page_size': 20,
        },
        headers=auth_header,
    )
    announcements = ann_resp.json().get('results', []) if ann_resp.ok else []
    return render(request, 'community/partials/announcement_list.html',
                  {'announcements': announcements})


@login_required
def htmx_create_announcement(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    if request.method == 'POST':
        user = request.user
        base_url = request.build_absolute_uri('/')[:-1]
        auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        perms_resp = requests.get(
            f'{base_url}/api/permissions/',
            params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
            headers=auth_header,
        )
        my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
        primary_perm = my_perms[0] if my_perms else None

        if not primary_perm:
            return HttpResponse('<p style="color:var(--error)">No tenant context.</p>')

        create_resp = requests.post(
            f'{base_url}/api/records/',
            json={
                'record_class':  'organizational',
                'record_family': 'community',
                'record_type':   'announcement',
                'title':         request.POST.get('title', '').strip(),
                'content':       request.POST.get('content', '').strip(),
                'tenant_id':     primary_perm['tenant_id'],
                'status':        'active',
                'metadata':      {'source_app': 'community'},
                'permissions':   {'visibility': 'tenant', 'required_level': 1},
            },
            headers=auth_header,
        )

        if create_resp.ok:
            # Refresh the announcement list
            return htmx_announcement_list(request)
        else:
            return HttpResponse(
                '<p style="color:var(--error)">Failed to create announcement. Please try again.</p>'
            )

    # GET — return the create form partial
    return render(request, 'community/partials/announcement_form.html')


@login_required
def htmx_archive_announcement(request, record_id):
    if not _require_level(request, 3):
        return HttpResponse('')

    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/records/{record_id}/',
        json={'status': 'archived'},
        headers=auth_header,
    )
    return htmx_announcement_list(request)
```

#### Task E.2 — HTMX views: gatherings (dual-write)

```python
# community/views.py — HTMX gathering handlers

@login_required
def htmx_create_gathering(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    if request.method == 'POST':
        user = request.user
        base_url = request.build_absolute_uri('/')[:-1]
        auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        perms_resp = requests.get(
            f'{base_url}/api/permissions/',
            params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
            headers=auth_header,
        )
        my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
        primary_perm = my_perms[0] if my_perms else None

        if not primary_perm:
            return HttpResponse('<p style="color:var(--error)">No tenant context.</p>')

        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        fmt          = request.POST.get('format', 'in_person')
        location     = request.POST.get('location', '').strip() or None
        stream_url   = request.POST.get('stream_url', '').strip() or None
        capacity     = request.POST.get('capacity', '').strip() or None
        scheduled_at = request.POST.get('scheduled_at', '').strip()
        tenant_id    = primary_perm['tenant_id']

        # Dual-write: atomic via try/except (both API calls in sequence)
        try:
            # Step 1 — create gathering Record
            rec_resp = requests.post(
                f'{base_url}/api/records/',
                json={
                    'record_class':  'organizational',
                    'record_family': 'community',
                    'record_type':   'gathering',
                    'title':         title,
                    'content':       description or None,
                    'tenant_id':     tenant_id,
                    'status':        'active',
                    'metadata':      {'source_app': 'community'},
                    'custom_fields': {
                        'format':       fmt,
                        'location':     location,
                        'stream_url':   stream_url,
                        'capacity':     int(capacity) if capacity else None,
                        'scheduled_at': scheduled_at,
                    },
                    'permissions': {'visibility': 'tenant', 'required_level': 1},
                },
                headers=auth_header,
            )
            rec_resp.raise_for_status()
            record_id = rec_resp.json()['id']

            # Step 2 — create event Activity
            act_resp = requests.post(
                f'{base_url}/api/activities/',
                json={
                    'activity_type': 'event',
                    'title':         title,
                    'description':   description or None,
                    'scheduled_at':  scheduled_at or None,
                    'tenant_id':     tenant_id,
                    'kgs_pillar':    'communities',
                    'kgs_pathway':   'community_life',
                    'status':        'pending',
                    'metadata':      {'source_app': 'community'},
                },
                headers=auth_header,
            )
            act_resp.raise_for_status()
            activity_id = act_resp.json()['id']

            # Step 3 — link Record → Activity
            rel_resp = requests.post(
                f'{base_url}/api/relationships/',
                json={
                    'from_record_id':    record_id,
                    'to_record_id':      activity_id,
                    'relationship_type': 'aligns_with',
                    'direction':         'directed',
                    'tenant_id':         tenant_id,
                },
                headers=auth_header,
            )
            rel_resp.raise_for_status()

        except Exception:
            return HttpResponse(
                '<p style="color:var(--error)">Failed to schedule gathering. Please try again.</p>'
            )

        # Success — return a success partial (the management page will refresh gatherings)
        return HttpResponse(
            '<div class="announcement-card" style="border-color:var(--success)">'
            f'<div class="announcement-title">✓ Gathering scheduled: {title}</div>'
            '</div>'
        )

    # GET — return the create form partial
    return render(request, 'community/partials/gathering_form.html')


@login_required
def htmx_cancel_gathering(request, record_id):
    if not _require_level(request, 3):
        return HttpResponse('')

    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    # Find the linked Activity via Relationship
    rel_resp = requests.get(
        f'{base_url}/api/relationships/',
        params={'from_record_id': str(record_id), 'relationship_type': 'aligns_with'},
        headers=auth_header,
    )
    relationships = rel_resp.json().get('results', []) if rel_resp.ok else []

    # Cancel Record
    requests.patch(
        f'{base_url}/api/records/{record_id}/',
        json={'status': 'cancelled'},
        headers=auth_header,
    )

    # Cancel linked Activity
    for rel in relationships:
        act_id = rel.get('to_record_id')
        if act_id:
            requests.patch(
                f'{base_url}/api/activities/{act_id}/',
                json={'status': 'cancelled'},
                headers=auth_header,
            )

    return HttpResponse(
        f'<div class="gathering-card" style="opacity:0.5">'
        f'<div class="gathering-title">Gathering cancelled</div></div>'
    )
```

#### Task E.3 — HTMX partials templates

```html
<!-- community/templates/community/partials/announcement_form.html -->
<div class="community-form" id="announcement-form">
  <div class="form-field">
    <label>Title</label>
    <input type="text" name="title" placeholder="Announcement title" required>
  </div>
  <div class="form-field">
    <label>Content</label>
    <textarea name="content" rows="4" placeholder="Announcement message…"></textarea>
  </div>
  <button class="btn-primary"
          hx-post="{% url 'htmx-create-announcement' %}"
          hx-target="#announcement-list"
          hx-swap="innerHTML"
          hx-include="#announcement-form">
    Publish Announcement
  </button>
</div>
```

```html
<!-- community/templates/community/partials/gathering_form.html -->
<div class="community-form" id="gathering-form">
  <div class="form-field">
    <label>Title</label>
    <input type="text" name="title" placeholder="e.g. Sunday Morning Service" required>
  </div>
  <div class="form-field">
    <label>Date & Time</label>
    <input type="datetime-local" name="scheduled_at" required>
  </div>
  <div class="form-field">
    <label>Format</label>
    <select name="format"
            hx-on:change="
              const fmt = this.value;
              document.getElementById('loc-field').classList.toggle('visible', fmt !== 'digital');
              document.getElementById('stream-field').classList.toggle('visible', fmt !== 'in_person');
            ">
      <option value="in_person">In Person</option>
      <option value="digital">Digital</option>
      <option value="hybrid">Hybrid</option>
    </select>
  </div>
  <div class="form-field format-conditional visible" id="loc-field">
    <label>Location</label>
    <input type="text" name="location" placeholder="Venue or address">
  </div>
  <div class="form-field format-conditional" id="stream-field">
    <label>Stream URL</label>
    <input type="url" name="stream_url" placeholder="https://youtube.com/live/…">
  </div>
  <div class="form-field">
    <label>Description (optional)</label>
    <textarea name="description" rows="3" placeholder="Agenda or notes…"></textarea>
  </div>
  <button class="btn-primary"
          hx-post="{% url 'htmx-create-gathering' %}"
          hx-target="#gathering-form-slot"
          hx-swap="innerHTML"
          hx-include="#gathering-form">
    Schedule Gathering
  </button>
</div>
```

```html
<!-- community/templates/community/partials/announcement_list.html -->
{% for ann in announcements %}
<div class="announcement-card" id="announcement-{{ ann.id }}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="announcement-title">{{ ann.title }}</div>
      <div class="announcement-content">{{ ann.content|truncatechars:200 }}</div>
      <div class="announcement-date">{{ ann.created_at|slice:":10" }}
        {% if ann.status == 'archived' %}<span style="color:var(--text-tertiary)"> · Archived</span>{% endif %}
      </div>
    </div>
    {% if ann.status == 'active' %}
    <button class="btn-danger btn-sm"
            hx-post="{% url 'htmx-archive-announcement' ann.id %}"
            hx-target="#announcement-list"
            hx-swap="innerHTML"
            hx-confirm="Archive this announcement?">
      Archive
    </button>
    {% endif %}
  </div>
</div>
{% empty %}
<div class="empty-state" style="padding:16px 0">No announcements yet.</div>
{% endfor %}
```

```bash
git add . && git commit -m "feat: community — announcement + gathering HTMX management complete"
```

---

### Phase F — Member Profile + Pastoral Assignment + Service Order

*Entry requirement: Phase E complete.*

#### Task F.1 — Member profile view (full implementation)

```python
# community/views.py — replace member_profile stub

@login_required
def member_profile(request, member_id):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    # Steward's scope
    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    scope_path = my_perms[0]['tenant_path'] if my_perms else None

    # Member's permission row (within steward's scope)
    member_perm_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={
            'user_id': str(member_id),
            'tenant_path__startswith': scope_path,
            'is_active': 'true',
        },
        headers=auth_header,
    )
    member_perms = member_perm_resp.json().get('results', []) if member_perm_resp.ok else []
    member_perm = member_perms[0] if member_perms else None

    if not member_perm:
        return render(request, 'community/locked.html',
                      {'min_level': 3, 'message': 'Member not found in your scope.'}, status=404)

    # Member user details
    member_resp = requests.get(
        f'{base_url}/api/auth/users/{member_id}/',
        headers=auth_header,
    )
    member_user = member_resp.json() if member_resp.ok else {}

    # Member's gifts
    gifts_resp = requests.get(
        f'{base_url}/api/activities/',
        params={
            'activity_type': 'skill',
            'created_by': str(member_id),
            'tenant_id': member_perm['tenant_id'],
            'status': 'active',
        },
        headers=auth_header,
    )
    gifts = gifts_resp.json().get('results', []) if gifts_resp.ok else []

    # Member's certifications (Learn App)
    certs_resp = requests.get(
        f'{base_url}/api/records/',
        params={
            'record_family': 'learning',
            'record_type': 'certification',
            'created_by': str(member_id),
            'status': 'active',
            'ordering': '-created_at',
        },
        headers=auth_header,
    )
    certifications = certs_resp.json().get('results', []) if certs_resp.ok else []

    # Potential shepherds (Level 3+ in this scope)
    shepherds_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={
            'tenant_path__startswith': scope_path,
            'level__gte': 3,
            'is_active': 'true',
        },
        headers=auth_header,
    )
    shepherds = shepherds_resp.json().get('results', []) if shepherds_resp.ok else []

    level = member_user.get('competence_level', 0)
    level_label = KGS_COMPETENCE_LABELS.get(level, f'Level {level}')
    stage_info = KGS_PARTICIPATION_STAGES.get(level, ('Member', 'Formation'))

    return render(request, 'community/member_profile.html', {
        'member_perm':    member_perm,
        'member_user':    member_user,
        'gifts':          gifts,
        'certifications': certifications,
        'shepherds':      shepherds,
        'order_choices':  KGS_SERVICE_ORDER_CHOICES,
        'level_label':    level_label,
        'stage_info':     stage_info,
    })
```

#### Task F.2 — HTMX views: pastoral + service order

```python
# community/views.py — pastoral and service order HTMX handlers

@login_required
def htmx_set_shepherd(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    shepherd_id = request.POST.get('shepherd_id', '').strip() or None
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/permissions/{permission_id}/',
        json={'metadata': {'shepherd_id': shepherd_id}},
        headers=auth_header,
    )

    label = 'No shepherd assigned'
    if shepherd_id:
        sh_resp = requests.get(f'{base_url}/api/auth/users/{shepherd_id}/', headers=auth_header)
        sh = sh_resp.json() if sh_resp.ok else {}
        label = sh.get('display_name', 'Shepherd assigned')

    return HttpResponse(
        f'<div class="info-card-value" id="shepherd-value">✓ {label}</div>'
    )


@login_required
def htmx_set_order(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    service_order = request.POST.get('service_order', '').strip() or None
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/permissions/{permission_id}/',
        json={'metadata': {'service_order': service_order}},
        headers=auth_header,
    )

    label = service_order if service_order else 'No service order assigned'
    return HttpResponse(
        f'<div class="info-card-value" id="order-value">✓ {label}</div>'
    )


@login_required
def htmx_deactivate_member(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/permissions/{permission_id}/',
        json={'is_active': False},
        headers=auth_header,
    )

    return HttpResponse(
        '<div class="announcement-card" style="border-color:var(--error)">'
        '<div class="announcement-title" style="color:var(--error)">Membership deactivated.</div>'
        '</div>'
    )


@login_required
def htmx_member_search(request):
    if not _require_level(request, 2):
        return HttpResponse('')

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    scope_path = my_perms[0]['tenant_path'] if my_perms else None

    params = {
        'tenant_path__startswith': scope_path,
        'is_active': 'true',
        'ordering': 'user__display_name',
        'page_size': 50,
    }
    q = request.GET.get('q', '').strip()
    level = request.GET.get('level', '').strip()
    order = request.GET.get('order', '').strip()
    if q:
        params['search'] = q
    if level:
        params['level'] = level
    if order:
        params['metadata__service_order'] = order

    members_resp = requests.get(f'{base_url}/api/permissions/', params=params, headers=auth_header)
    members = members_resp.json().get('results', []) if members_resp.ok else []

    return render(request, 'community/partials/member_list.html', {'members': members})
```

#### Task F.3 — Member profile template

```html
<!-- community/templates/community/member_profile.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<!-- Header -->
<div class="community-header">
  <div class="member-avatar" style="width:56px;height:56px;font-size:22px">
    {{ member_user.display_name|first|upper }}
  </div>
  <div>
    <div class="community-name">{{ member_user.display_name }}</div>
    <div class="community-tier">{{ level_label }} · {{ stage_info.1 }}</div>
  </div>
</div>

<!-- Formation steps -->
<div class="formation-card">
  <div class="formation-stage-label">Formation</div>
  <div class="formation-level-name">{{ level_label }}</div>
  <div class="formation-participation">{{ stage_info.1 }}</div>
  <div class="formation-steps">
    {% for step in "12345" %}
    <div class="formation-step {% if forloop.counter <= member_user.competence_level %}active{% endif %}"></div>
    {% endfor %}
  </div>
</div>

<!-- Shepherd assignment -->
<div class="info-card" id="shepherd-card">
  <div class="info-card-icon">🤝</div>
  <div style="flex:1">
    <div class="info-card-label">Shepherd</div>
    <div class="info-card-value" id="shepherd-value">
      {% if member_perm.metadata.shepherd_id %}Assigned{% else %}Not assigned{% endif %}
    </div>
    <form style="margin-top:8px;display:flex;gap:8px;align-items:center">
      <select name="shepherd_id" style="flex:1;padding:6px;border:1px solid var(--border);
              border-radius:6px;background:var(--background);color:var(--text-primary);font-size:13px">
        <option value="">— Remove shepherd —</option>
        {% for s in shepherds %}
        <option value="{{ s.user_id }}"
                {% if s.user_id == member_perm.metadata.shepherd_id %}selected{% endif %}>
          {{ s.display_name }}
        </option>
        {% endfor %}
      </select>
      <button class="btn-secondary btn-sm"
              hx-post="{% url 'htmx-set-shepherd' member_perm.id %}"
              hx-target="#shepherd-value"
              hx-swap="outerHTML"
              hx-include="[name='shepherd_id']">
        Set
      </button>
    </form>
  </div>
</div>

<!-- Service order placement -->
<div class="info-card" id="order-card">
  <div class="info-card-icon">⚙️</div>
  <div style="flex:1">
    <div class="info-card-label">Service Order</div>
    <div class="info-card-value" id="order-value">
      {{ member_perm.metadata.service_order|default:"Not assigned" }}
    </div>
    <form style="margin-top:8px;display:flex;gap:8px;align-items:center">
      <select name="service_order" style="flex:1;padding:6px;border:1px solid var(--border);
              border-radius:6px;background:var(--background);color:var(--text-primary);font-size:13px">
        <option value="">— Remove placement —</option>
        {% for val, label in order_choices %}
        <option value="{{ val }}"
                {% if val == member_perm.metadata.service_order %}selected{% endif %}>
          {{ val }}
        </option>
        {% endfor %}
      </select>
      <button class="btn-secondary btn-sm"
              hx-post="{% url 'htmx-set-order' member_perm.id %}"
              hx-target="#order-value"
              hx-swap="outerHTML"
              hx-include="[name='service_order']">
        Set
      </button>
    </form>
  </div>
</div>

<!-- Gifts summary -->
{% if gifts %}
<div class="section-heading">Gifts Register</div>
{% for gift in gifts %}
<div class="announcement-card">
  <div class="announcement-title">{{ gift.title }}</div>
  <div class="announcement-content">
    Competence: {{ gift.progress }}%
    {% if gift.metadata.service_order %} · {{ gift.metadata.service_order }}{% endif %}
  </div>
</div>
{% endfor %}
{% endif %}

<!-- Certifications -->
{% if certifications %}
<div class="section-heading">Certifications</div>
{% for cert in certifications %}
<div class="announcement-card">
  <div class="announcement-title">{{ cert.title }}</div>
  <div class="announcement-date">{{ cert.created_at|slice:":10" }}</div>
</div>
{% endfor %}
{% endif %}

<!-- Deactivate membership -->
<div style="margin-top:24px;padding-top:16px;border-top:1px solid var(--border)">
  <button class="btn-danger"
          hx-post="{% url 'htmx-deactivate-member' member_perm.id %}"
          hx-target="#deactivate-slot"
          hx-swap="innerHTML"
          hx-confirm="Deactivate this member's community membership? This cannot be undone without steward action.">
    Deactivate Membership
  </button>
  <div id="deactivate-slot"></div>
</div>

{% endblock %}
```

```bash
git add . && git commit -m "feat: community — member profile, pastoral assignment, service order HTMX complete"
```

---

### Phase G — Smoke Test Checklist

*Entry requirement: Phases A–F complete.*

Verify manually on mobile (and desktop for management surface):

**My Community surface:**
- [ ] Level 1 member sees community header with tenant name and tier
- [ ] Formation card shows correct level label and participation stage; progress steps reflect level
- [ ] Shepherd card appears when `shepherd_id` is set; hidden when null
- [ ] Service order card appears when `service_order` is set; hidden when null
- [ ] Gifts summary shows correct count; link to Activity App gifts register works
- [ ] Upcoming gatherings list shows events within 30 days with format badge and location/stream link
- [ ] Announcements list shows 5 most recent active announcements
- [ ] Seeker (Level 0b) sees seeker gate — no community content
- [ ] Level 0 member with no UserPermission rows sees "not yet part of a community" empty state

**Community Management surface:**
- [ ] Level 2 user sees locked.html with "Level 3+ required" message
- [ ] Level 3 steward sees management home with member count, announcement section, and gathering section
- [ ] Member directory loads and shows all active members in scope
- [ ] Search by name filters member list via HTMX without page reload
- [ ] Level and service order filter dropdowns work correctly via HTMX
- [ ] Formation pipeline shows correct member counts per level column
- [ ] Member profile loads: avatar, level, shepherd, service order, gifts, certifications

**Announcements:**
- [ ] Create announcement form appears via HTMX; submitting creates a Record and refreshes list
- [ ] Archive button archives the record (status:'archived'); refreshed list shows archived state
- [ ] Announcement appears on My Community surface for Level 1 members in same tenant

**Gatherings:**
- [ ] Create gathering form appears via HTMX
- [ ] Location field shows only when format is 'in_person' or 'hybrid'
- [ ] Stream URL field shows only when format is 'digital' or 'hybrid'
- [ ] Submitting creates: one gathering Record, one event Activity (source_app:'community'),
      one aligns_with Relationship — verify all three in Django admin
- [ ] `GET /api/calendar/events/?source_app=community&tenant_id={id}` returns the new gathering
- [ ] Gathering appears in My Community upcoming gatherings (within 30 days)
- [ ] Cancel gathering PATCHes both Record and Activity to status:'cancelled'
- [ ] Cancelled gathering disappears from Calendar endpoint results

**Pastoral assignment:**
- [ ] Set shepherd on member profile: HTMX select → PATCH → shepherd-value updates inline
- [ ] Shepherd name appears on member's My Community surface after assignment
- [ ] Clear shepherd: select "Remove shepherd" → shepherd-value shows "Not assigned"

**Service order:**
- [ ] Set service order on member profile: HTMX select → PATCH → order-value updates inline
- [ ] Service order appears on member directory card after assignment
- [ ] Service order filter in directory correctly filters by `metadata__service_order`

**Access control:**
- [ ] `GET /api/community/health/` returns `{"status": "ok", "app": "community"}`
- [ ] All management views return 403 / locked template for Level 2 and below
- [ ] Steward cannot see members outside their scope_path (verify with two tenants)

```bash
git add . && git commit -m "feat: community app — smoke test pass, all phases complete"
```

---

## Django Endpoint Summary

```
# Community App health
GET    /api/community/health/

# Template views
GET    /community/                          My Community (Level 1+)
GET    /community/management/              Management home (Level 3+)
GET    /community/management/members/      Member directory (Level 3+)
GET    /community/management/members/{id}/ Member profile (Level 3+)
GET    /community/management/pipeline/     Formation pipeline (Level 3+)

# HTMX partials
GET    /community/htmx/announcement/create/          announcement create form
POST   /community/htmx/announcement/create/          create announcement (Level 3+)
POST   /community/htmx/announcement/{id}/archive/    archive announcement (Level 3+)
GET    /community/htmx/gathering/create/             gathering create form
POST   /community/htmx/gathering/create/             create gathering — dual-write (Level 3+)
POST   /community/htmx/gathering/{id}/cancel/        cancel gathering (Level 3+)
POST   /community/htmx/member/{id}/shepherd/         set shepherd (Level 3+)
POST   /community/htmx/member/{id}/order/            set service order (Level 3+)
POST   /community/htmx/member/{id}/deactivate/       deactivate membership (Level 3+)
GET    /community/htmx/members/search/               HTMX member search (Level 2+)
GET    /community/htmx/announcements/                HTMX announcement list (Level 3+)

# Existing platform endpoints consumed by Community App (no changes)
GET    /api/permissions/?tenant_path__startswith={}&is_active=true
POST   /api/permissions/
PATCH  /api/permissions/{id}/
GET    /api/records/?record_family=community&record_type=announcement
GET    /api/records/?record_family=community&record_type=gathering
POST   /api/records/
PATCH  /api/records/{id}/
POST   /api/activities/
PATCH  /api/activities/{id}/
POST   /api/relationships/
GET    /api/relationships/?from_record_id={}&relationship_type=aligns_with
GET    /api/calendar/events/?source_app=community
GET    /api/activities/?activity_type=skill&created_by={}&tenant_id={}
GET    /api/records/?record_family=learning&record_type=certification&created_by={}
```

---

## File Map (Community App additions)

```
~/ics/
  community/
    __init__.py
    apps.py
    models.py                  ← NEW: MembershipRequest (stubbed, not wired to UI)
    constants.py               ← NEW: KGS_SERVICE_ORDERS, KGS_PARTICIPATION_STAGES, KGS_COMPETENCE_LABELS
    api_views.py               ← NEW: community_health endpoint
    views.py                   ← NEW: all Django template views + HTMX partials
    urls.py                    ← NEW: full URL structure
    templates/
      community/
        base_community.html    ← NEW
        my_community.html      ← NEW
        management.html        ← NEW
        member_directory.html  ← NEW
        member_profile.html    ← NEW
        formation_pipeline.html← NEW
        seeker_gate.html       ← NEW
        locked.html            ← NEW
        partials/
          member_list.html     ← NEW (HTMX target for search/filter)
          announcement_list.html ← NEW (HTMX target for create/archive)
          announcement_form.html ← NEW
          gathering_form.html    ← NEW

  frontend/assets/css/
    community.css              ← NEW
```

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|-------|----------------|-------------------|---------------|
| A | Django app scaffold, MembershipRequest model stub, service order constants, URL structure, health check | Phases 0–4 of main roadmap done | Health check returns 200; migration applied |
| B | Base template, community.css, stub views | Phase A done | All URLs resolve; base template loads with CSS |
| C | My Community surface: tenant header, formation stage, shepherd, service order, gatherings, announcements, gifts summary | Phase B done | Level 1 member sees full My Community page; seeker gate shown for Level 0b |
| D | Member directory, formation pipeline, management home | Phase C done | Steward sees member list with search/filter; pipeline shows correct counts |
| E | Announcement management (create/archive HTMX), gathering management (dual-write create/cancel HTMX) | Phase D done | Announcement creates Record; gathering creates Record + Activity + Relationship; Calendar endpoint returns gathering |
| F | Member profile, pastoral assignment (HTMX), service order placement (HTMX), deactivation | Phase E done | Steward sets shepherd and service order on member; values update inline; appear on member's My Community surface |
| G | Smoke test checklist | Phase F done | All checklist items pass; admin confirms dual-write objects; Calendar endpoint confirms community events |

---

## Deferred (Post-MVP)

- `MembershipRequest` flow — self-service join request, steward approval queue,
  induction training gate (Learn App integration)
- `report` record type — community health and activity reports
- `pastoral_note` record type — confidential steward notes on members (privacy design required)
- Attendance tracking — `AttendanceLog` model (privacy-sensitive; deferred)
- `PastoralAssignment` model — upgrade from `UserPermission.metadata.shepherd_id`
  when shepherd management needs versioning and history
- GinIndex on `UserPermission.metadata` — add if directory filter performance degrades
- Shepherd's flock view — filtered directory showing all members under a specific shepherd
- Community analytics dashboard — formation pipeline trends over time, service order coverage gaps
- Collective-level gathering visibility — gatherings visible across Church Collective network
- iCS Live Stream integration — gathering `stream_url` pointing to native Video App stream
  (no data contract change required — `stream_url` is already a string field)
- Notifications on new announcements — wired to Notifications App stub (Phase 5.7)
- Paraclete integration — "You have a gathering tomorrow" in daily digest
  (Calendar endpoint already supports this; Paraclete implementation is Phase 6)
- Calendar App Phase 2 — community gatherings appear in grid calendar UI


---

ICS Platform · Task 5.5

**Governance App**

System Design & Build Roadmap

2026-04-10 · Data Contract reference: v9

> *UI Architecture: Django templates + HTMX throughout. All UI is
> server-rendered. HTMX handles form submissions, record list updates,
> linked records panels, and version history partials. storage.js is
> retained for UI state (theme, session token) only.*
>
> *Data Contract reference: 2026-04-10-ics-platform-data-contract_v9.md
> --- all schemas and patterns in this document originate from Parts
> 2.5, 3.1, 7, and 15 of that contract. Read the contract before
> implementing.*

**Goal & Architecture**

Build the ICS Governance App --- the digital expression of the
Prophet\'s Handbook and the Apostolic Properties system. The Governance
App gives Level 3--5 operators structured access to the three branches
of Apostolic Properties: the Reference Library (compiled from Scripture
via HRS), the Keys Library (personal symbol-to-meaning mappings), and
the Mandate branch (received directives translated into governance
documents and platform).

Architecture: Django + DRF backend with a dedicated governance Django
app (to be scaffolded). The Governance App adds Django template views
and HTMX interactions on top of the existing Records Engine. It owns no
models of its own --- it is a UI and transaction coordination layer. All
writes go through existing DRF endpoints.

Tech Stack: Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX,
governance.css (mobile-first, CSS variables).

**System Overview**

**The Governance Stack**

> KGS Layer Pillar 2 --- Strategy & Governance
>
> Office of Governance and Policy (18.3)
>
> Office of Strategic Development (18.4)
>
> ↓ expressed as
>
> Apostolic Layer Prophet\'s Handbook (Apostolic Properties)
>
> ↓ organised into three branches
>
> Branch 1 Reference Library --- compiled from Scripture via HRS
>
> record_family: \'governance\', record_class: \'governance\'
>
> record_type: class \| principle \| concept \| divine_pattern
>
> \| subject \| entity \| narrative \| framework
>
> ↓ linked to
>
> Scripture Layer BibleVerse (via Relationship.bible_verse_id)
>
> ↓ alongside
>
> Branch 2 Keys Library --- personal operator mappings
>
> record_family: \'reference\', record_class: \'personal\'
>
> record_type: key
>
> ↓ sourced from
>
> Journal Layer Dream Journal, Spirit Journal (record_family:
> \'journal\')
>
> ↓ mandate branch
>
> Branch 3 Mandate --- received directives, governance documents
>
> record_family: \'governance\', record_class: \'governance\'
>
> record_type: mandate \| statement \| programme
>
> \| protocol \| procedure
>
> ↓ versioned via
>
> Version Chain previous_version_id / superseded_by
>
> ↓ linked to
>
> Reference Library Relationship (part_of, derived_from, authorised_by,
> etc.)

**Three-Surface Model**

> Governance App
>
> │
>
> ├── \'Reference Library\' (read --- Level 3+)
>
> │ Scope: /global/handbook/ tenant
>
> │ Browse: by record_type --- Classes, Principles, Concepts,
>
> │ Divine Patterns, Subjects, Entities, Narratives, Frameworks
>
> │ Detail: Property Attributes (HRS custom_fields)
>
> │ Linked Records panel (HRS relationships)
>
> │ Scripture links (BibleVerse via Relationship)
>
> │
>
> ├── \'Mandate\' (read Level 4+, write Level 5)
>
> │ Scope: /global/handbook/ tenant
>
> │ Browse: by record_type --- Mandates, Statements, Programmes,
>
> │ Protocols, Procedures
>
> │ Detail: Version History chain
>
> │ Linked Records panel (HRS relationships)
>
> │ Source journal links
>
> │ Write: Create / edit / lock / supersede (Level 5)
>
> │
>
> └── \'My Keys\' (personal --- Level 3+)
>
> Scope: record_family: \'reference\', record_type: \'key\',
>
> created_by = request.user
>
> Shows: Personal symbol-to-meaning mappings
>
> Source journal links (dream, note)
>
> Write: Create / edit own Key Records (Level 3+)

**User Roles in the Governance App**

  -----------------------------------------------------------------------------
  **Level**               **Reference   **Mandate**   **My       **Write
                          Library**                   Keys**     (Handbook)**
  ----------------------- ------------- ------------- ---------- --------------
  Seeker (0b) / Member    ✗             ✗             ✗          ✗
  (1) / Disciple (2)                                             

  Steward (Level 3)       Read only     ✗             Full       ✗

  Senior Steward (Level   Read only     Read only     Full       ✗
  4+)                                                            

  Architect (Level 5)     Read + Write  Read + Write  Full       Full
  -----------------------------------------------------------------------------

**Feature List (All Features --- Unphased)**

**F1 --- Reference Library Browser (Level 3+)**

-   Landing page: eight record_type sections presented as a structured
    menu

```{=html}
<!-- -->
```
-   Classes · Principles · Concepts · Divine Patterns · Subjects ·
    Entities · Narratives · Frameworks

```{=html}
<!-- -->
```
-   Each section: paginated list of records --- title, summary (if
    present), tags

-   HTMX typeahead search: filters records by title within the selected
    type

-   Record detail view: title, content (markdown rendered), summary,
    tags, categories

-   Property Attributes panel: displays the six HRS custom_fields
    (Complexity, Relationship Polarity, Position, Direction, Speed,
    Emotional Tone) where set --- hidden if all null

-   Linked Records panel: all Relationship objects for this record (see
    F4)

-   Scripture links: BibleVerse relationships rendered as verse text
    with reference label

-   Tags and categories: displayed as chips; clicking a tag filters the
    list (HTMX)

**F2 --- Mandate Branch (Level 4+ read, Level 5 write)**

-   Landing page: five record_type sections --- Mandates, Statements,
    Programmes, Protocols, Procedures

-   Each section: list of records sorted by version desc, status badge
    (draft / active / locked / superseded)

-   Record detail view: title, content (markdown rendered), status
    badge, version number, locked_by / locked_at if locked

-   Version History panel: ordered chain of versions (v1 → v2 → v3) via
    previous_version_id / superseded_by traversal; each entry links to
    its detail view

-   Linked Records panel: HRS relationships (see F4)

-   Source journal links: journal records linked via \'references\'
    relationship (Spirit Journal, Dream Journal, Article)

-   Level 5 write actions:

```{=html}
<!-- -->
```
-   Create record --- form with title, content, record_type selector,
    status (draft / active), tags, categories

-   Edit record --- same form, pre-filled; only if status is not
    \'locked\'

-   Lock record --- HTMX action; sets status: \'locked\', locked_by,
    locked_at

-   Supersede record --- creates new draft version; sets
    previous_version_id = current.id; patches current to status:
    \'superseded\', superseded_by = new.id

-   Add HRS link --- inline form to create a Relationship from this
    record

-   Add scripture link --- inline form to link a BibleVerse via
    Relationship

-   Add journal source link --- inline form to link a journal record via
    \'references\' Relationship

**F3 --- My Keys (Level 3+ personal)**

-   List view: all Key Records created_by = request.user, sorted by
    created_at desc

-   Each card: symbol (from custom_fields.symbol), meaning preview,
    source journal link if present

-   Create Key Record: form with symbol, meaning, source_context,
    optional link to a Dream or Spirit Journal record

-   Edit / archive own Key Records

-   Source journal link: HTMX typeahead to search own journal records
    (dream, note) and create a \'derived_from\' Relationship

-   Empty state for new operators with instructions on building a Keys
    Library

**F4 --- Linked Records Panel (shared component)**

-   Used by both Reference Library and Mandate branch detail views

-   Fetches all Relationships where from_record_id or to_record_id =
    record.id

-   Groups links by relationship_type: part_of / derived_from /
    aligns_with / authorised_by / references / has_subject / has_entity

-   Scripture links (bible_verse_id set): renders verse text inline;
    shows book/chapter/verse label

-   Each linked record shown as title + type badge; clicking navigates
    to its detail view

-   Level 5 only: \'Add link\' affordance --- inline HTMX form to create
    a new Relationship

-   Rendered as HTMX partial: GET /governance/htmx/relationships/{id}/

**F5 --- Version History Panel (shared component)**

-   Used by Mandate branch detail views

-   Traverses previous_version_id chain backward and superseded_by chain
    forward

-   Renders as ordered list: v1 (superseded) → v2 (superseded) → v3
    (current / locked)

-   Each entry: version number, status badge, created_at, locked_at if
    locked, link to detail view

-   Current version highlighted

-   Rendered as HTMX partial: GET /governance/htmx/versions/{id}/

**F6 --- Reference Library Authorship (Level 5 only)**

-   Create / edit any Reference Library record type (class, principle,
    concept, divine_pattern, subject, entity, narrative, framework)

-   Form fields: title, content (markdown textarea), summary,
    record_type selector, tags, categories

-   Property Attributes section: six optional structured fields ---
    Complexity (text), Relationship Polarity (dropdown: subjective /
    objective), Position (dropdown: up / down / left / right), Direction
    (dropdown: forward / backward), Speed (dropdown: fast / slow),
    Emotional Tone (text)

-   Stored in custom_fields; no validation beyond enum membership

-   Status control: draft / active / locked

-   After save: redirect to record detail view with Linked Records panel

**Django App Structure**

**File map**

> \~/ics/governance/
>
> \_\_init\_\_.py
>
> apps.py
>
> views.py class-based views; get_template_names() for HTMX detection
>
> urls.py all governance URL patterns
>
> services.py query helpers (handbook record lists, version chain
> traversal)
>
> templates/
>
> governance/
>
> governance.html full-page shell (extends base.html)
>
> \_home.html branch selector landing partial
>
> \_library_list.html Reference Library type list partial
>
> \_library_detail.html Reference Library record detail partial
>
> \_mandate_list.html Mandate branch type list partial
>
> \_mandate_detail.html Mandate record detail partial
>
> \_keys_list.html My Keys list partial
>
> \_keys_detail.html Key Record detail partial
>
> \_linked_records.html Linked Records panel partial (HTMX)
>
> \_version_history.html Version History panel partial (HTMX)
>
> \_record_form.html Create / edit form partial (HTMX)
>
> \_relationship_form.html Add HRS link form partial (HTMX)
>
> \_lock_confirm.html Lock confirmation partial (HTMX)
>
> \_supersede_confirm.html Supersede confirmation partial (HTMX)
>
> governance.css mobile-first, CSS variables, governance colour palette

**View pattern --- HTMX partial detection**

All views follow the Records App pattern: CBV with get_template_names()
override. When the request carries HX-Request header, the view returns
the partial template (\_name.html). Otherwise it wraps in the full
governance.html shell.

> class LibraryDetailView(LoginRequiredMixin, View):
>
> def get_template_names(self):
>
> if self.request.headers.get(\'HX-Request\'):
>
> return \[\'governance/\_library_detail.html\'\]
>
> return \[\'governance/governance.html\'\]
>
> def get(self, request, record_id):
>
> \# Permission check: Level 3+ for Reference Library
>
> if request.user.competence_level \< 3:
>
> raise PermissionDenied
>
> \# Fetch via DRF endpoint or direct ORM (within governance app
> boundary)
>
> record = get_object_or_404(Record, id=record_id,
>
> record_family=\'governance\',
>
> tenant\_\_path=\'/global/handbook/\')
>
> return render(request, self.get_template_names()\[0\],
>
> {\'record\': record})

**services.py --- key helpers**

> def get_handbook_records(record_type, user):
>
> \"\"\"Returns QS of Handbook records of given type accessible to
> user.\"\"\"
>
> def get_version_chain(record):
>
> \"\"\"Traverses previous_version_id backward and superseded_by
> forward.
>
> Returns ordered list of records from v1 to current.\"\"\"
>
> def get_linked_records(record_id):
>
> \"\"\"Returns all Relationship rows for a record, with related Record
> objects.\"\"\"
>
> def create_new_version(old_record, user, new_data):
>
> \"\"\"Atomic: creates new Record with previous_version_id set,
>
> patches old_record to status=\'superseded\',
> superseded_by=new.id.\"\"\"

**URL Patterns**

  -----------------------------------------------------------------------------------------------
  **URL**                                              **View**                 **Level**
  ---------------------------------------------------- ------------------------ -----------------
  GET /governance/                                     GovernanceHomeView       3+

  GET /governance/library/                             LibraryHomeView          3+

  GET /governance/library/\<str:record_type\>/         LibraryListView          3+

  GET /governance/library/record/\<uuid:record_id\>/   LibraryDetailView        3+

  GET /governance/mandate/                             MandateHomeView          4+

  GET /governance/mandate/\<str:record_type\>/         MandateListView          4+

  GET /governance/mandate/record/\<uuid:record_id\>/   MandateDetailView        4+

  GET /governance/keys/                                KeysListView             3+

  GET /governance/keys/\<uuid:record_id\>/             KeysDetailView           3+

  GET                                                  LinkedRecordsPartial     3+
  /governance/htmx/relationships/\<uuid:record_id\>/                            

  GET /governance/htmx/versions/\<uuid:record_id\>/    VersionHistoryPartial    4+

  POST /governance/htmx/record/create/                 RecordCreateView         3+ (5 for
                                                                                Handbook)

  GET+POST /governance/htmx/record/\<uuid:id\>/edit/   RecordEditView           5 (Handbook)

  POST /governance/htmx/record/\<uuid:id\>/lock/       RecordLockView           5 (Handbook)

  POST /governance/htmx/record/\<uuid:id\>/supersede/  RecordSupersedeView      5 (Handbook)

  POST /governance/htmx/relationship/create/           RelationshipCreateView   5

  GET /api/governance/health/                          GovernanceHealthView     any
  -----------------------------------------------------------------------------------------------

**HTMX Interaction Patterns**

**1 --- Record list with type filter**

> \<!\-- Library landing --- clicking a type loads list via HTMX \--\>
>
> \<button hx-get=\'/governance/library/principle/\'
>
> hx-target=\'#governance-content\'
>
> hx-push-url=\'true\'\>
>
> Principles
>
> \</button\>

**2 --- Search within a type**

> \<!\-- HTMX typeahead search within the library list \--\>
>
> \<input type=\'text\' name=\'q\'
>
> hx-get=\'/governance/library/principle/\'
>
> hx-trigger=\'keyup changed delay:300ms\'
>
> hx-target=\'#record-list\'
>
> placeholder=\'Search principles\...\'\>

**3 --- Record detail with Linked Records panel**

> \<!\-- Detail view loads inline; Linked Records panel is a separate
> HTMX call \--\>
>
> \<div hx-get=\'/governance/htmx/relationships/{{ record.id }}/\'
>
> hx-trigger=\'load\'
>
> hx-target=\'#linked-records-panel\'\>
>
> Loading linked records\...
>
> \</div\>

**4 --- Lock record (Level 5)**

> \<!\-- Lock confirmation --- HTMX swap replaces the action area \--\>
>
> \<button hx-post=\'/governance/htmx/record/{{ record.id }}/lock/\'
>
> hx-confirm=\'Lock this record? It cannot be edited after locking.\'
>
> hx-target=\'#record-status-area\'
>
> hx-swap=\'outerHTML\'\>
>
> Lock Record
>
> \</button\>

**5 --- Supersede a locked record (Level 5)**

> \<!\-- Supersede triggers creation of a new draft version \--\>
>
> \<button hx-post=\'/governance/htmx/record/{{ record.id
> }}/supersede/\'
>
> hx-confirm=\'Create a new version of this record?\'
>
> hx-target=\'#governance-content\'
>
> hx-push-url=\'true\'\>
>
> Create New Version
>
> \</button\>

**6 --- Add HRS relationship link (Level 5)**

> \<!\-- Inline form to add a Relationship from this record \--\>
>
> \<form hx-post=\'/governance/htmx/relationship/create/\'
>
> hx-target=\'#linked-records-panel\'
>
> hx-swap=\'outerHTML\'\>
>
> \<input type=\'hidden\' name=\'from_record_id\' value=\'{{ record.id
> }}\'\>
>
> \<select name=\'relationship_type\'\>
>
> \<option\>part_of\</option\>
>
> \<option\>derived_from\</option\>
>
> \<option\>aligns_with\</option\>
>
> \<option\>authorised_by\</option\>
>
> \<option\>references\</option\>
>
> \<option\>has_subject\</option\>
>
> \<option\>has_entity\</option\>
>
> \</select\>
>
> \<!\-- HTMX typeahead to search target record \--\>
>
> \<input type=\'text\' name=\'to_record_search\'
>
> hx-get=\'/api/records/?record_family=governance&search=\'
>
> hx-trigger=\'keyup changed delay:300ms\'
>
> hx-target=\'#link-search-results\'\>
>
> \<button type=\'submit\'\>Add Link\</button\>
>
> \</form\>

**Versioning --- Transaction Pattern**

**Supersede flow (atomic)**

When a Level 5 operator supersedes a locked record, the Governance App
view executes the following in transaction.atomic():

> \# Step 1 --- Create new draft version
>
> new_record = requests.post(\'/api/records/\', json={
>
> \'record_class\': old_record\[\'record_class\'\],
>
> \'record_family\': old_record\[\'record_family\'\],
>
> \'record_type\': old_record\[\'record_type\'\],
>
> \'title\': old_record\[\'title\'\],
>
> \'content\': old_record\[\'content\'\], \# operator edits this
>
> \'version\': old_record\[\'version\'\] + 1,
>
> \'previous_version_id\': old_record\[\'id\'\],
>
> \'tenant_id\': old_record\[\'tenant_id\'\],
>
> \'status\': \'draft\',
>
> \'tags\': old_record\[\'tags\'\],
>
> \'custom_fields\': old_record\[\'custom_fields\'\],
>
> \'metadata\': {\'source_app\': \'governance\'},
>
> \'permissions\': old_record\[\'permissions\'\],
>
> })
>
> \# Step 2 --- Mark old record as superseded
>
> requests.patch(f\'/api/records/{old_record\[\"id\"\]}/\', json={
>
> \'status\': \'superseded\',
>
> \'superseded_by\': new_record\[\'id\'\],
>
> })
>
> *If Step 2 fails, Step 1 is rolled back via transaction.atomic(). The
> operator is shown an error and the old record remains locked and
> unchanged.*

**Permission Check Summary**

  ------------------------------------------------------------------------
  **Action**          **Record type group** **Required    **Check
                                            level**       location**
  ------------------- --------------------- ------------- ----------------
  Read Reference      class, principle,     Level 3+      View layer + DRF
  Library records     concept,                            
                      divine_pattern,                     
                      subject, entity,                    
                      narrative, framework                

  Read Mandate branch mandate, statement,   Level 4+      View layer + DRF
  records             programme, protocol,                
                      procedure                           

  Create / edit any   All governance types  Level 5       View layer + DRF
  Handbook record                                         

  Lock any Handbook   All governance types  Level 5       View layer
  record                                                  

  Supersede a locked  All governance types  Level 5       View layer
  Handbook record                                         

  Create / edit /     record_family:        Level 3+ (own View layer
  read Key Records    reference,            records only) 
                      record_type: key                    

  Create / edit       record_family:        Level 1+      View layer
  journal Article     journal, record_type:               
                      article                             

  Create Relationship Any governance type   Level 5       View layer
  on Handbook records                                     
  ------------------------------------------------------------------------

> *The Handbook tenant short-circuit in Part 7 is amended in v9: Level
> 3+ read access for Reference Library types, Level 4+ read for Mandate
> branch types, Level 5 for all writes. The view layer enforces the
> type-group split. The DRF layer enforces the minimum Level 3 floor on
> all Handbook reads.*

**governance.css --- Design Notes**

governance.css follows the mobile-first, CSS variables pattern
established by the other app stylesheets. The governance colour palette
is distinct from community (blue) and activity (green) --- it uses a
deep violet/purple accent to signal authority and the apostolic
register.

  --------------------------------------------------------------------------
  **Token**           **Value**      **Usage**
  ------------------- -------------- ---------------------------------------
  \--gov-accent       #7B5EA7        Branch headers, status badges, section
                                     labels

  \--gov-light        #EEE8F5        Card backgrounds, panel fills

  \--gov-border       #C9B8E8        Panel borders, dividers

  \--gov-locked       #2E5D9E        Locked status badge (blue --- carries
                                     authority)

  \--gov-superseded   #888888        Superseded status badge (grey ---
                                     archived)

  \--gov-draft        #E8A020        Draft status badge (amber --- in
                                     progress)
  --------------------------------------------------------------------------

**Build Phases**

**Phase 1 --- MVP (this task)**

-   Scaffold governance Django app, urls.py, views.py, services.py,
    governance.css

-   Reference Library browser: all eight record_type sections, list +
    detail views

-   Property Attributes panel on detail view

-   Linked Records panel (F4) --- read-only, HTMX partial

-   Mandate branch browser: all five record_type sections, list + detail
    views

-   Version History panel (F5) --- HTMX partial

-   Level 5 authorship: create / edit / lock / supersede for all
    Handbook types

-   HRS relationship create (Level 5)

-   My Keys: list, detail, create, edit

-   Permission gates at view layer for all three surfaces

-   Health check endpoint

-   Commit: git add . && git commit -m \'feat: governance app\'

**Phase 2 --- Deferred**

-   calendar record type --- Great Calendar, seasons, appointed times;
    custom_fields specification and Calendar App integration

-   Full HRS graph visualisation --- network diagram of governance
    record relationships

-   Approval queue --- submitted status UI (Level 4 submits → Level 5
    approves → auto-lock)

-   Tenant-scoped governance records for Level 4 district/province
    stewards

-   Rich text editor for governance record content (markdown textarea in
    MVP)

-   Full-text search across entire Handbook

-   Paraclete integration --- governance digest, mandate alignment
    suggestions, discipline prompts sourced from Mandate records

-   article record type --- accessible from the Governance App journal
    input panel

**Exit Criteria**

The Governance App build is complete when:

  -----------------------------------------------------------------------
  **Criterion**                   **Test**
  ------------------------------- ---------------------------------------
  Level 3 user can browse all     Navigate to /governance/library/ ---
  Reference Library record types  all eight type sections load; record
                                  detail loads with Property Attributes
                                  and Linked Records panels

  Level 4 user can read Mandate   Navigate to /governance/mandate/ ---
  branch records but cannot write records load; no create/edit/lock
                                  controls visible

  Level 5 user can create, edit,  Full create → lock → supersede flow
  lock, and supersede a           produces a version chain with
  governance record               previous_version_id and superseded_by
                                  set correctly

  Version history panel shows     Superseded record detail shows v1
  correct chain                   (superseded) → v2 (current)

  Linked Records panel loads HRS  Record with Relationship rows shows
  relationships                   correct linked record titles and types

  Scripture links render verse    Relationship with bible_verse_id shows
  text                            verse text from BibleVerse table

  Level 3 user can create and     POST to /governance/htmx/record/create/
  edit own Key Records            with record_family: \'reference\',
                                  record_type: \'key\' succeeds; appears
                                  in My Keys list

  Level 2 user cannot access the  /governance/ returns 403 for Level 2
  Governance App                  user

  Health check passes             GET /api/governance/health/ returns
                                  {status: \'ok\'}
  -----------------------------------------------------------------------

ICS Platform · Task 5.5 Governance App · System Design · 2026-04-10


---

# ICS Platform — Django Templates + HTMX Migration
## Architectural Decision Record + Migration Plan

> **Version:** 1.0 — 2026-04-07
> **Status:** LOCKED
> **Scope:** All app UI work going forward. Supersedes the vanilla JS IIFE frontend
> layer described in build roadmap v2 Tasks 2.2, 3.2, 4.1–4.2, 5.1–5.6, 6.2, 7.1.
> DRF endpoints, Django models, serializers, signals — all unchanged.

---

## Part 1 — Architectural Decision

### 1.1 The Decision

All ICS app UI is rendered via **Django templates + HTMX**. The existing vanilla JS
engine service files (`records.service.js`, `activity.service.js`, etc.) are
**not built**. The existing frontend IIFE app files (`records-app.js`, etc.) are
**not built**. Django views serve HTML pages; HTMX handles dynamic interactions
within those pages.

DRF endpoints are **not retired**. They remain the canonical data API for mobile
clients and future integrations. Django template views call the Django ORM and
service layer directly — they do not call DRF endpoints internally.

### 1.2 What Replaces What

| Old (vanilla JS) | New (Django templates + HTMX) |
|---|---|
| `records-app.js` IIFE module | `records/` Django app views + templates |
| `records.service.js` fetch calls | Django ORM calls inside views |
| `learn-app.js` + `learn.service.js` | `learn/` Django app views + templates |
| `activity-app.js` + `activity.service.js` | `activity/` Django app views + templates |
| `auth.js` register/login/logout | Django `django.contrib.auth` views + forms |
| `router.js` auth guard + navigation | Django `@login_required` decorator + middleware |
| `storage.js` data persistence role | **Removed** — Django session handles auth state |

| Kept unchanged | Reason |
|---|---|
| `storage.js` (UI state role only) | Theme preference, sidebar state — not persisted to DB |
| All CSS files (`main.css`, `navbar.css`, `learn.css`, etc.) | Design system is unchanged |
| `navbar.js` for app drawer toggle | Pure UI state interaction — no data involved |
| DRF endpoints at `/api/…` | Mobile + future integration layer |
| Django models, serializers, signals | Backend is unchanged |

### 1.3 Where Vanilla JS Remains Appropriate

Vanilla JS is retained **only** for interactions that are:
- Pure UI state (no server round-trip needed), **or**
- Browser API access (localStorage for theme, matchMedia for responsive hints)

| Vanilla JS use | File | Rationale |
|---|---|---|
| Theme toggle (light/dark/system) | `storage.js` | Reads/writes `localStorage`; no server state |
| App drawer open/close | `navbar.js` | CSS class toggle only |
| Navbar scroll-hide behaviour | `navbar.js` | IntersectionObserver — no data |
| Bottom nav active state | `navbar.js` | Derived from current URL |
| HTMX `htmx:afterSwap` hooks | Inline `<script>` in templates | Re-initialise CSS state after partial swap |

Everything else — form submissions, list loading, progress updates, detail views,
search, filtering, pagination — is HTMX + Django views.

### 1.4 HTMX Usage Patterns

**Pattern A — Form submissions (create/update)**

```html
<form hx-post="{% url 'records:create' %}"
      hx-target="#record-list"
      hx-swap="afterbegin"
      hx-on::after-request="this.reset()">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Save</button>
</form>
```

The view returns a single rendered `_record_card.html` partial. HTMX prepends it
to the list. No full page reload. No JavaScript written by us.

**Pattern B — List views with pagination / filtering**

```html
<div id="record-list"
     hx-get="{% url 'records:list' %}"
     hx-trigger="load"
     hx-indicator="#list-spinner">
  {# populated by HTMX on page load #}
</div>

<input type="search" name="q"
       hx-get="{% url 'records:list' %}"
       hx-target="#record-list"
       hx-trigger="keyup changed delay:300ms"
       hx-include="[name='q']">
```

**Pattern C — Inline detail expand**

```html
<li hx-get="{% url 'records:detail' record.id %}"
    hx-target="#detail-panel"
    hx-swap="innerHTML"
    hx-push-url="true">
  {{ record.title }}
</li>
```

`hx-push-url="true"` keeps the browser URL in sync so deep links and back-button
work correctly.

**Pattern D — Progress bar / queue refresh (Learn App)**

```html
<div id="progress-bar"
     hx-get="{% url 'learn:progress' activity.id %}"
     hx-trigger="every 5s"
     hx-swap="outerHTML">
  <progress value="{{ activity.progress }}" max="100"></progress>
</div>
```

**Pattern E — Delete with confirmation**

```html
<button hx-delete="{% url 'records:delete' record.id %}"
        hx-target="#record-{{ record.id }}"
        hx-swap="outerHTML swap:0.3s"
        hx-confirm="Delete this record?">
  Delete
</button>
```

The view returns an empty `<span>` (or nothing) and HTMX removes the element.

### 1.5 URL Routing Strategy

Two URL namespaces exist side by side:

```
/api/…          DRF endpoints (JSON, token auth) — mobile + integrations
/…              Django template views (HTML, session auth) — web UI
```

URL routing rules:

```python
# ics_project/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),          # DRF router — all /api/ routes
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', include('accounts.urls')),
    path('records/', include('records.urls', namespace='records')),
    path('learn/', include('learn.urls', namespace='learn')),
    path('activity/', include('activity.urls', namespace='activity')),
    path('community/', include('community.urls', namespace='community')),
    path('governance/', include('governance.urls', namespace='governance')),
    path('', include('dashboard.urls', namespace='dashboard')),
]
```

Template view URL patterns follow a consistent REST-style shape:

```python
# records/urls.py
app_name = 'records'
urlpatterns = [
    path('',                   views.RecordListView.as_view(),   name='list'),
    path('create/',            views.RecordCreateView.as_view(), name='create'),
    path('<uuid:pk>/',         views.RecordDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/',    views.RecordUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/',  views.RecordDeleteView.as_view(), name='delete'),
]
```

HTMX partial requests are distinguished from full-page requests via the
`HX-Request` header. Views return partials when this header is present:

```python
class RecordListView(LoginRequiredMixin, View):
    def get(self, request):
        records = Record.objects.filter(tenant=request.user.active_tenant)
        if request.headers.get('HX-Request'):
            return render(request, 'records/_list.html', {'records': records})
        return render(request, 'records/list.html', {'records': records})
```

### 1.6 Authentication Strategy

Django session authentication for template views. DRF token authentication for
`/api/` routes. These are parallel, independent auth stacks.

```
Web UI:   Browser → Django session cookie → @login_required → view
Mobile:   App → Authorization: Token {token} → DRF TokenAuthentication → DRF view
```

The `django.contrib.auth` login view sets the session. No JWT. No localStorage
token. The `router.js` auth guard is retired; Django's `@login_required` and
`LoginRequiredMixin` are the auth guard.

`LOGIN_URL = '/accounts/login/'` in `settings/base.py`. Unauthenticated requests
to any `@login_required` view are redirected there.

Post-login redirect: `LOGIN_REDIRECT_URL = '/'` (dashboard).
Post-logout redirect: `LOGOUT_REDIRECT_URL = '/accounts/login/'`.

### 1.7 CSRF

Django CSRF middleware is active (already in the default middleware stack). HTMX
must send the CSRF token on all state-mutating requests. Add this once in
`base.html`:

```html
<script>
  document.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] =
      document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
  });
</script>
```

This is the **only** piece of vanilla JS wiring HTMX requires. It lives in
`base.html` and never needs to be repeated.

---

## Part 2 — Template Structure

### 2.1 Directory Layout

```
ics/
  templates/
    base.html                     ← master shell: navbar, drawer, bottom nav, theme
    base_partial.html             ← HTMX-only base: no chrome, just main content
    components/
      _navbar.html
      _app_drawer.html
      _bottom_nav.html
      _toast.html
      _spinner.html
      _empty_state.html
      _record_card.html
      _activity_card.html
    accounts/
      login.html
      register.html
      profile.html
    records/
      list.html
      _list.html                  ← HTMX partial
      detail.html
      _detail.html                ← HTMX partial
      create.html
      _form.html                  ← HTMX partial (form only)
      edit.html
    learn/
      index.html
      _my_learning.html
      _catalogue.html
      _lesson_viewer.html
      _progress_bar.html
      _cert_queue.html
    activity/
      list.html
      _list.html
      detail.html
    dashboard/
      index.html
      _digest_widget.html
      _activity_widget.html
    community/
      index.html
      _member_list.html
    governance/
      index.html
      _mandate_list.html
```

Naming convention:
- Files prefixed with `_` are **partials** — they return fragments, not full pages.
- Files without `_` prefix are **full pages** — they extend `base.html`.

### 2.2 `base.html` — Master Shell

This is the single source of truth for the page chrome. Every full-page template
extends this. It carries the navbar, app drawer, bottom nav, theme system, and
all CSS/JS load order.

```html
<!DOCTYPE html>
<html lang="en" data-theme="system">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}ICS{% endblock %} — Integrated Community System</title>

  {# Design system — load order is fixed; do not reorder #}
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  <link rel="stylesheet" href="{% static 'css/navbar.css' %}">
  {% block extra_css %}{% endblock %}

  {# HTMX — loaded in <head> so hx-* attributes work on first paint #}
  <script src="{% static 'js/htmx.min.js' %}" defer></script>

  {# UI state only — theme + drawer. Loaded before body renders to prevent flash #}
  <script src="{% static 'js/storage.js' %}"></script>
</head>
<body class="ics-shell" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

  {# Top navbar #}
  {% include "components/_navbar.html" %}

  {# App drawer (slide-in overlay) #}
  {% include "components/_app_drawer.html" %}

  {# Main content region — all page content swaps happen here #}
  <main id="main-content" class="ics-main" role="main">
    {# Toast notification anchor #}
    <div id="toast-container" aria-live="polite"></div>

    {% block content %}{% endblock %}
  </main>

  {# Bottom navigation — mobile only #}
  {% include "components/_bottom_nav.html" %}

  {# CSRF wiring for HTMX state-mutating requests #}
  <script>
    document.addEventListener('htmx:configRequest', (e) => {
      e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
    });
  </script>

  {# Navbar UI: app drawer toggle, scroll-hide, bottom nav active state #}
  <script src="{% static 'js/navbar.js' %}" defer></script>

  {% block extra_js %}{% endblock %}
</body>
</html>
```

**Notes on `hx-headers`:** Using `hx-headers` on `<body>` is an alternative CSRF
strategy to the `htmx:configRequest` event listener. Both are shown; keep one.
The event listener approach is more explicit and easier to audit — prefer it.

### 2.3 `base_partial.html` — HTMX Fragment Base

Partials must not extend `base.html` (that would return the full chrome on every
HTMX swap). They extend this instead — which is empty:

```html
{# base_partial.html — intentionally empty. Partials extend this. #}
{% block content %}{% endblock %}
```

Partials that need no base at all can simply skip `{% extends %}` entirely. The
convention is to omit `extends` in partials — the template is a fragment by
definition.

### 2.4 Component Pattern — `_navbar.html`

```html
{# components/_navbar.html #}
<header class="ics-navbar" role="banner">
  <button class="ics-navbar__drawer-btn"
          aria-label="Open app menu"
          aria-expanded="false"
          aria-controls="app-drawer"
          id="drawer-toggle">
    <span class="material-icon">menu</span>
  </button>

  <a href="{% url 'dashboard:index' %}" class="ics-navbar__wordmark">ICS</a>

  <nav class="ics-navbar__actions" aria-label="Top actions">
    {% if user.is_authenticated %}
      <a href="{% url 'accounts:notifications' %}"
         class="ics-navbar__icon-btn"
         aria-label="Notifications"
         hx-get="{% url 'accounts:notifications_count' %}"
         hx-trigger="load, every 60s"
         hx-target="#notif-badge">
        <span class="material-icon">notifications</span>
        <span id="notif-badge" class="badge"></span>
      </a>
      <a href="{% url 'accounts:profile' %}" class="ics-navbar__avatar">
        {% if user.avatar_url %}
          <img src="{{ user.avatar_url }}" alt="{{ user.display_name }}">
        {% else %}
          <span class="avatar-initials">{{ user.display_name|first }}</span>
        {% endif %}
      </a>
    {% else %}
      <a href="{% url 'accounts:login' %}" class="btn btn--ghost">Sign in</a>
    {% endif %}
  </nav>
</header>
```

### 2.5 App-Specific CSS Load

Each app that has its own CSS (e.g. `learn.css`) loads it via the `extra_css`
block in the full-page template:

```html
{# learn/index.html #}
{% extends "base.html" %}
{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/learn.css' %}">
{% endblock %}
{% block content %}
  ...
{% endblock %}
```

This keeps CSS scoped to where it is needed without loading everything globally.

---

## Part 3 — Script Load Order

The final, locked load order for the Django template era:

```
HEAD (blocking)
  htmx.min.js          — HTMX engine. Must be present before body renders.
  storage.js           — Theme init. Must run before body renders to prevent flash.

BODY end (defer)
  navbar.js            — App drawer toggle, scroll-hide, bottom nav active state.
  [app-specific JS]    — Only if a page needs minor vanilla JS (e.g. quiz timer).
```

**What is gone:**
- `router.js` — retired. Django `@login_required` + `LoginRequiredMixin` replace it.
- `auth.js` — retired. `django.contrib.auth` views replace it.
- All `*.service.js` files — **never built**. Django views call ORM directly.
- All `*-app.js` IIFE files — **never built**. Django template views replace them.

**What `storage.js` now does (trimmed scope):**

```javascript
// storage.js — UI state only. No data persistence. No auth tokens.
const ICSStorage = (() => {
  const THEME_KEY = 'ics_theme';

  function getTheme() {
    return localStorage.getItem(THEME_KEY) ?? 'system';
  }

  function setTheme(theme) {
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.setAttribute('data-theme', theme);
  }

  // Apply theme on load (prevents flash)
  setTheme(getTheme());

  return { getTheme, setTheme };
})();
```

Everything else that was in `storage.js` (user objects, records cache, session
token) is removed. Those live in the Django session and PostgreSQL.

---

## Part 4 — Migration Plan

### Phase M0 — Install HTMX + Update Settings

**Files:**
- Download: `frontend/assets/js/htmx.min.js` (or `static/js/htmx.min.js`)
- Modify: `ics_project/settings/base.py`
- Modify: `ics_project/urls.py`

**Step 1:** Download HTMX 1.9.x minified from `https://unpkg.com/htmx.org/dist/htmx.min.js`
and place at `static/js/htmx.min.js`.

**Step 2:** Add to `settings/base.py`:
```python
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
```

**Step 3:** Add to `settings/base.py` middleware (session must be present):
```python
MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    ...
]
```

**Step 4:** Wire `django.contrib.auth.urls` in `ics_project/urls.py`:
```python
path('accounts/', include('django.contrib.auth.urls')),
```

Commit: `git commit -m "chore: install htmx, configure template settings, wire auth urls"`

---

### Phase M1 — Migrate Navigation System

The navbar, app drawer, bottom nav, and theme system move from `index.html` +
inline JS into Django template components. The CSS is **unchanged**.

**Files:**
- Create: `templates/base.html`
- Create: `templates/components/_navbar.html`
- Create: `templates/components/_app_drawer.html`
- Create: `templates/components/_bottom_nav.html`
- Create: `templates/components/_toast.html`
- Create: `templates/components/_spinner.html`
- Trim: `static/js/storage.js` (remove data persistence, keep theme only)
- Keep: `static/js/navbar.js` (unchanged — pure UI state)
- Keep: `static/css/main.css`, `static/css/navbar.css` (unchanged)

**Step 1:** Create `templates/base.html` per the spec in Part 2.2 above.

**Step 2:** Extract navbar HTML from `index.html` → `templates/components/_navbar.html`.
Port hard-coded links to `{% url %}` tags. The structure and CSS classes are
identical — only the link hrefs change.

**Step 3:** Extract app drawer HTML → `templates/components/_app_drawer.html`.
App drawer links become `{% url %}` tags. Active state is set server-side:
```html
<a href="{% url 'records:list' %}"
   class="drawer-item {% if request.resolver_match.app_name == 'records' %}drawer-item--active{% endif %}">
  Records
</a>
```

**Step 4:** Extract bottom nav → `templates/components/_bottom_nav.html`.
Same active-state pattern as above.

**Step 5:** Trim `storage.js` to theme-only per the spec in Part 3.

**Step 6:** Create a smoke-test view:
```python
# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'dashboard/index.html')
```
```python
# dashboard/urls.py
app_name = 'dashboard'
urlpatterns = [path('', views.index, name='index')]
```
```html
{# templates/dashboard/index.html #}
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
  <h1>Dashboard</h1>
{% endblock %}
```

**Step 7:** Visit `http://localhost:8000/`. Verify:
- Navbar renders with correct links
- App drawer opens/closes via `navbar.js`
- Theme toggle works via `storage.js`
- Bottom nav highlights correct item
- `@login_required` redirects to `/accounts/login/`

Commit: `git commit -m "feat: base.html, nav components, theme system — Django templates"`

---

### Phase M2 — Migrate Auth Flows

The register/login/logout flows move from `auth.js` (DRF fetch calls) to Django
auth views. The DRF `/api/auth/` endpoints remain for mobile.

**Files:**
- Create: `templates/accounts/login.html`
- Create: `templates/accounts/register.html`
- Create: `templates/accounts/profile.html`
- Create: `accounts/forms.py` (registration form)
- Modify: `accounts/views.py` (add RegisterView)
- Modify: `accounts/urls.py`
- Remove from load order: `auth.js`, `router.js`

**Step 1:** `accounts/forms.py`:
```python
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    display_name = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['email', 'display_name', 'password']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned
```

**Step 2:** `accounts/views.py` — RegisterView:
```python
from django.contrib.auth import login
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import RegisterForm

class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('dashboard:index')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        login(self.request, user)
        return super().form_valid(form)
```

**Step 3:** `templates/accounts/login.html`:
```html
{% extends "base.html" %}
{% block title %}Sign In{% endblock %}
{% block content %}
<div class="auth-card">
  <h1>Sign In</h1>
  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn--primary">Sign In</button>
  </form>
  <p>No account? <a href="{% url 'accounts:register' %}">Register</a></p>
</div>
{% endblock %}
```

**Step 4:** `templates/accounts/register.html` — same pattern as login.

**Step 5:** Verify: register → auto-login → redirect to dashboard. Logout →
redirect to `/accounts/login/`.

Commit: `git commit -m "feat: Django auth views — register, login, logout"`

---

### Phase M3 — Migrate Records App

The Records app UI moves from the vanilla JS IIFE `records-app.js` to Django
class-based views + HTMX partials.

**Files:**
- Create: `records/views.py` (CBVs)
- Create: `records/urls.py`
- Create: `records/forms.py`
- Create: `templates/records/list.html`
- Create: `templates/records/_list.html` (HTMX partial)
- Create: `templates/records/detail.html`
- Create: `templates/records/_detail.html` (HTMX partial)
- Create: `templates/records/_form.html` (HTMX partial)
- Create: `templates/records/create.html`
- Create: `templates/records/edit.html`
- Create: `templates/components/_record_card.html`

**Step 1:** `records/forms.py` — ModelForm wrapping the Record model:
```python
from django import forms
from .models import Record

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['title', 'record_type', 'record_class', 'record_family',
                  'body', 'status', 'visibility']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }
```

**Step 2:** `records/views.py`:
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Record
from .forms import RecordForm

class RecordListView(LoginRequiredMixin, ListView):
    model = Record
    context_object_name = 'records'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_list.html']
        return ['records/list.html']

    def get_queryset(self):
        qs = Record.objects.filter(
            tenant=self.request.user.active_tenant
        ).order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

class RecordDetailView(LoginRequiredMixin, DetailView):
    model = Record
    context_object_name = 'record'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_detail.html']
        return ['records/detail.html']

class RecordCreateView(LoginRequiredMixin, CreateView):
    model = Record
    form_class = RecordForm
    success_url = reverse_lazy('records:list')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_form.html']
        return ['records/create.html']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.tenant = self.request.user.active_tenant
        return super().form_valid(form)

class RecordUpdateView(LoginRequiredMixin, UpdateView):
    model = Record
    form_class = RecordForm
    success_url = reverse_lazy('records:list')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_form.html']
        return ['records/edit.html']

class RecordDeleteView(LoginRequiredMixin, DeleteView):
    model = Record
    success_url = reverse_lazy('records:list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if request.headers.get('HX-Request'):
            return HttpResponse('')  # HTMX removes the element
        return response
```

**Step 3:** `templates/records/list.html`:
```html
{% extends "base.html" %}
{% block title %}Records{% endblock %}
{% block content %}
<div class="records-page">
  <header class="page-header">
    <h1>Records</h1>
    <a href="{% url 'records:create' %}" class="btn btn--primary">New Record</a>
  </header>

  <input type="search"
         name="q"
         placeholder="Search records…"
         hx-get="{% url 'records:list' %}"
         hx-target="#record-list"
         hx-trigger="keyup changed delay:300ms"
         hx-include="[name='q']"
         class="search-input">

  <div id="record-list"
       hx-get="{% url 'records:list' %}"
       hx-trigger="load"
       hx-indicator="#list-spinner">
    {% include "components/_spinner.html" with id="list-spinner" %}
  </div>
</div>
{% endblock %}
```

**Step 4:** `templates/records/_list.html` (the partial returned by HTMX):
```html
{% for record in records %}
  {% include "components/_record_card.html" %}
{% empty %}
  {% include "components/_empty_state.html" with message="No records yet." %}
{% endfor %}
```

**Step 5:** `templates/components/_record_card.html`:
```html
<article class="record-card" id="record-{{ record.id }}"
         hx-get="{% url 'records:detail' record.id %}"
         hx-target="#detail-panel"
         hx-push-url="true">
  <h3 class="record-card__title">{{ record.title }}</h3>
  <span class="badge badge--{{ record.record_class }}">{{ record.record_type }}</span>
  <time class="record-card__date">{{ record.created_at|date:"d M Y" }}</time>
</article>
```

**Step 6:** Verify all CRUD operations: create, list, search, detail, edit, delete.
Verify HTMX partials swap correctly without full page reload.

Commit: `git commit -m "feat: records app — Django CBVs + HTMX partials"`

---

### Phase M4 — Update `settings/base.py` Static Files

Move static assets from `frontend/assets/` to Django's standard `static/`
directory so `{% static %}` template tags resolve correctly.

```python
# settings/base.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

File moves (copy, not delete — verify before removing originals):
```
frontend/assets/css/main.css    → static/css/main.css
frontend/assets/css/navbar.css  → static/css/navbar.css
frontend/assets/js/storage.js   → static/js/storage.js
frontend/assets/js/navbar.js    → static/js/navbar.js
htmx.min.js                     → static/js/htmx.min.js
```

All app-specific CSS files follow the same pattern (`learn.css`, `records.css`).

Commit: `git commit -m "chore: migrate static assets to Django static/ directory"`

---

## Part 5 — What This Means for Remaining App Builds

All remaining apps (Activity, Learn, Community, Governance, Dashboard, Profile,
Settings, Notifications) follow **Phase M3** as their template. For each app:

1. Create Django app + models (unchanged from roadmap)
2. Create DRF serializers + views + URLs at `/api/<app>/` (unchanged)
3. Create Django CBVs + template views at `/<app>/`
4. Create `templates/<app>/` directory with `list.html`, `detail.html`, partials
5. HTMX handles list loading, form submission, and any polling interactions
6. No `<app>.service.js`, no `<app>-app.js` — these are not built

**Learn App specifically:** Phases A and B from the Learn App system design
(Django `learn` app, models, DRF endpoints, signals) are unchanged. Phases C–G
(UI layer) are implemented as Django template views + HTMX, not `learn-app.js`.
`learn.css` is carried forward identically.

---

## Part 6 — Decision Log

| Decision | Rationale |
|---|---|
| HTMX over React/Vue | No build toolchain. Preserves Django template rendering. Consistent with no-JS-framework constraint. |
| Django session auth (not JWT in browser) | Simpler. No token storage in `localStorage`. CSRF + session cookies are the browser-native security model. |
| DRF endpoints retained | Mobile clients exist. Future integrations exist. Template views and DRF views share the same ORM layer — no duplication of business logic. |
| `hx-push-url="true"` on detail views | Deep links and back-button must work. HTMX does not push URL by default. |
| CBVs over function views | `LoginRequiredMixin`, `get_template_names()` override for partial detection — CBVs make these patterns clean and consistent. |
| Partials named with `_` prefix | Unambiguous convention. Any template starting with `_` is a fragment. Full-page templates never start with `_`. |
| No `base_partial.html` extends | Partials simply omit `{% extends %}`. They are fragments by definition. An explicit empty base adds indirection with no benefit. |
| CSS unchanged | The design system is a solved problem. Migrating to HTMX is an engine swap, not a redesign. |

---

*End of document. This ADR supersedes the vanilla JS IIFE frontend layer described
in build roadmap v2. All subsequent app build sessions should reference this
document as the UI architecture specification.*
