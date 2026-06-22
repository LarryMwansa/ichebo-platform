"""
paraclete/service.py — Paraclete Intelligence Service

Read-only orchestration module. Reads Django ORM directly, applies
rules, returns a ParacleteDigest dataclass. Never writes to any table.
"""
import datetime
import random
from dataclasses import dataclass, field
from typing import Optional

from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ActivityCard:
    id: str
    title: str
    activity_type: str
    status: str
    due_at: Optional[str]
    kgs_pathway: Optional[str]


@dataclass
class HabitStreak:
    activity_id: str
    title: str
    streak: int
    last_completed: Optional[str]


@dataclass
class ProgrammeCard:
    record_id: str
    title: str
    progress: int


@dataclass
class LessonCard:
    record_id: str
    title: str
    programme_title: str
    url: str


@dataclass
class VideoProgressCard:
    activity_id: str
    video_record_id: str
    title: str
    progress: int      # 0–100 (milestone last fired: 25/50/75/100)
    url: str


@dataclass
class DARCard:
    record_id: str
    title: str
    created_at: str
    url: str


@dataclass
class ParacleteDigest:
    generated_at: str
    user_id: str
    competence_level: int

    # Activity surface
    pending_count: int = 0
    overdue_count: int = 0
    due_today: list = field(default_factory=list)
    overdue_items: list = field(default_factory=list)
    habit_streaks: list = field(default_factory=list)

    # Reminders
    pending_reminders: list = field(default_factory=list)

    # Learn
    active_enrolments: list = field(default_factory=list)
    next_lesson: Optional[object] = None

    # Prompt
    discipline_prompt: str = ''
    prompt_pathway: str = ''

    # DAR
    dar_today: Optional[object] = None

    # Video learning progress (media records being watched)
    video_in_progress: list = field(default_factory=list)

    # Suggestions (stub in MVP)
    suggestions: list = field(default_factory=list)
    suggestion_method: str = 'deferred'

    # Team (Level 3+)
    team_pending_count: Optional[int] = None
    team_overdue_count: Optional[int] = None


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def build_digest(user) -> ParacleteDigest:
    """
    Entry point. Called by DRF view after cache miss.
    Reads ORM, applies rules, returns ParacleteDigest.
    Never writes to any table.
    """
    # competence_level is on User directly (not on a userprofile sub-object)
    level = getattr(user, 'competence_level', 0)
    now = timezone.now()
    today = timezone.localtime(now).date()

    digest = ParacleteDigest(
        generated_at=now.isoformat(),
        user_id=str(user.id),
        competence_level=level,
    )

    # All users (including Level 0 seekers) receive a prompt
    prompt, pathway = _select_prompt(user, level)
    digest.discipline_prompt = prompt
    digest.prompt_pathway = pathway

    # Level 0 (seeker) — prompt only
    if level < 1:
        return digest

    # Level 1+ — full personal digest
    _populate_activity_surface(digest, user, now, today)
    _populate_reminders(digest, user, now)
    _populate_learn(digest, user)
    _populate_video_progress(digest, user)
    digest.dar_today = _get_dar_today(user, today)

    # Level 3+ — team counts
    if level >= 3:
        _populate_team_counts(digest, user, now, today)

    # Suggestions — rule-based, generated after all other data is populated
    digest.suggestions = _build_suggestions(digest)
    digest.suggestion_method = 'rules'

    return digest


# ---------------------------------------------------------------------------
# Helper: ActivityCard converter
# ---------------------------------------------------------------------------

def _to_activity_card(activity) -> ActivityCard:
    return ActivityCard(
        id=str(activity.id),
        title=activity.title,
        activity_type=activity.activity_type,
        status=activity.status,
        due_at=activity.due_at.isoformat() if activity.due_at else None,
        kgs_pathway=activity.kgs_pathway,
    )


# ---------------------------------------------------------------------------
# Activity surface
# ---------------------------------------------------------------------------

