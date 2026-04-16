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
