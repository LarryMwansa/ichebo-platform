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
    today = now.date()

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
    digest.dar_today = _get_dar_today(user, today)

    # Level 3+ — team counts
    if level >= 3:
        _populate_team_counts(digest, user, now, today)

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

    completed_dates = {l.date() for l in logs}
    streak = 0
    check_date = timezone.now().date()
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
    from records.models import Record
    from activity.models import Activity

    # Active enrolment activities (programme-level, in_progress)
    enrolments = Activity.objects.filter(
        deleted_at__isnull=True,
        created_by=user,
        metadata__source_app='learn',
        status='in_progress',
    )

    cards = []
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
        except Record.DoesNotExist:
            pass

    digest.active_enrolments = cards

    # Next lesson: most recently updated incomplete lesson task
    next_task = Activity.objects.filter(
        deleted_at__isnull=True,
        created_by=user,
        metadata__source_app='learn',
        activity_type='task',
        status__in=['pending', 'in_progress'],
    ).order_by('-updated_at').first()

    if next_task:
        lesson_id = next_task.metadata.get('lesson_record_id')
        prog_title = next_task.metadata.get('programme_title', '')
        if lesson_id:
            try:
                lesson = Record.objects.get(id=lesson_id)
                digest.next_lesson = LessonCard(
                    record_id=str(lesson.id),
                    title=lesson.title,
                    programme_title=prog_title,
                    url=f'/learn/lesson/{lesson.id}/',
                )
            except Record.DoesNotExist:
                pass


# ---------------------------------------------------------------------------
# DAR lookup
# ---------------------------------------------------------------------------

def _get_dar_today(user, today) -> Optional[DARCard]:
    from records.models import Record

    dar = Record.objects.filter(
        created_by=user,
        record_type='note',
        created_at__date=today,
        metadata__dar=True,
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