def _populate_activity_surface(digest, user, now, today):
    from activity.models import Activity

    # Tenant IDs the user is active in
    # related_name on UserPermission.user is 'tenant_permissions'
    tenant_ids = user.tenant_permissions.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    # Personal (no tenant) OR assigned in the user's tenants
    qs = Activity.objects.filter(
        deleted_at__isnull=True
    ).filter(
        models.Q(created_by=user, tenant__isnull=True) |
        models.Q(assigned_to=user, tenant_id__in=list(tenant_ids))
    )

    active = qs.filter(status__in=['pending', 'in_progress'])
    digest.pending_count = active.count()

    overdue_qs = active.filter(
        due_at__isnull=False,
        due_at__lt=now,
    ).exclude(activity_type='reminder')
    digest.overdue_count = overdue_qs.count()
    digest.overdue_items = [
        _to_activity_card(a) for a in overdue_qs.order_by('due_at')[:5]
    ]

    due_today_qs = active.filter(
        due_at__date=today,
    ).exclude(activity_type='reminder')
    digest.due_today = [
        _to_activity_card(a) for a in due_today_qs.order_by('due_at')[:5]
    ]

    habits = qs.filter(
        activity_type='habit',
        recurrence='daily',
        status__in=['pending', 'in_progress'],
    )
    digest.habit_streaks = [_calculate_streak(h) for h in habits]


# ---------------------------------------------------------------------------
# Habit streak
# ---------------------------------------------------------------------------

def _calculate_streak(activity) -> HabitStreak:
    from activity.models import ActivityLog

    logs = ActivityLog.objects.filter(
        activity=activity,
        event_type='status_changed',
        new_value='completed',
    ).order_by('-created_at').values_list('created_at', flat=True)

    # Both sides of this comparison must use the same (local) calendar date —
    # l is a UTC-stored created_at; .date() alone would give the UTC date.
    completed_dates = {timezone.localtime(l).date() for l in logs}
    streak = 0
    check_date = timezone.localtime(timezone.now()).date()
    while check_date in completed_dates:
        streak += 1
        check_date -= datetime.timedelta(days=1)

    last = logs.first()
    return HabitStreak(
        activity_id=str(activity.id),
        title=activity.title,
        streak=streak,
        last_completed=last.date().isoformat() if last else None,
    )


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

def _populate_reminders(digest, user, now):
    from activity.models import Activity

    cutoff = now + datetime.timedelta(hours=24)
    qs = Activity.objects.filter(
        deleted_at__isnull=True,
        created_by=user,
        activity_type='reminder',
        status__in=['pending', 'in_progress'],
        due_at__isnull=False,
        due_at__lte=cutoff,
        due_at__gte=now,
    ).order_by('due_at')[:5]

    digest.pending_reminders = [_to_activity_card(a) for a in qs]


# ---------------------------------------------------------------------------
# Learn surface
# ---------------------------------------------------------------------------

def _populate_learn(digest, user):
    from records.models import Record, Relationship
    from activity.models import Activity

    # Programme enrolments (in_progress or pending)
    enrolments = Activity.objects.filter(
        deleted_at__isnull=True,
        assigned_to=user,
        activity_type='programme',
        metadata__source_app='learn',
        status__in=['pending', 'in_progress'],
    ).order_by('-updated_at')

    cards = []
    first_programme = None
    for enr in enrolments:
        prog_id = enr.metadata.get('programme_record_id')
        if not prog_id:
            continue
        try:
            rec = Record.objects.get(id=prog_id)
            cards.append(ProgrammeCard(
                record_id=str(rec.id),
                title=rec.title,
                progress=enr.progress,
            ))
            if first_programme is None:
                first_programme = rec
        except Record.DoesNotExist:
            pass

    digest.active_enrolments = cards

    if first_programme is None:
        return

    # Next lesson: first uncompleted lesson in the learner's most recent active programme
    completed_lesson_ids = set(
        Activity.objects.filter(
            assigned_to=user,
            activity_type='lesson',
            status='completed',
        ).values_list('metadata__lesson_record_id', flat=True)
    )

    course_ids = Relationship.objects.filter(
        to_record_id=first_programme.id,
        relationship_type='part_of',
    ).values_list('from_record_id', flat=True)

    for course_id in course_ids:
        lesson_rels = (
            Relationship.objects
            .filter(to_record_id=course_id, relationship_type='part_of')
            .select_related('from_record')
            .order_by('from_record__created_at')
        )
        for rel in lesson_rels:
            if str(rel.from_record_id) not in completed_lesson_ids:
                lesson = rel.from_record
                digest.next_lesson = LessonCard(
                    record_id=str(lesson.id),
                    title=lesson.title,
                    programme_title=first_programme.title,
                    url=f'/learn/lesson/{lesson.id}/',
                )
                return


