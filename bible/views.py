from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
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
    Book and chapter default to GEN 1 or the user's last position.
    """

    def get(self, request, book_code=DEFAULT_BOOK, chapter=DEFAULT_CHAPTER):
        translation = get_user_translation(request.user)
        books = get_all_books()
        book = BibleBook.objects.filter(code=book_code).first()
        if not book:
            if book_code != DEFAULT_BOOK:
                return redirect('bible:reader')
            raise Http404("Bible data is not loaded. Please run the Bible import management command.")

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
    try:
        chapter = int(request.GET.get('chapter', DEFAULT_CHAPTER))
    except (ValueError, TypeError):
        chapter = DEFAULT_CHAPTER

    if chapter < 1:
        chapter = 1

    translation = get_user_translation(request.user)
    verses = get_chapter_verses(translation, book_code, chapter)

    if not verses.exists():
        chapter = DEFAULT_CHAPTER
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
    competence_level = getattr(user, 'competence_level', 0)

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
        user.userpermissions.filter(is_active=True).values_list('tenant_id', flat=True)
        if hasattr(user, 'userpermissions') else []
    )
    tenant_notes = Record.objects.filter(
        record_family='bible',
        record_type='bible_note',
        record_class='organizational',
        permissions_data__visibility='tenant',
        tenant_id__in=user_tenant_ids,
        custom_fields__book_code=verse.book.code,
        custom_fields__chapter=verse.chapter,
        custom_fields__verse=verse.verse,
        status='active',
        deleted_at__isnull=True,
    ).select_related('created_by')

    # Learn cross-references
    verse_ref_str = f"{verse.book.code} {verse.chapter}:{verse.verse}"
    learn_references = Record.objects.filter(
        record_family='learning',
        record_type='lesson',
        status='active',
        custom_fields__scripture_reference__icontains=verse_ref_str,
    ).values('id', 'title', 'metadata')[:5]

    # All formal relationships (Linking Governance, Activities, etc)
    relationships = Relationship.objects.filter(
        bible_verse=verse,
        deleted_at__isnull=True,
    ).select_related('from_record')

    # Group by family for cleaner UI
    links = {
        'governance': [r for r in relationships if r.from_record.record_family == 'governance'],
        'activity': [r for r in relationships if r.from_record.record_family == 'activity'],
        'other': [r for r in relationships if r.from_record.record_family not in ['governance', 'activity']],
    }

    # Learn cross-references (Smart search in lessons)
    verse_ref_str = f"{verse.book.code} {verse.chapter}:{verse.verse}"
    learn_references = Record.objects.filter(
        record_family='learning',
        record_type='lesson',
        status='active',
        custom_fields__scripture_reference__icontains=verse_ref_str,
    ).values('id', 'title', 'metadata')[:10]

    context = {
        'verse': verse,
        'verse_ref': verse_ref_str,
        'personal_note': personal_note,
        'tenant_notes': tenant_notes,
        'learn_references': learn_references,
        'links': links,
        'competence_level': competence_level,
        'can_publish_tenant_note': competence_level >= 3,
        'book': verse.book,
        'chapter': verse.chapter,
    }
    return render(request, 'bible/_annotation_panel.html', context)


@login_required
def htmx_save_note(request):
    """
    HTMX: create or update a personal or tenant bible note.
    POST params: verse_id, content, note_id (optional), note_class
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    from .models import BibleVerse
    from records.models import Record

    verse_id = request.POST.get('verse_id')
    content = request.POST.get('content', '').strip()
    note_id = request.POST.get('note_id', '')
    note_class = request.POST.get('note_class', 'personal')
    user = request.user
    competence_level = getattr(user, 'competence_level', 0)

    if note_class == 'organizational' and competence_level < 3:
        return HttpResponse("Permission denied.", status=403)

    verse = BibleVerse.objects.select_related('book').get(id=verse_id)
    verse_ref = f"{verse.book.name} {verse.chapter}:{verse.verse}"

    if note_id:
        note = Record.objects.get(id=note_id, created_by=user)
        note.content = content
        note.save(update_fields=['content', 'updated_at'])
    else:
        # Seeker 10-record limit check
        if note_class == 'personal' and competence_level == 0:
            personal_count = Record.objects.filter(
                record_class='personal',
                created_by=user,
                deleted_at__isnull=True
            ).count()
            if personal_count >= 10:
                return render(request, 'bible/_note_limit_reached.html', {})

        # Resolve tenant for tenant notes
        active_tenant_id = None
        if note_class == 'organizational' and hasattr(user, 'userpermissions'):
            perm = user.userpermissions.filter(is_active=True).first()
            if perm:
                active_tenant_id = perm.tenant_id

        Record.objects.create(
            tenant_id=active_tenant_id if note_class == 'organizational' else None,
            created_by=user,
            record_class=note_class,
            record_family='bible',
            record_type='bible_note',
            title=verse_ref,
            content=content,
            status='active',
            metadata={'source_app': 'bible'},
            custom_fields={
                'book_code': verse.book.code,
                'chapter': verse.chapter,
                'verse': verse.verse,
            },
            permissions_data={
                'visibility': 'tenant' if note_class == 'organizational' else 'private',
                'required_level': 1,
                'roles_allowed': [],
                'can_edit': [],
            }
        )

    has_personal = note_class == 'personal' or Record.objects.filter(
        record_family='bible', record_type='bible_note', record_class='personal',
        created_by=user,
        custom_fields__book_code=verse.book.code,
        custom_fields__chapter=verse.chapter,
        custom_fields__verse=verse.verse,
        deleted_at__isnull=True,
    ).exists()

    has_tenant = note_class == 'organizational' or False

    return render(request, 'bible/_verse_indicators.html', {
        'verse': verse,
        'has_personal_note': has_personal,
        'has_tenant_note': has_tenant,
    })


