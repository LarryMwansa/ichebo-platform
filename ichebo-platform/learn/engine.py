"""
learn/engine.py — the curriculum engine.

One engine, any programme. Supplies ordered steps, sequential unlock, quiz
scoring with a configurable pass threshold, attempt limits, and pathway
forking. Induction is simply the first programme to switch it on; nothing in
here knows what induction is.

WHERE STATE LIVES — this matters, because getting it wrong is what the old
induction_service did:

    Completion, progress %, rollup, certification   → activity.Activity tree
                                                      (built by services.py)
    Attempt history and scores                      → AssessmentAttempt
    Unlock state                                    → DERIVED, never stored
    competence_level                                → services.confirm_certification_record
                                                      and nothing else, ever

Unlock is computed from the ordered chain of task Activities on every read.
The predecessor model stored a per-step status row and unlocked only the
immediately-following step, so inserting a step mid-curriculum left everyone
already enrolled permanently stuck behind it. Deriving costs one extra query
and cannot drift.

Engine config is read from Record.custom_fields['engine'], merged programme →
course, with per-record overrides for pass_score. A programme without an
'engine' key behaves exactly as before: free browsing, no gates.
"""
from dataclasses import dataclass, field
from typing import Optional

from django.db import transaction

from activity.models import Activity
from records.models import Record, Relationship

from learn import services
from learn.models import AssessmentAttempt, AssessmentQuestion

# Record types that can be a step in a curriculum.
STEP_TYPES = ['lesson', 'assignment', 'quiz']

# Statuses a Record must have to be visible to a learner.
LIVE_STATUSES = ['active', 'locked']

STEP_KIND_LABELS = {
    'lesson': 'Lesson',
    'assignment': 'Assignment',
    'quiz': 'Knowledge Check Quiz',
    'module_test': 'Module Test',
    'final_test': 'Final Test',
}

DEFAULT_CONFIG = {
    'enabled': False,
    'sequential_unlock': False,
    'pass_score': 70,
    'max_attempts': 0,          # 0 = unlimited
    'pathway_attr': '',
}


class EngineError(Exception):
    """Raised when an action is attempted against the engine's rules."""


# ── Ordering ─────────────────────────────────────────────────────────────────

def ordered_child_edges(parent, types=None, statuses=None):
    """Return [(child_record, edge)] for a parent, in curriculum order.

    `parent` may be a Record or its id. Order is (sequence_order, created_at);
    the created_at tiebreak keeps behaviour stable for edges the backfill
    didn't reach — they all sit at 0 and fall back to the old ordering.
    """
    parent_id = getattr(parent, 'id', parent)
    edges = (
        Relationship.objects
        .filter(
            to_record_id=parent_id,
            relationship_type='part_of',
            deleted_at__isnull=True,
        )
        .select_related('from_record')
        .order_by('sequence_order', 'from_record__created_at')
    )

    rows = []
    for edge in edges:
        child = edge.from_record
        if child is None or child.deleted_at is not None:
            continue
        if types is not None and child.record_type not in types:
            continue
        if statuses is not None and child.status not in statuses:
            continue
        rows.append((child, edge))
    return rows


def ordered_children(parent, types=None, statuses=None):
    """Return child Records of a parent in curriculum order.

    `parent` may be a Record or its id.
    """
    return [child for child, _ in ordered_child_edges(parent, types, statuses)]


# ── Config ───────────────────────────────────────────────────────────────────

def get_engine_config(programme, course=None, record=None):
    """Merge engine config: defaults → programme → course → record."""
    cfg = dict(DEFAULT_CONFIG)

    for source in (programme, course):
        if source is None:
            continue
        cfg.update((source.custom_fields or {}).get('engine') or {})

    if record is not None:
        custom = record.custom_fields or {}
        if custom.get('pass_score') is not None:
            cfg['pass_score'] = custom['pass_score']

    return cfg


def pathway_for(user, programme):
    """Return the set of edge pathway values this user should see.

    'all' is always included — most steps are shared. A programme that
    doesn't fork (no pathway_attr) therefore just gets {'all'}, and any
    pathway-tagged edge is invisible to everyone, which is the safe default.
    """
    cfg = get_engine_config(programme)
    attr = cfg.get('pathway_attr')
    if not attr:
        return {'all'}
    value = getattr(user, attr, None) or 'all'
    return {'all', value}