# ---------------------------------------------------------------------------
# Video learning progress
# ---------------------------------------------------------------------------

def _populate_video_progress(digest, user):
    """
    Surface learning videos that the user has started but not completed.
    These are Activity records written by VideoProgressTracker on Desktop:
      - activity_type = 'lesson'  (or any type with source_app = 'learn')
      - metadata.video_record_id set
      - progress in (25, 50, 75) — started but not at 100
    Completed videos (progress == 100 / status == 'completed') are excluded.
    """
    from activity.models import Activity
    from records.models import Record

    qs = Activity.objects.filter(
        deleted_at__isnull=True,
        assigned_to=user,
        status__in=['pending', 'in_progress'],
        progress__gt=0,
        progress__lt=100,
        metadata__source_app='learn',
    ).order_by('-updated_at')[:5]

    cards = []
    for activity in qs:
        video_record_id = activity.metadata.get('video_record_id')
        if not video_record_id:
            continue
        try:
            rec = Record.objects.get(id=video_record_id, record_family='media')
        except Record.DoesNotExist:
            continue
        cards.append(VideoProgressCard(
            activity_id=str(activity.id),
            video_record_id=video_record_id,
            title=rec.title,
            progress=activity.progress,
            url=f'/video/{video_record_id}/',
        ))

    digest.video_in_progress = cards


# ---------------------------------------------------------------------------
# DAR lookup
# ---------------------------------------------------------------------------

def _get_dar_today(user, today) -> Optional[DARCard]:
    from records.models import Record

    dar = Record.objects.filter(
        created_by=user,
        created_at__date=today,
    ).filter(
        models.Q(record_type='dar') | models.Q(metadata__dar=True)
    ).first()

    if not dar:
        return None

    return DARCard(
        record_id=str(dar.id),
        title=dar.title,
        created_at=dar.created_at.isoformat(),
        url=f'/records/{dar.id}/',
    )


# ---------------------------------------------------------------------------
# Team counts (Level 3+)
# ---------------------------------------------------------------------------

def _populate_team_counts(digest, user, now, today):
    from activity.models import Activity

    # Primary steward tenant: highest-level UserPermission
    # UserPermission.level (not competence_level) is the ordering field
    perm = user.tenant_permissions.filter(
        is_active=True
    ).order_by('-level').first()

    if not perm:
        return

    tenant = perm.tenant
    team_qs = Activity.objects.filter(
        deleted_at__isnull=True,
        tenant=tenant,
        status__in=['pending', 'in_progress'],
    )
    digest.team_pending_count = team_qs.count()
    digest.team_overdue_count = team_qs.filter(
        due_at__isnull=False,
        due_at__lt=now,
    ).count()


# ---------------------------------------------------------------------------
# Suggestions (rule-based)
# ---------------------------------------------------------------------------

