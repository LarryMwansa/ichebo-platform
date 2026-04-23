import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    competence_level = models.IntegerField(default=0)
    # 0 = seeker, 1-5 = formation levels per KGS
    status = models.CharField(
        max_length=30,
        choices=[
            ('seeker', 'Seeker'),
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('pending_verification', 'Pending Verification'),
        ],
        default='seeker'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    preferred_bible_translation = models.ForeignKey(
        'bible.BibleTranslation',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='preferred_by_users'
    )
    preferences = models.JSONField(default=dict, blank=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'accounts_user'

    def __str__(self):
        return self.email