def step_kind(record):
    """The step's kind: its assessment_kind if set, else its record_type."""
    return (record.custom_fields or {}).get('assessment_kind') or record.record_type


# ── Step ─────────────────────────────────────────────────────────────────────

@dataclass
class Step:
    """A curriculum step resolved for one learner.

    The shim properties at the bottom (.id, .title, .step_type, .module …)
    exist so templates written against the old InductionStep keep working.
    """
    record: Record
    course: Record
    sequence: int
    pathway: str
    kind: str
    pass_score: int
    max_attempts: int
    activity: Optional[Activity] = None
    attempts: list = field(default_factory=list)
    unlocked: bool = False
    status: str = 'locked'

    # ── shims for templates written against InductionStep ──
    @property
    def id(self):
        return self.record.id

    @property
    def title(self):
        return self.record.title

    @property
    def content(self):
        return self.record.content or ''

    @property
    def step_type(self):
        return self.kind

    def get_step_type_display(self):
        return STEP_KIND_LABELS.get(self.kind, self.kind.replace('_', ' ').title())

    @property
    def module(self):
        return self.course.title

    # ── state ──
    @property
    def is_assessment(self):
        return self.record.record_type == 'quiz' or self.kind in (
            'quiz', 'module_test', 'final_test'
        )

    @property
    def is_final(self):
        return bool((self.record.custom_fields or {}).get('is_final_assessment'))

    @property
    def passed(self):
        return self.status in ('passed', 'awaiting_steward')

    @property
    def attempt_count(self):
        return len(self.attempts)

    @property
    def score(self):
        """Best score achieved, or None if never attempted."""
        if not self.attempts:
            return None
        return max(a.score for a in self.attempts)

    @property
    def video_url(self):
        return (self.record.custom_fields or {}).get('video_url') or ''


# ── Reading the curriculum ───────────────────────────────────────────────────

def get_steps(user, programme):
    """Resolve the full ordered step list for a learner, with unlock state.

    Four queries regardless of curriculum size: courses, step edges,
    the learner's task Activities, and their attempts.
    """
    cfg = get_engine_config(programme)
    pathways = pathway_for(user, programme)

    rows = []          # (course, record, edge, course_cfg)
    for course in ordered_children(programme, ['course'], LIVE_STATUSES):
        course_cfg = get_engine_config(programme, course)
        for record, edge in ordered_child_edges(course, STEP_TYPES, LIVE_STATUSES):
            edge_pathway = (edge.metadata or {}).get('pathway') or 'all'
            if edge_pathway not in pathways:
                continue
            rows.append((course, record, edge, edge_pathway, course_cfg))

    record_ids = [r.id for _, r, _, _, _ in rows]
    if not record_ids:
        return []

    activities = {
        a.linked_record_id: a
        for a in Activity.objects.filter(
            assigned_to=user,
            activity_type='task',
            linked_record_id__in=record_ids,
            deleted_at__isnull=True,
        )
    }

    attempts_by_record = {}
    for attempt in AssessmentAttempt.objects.filter(
        user=user, record_id__in=record_ids
    ).order_by('record_id', '-created_at'):
        attempts_by_record.setdefault(attempt.record_id, []).append(attempt)

    pending_cert = awaiting_confirmation(user, programme)

    steps = []
    previous_complete = True        # the first step is always reachable
    for index, (course, record, edge, edge_pathway, course_cfg) in enumerate(rows, start=1):
        step_cfg = get_engine_config(programme, course, record)
        activity = activities.get(record.id)
        attempts = attempts_by_record.get(record.id, [])
        is_complete = activity is not None and activity.status == 'completed'

        step = Step(
            record=record,
            course=course,
            sequence=index,
            pathway=edge_pathway,
            kind=step_kind(record),
            pass_score=step_cfg['pass_score'],
            max_attempts=step_cfg['max_attempts'],
            activity=activity,
            attempts=attempts,
            unlocked=(not course_cfg['sequential_unlock']) or previous_complete,
        )

        if is_complete and step.is_final and pending_cert is not None:
            step.status = 'awaiting_steward'
        elif is_complete:
            step.status = 'passed'
        elif not step.unlocked:
            step.status = 'locked'
        elif attempts:
            step.status = 'in_progress'
        else:
            step.status = 'available'

        steps.append(step)
        previous_complete = is_complete

    return steps