def _build_suggestions(digest) -> list:
    """
    Generate a prioritised list of plain-text action suggestions based on
    the fully-populated ParacleteDigest. Called after all other helpers so
    it can read any field on the digest.

    Returns at most 5 suggestions, most urgent first.
    Each suggestion is a dict with keys: { text, priority, action_url }.
    """
    suggestions = []

    # Rule 1 — Overdue items (highest urgency)
    if digest.overdue_count > 0:
        first = digest.overdue_items[0] if digest.overdue_items else None
        if first:
            suggestions.append({
                'text': f'"{first.title}" is overdue — address this today.',
                'priority': 1,
                'action_url': f'/activity/{first.id}/',
            })
        if digest.overdue_count > 1:
            suggestions.append({
                'text': f'You have {digest.overdue_count} overdue activities. Clear the backlog.',
                'priority': 1,
                'action_url': '/activity/',
            })

    # Rule 2 — No DAR submitted today (Level 1+)
    if not digest.dar_today:
        suggestions.append({
            'text': 'Submit your Daily Activity Report before the day ends.',
            'priority': 2,
            'action_url': '/records/htmx/create/?record_type=dar',
        })

    # Rule 3 — Habit streak broken (streak == 0 means not completed today)
    broken_habits = [h for h in digest.habit_streaks if h.streak == 0]
    if broken_habits:
        h = broken_habits[0]
        suggestions.append({
            'text': f'Restart your "{h.title}" habit — mark it complete today.',
            'priority': 2,
            'action_url': f'/activity/{h.activity_id}/',
        })

    # Rule 4 — Active enrolments but no next lesson found
    if digest.active_enrolments and digest.next_lesson is None:
        prog = digest.active_enrolments[0]
        suggestions.append({
            'text': f'Continue your programme "{prog.title}" — find the next lesson.',
            'priority': 3,
            'action_url': f'/learn/programme/{prog.record_id}/',
        })

    # Rule 5 — Next lesson is ready
    if digest.next_lesson:
        suggestions.append({
            'text': f'Your next lesson is ready: "{digest.next_lesson.title}".',
            'priority': 3,
            'action_url': digest.next_lesson.url,
        })

    # Rule 5b — Video lesson in progress
    if digest.video_in_progress:
        v = digest.video_in_progress[0]
        suggestions.append({
            'text': f'Continue watching "{v.title}" — you\'re {v.progress}% through.',
            'priority': 3,
            'action_url': v.url,
        })

    # Rule 6 — Many pending items (workload warning)
    if digest.pending_count >= 10:
        suggestions.append({
            'text': f'You have {digest.pending_count} pending activities. Consider delegating or deferring.',
            'priority': 3,
            'action_url': '/activity/',
        })

    # Rule 7 — Team overdue (Level 3+)
    if digest.team_overdue_count and digest.team_overdue_count > 0:
        suggestions.append({
            'text': f'Your team has {digest.team_overdue_count} overdue activities. Review with your members.',
            'priority': 2,
            'action_url': '/community/management/',
        })

    # Sort by priority (ascending = most urgent first), deduplicate by text
    seen = set()
    unique = []
    for s in sorted(suggestions, key=lambda x: x['priority']):
        if s['text'] not in seen:
            seen.add(s['text'])
            unique.append(s)

    return unique[:5]


# ---------------------------------------------------------------------------
# Prompt selection
# ---------------------------------------------------------------------------

def _select_prompt(user, level):
    from activity.models import Activity
    from .models import ParacletePrompt

    cutoff = timezone.now() - datetime.timedelta(days=14)

    pathway_counts = (
        Activity.objects
        .filter(
            created_by=user,
            status='completed',
            updated_at__gte=cutoff,
            kgs_pathway__isnull=False,
        )
        .values('kgs_pathway')
        .annotate(n=models.Count('id'))
        .order_by('n')
    )

    least_pathway = (
        pathway_counts.first()['kgs_pathway']
        if pathway_counts.exists() else None
    )

    qs = ParacletePrompt.objects.filter(is_active=True, min_level__lte=level)

    if least_pathway:
        pathway_qs = qs.filter(pathway=least_pathway)
        if pathway_qs.exists():
            qs = pathway_qs

    prompt = random.choice(list(qs)) if qs.exists() else None

    if prompt:
        return prompt.text, prompt.pathway

    return ('Press into the Lord today.', 'spiritual_formation')
