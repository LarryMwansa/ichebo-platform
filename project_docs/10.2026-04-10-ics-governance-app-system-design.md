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
