import json
import os
from django.core.management.base import BaseCommand
from bible.models import BibleTranslation, BibleBook, BibleVerse

TESTAMENT_MAP = {
    **{i: 'OT' for i in range(1, 40)},
    **{i: 'NT' for i in range(40, 67)},
}

BOOK_CODE_MAP = {
    1: 'GEN',  2: 'EXO',  3: 'LEV',  4: 'NUM',  5: 'DEU',
    6: 'JOS',  7: 'JDG',  8: 'RUT',  9: '1SA',  10: '2SA',
    11: '1KI', 12: '2KI', 13: '1CH', 14: '2CH', 15: 'EZR',
    16: 'NEH', 17: 'EST', 18: 'JOB', 19: 'PSA', 20: 'PRO',
    21: 'ECC', 22: 'SNG', 23: 'ISA', 24: 'JER', 25: 'LAM',
    26: 'EZK', 27: 'DAN', 28: 'HOS', 29: 'JOL', 30: 'AMO',
    31: 'OBA', 32: 'JON', 33: 'MIC', 34: 'NAH', 35: 'HAB',
    36: 'ZEP', 37: 'HAG', 38: 'ZEC', 39: 'MAL',
    40: 'MAT', 41: 'MRK', 42: 'LUK', 43: 'JHN', 44: 'ACT',
    45: 'ROM', 46: '1CO', 47: '2CO', 48: 'GAL', 49: 'EPH',
    50: 'PHP', 51: 'COL', 52: '1TH', 53: '2TH', 54: '1TI',
    55: '2TI', 56: 'TIT', 57: 'PHM', 58: 'HEB', 59: 'JAS',
    60: '1PE', 61: '2PE', 62: '1JN', 63: '2JN', 64: '3JN',
    65: 'JUD', 66: 'REV',
}

class Command(BaseCommand):
    help = 'Load a Bible translation from a flat JSON source file'

    def add_arguments(self, parser):
        parser.add_argument('translation_code', type=str,
                            help='Translation code: KJV | ASV | WEB')
        parser.add_argument('--set-default', action='store_true',
                            help='Set this translation as the platform default')
        parser.add_argument('--file', type=str, default=None,
                            help='Path to JSON file (optional)')

    def handle(self, *args, **options):
        code = options['translation_code'].upper()

        if options['file']:
            data_path = options['file']
        else:
            data_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', f'{code.lower()}.json'
            )

        if not os.path.exists(data_path):
            self.stderr.write(f"Data file not found: {data_path}")
            return

        self.stdout.write(f"Loading {code} from {data_path}…")

        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        meta = data.get('metadata', {})
        restrict = meta.get('restrict', 0)
        is_copyright_val = bool(meta.get('copyright', 0))

        translation, created = BibleTranslation.objects.update_or_create(
            code=code,
            defaults={
                'name':                meta.get('name', code),
                'language':            meta.get('lang_short', 'en'),
                'language_full':       meta.get('lang', 'English'),
                'year':                meta.get('year'),
                'description':         meta.get('description'),
                'copyright_statement': meta.get('copyright_statement'),
                'is_copyright':        is_copyright_val,
                'is_public':           restrict == 0,
                'is_default':          options['set_default'],
            }
        )

        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} translation: {translation.name} ({code})")

        if not created:
            deleted_count, _ = BibleVerse.objects.filter(translation=translation).delete()
            self.stdout.write(f"Cleared {deleted_count} existing verses.")

        verses_data = data.get('verses', [])
        if not verses_data:
            self.stderr.write("No verses found in file. Check JSON structure.")
            return

        book_cache = {}

        verses_to_create = []
        skipped = 0

        for row in verses_data:
            book_int  = row.get('book')
            chapter   = row.get('chapter')
            verse     = row.get('verse')
            text      = row.get('text', '')
            book_name = row.get('book_name', '')

            if not all([book_int, chapter, verse, text]):
                skipped += 1
                continue

            if book_int not in book_cache:
                book_code = BOOK_CODE_MAP.get(book_int)
                testament = TESTAMENT_MAP.get(book_int, 'OT')

                if not book_code:
                    self.stderr.write(f"Unknown book {book_int} — skipping.")
                    skipped += 1
                    continue

                book_obj, _ = BibleBook.objects.get_or_create(
                    code=book_code,
                    defaults={
                        'name':      book_name,
                        'testament': testament,
                        'order':     book_int,
                    }
                )
                book_cache[book_int] = book_obj

            verses_to_create.append(BibleVerse(
                translation=translation,
                book=book_cache[book_int],
                chapter=chapter,
                verse=verse,
                text=text,
            ))

        batch_size = 1000
        total = len(verses_to_create)
        for i in range(0, total, batch_size):
            BibleVerse.objects.bulk_create(
                verses_to_create[i:i + batch_size],
                batch_size=batch_size
            )
            self.stdout.write(f"  Inserted {min(i + batch_size, total)}/{total} verses…")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Loaded {total} verses for {code}. Skipped: {skipped}."
        ))
