from rest_framework import generics
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
