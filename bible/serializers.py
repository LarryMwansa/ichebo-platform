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
