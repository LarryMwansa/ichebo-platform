import os
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from bible.models import BibleTranslation, BibleBook, BibleVerse

BOOK_NAMES_ORDER = [
    'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
    'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
    '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra',
    'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
    'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations',
    'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
    'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
    'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
    'Matthew', 'Mark', 'Luke', 'John', 'Acts',
    'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
    'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy',
    '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
    '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
    'Jude', 'Revelation'
]

BOOK_CODE_MAP = {
    'Genesis': 'GEN', 'Exodus': 'EXO', 'Leviticus': 'LEV', 'Numbers': 'NUM', 'Deuteronomy': 'DEU',
    'Joshua': 'JOS', 'Judges': 'JDG', 'Ruth': 'RUT', '1 Samuel': '1SA', '2 Samuel': '2SA',
    '1 Kings': '1KI', '2 Kings': '2KI', '1 Chronicles': '1CH', '2 Chronicles': '2CH', 'Ezra': 'EZR',
    'Nehemiah': 'NEH', 'Esther': 'EST', 'Job': 'JOB', 'Psalms': 'PSA', 'Psalm': 'PSA', 'Proverbs': 'PRO',
    'Ecclesiastes': 'ECC', 'Song of Solomon': 'SNG', 'Isaiah': 'ISA', 'Jeremiah': 'JER', 'Lamentations': 'LAM',
    'Ezekiel': 'EZK', 'Daniel': 'DAN', 'Hosea': 'HOS', 'Joel': 'JOL', 'Amos': 'AMO',
    'Obadiah': 'OBA', 'Jonah': 'JON', 'Micah': 'MIC', 'Nahum': 'NAH', 'Habakkuk': 'HAB',
    'Zephaniah': 'ZEP', 'Haggai': 'HAG', 'Zechariah': 'ZEC', 'Malachi': 'MAL',
    'Matthew': 'MAT', 'Mark': 'MRK', 'Luke': 'LUK', 'John': 'JHN', 'Acts': 'ACT',
    'Romans': 'ROM', '1 Corinthians': '1CO', '2 Corinthians': '2CO', 'Galatians': 'GAL', 'Ephesians': 'EPH',
    'Philippians': 'PHP', 'Colossians': 'COL', '1 Thessalonians': '1TH', '2 Thessalonians': '2TH', '1 Timothy': '1TI',
    '2 Timothy': '2TI', 'Titus': 'TIT', 'Philemon': 'PHM', 'Hebrews': 'HEB', 'James': 'JAS',
    '1 Peter': '1PE', '2 Peter': '2PE', '1 John': '1JN', '2 John': '2JN', '3 John': '3JN',
    'Jude': 'JUD', 'Revelation': 'REV'
}

TRANSLATION_NAMES = {
    'AMP': 'Amplified Bible',
    'ESV': 'English Standard Version',
    'MSG': 'The Message',
    'NASB': 'New American Standard Bible',
    'NIV': 'New International Version',
    'NKJV': 'New King James Version',
    'NLT': 'New Living Translation',
    'TNIV': 'Today\'s New International Version',
    'ASV': 'American Standard Version',
    'KJV': 'Authorized King James Version',
}

class Command(BaseCommand):
    help = 'Load a Bible translation from an XML source file'

    def add_arguments(self, parser):
        parser.add_argument('translation_code', type=str)
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        code = options['translation_code'].upper()
        data_path = options['file_path']

        if not os.path.exists(data_path):
            self.stderr.write(f"File not found: {data_path}")
            return

        self.stdout.write(f"Parsing XML from {data_path}...")
        tree = ET.parse(data_path)
        root = tree.getroot()

        # Prefer the curated full name over the XML's own biblename attribute —
        # source files are inconsistent (bare codes, typos like NASB's "NSAB",
        # or mangled values like TNIV's "ENGLISHTNV").
        xml_biblename = root.get('biblename')

        translation, created = BibleTranslation.objects.update_or_create(
            code=code,
            defaults={
                'name': TRANSLATION_NAMES.get(code) or xml_biblename or code,
                'language': 'en',
                'language_full': 'English',
                'is_public': True,
            }
        )

        if not created:
            deleted, _ = BibleVerse.objects.filter(translation=translation).delete()
            self.stdout.write(f"Cleared {deleted} existing verses for {code}.")

        verses_to_create = []

        for book_node in root.findall('BIBLEBOOK'):
            bname = book_node.get('bname')
            book_code = BOOK_CODE_MAP.get(bname)
            
            if not book_code:
                self.stderr.write(f"Warning: Unknown book name '{bname}'. Skipping.")
                continue

            # Optimize by fetching book once per translation
            book_obj = BibleBook.objects.get(code=book_code)
            
            for chap_node in book_node.findall('CHAPTER'):
                cnumber = int(chap_node.get('cnumber'))
                for vers_node in chap_node.findall('VERS'):
                    vnumber = int(vers_node.get('vnumber'))
                    text = vers_node.text.strip() if vers_node.text else ""
                    
                    verses_to_create.append(BibleVerse(
                        translation=translation,
                        book=book_obj,
                        chapter=cnumber,
                        verse=vnumber,
                        text=text
                    ))

        self.stdout.write(f"Found {len(verses_to_create)} verses. Starting bulk insert...")
        
        batch_size = 1000
        for i in range(0, len(verses_to_create), batch_size):
            BibleVerse.objects.bulk_create(verses_to_create[i:i+batch_size])
            self.stdout.write(f"  Inserted {min(i+batch_size, len(verses_to_create))} verses...")

        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {code}."))
