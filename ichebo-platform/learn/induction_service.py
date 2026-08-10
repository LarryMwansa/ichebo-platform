# learn/induction_service.py — business logic for the induction curriculum
from django.utils import timezone
from .models import InductionStep, InductionProgress


PASS_SCORE = 70  # % threshold to pass a quiz or test


def enrol_user(user):
    """Create InductionProgress rows for all steps visible to this user.

    Called when a user is first placed in the Induction tenant. The first
    step is set to 'available'; everything else starts 'locked'.
    Idempotent — safe to call multiple times."""
    pathway = getattr(user, 'induction_pathway', 'beginners') or 'beginners'
    steps = _steps_for_pathway(pathway)

    existing_ids = set(
        InductionProgress.objects.filter(user=user)
        .values_list('step_id', flat=True)
    )

    to_create = []
    for i, step in enumerate(steps):
        if step.id not in existing_ids:
            status = 'available' if i == 0 else 'locked'
            to_create.append(InductionProgress(
                user=user,
                step=step,
                status=status,
            ))

    if to_create:
        InductionProgress.objects.bulk_create(to_create)

    return len(to_create)


def get_progress_for_user(user):
    """Return ordered list of (step, progress) for this user's pathway.

    Steps not in the user's pathway (e.g. reconditioning lessons for a
    beginner) are excluded entirely."""
    pathway = getattr(user, 'induction_pathway', 'beginners') or 'beginners'
    steps = _steps_for_pathway(pathway)
    step_ids = [s.id for s in steps]

    progress_map = {
        p.step_id: p
        for p in InductionProgress.objects.filter(user=user, step_id__in=step_ids)
    }

    result = []
    for step in steps:
        prog = progress_map.get(step.id)
        result.append((step, prog))
    return result


def get_current_step(user):
    """Return the (step, progress) the user should be working on now —
    the first 'available' or 'in_progress' entry, or None if complete."""
    pathway = getattr(user, 'induction_pathway', 'beginners') or 'beginners'
    steps = _steps_for_pathway(pathway)
    step_ids = [s.id for s in steps]

    prog = (
        InductionProgress.objects
        .filter(user=user, step_id__in=step_ids, status__in=('available', 'in_progress'))
        .select_related('step')
        .order_by('step__sequence_order')
        .first()
    )
    if prog:
        return prog.step, prog

    # All passed or awaiting_steward — find awaiting_steward
    awaiting = (
        InductionProgress.objects
        .filter(user=user, step_id__in=step_ids, status='awaiting_steward')
        .select_related('step')
        .first()
    )
    if awaiting:
        return awaiting.step, awaiting

    return None, None


def mark_lesson_read(user, step):
    """Mark a lesson step as passed and unlock the next step."""
    if step.step_type != 'lesson':
        return
    prog, _ = InductionProgress.objects.get_or_create(
        user=user, step=step,
        defaults={'status': 'available'},
    )
    if prog.status in ('locked', 'available', 'in_progress'):
        prog.status = 'passed'
        prog.completed_at = timezone.now()
        if not prog.started_at:
            prog.started_at = timezone.now()
        prog.save(update_fields=['status', 'completed_at', 'started_at'])
        _unlock_next(user, step)


def submit_quiz(user, step, answer_ids):
    """Score a quiz/test submission.

    answer_ids — list of InductionAnswer UUIDs the user selected (one per question).
    Returns dict: {score, passed, correct, total, prog}.
    """
    from .models import InductionQuestion, InductionAnswer

    questions = list(step.questions.prefetch_related('answers'))
    total = len(questions)
    if total == 0:
        return {'score': 100, 'passed': True, 'correct': 0, 'total': 0, 'prog': None}

    answer_ids_set = set(str(a) for a in answer_ids)
    correct = 0
    for q in questions:
        correct_answer = q.answers.filter(is_correct=True).first()
        if correct_answer and str(correct_answer.id) in answer_ids_set:
            correct += 1

    score = int((correct / total) * 100)
    passed = score >= step.pass_score

    prog, _ = InductionProgress.objects.get_or_create(
        user=user, step=step,
        defaults={'status': 'in_progress'},
    )
    prog.attempts += 1
    prog.score = score
    if not prog.started_at:
        prog.started_at = timezone.now()

    if passed:
        if step.step_type == 'final_test':
            prog.status = 'awaiting_steward'
        else:
            prog.status = 'passed'
            prog.completed_at = timezone.now()
            _unlock_next(user, step)
    else:
        prog.status = 'in_progress'

    prog.save(update_fields=['status', 'score', 'attempts', 'started_at', 'completed_at'])

    return {
        'score': score,
        'passed': passed,
        'correct': correct,
        'total': total,
        'prog': prog,
    }


def confirm_final_test(user, confirmed_by):
    """Steward confirms the Final Test — advances user to competence_level 1."""
    from accounts.models import User as UserModel

    pathway = getattr(user, 'induction_pathway', 'beginners') or 'beginners'
    steps = _steps_for_pathway(pathway)
    step_ids = [s.id for s in steps]

    final = (
        InductionProgress.objects
        .filter(user=user, step_id__in=step_ids, status='awaiting_steward')
        .select_related('step')
        .first()
    )
    if not final:
        return False

    final.status = 'passed'
    final.completed_at = timezone.now()
    final.save(update_fields=['status', 'completed_at'])

    UserModel.objects.filter(pk=user.pk).update(competence_level=1)
    user.refresh_from_db(fields=['competence_level'])
    return True


def _steps_for_pathway(pathway):
    """All active steps visible to a given pathway — 'all' steps plus the
    pathway-specific Module 2 steps."""
    return list(
        InductionStep.objects
        .filter(is_active=True)
        .filter(pathway__in=('all', pathway))
        .order_by('sequence_order')
    )


def _unlock_next(user, completed_step):
    """Unlock the step immediately after completed_step in this user's pathway."""
    pathway = getattr(user, 'induction_pathway', 'beginners') or 'beginners'
    steps = _steps_for_pathway(pathway)

    ids = [s.id for s in steps]
    try:
        idx = ids.index(completed_step.id)
    except ValueError:
        return

    if idx + 1 < len(steps):
        next_step = steps[idx + 1]
        InductionProgress.objects.filter(
            user=user, step=next_step, status='locked'
        ).update(status='available')
