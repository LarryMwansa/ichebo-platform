import uuid
from django.db import models
from django.utils import timezone


class WaitlistEntry(models.Model):
    PATH_CHOICES = [
        ('leader', 'Pastor / Leader'),
        ('individual', 'Individual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    path = models.CharField(max_length=20, choices=PATH_CHOICES)
    consent = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Waitlist Entry'
        verbose_name_plural = 'Waitlist Entries'

    def __str__(self):
        return f'{self.name} ({self.email}) — {self.get_path_display()}'
