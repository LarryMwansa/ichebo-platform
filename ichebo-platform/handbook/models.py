import uuid
from django.conf import settings
from django.db import models


class HandbookAccess(models.Model):
    """
    Permission gate for the Handbook authorship workspace.
    Not a content model — governs who may enter the Handbook and in what role.
    Compliant with data contract Part 1.6 (not a content model table).
    """
    ROLE_READER = 'reader'   # Level 3-4: read all governance records incl. drafts
    ROLE_AUTHOR = 'author'   # Level 5: write governance records
    ROLE_EDITOR = 'editor'   # Level 5 + admin: manage access
    ROLE_CHOICES = [
        (ROLE_READER, 'Reader'),
        (ROLE_AUTHOR, 'Author'),
        (ROLE_EDITOR, 'Editor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='handbook_access',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_READER)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='handbook_access_granted',
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user',)]

    def __str__(self):
        return f'{self.user} ({self.role})'
