from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Fix BibleVerse.book_id — confirmed still `bigint` in the real database
    despite migration 0003's AlterField on the same field. `sqlmigrate bible
    0003` shows that operation as "-- (no-op)": AlterField only emits real
    SQL when Django's autodetector sees the field's *state* differ between
    migrations, and 0003's AlterField used an identical ForeignKey
    definition to what already existed, so Django emitted nothing.
    BibleBook.id's RemoveField/AddField pair in the same migration worked
    correctly because that genuinely changed field types (BigAutoField ->
    UUIDField) — the FK column referencing it was never actually altered to
    match on the database side.

    Uses SeparateDatabaseAndState because a plain RemoveField/AddField pair
    on `book` hits the same no-op detection (Django would see the field
    removed then re-added with the same final shape and may still skip the
    real ALTER). Forcing the database operations explicitly guarantees the
    column is actually dropped and recreated as uuid, on both SQLite (table
    rebuild) and PostgreSQL (native ALTER), while keeping Django's model
    state in sync via the parallel state_operations.

    BibleVerse is purely seed data reloaded by the load_bible management
    command — confirmed empty in the affected production database before
    this migration runs, so no data-preserving step is needed (unlike
    0003's wipe step, which protected real BibleBook rows).
    """

    dependencies = [
        ('bible', '0003_biblebook_uuid_pk'),
    ]

    operations = [
        # Drop the constraints/indexes that reference `book` first — on
        # SQLite, Django's table-rebuild for RemoveField fails if an index
        # or unique_together still references the field being removed
        # (confirmed via sqlmigrate: FieldDoesNotExist inside _remake_table).
        migrations.AlterUniqueTogether(
            name='bibleverse',
            unique_together=set(),
        ),
        migrations.RemoveIndex(
            model_name='bibleverse',
            name='bible_bible_transla_62ac79_idx',
        ),
        migrations.RemoveIndex(
            model_name='bibleverse',
            name='bible_bible_book_id_fb4fe4_idx',
        ),

        migrations.RemoveField(
            model_name='bibleverse',
            name='book',
        ),
        migrations.AddField(
            model_name='bibleverse',
            name='book',
            field=models.ForeignKey(
                to='bible.biblebook',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='verses',
                default=None,
            ),
            preserve_default=False,
        ),

        # Recreate the constraints/indexes now that `book` is the correct type.
        migrations.AlterUniqueTogether(
            name='bibleverse',
            unique_together={('translation', 'book', 'chapter', 'verse')},
        ),
        migrations.AddIndex(
            model_name='bibleverse',
            index=models.Index(fields=['translation', 'book', 'chapter'], name='bible_bible_transla_62ac79_idx'),
        ),
        migrations.AddIndex(
            model_name='bibleverse',
            index=models.Index(fields=['book', 'chapter', 'verse'], name='bible_bible_book_id_fb4fe4_idx'),
        ),
    ]
