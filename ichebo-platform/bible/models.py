import uuid
from django.db import models


class BibleTranslation(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code                = models.CharField(max_length=10, unique=True)
    name                = models.CharField(max_length=100)
    language            = models.CharField(max_length=10, default='en')       # from metadata.lang_short
    language_full       = models.CharField(max_length=50, default='English')  # from metadata.lang
    year                = models.CharField(max_length=20, null=True, blank=True)  # from metadata.year
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

    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
