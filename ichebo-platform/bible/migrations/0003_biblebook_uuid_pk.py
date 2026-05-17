import uuid
from django.db import migrations, models


def wipe_bible_seed_data(apps, schema_editor):
    """
    Delete all BibleVerse and BibleBook rows before re-keying the PK.
    BibleVerse must be deleted first due to the FK constraint.
    Both tables are seed data only — they are reloaded by management command.
    """
    BibleVerse = apps.get_model('bible', 'BibleVerse')
    BibleBook = apps.get_model('bible', 'BibleBook')
    BibleVerse.objects.all().delete()
    BibleBook.objects.all().delete()


class Migration(migrations.Migration):
    """
    Migrate BibleBook.id from BigAutoField to UUIDField.

    BibleBook and BibleVerse are purely seed data loaded by management command.
    We delete all rows before altering the schema, then the management command
    reloads all data with the new UUID PKs.

    The BibleVerse.book_id FK column must also change from bigint to uuid.
    """

    dependencies = [
        ('bible', '0002_widen_year_field'),
    ]

    operations = [
        # 1. Wipe all existing seed data (BibleVerse first, then BibleBook)
        migrations.RunPython(wipe_bible_seed_data, migrations.RunPython.noop),

        # 2. Drop the old auto-increment PK from BibleBook
        migrations.RemoveField(
            model_name='biblebook',
            name='id',
        ),

        # 3. Add the new UUID PK to BibleBook
        migrations.AddField(
            model_name='biblebook',
            name='id',
            field=models.UUIDField(
                primary_key=True,
                default=uuid.uuid4,
                editable=False,
                serialize=False,
            ),
        ),

        # 4. The BibleVerse.book FK column (book_id) references BibleBook.id.
        #    After removing/re-adding BibleBook.id, Django needs to know the FK
        #    column type has changed to uuid. We alter the FK field explicitly.
        migrations.AlterField(
            model_name='bibleverse',
            name='book',
            field=models.ForeignKey(
                to='bible.BibleBook',
                on_delete=models.CASCADE,
                related_name='verses',
            ),
        ),
    ]
