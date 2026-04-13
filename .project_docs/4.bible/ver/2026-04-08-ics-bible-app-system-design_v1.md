# ICS Bible App — System Design & Build Roadmap

> **Version:** v1 — 2026-04-08
> **Status:** LOCKED — pending data contract amendment (Part 0.3 below)
> **UI Architecture:** Django templates + HTMX (per HTMX ADR — 2026-04-07)
> **Data Contract reference:** `2026-04-08-ics-platform-data-contract_v5.md`
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
  id:          "uuid",
  code:        "string",          # 'KJV', 'ASV', 'WEB'
  name:        "string",          # 'King James Version'
  language:    "string",          # 'en', 'af', 'zu'
  is_default:  "boolean",         # exactly one row is True — KJV at setup
  is_public:   "boolean",         # False = licensed translation, restricted
  created_at:  "ISO-8601"
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)   # 'KJV', 'ASV', 'WEB'
    name = models.CharField(max_length=100)               # 'King James Version'
    language = models.CharField(max_length=10, default='en')
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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

**Source data format expected (one file per translation):**

```json
{
  "translation": "KJV",
  "name": "King James Version",
  "language": "en",
  "books": [
    {
      "code": "GEN",
      "name": "Genesis",
      "testament": "OT",
      "order": 1,
      "chapters": [
        {
          "chapter": 1,
          "verses": [
            { "verse": 1, "text": "In the beginning God created the heaven and the earth." }
          ]
        }
      ]
    }
  ]
}
```

Public domain sources for each translation:
- **KJV** — `thiagobodruk/bible` on GitHub (JSON, structured)
- **ASV** — `christos-c/bible-api` on GitHub (JSON)
- **WEB** — `scrollmapper/bible_databases` on GitHub (multiple formats including JSON)

Download each, convert to the format above, place in `bible/data/kjv.json`,
`bible/data/asv.json`, `bible/data/web.json`.

```python
# bible/management/commands/load_bible.py
import json
import os
from django.core.management.base import BaseCommand
from bible.models import BibleTranslation, BibleBook, BibleVerse


class Command(BaseCommand):
    help = 'Load a Bible translation from a JSON source file'

    def add_arguments(self, parser):
        parser.add_argument('translation_code', type=str,
                            help='Translation code: KJV | ASV | WEB')
        parser.add_argument('--set-default', action='store_true',
                            help='Set this translation as the platform default')

    def handle(self, *args, **options):
        code = options['translation_code'].upper()
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', f'{code.lower()}.json'
        )

        if not os.path.exists(data_path):
            self.stderr.write(f"Data file not found: {data_path}")
            return

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        translation, created = BibleTranslation.objects.get_or_create(
            code=code,
            defaults={
                'name': data['name'],
                'language': data.get('language', 'en'),
                'is_default': options['set_default'],
                'is_public': True,
            }
        )

        if not created:
            self.stdout.write(f"Translation {code} already exists — updating verses.")
            BibleVerse.objects.filter(translation=translation).delete()

        verse_count = 0
        for book_data in data['books']:
            book, _ = BibleBook.objects.get_or_create(
                code=book_data['code'],
                defaults={
                    'name': book_data['name'],
                    'testament': book_data['testament'],
                    'order': book_data['order'],
                }
            )

            verses_to_create = []
            for chapter_data in book_data['chapters']:
                for verse_data in chapter_data['verses']:
                    verses_to_create.append(BibleVerse(
                        translation=translation,
                        book=book,
                        chapter=chapter_data['chapter'],
                        verse=verse_data['verse'],
                        text=verse_data['text'],
                    ))

            BibleVerse.objects.bulk_create(verses_to_create, batch_size=500)
            verse_count += len(verses_to_create)

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {verse_count} verses for {code} ({translation.name})"
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
# Expected: ~93,573 total verses (31,191 × 3), KJV is default
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
        fields = ['id', 'code', 'name', 'language', 'is_default', 'is_public']


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

**Data files note:** `bible/data/*.json` source files must be added to `.gitignore`
if they exceed GitHub's file size limits (~50MB per file uncompressed). The management
command is committed; the data is loaded at deployment via `python manage.py load_bible`.

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|---|---|---|---|
| A | Django `bible` app, models, migrations, management command, data load | Phases 0–2 done + data contract amended | `/api/bible/health/` 200. 93K+ verse rows in DB. Relationship.bible_verse_id field exists. |
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