@login_required
def bible_search_view(request):
    """
    Full-page Bible search view.
    Template handles HTMX search requests.
    """
    return render(request, 'bible/search.html')


@login_required
def htmx_search(request):
    """
    HTMX: search verses in real-time.
    GET param: q (search query)
    Returns list of matching verses.
    """
    from .models import BibleVerse

    query = request.GET.get('q', '').strip()
    results = []

    if len(query) >= 2:
        translation = get_user_translation(request.user)
        results = BibleVerse.objects.filter(
            text__icontains=query,
            translation=translation
        ).select_related('book')[:30]

    return render(request, 'bible/_search_results.html', {
        'results': results,
        'query': query,
    })


@login_required
def bible_picker_view(request):
    """
    Book/chapter/verse picker. Handles both full-page and HTMX partials.
    """
    back_url = request.GET.get('back', '/bible/')
    book_code = request.GET.get('book_code', DEFAULT_BOOK)
    try:
        chapter = int(request.GET.get('chapter', DEFAULT_CHAPTER))
    except (ValueError, TypeError):
        chapter = DEFAULT_CHAPTER

    books = get_all_books()
    book = BibleBook.objects.filter(code=book_code).first()
    chapters = get_book_chapters(book_code)

    all_chapters = {}
    for b in books:
        all_chapters[b.code] = list(get_book_chapters(b.code))

    context = {
        'books': books,
        'book': book,
        'chapter': chapter,
        'chapters': list(chapters),
        'all_chapters': all_chapters,
        'back_url': back_url,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'bible/partials/_picker_sheet.html', context)
    return render(request, 'bible/picker.html', context)


@login_required
def bible_versions_view(request):
    """
    Bible versions list. Handles both full-page and HTMX partials.
    """
    book_code = request.GET.get('book_code', DEFAULT_BOOK)
    try:
        chapter = int(request.GET.get('chapter', DEFAULT_CHAPTER))
    except (ValueError, TypeError):
        chapter = DEFAULT_CHAPTER

    current_translation = get_user_translation(request.user)
    translations = BibleTranslation.objects.filter(is_public=True).order_by('language_full', 'name')

    versions_by_language = {}
    for trans in translations:
        lang = trans.language_full or 'Unknown'
        if lang not in versions_by_language:
            versions_by_language[lang] = []
        versions_by_language[lang].append(trans)

    context = {
        'current_translation': current_translation,
        'versions_by_language': versions_by_language,
        'all_translations': translations,
        'book_code': book_code,
        'chapter': chapter,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'bible/partials/_versions_sheet.html', context)
    return render(request, 'bible/versions.html', context)


@login_required
def bible_languages_view(request):
    """
    Bible languages list. Handles both full-page and HTMX partials.
    """
    translations = BibleTranslation.objects.filter(is_public=True).order_by('language_full', 'name')
    languages_data = {}
    for trans in translations:
        lang = trans.language_full or 'Unknown'
        if lang not in languages_data:
            languages_data[lang] = {
                'name': lang,
                'count': 0,
                'short_code': trans.language,
            }
        languages_data[lang]['count'] += 1

    languages_list = sorted(languages_data.values(), key=lambda x: x['name'])
    context = {'languages': languages_list}

    if request.headers.get('HX-Request'):
        return render(request, 'bible/partials/_languages_sheet.html', context)
    return render(request, 'bible/languages.html', context)


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
    # Return OOB to clear indicator + success message for drawer
    verse = note.custom_fields.get('verse') # This might be tricky if custom_fields is JSON
    # Better: get the verse from the record metadata or lookup
    from .models import BibleVerse
    verse_obj = BibleVerse.objects.filter(
        translation__code=note.custom_fields.get('translation_code', 'ESV'), # Fallback
        book__code=note.custom_fields.get('book_code'),
        chapter=note.custom_fields.get('chapter'),
        verse=note.custom_fields.get('verse'),
    ).first()

    response_html = f'<div id="indicators-{verse_obj.id}" hx-swap-oob="innerHTML"></div>' if verse_obj else ''
    response_html += '<div class="alert alert-info">Note deleted.</div>'
    return HttpResponse(response_html)


@login_required
def htmx_set_translation(request):
    """
    HTMX: update user's preferred translation.
    POST params: translation_code, book_code, chapter
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    translation_code = request.POST.get('translation_code')
    book_code = request.POST.get('book_code', DEFAULT_BOOK)
    try:
        chapter = int(request.POST.get('chapter', DEFAULT_CHAPTER))
    except (ValueError, TypeError):
        chapter = DEFAULT_CHAPTER

    translation = BibleTranslation.objects.filter(
        code=translation_code, is_public=True
    ).first()

    if translation:
        request.user.preferred_bible_translation = translation
        request.user.save(update_fields=['preferred_bible_translation'])

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
def htmx_appearance_sheet(request):
    """
    Returns appearance settings bottom sheet.
    """
    return render(request, 'bible/partials/_appearance_sheet.html')
