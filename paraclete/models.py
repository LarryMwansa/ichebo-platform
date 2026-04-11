from django.db import models


class ParacletePrompt(models.Model):
    KGS_PATHWAYS = [
        ('new_life', 'New Life'),
        ('spiritual_formation', 'Spiritual Formation'),
        ('community_life', 'Community Life'),
        ('service', 'Service'),
        ('leadership', 'Leadership'),
        ('learning', 'Learning'),
        ('mission', 'Mission'),
        ('apostolic_stewardship', 'Apostolic Stewardship'),
    ]

    text = models.TextField(help_text='The prompt text shown to the user')
    pathway = models.CharField(
        max_length=30, choices=KGS_PATHWAYS,
        help_text='KGS pathway this prompt relates to'
    )
    min_level = models.IntegerField(
        default=0,
        help_text='Minimum competence level to receive this prompt'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['pathway', 'min_level']

    def __str__(self):
        return f'{self.pathway} (L{self.min_level}): {self.text[:60]}'
