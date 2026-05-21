from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0004_relationship_metadata_and_bible_verse_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='record_family',
            field=models.CharField(
                choices=[
                    ('journal', 'Journal'),
                    ('governance', 'Governance'),
                    ('activity', 'Activity'),
                    ('learning', 'Learning'),
                    ('reference', 'Reference'),
                    ('bible', 'Bible'),
                    ('community', 'Community'),
                    ('media', 'Media'),
                ],
                max_length=20,
            ),
        ),
    ]
