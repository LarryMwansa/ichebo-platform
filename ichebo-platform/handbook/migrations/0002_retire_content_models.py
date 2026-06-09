from django.db import migrations


class Migration(migrations.Migration):
    """
    ADR-022: Retire HandbookRecord and HandbookRelationship.
    Both tables were empty (0 rows). HandbookAccess is retained as a permission gate.
    All governance content lives in records.Record with record_family='governance'.
    """

    dependencies = [
        ('handbook', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='HandbookRelationship'),
        migrations.DeleteModel(name='HandbookRecord'),
    ]
