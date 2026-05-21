import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('records', '0005_record_family_media'),
    ]

    operations = [
        migrations.CreateModel(
            name='TranscodeJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('job_id', models.CharField(max_length=100)),
                ('status', models.CharField(default='queued', max_length=20)),
                ('progress_pct', models.IntegerField(default=0)),
                ('error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('record', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='transcode_jobs',
                    to='records.record',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
