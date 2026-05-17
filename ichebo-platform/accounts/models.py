import uuid
import secrets
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedCharField


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
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

    # Induction tracking (v10 Amendment 10.2)
    induction_enrolled_at = models.DateTimeField(null=True, blank=True)
    induction_completed_at = models.DateTimeField(null=True, blank=True)
    induction_pathway = models.CharField(
        max_length=20,
        null=True, blank=True,
        choices=[('reconditioning', 'Reconditioning'), ('beginners', 'Beginners')],
    )

    class Meta:
        db_table = 'accounts_user'

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else None

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    TITLE_CHOICES = [
        ('mr', 'Mr'), ('mrs', 'Mrs'), ('ms', 'Ms'), ('miss', 'Miss'),
        ('dr', 'Dr'), ('prof', 'Prof'), ('rev', 'Rev'), ('pastor', 'Pastor'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'), ('female', 'Female'),
    ]
    MARITAL_CHOICES = [
        ('single', 'Single'), ('married', 'Married'),
        ('divorced', 'Divorced'), ('widowed', 'Widowed'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', primary_key=True
    )

    # --- Personal Details ---
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=2, blank=True)        # ISO 3166-1 alpha-2
    id_number = EncryptedCharField(max_length=100, blank=True, null=True)  # ENCRYPTED
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=10, choices=MARITAL_CHOICES, blank=True)

    # KGS Member Number — auto-assigned on profile completion
    # Format: KMN-{ISO2}-{YYYY}-{NNNNN}  e.g. KMN-ZA-2026-00001
    member_number = models.CharField(max_length=30, unique=True, null=True, blank=True)

    # --- Qualifications, Gifts & Skills ---
    occupation = models.CharField(max_length=255, blank=True)
    education = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    gifts_skills = models.TextField(blank=True)

    # --- Existing Christian Section ---
    accepted_christ = models.BooleanField(null=True)
    church_member = models.BooleanField(null=True)
    church_name = models.CharField(max_length=255, blank=True)
    referee_1_name = models.CharField(max_length=255, blank=True)
    referee_2_name = models.CharField(max_length=255, blank=True)
    # Referee letters — stored in MinIO ics-private bucket
    referee_letter_1 = models.FileField(upload_to='referee-letters/', blank=True, null=True)
    referee_letter_2 = models.FileField(upload_to='referee-letters/', blank=True, null=True)

    # --- Consent ---
    terms_accepted = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    # --- Bio (existing field for profile page) ---
    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_userprofile'

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def assign_member_number(self):
        """Generate and save KMN if not already assigned."""
        if self.member_number:
            return
        from django.utils import timezone
        year = timezone.now().year
        country = (self.country or 'XX').upper()
        prefix = f'KMN-{country}-{year}-'
        last = (
            UserProfile.objects
            .filter(member_number__startswith=prefix)
            .order_by('member_number')
            .values_list('member_number', flat=True)
            .last()
        )
        seq = 1
        if last:
            try:
                seq = int(last.split('-')[-1]) + 1
            except (ValueError, IndexError):
                pass
        self.member_number = f'{prefix}{seq:05d}'
        self.save(update_fields=['member_number'])

    def __str__(self):
        return f'Profile({self.user.email})'


class EmailVerificationToken(models.Model):
    """Single-use token emailed to new users to verify their address."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'accounts_email_verification_token'

    @classmethod
    def create_for_user(cls, user):
        token_str = secrets.token_urlsafe(48)
        return cls.objects.create(
            user=user,
            token=token_str,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )

    @property
    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at

    def consume(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])

    def __str__(self):
        return f'VerifyToken({self.user.email})'