def get_step(user, programme, record_id):
    """One resolved Step by record id, or None."""
    for step in get_steps(user, programme):
        if str(step.record.id) == str(record_id):
            return step
    return None


def get_current_step(steps):
    """The first step the learner can act on, or None if all are done."""
    for step in steps:
        if step.unlocked and step.status not in ('passed', 'awaiting_steward'):
            return step
    return None


def progress_summary(steps):
    """(passed, total, percent) for a resolved step list."""
    total = len(steps)
    passed = sum(1 for s in steps if s.passed)
    percent = int((passed / total) * 100) if total else 0
    return passed, total, percent


def group_by_course(steps):
    """[{'course': Record, 'steps': [Step, …]}] preserving curriculum order."""
    grouped = []
    for step in steps:
        if not grouped or grouped[-1]['course'].id != step.course.id:
            grouped.append({'course': step.course, 'steps': []})
        grouped[-1]['steps'].append(step)
    return grouped


# ── Locating a programme from a step ─────────────────────────────────────────

def programme_for_step(record):
    """Walk lesson → course → programme. Returns (programme, course) or (None, None)."""
    course_edge = (
        Relationship.objects
        .filter(from_record=record, relationship_type='part_of', deleted_at__isnull=True)
        .select_related('to_record')
        .first()
    )
    if course_edge is None or course_edge.to_record is None:
        return None, None
    course = course_edge.to_record

    programme_edge = (
        Relationship.objects
        .filter(from_record=course, relationship_type='part_of', deleted_at__isnull=True)
        .select_related('to_record')
        .first()
    )
    if programme_edge is None or programme_edge.to_record is None:
        return None, course
    return programme_edge.to_record, course


# ── Enrolment ────────────────────────────────────────────────────────────────

def get_enrolment(user, programme):
    """The learner's programme Activity for this programme, or None."""
    return Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        linked_record=programme,
        deleted_at__isnull=True,
    ).first()


def ensure_enrolled(user, programme, tenant=None):
    """Enrol if not already enrolled. Idempotent — safe on every page load."""
    existing = get_enrolment(user, programme)
    if existing is not None:
        return existing
    try:
        return services.enrol_in_programme(user, programme, tenant=tenant)
    except services.EnrolmentError:
        # Raced with another request, or prerequisites fail. Either way the
        # caller wants whatever enrolment exists, not an exception.
        return get_enrolment(user, programme)


@transaction.atomic
def sync_enrolment(user, programme, tenant=None):
    """Add task Activities for steps published after the learner enrolled.

    Without this, anyone already enrolled is frozen at the curriculum as it
    stood on their enrolment day — which is exactly the situation when 42
    steps replace 4. Returns the number of task Activities created.
    """
    programme_activity = get_enrolment(user, programme)
    if programme_activity is None:
        return 0

    steps = get_steps(user, programme)
    missing = [s for s in steps if s.activity is None]
    if not missing:
        return 0

    # Course-level Activities, keyed by the course Record they track.
    course_activities = {
        a.linked_record_id: a
        for a in Activity.objects.filter(
            parent_activity=programme_activity,
            activity_type='project',
            deleted_at__isnull=True,
        )
    }

    created = 0
    for step in missing:
        course_activity = course_activities.get(step.course.id)
        if course_activity is None:
            course_activity = Activity.objects.create(
                tenant=tenant or programme_activity.tenant,
                created_by=user,
                assigned_to=user,
                activity_type='project',
                title=step.course.title,
                status='in_progress',
                progress=0,
                parent_activity=programme_activity,
                linked_record=step.course,
                metadata={
                    'source_app': 'learn',
                    'course_record_id': str(step.course.id),
                    'programme_record_id': str(programme.id),
                },
            )
            course_activities[step.course.id] = course_activity

        Activity.objects.create(
            tenant=tenant or programme_activity.tenant,
            created_by=user,
            assigned_to=user,
            activity_type='task',
            title=step.record.title,
            status='pending',
            progress=0,
            parent_activity=course_activity,
            linked_record=step.record,
            metadata={
                'source_app': 'learn',
                'lesson_record_id': str(step.record.id),
                'course_record_id': str(step.course.id),
                'programme_record_id': str(programme.id),
            },
        )
        created += 1

    for course_activity in course_activities.values():
        services._recalculate_progress(course_activity)
    services._recalculate_progress(programme_activity)

    return created


