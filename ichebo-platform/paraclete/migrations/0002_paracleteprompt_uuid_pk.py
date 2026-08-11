import uuid
from django.db import migrations, models


def backfill_uuids(apps, schema_editor):
    ParacletePrompt = apps.get_model('paraclete', 'ParacletePrompt')
    for prompt in ParacletePrompt.objects.all():
        prompt.uuid_id = uuid.uuid4()
        prompt.save(update_fields=['uuid_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('paraclete', '0001_initial'),
    ]

    operations = [
        # 1. Add a temporary uuid column (nullable so existing rows are accepted)
        migrations.AddField(
            model_name='paracleteprompt',
            name='uuid_id',
            field=models.UUIDField(null=True),
        ),
        # 2. Populate uuid_id for all existing rows
        migrations.RunPython(backfill_uuids, migrations.RunPython.noop),
        # 3. Make uuid_id non-nullable now that all rows have a value
        migrations.AlterField(
            model_name='paracleteprompt',
            name='uuid_id',
            field=models.UUIDField(null=False),
        ),
        # 4. Drop the old integer primary key
        migrations.RemoveField(
            model_name='paracleteprompt',
            name='id',
        ),
        # 5. Promote uuid_id to primary key BEFORE renaming it.
        #     Order matters on SQLite: it has no ALTER COLUMN, so Django
        #     rebuilds the table for each operation. Renaming to 'id' while
        #     the table still carries SQLite's implicit rowid alias produces
        #     "duplicate column name: id" and every test run dies during
        #     migrate. Making it the primary key first forces the rebuild
        #     that genuinely retires the old column, so the rename lands on
        #     a clean table. Postgres is indifferent to the order, and the
        #     end state is identical on both, so this is safe to change
        #     after the migration has already been applied in production.
        migrations.AlterField(
            model_name='paracleteprompt',
            name='uuid_id',
            field=models.UUIDField(
                primary_key=True,
                default=uuid.uuid4,
                editable=False,
                serialize=False,
            ),
        ),
        # 6. Rename uuid_id → id
        migrations.RenameField(
            model_name='paracleteprompt',
            old_name='uuid_id',
            new_name='id',
        ),
    ]
