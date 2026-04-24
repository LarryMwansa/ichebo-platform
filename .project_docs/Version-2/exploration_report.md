# ICS Platform Exploration Report

The **ICS (Ichebo Christian Services) Platform** is a Django-based digital twin of the "Kingdom Governance System (KGS)". It uses a highly flexible, record-based architecture designed for multi-tenant, mobile-first interaction.

## Architecture Overview

### Core Stack
- **Backend**: Django 5.2 (LTS) + Django REST Framework.
- **Frontend**: Vanilla JS modules + HTMX for partial page updates and interactive UI.
- **Database**: PostgreSQL (Production) / SQLite (Development).
- **Caching**: File-based caching.
- **Styling**: Vanilla CSS with a strong emphasis on variables (`static/css/variables.css`).

### Key Concepts

#### 1. The Record System (`records` app)
The `Record` model is the central data structure. Instead of having dozens of specific models for different entities, the system uses a generic `Record` with metadata:
- **`record_class`**: (Personal, Organizational, Governance)
- **`record_family`**: (Journal, Governance, Activity, Learning, Bible, etc.)
- **`record_type`**: Specific subtype (e.g., 'key', 'mandate', 'law').
- **Status & Versioning**: Support for version chains and superseding records.

#### 2. Relationships
A polymorphic-like relationship model allows connecting any `Record` to:
- Another `Record`.
- A `BibleVerse` (via the `bible` app).
This enables deep cross-referencing between governance documents and scripture.

#### 3. Competence Levels
Access control is tied to a `competence_level` field on the User model:
- **Level 3+**: Can view/create personal Keys and Reference Library.
- **Level 4+**: Access to the Mandate branch.
- **Level 5**: Full administrative/editing capabilities for Handbook records.

## App Structure

| App | Purpose |
| :--- | :--- |
| `accounts` | Custom User model, competence-based permissions, and auth. |
| `records` | Core storage for all entities and their inter-relationships. |
| `bible` | Bible translations, books, and verses. Used for cross-referencing. |
| `governance` | The "Handbook" logic (Library and Mandates) and personal "Keys". |
| `activity` | Likely tracks tasks or events (needs further investigation). |
| `tenants` | Multi-tenancy support for different organizations/groups. |
| `core` | Shared utilities, context processors, and base templates. |
| `paraclete` | Mentioned as an origin for records (AI/system assistant?). |

## Current Focus (Inferred from Open Files)
The user is currently working on:
1. **Styling**: `variables.css` suggests a design system refinement.
2. **Governance UI**: `_mandate_detail.html` and `views.py` indicate work on the Mandate branch.
3. **Bible Integration**: `_annotation_panel.html` and `_chapter.html` show work on the scripture exploration interface.

## Next Exploration Steps
- [ ] Investigate `activity` app to see how tasks/logs are handled.
- [ ] Explore `paraclete` to understand the AI integration aspect.
- [ ] Review the `static/js` folder to understand the frontend module system.