def enrol_and_sync(user, programme, tenant=None):
    """Enrol if needed, then top up any missing steps. Returns the Activity.

    The sync is skipped unless the step count and task-Activity count actually
    disagree, so a normal page load stays read-only.
    """
    programme_activity = ensure_enrolled(user, programme, tenant=tenant)
    if programme_activity is None:
        return None

    expected = len(get_steps(user, programme))
    actual = Activity.objects.filter(
        assigned_to=user,
        activity_type='task',
        parent_activity__parent_activity=programme_activity,
        deleted_at__isnull=True,
    ).count()

    if expected != actual:
        sync_enrolment(user, programme, tenant=tenant)

    return programme_activity


# ── Completing steps ─────────────────────────────────────────────────────────

def mark_lesson_complete(user, step):
    """Complete a lesson step. Delegates to services so rollup and the
    certification signal fire through the one existing path."""
    if not step.unlocked:
        raise EngineError('This step is locked.')
    if step.activity is None:
        raise EngineError('You are not enrolled in this programme.')
    if step.activity.status == 'completed':
        return step.activity
    return services.complete_lesson(user, step.activity)


def score_assessment(user, step, selected_option_ids):
    """Score a submission, record the attempt, and complete the step on a pass.

    `selected_option_ids` is the flat list of chosen AssessmentOption ids —
    exactly what request.POST.getlist('answer') returns. Which question each
    belongs to is resolved here rather than trusted from the form.
    """
    if not step.unlocked:
        raise EngineError('This step is locked.')

    if step.max_attempts and step.attempt_count >= step.max_attempts:
        raise EngineError(
            f'You have used all {step.max_attempts} attempts for this assessment.'
        )

    questions = list(
        AssessmentQuestion.objects
        .filter(record=step.record)
        .prefetch_related('options')
        .order_by('order')
    )
    if not questions:
        raise EngineError('This assessment has no questions yet.')

    chosen = {str(o) for o in selected_option_ids}

    responses = {}
    correct_count = 0
    for question in questions:
        options = list(question.options.all())
        selected = {str(o.id) for o in options if str(o.id) in chosen}
        expected = {str(o.id) for o in options if o.is_correct}

        responses[str(question.id)] = sorted(selected)

        # Exact-set match handles single and multi choice identically, and
        # correctly refuses a multi-choice answer that is merely a subset.
        if expected and selected == expected:
            correct_count += 1

    total = len(questions)
    score = int((correct_count / total) * 100)
    passed = score >= step.pass_score

    attempt = AssessmentAttempt.objects.create(
        user=user,
        record=step.record,
        attempt_number=step.attempt_count + 1,
        score=score,
        passed=passed,
        responses=responses,
    )

    # Keep the in-memory step consistent for anything rendering off it after.
    step.attempts.insert(0, attempt)

    if passed:
        mark_lesson_complete(user, step)

    return {
        'attempt': attempt,
        'score': score,
        'passed': passed,
        'correct': correct_count,
        'total': total,
        'pass_score': step.pass_score,
    }


# ── Steward gate ─────────────────────────────────────────────────────────────

def awaiting_confirmation(user, programme):
    """The learner's draft certification for this programme, or None.

    Created by learn.signals.auto_create_draft_certification once the
    programme Activity hits 100%. Confirmed — and competence_level advanced —
    only by services.confirm_certification_record.
    """
    return Record.objects.filter(
        record_type='certification',
        created_by=user,
        metadata__programme_record_id=str(programme.id),
        status='draft',
        deleted_at__isnull=True,
    ).first()


def pending_confirmations(programme=None, context=None):
    """Draft certifications awaiting a steward, newest first.

    Filter by `context='induction_completion'` for the induction queue.
    """
    qs = Record.objects.filter(
        record_type='certification',
        status='draft',
        deleted_at__isnull=True,
    )
    if programme is not None:
        qs = qs.filter(metadata__programme_record_id=str(programme.id))
    if context:
        qs = qs.filter(metadata__context=context)
    return qs.select_related('created_by').order_by('-created_at')
