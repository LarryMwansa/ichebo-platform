import uuid
from django.db import models
from django.conf import settings
from core.managers import SoftDeleteMixin


class CertificationConfirmation(SoftDeleteMixin, models.Model):
    """
    Audit record of a steward confirming a learner's certification.
    The certification itself is a records.Record with record_type='certification'.
    This model records WHO confirmed it and WHEN, separately from the Record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certification_record_id = models.UUIDField(db_index=True)   # FK → records.Record
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='certifications_confirmed'
    )
    learner_id = models.UUIDField(db_index=True)                # FK → User (the learner)
    previous_competence_level = models.IntegerField()
    new_competence_level = models.IntegerField()
    confirmed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        ordering = ['-confirmed_at']
        indexes = [
            models.Index(fields=['certification_record_id']),
            models.Index(fields=['learner_id']),
            models.Index(fields=['confirmed_by']),
        ]

    def __str__(self):
        return f"Certification {self.certification_record_id} confirmed by {self.confirmed_by}"


# ---------------------------------------------------------------------------
# Induction curriculum models
# ---------------------------------------------------------------------------

class InductionStep(models.Model):
    """One step in the induction curriculum — a lesson, quiz, or module test.

    Steps are globally ordered by sequence_order. The pathway field gates
    Module 2 steps: 'all' shows to everyone, 'beginners' only to new
    believers, 'reconditioning' only to reforming existing Christians.
    Steps for modules 1, 3, and 4 all use pathway='all'.
    """
    STEP_TYPES = [
        ('lesson', 'Lesson'),
        ('quiz', 'Knowledge Check Quiz'),
        ('module_test', 'Module Test'),
        ('final_test', 'Final Test'),
    ]
    PATHWAY_CHOICES = [
        ('all', 'All'),
        ('beginners', 'Beginners'),
        ('reconditioning', 'Reconditioning'),
    ]
    MODULE_CHOICES = [
        (1, 'Module 1 — Keys to the Kingdom'),
        (2, 'Module 2 — Repentance / Reformation'),
        (3, 'Module 3 — Secret to a Fulfilled Life'),
        (4, 'Module 4 — The Sceptre Community'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.IntegerField(choices=MODULE_CHOICES)
    sequence_order = models.IntegerField(unique=True)
    step_type = models.CharField(max_length=20, choices=STEP_TYPES)
    pathway = models.CharField(max_length=20, choices=PATHWAY_CHOICES, default='all')

    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='Lesson content coming soon.')

    # For quizzes and tests — pass threshold (0–100)
    pass_score = models.IntegerField(default=70)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence_order']

    def __str__(self):
        return f"[{self.get_module_display()}] {self.title}"

    def is_quiz_type(self):
        return self.step_type in ('quiz', 'module_test', 'final_test')


class InductionQuestion(models.Model):
    """A multiple-choice question belonging to an InductionStep quiz/test."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step = models.ForeignKey(
        InductionStep,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    question_text = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.step.title} — Q{self.order}: {self.question_text[:60]}"


class InductionAnswer(models.Model):
    """One answer option for an InductionQuestion."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        InductionQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.answer_text[:60]}"


class InductionProgress(models.Model):
    """Tracks each learner's progress on every induction step.

    One row per (user, step). Created with status='locked' when the
    curriculum is seeded for a new user; unlocked as they advance.
    The first step is always unlocked on enrolment.
    """
    STATUS_CHOICES = [
        ('locked', 'Locked'),
        ('available', 'Available'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('awaiting_steward', 'Awaiting Steward Confirmation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='induction_progress',
    )
    step = models.ForeignKey(
        InductionStep,
        on_delete=models.CASCADE,
        related_name='progress_records',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='locked')
    score = models.IntegerField(null=True, blank=True)       # % score on quiz/test
    attempts = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'step')
        ordering = ['step__sequence_order']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user} — {self.step.title} ({self.status})"


# ---------------------------------------------------------------------------
# Curriculum engine — generic, Record-backed
#
# These replace the induction-specific models above. Any learning Record can
# carry questions and be assessed; nothing here knows what induction is.
#
# Deliberately absent: a per-step progress table. Completion already lives on
# the activity.Activity tree (programme → project → task), which is what drives
# progress rollup and the certification signal. A second status column would
# duplicate it and drift — the old InductionProgress did exactly that, and its
# _unlock_next only ever unlocked the immediately-following step, so inserting
# a step mid-curriculum left existing learners permanently blocked. Unlock is
# derived from the Activity chain instead; see learn/engine.py.
# ---------------------------------------------------------------------------

class AssessmentQuestion(SoftDeleteMixin, models.Model):
    """A question on any learning Record (normally record_type='quiz')."""

    QUESTION_TYPES = [
        ('single_choice', 'Single Choice'),
        ('multi_choice', 'Multiple Choice'),
        ('free_text', 'Free Text'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(
        'records.Record',
        on_delete=models.CASCADE,
        related_name='assessment_questions',
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPES, default='single_choice'
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['record', 'order']),
        ]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:60]}"

    @property
    def answers(self):
        """Alias for `options`.

        Kept so templates written against the old InductionQuestion.answers
        related name (templates/sceptre/induction/quiz.html) need no edit.
        """
        return self.options


class AssessmentOption(SoftDeleteMixin, models.Model):
    """One selectable answer on an AssessmentQuestion."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name='options',
    )
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['question', 'order']),
        ]

    def __str__(self):
        mark = '✓' if self.is_correct else '·'
        return f"{mark} {self.answer_text[:60]}"


class AssessmentAttempt(models.Model):
    """One submission of an assessment. Immutable — never updated, only added.

    Attempt history is the audit trail: a learner's current state is the latest
    row, and the whole sequence is available for reporting on which questions
    trip people up. Not soft-deletable — an attempt happened or it didn't.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessment_attempts',
    )
    record = models.ForeignKey(
        'records.Record',
        on_delete=models.CASCADE,
        related_name='assessment_attempts',
    )
    attempt_number = models.IntegerField(default=1)
    score = models.IntegerField()                   # 0–100
    passed = models.BooleanField(default=False)
    # {question_id: [option_id, ...]} — what was actually submitted
    responses = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'record']),
            models.Index(fields=['record', 'passed']),
        ]

    def __str__(self):
        return f"{self.user} — {self.record.title} attempt {self.attempt_number}: {self.score}%"


class LearningAttachment(SoftDeleteMixin, models.Model):
    """A file attached to a learning Record — handout, worksheet, slides, PDF.

    Stored under learn/protected/ so nginx can refuse to serve it directly;
    reaching it goes through learn.views.lesson_file, which checks enrolment.
    Video is NOT here — it goes through the media engine and lives in
    Record.custom_fields['video_url'].
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(
        'records.Record',
        on_delete=models.CASCADE,
        related_name='learning_attachments',
    )
    file = models.FileField(upload_to='learn/protected/%Y/%m/')
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='learning_attachments',
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['record', 'order']),
        ]

    def __str__(self):
        return f"{self.original_name} ({self.record.title})"

    @property
    def is_pdf(self):
        return self.content_type == 'application/pdf'
