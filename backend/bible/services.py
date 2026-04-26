"""
Bible App service layer — ORM queries for template views.
Template views call these functions; they do not call DRF endpoints internally.
"""
from .models import BibleTranslation, BibleBook, BibleVerse


def get_user_translation(user):
    """Return the user's preferred translation, falling back to system default."""
    pref = getattr(user, 'preferred_bible_translation', None)
    if pref:
        return pref
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
    # Try default translation first
    chapters = list(
        BibleVerse.objects
        .filter(book__code=book_code, translation__is_default=True)
        .values_list('chapter', flat=True)
        .distinct()
        .order_by('chapter')
    )
    if not chapters:
        # Fallback to any available translation
        chapters = list(
            BibleVerse.objects
            .filter(book__code=book_code)
            .values_list('chapter', flat=True)
            .distinct()
            .order_by('chapter')
        )
    return chapters


def get_chapter_note_verse_numbers(user, translation, book_code, chapter):
    """
    Return two sets of verse numbers for a chapter:
    - personal_noted: verses where the user has a personal note
    - tenant_noted:   verses where a tenant note exists for the user's tenant(s)
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

    user_tenant_ids = (
        user.userpermissions.filter(is_active=True).values_list('tenant_id', flat=True)
        if hasattr(user, 'userpermissions') else []
    )

    tenant_noted = set(
        Record.objects.filter(
            record_family='bible',
            record_type='bible_note',
            record_class='organizational',
            permissions_data__visibility='tenant',
            tenant_id__in=user_tenant_ids,
            custom_fields__book_code=book_code,
            custom_fields__chapter=chapter,
            status='active',
            deleted_at__isnull=True,
        ).values_list('custom_fields__verse', flat=True)
    )

    return personal_noted, tenant_noted
