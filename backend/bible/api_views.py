from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import BibleTranslation, BibleBook, BibleVerse
from .serializers import BibleTranslationSerializer, BibleBookSerializer, BibleVerseSerializer
from .services import get_book_chapters


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
        elif getattr(self.request.user, 'preferred_bible_translation', None):
            translation = self.request.user.preferred_bible_translation
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chapter_list(request):
    """
    GET /api/bible/chapters/?book_code=GEN
    Returns the list of chapter numbers for a book.
    """
    book_code = request.query_params.get('book_code', '').upper()
    if not book_code:
        return Response({'error': 'book_code is required'}, status=400)
    chapters = list(get_book_chapters(book_code))
    return Response({'book_code': book_code, 'chapters': chapters})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_verses(request):
    """
    GET /api/bible/search/?q=grace&translation_code=KJV
    Full-text verse search across a translation.
    Returns up to 30 results: book_code, book_name, chapter, verse, text snippet.
    """
    q = request.query_params.get('q', '').strip()
    translation_code = request.query_params.get('translation_code', '').strip()

    if not q or len(q) < 2:
        return Response({'results': []})

    if translation_code:
        translation = BibleTranslation.objects.filter(
            code=translation_code, is_public=True
        ).first()
    elif getattr(request.user, 'preferred_bible_translation', None):
        translation = request.user.preferred_bible_translation
    else:
        translation = BibleTranslation.objects.filter(is_default=True).first()

    if not translation:
        return Response({'results': []})

    verses = (
        BibleVerse.objects
        .filter(translation=translation, text__icontains=q)
        .select_related('book')
        .order_by('book__order', 'chapter', 'verse')[:30]
    )

    results = [
        {
            'id': str(v.id),
            'book_code': v.book.code,
            'book_name': v.book.name,
            'chapter': v.chapter,
            'verse': v.verse,
            'text': v.text,
            'reference': f'{v.book.name} {v.chapter}:{v.verse}',
        }
        for v in verses
    ]
    return Response({'results': results})
