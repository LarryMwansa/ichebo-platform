"""
Convert the standalone induction curriculum into ordinary learning Records.

Before: InductionStep/Question/Answer/Progress — a parallel system with no
authoring UI, reachable only from sceptre.
After:  Records + Relationships driven by learn/engine.py — authored through
        the same Curriculum Authoring surface as every other programme.

Shape produced:

    Induction Programme            (existing Record, record_type='induction')
      └─ Module 1 — Keys to the Kingdom      (course, sequence_order=1)
           ├─ Lesson 1: What is the Kingdom? (lesson, sequence_order=1)
           ├─ Knowledge Check Quiz 1         (quiz,   sequence_order=2)
           └─ …
      └─ Module 2 … 4

The four existing skeleton lesson Records are *converted* into the four module
courses — their titles already match the modules, so reusing them keeps the
records anyone has already linked to.

Idempotent. Safe to re-run. Always dry-run against a production restore first:

    python manage.py migrate_induction_to_records --dry-run
    python manage.py migrate_induction_to_records
"""
import json
from pathlib import Path

from django.core import serializers as django_serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from activity.models import Activity
from records.models import Record, Relationship

from learn import engine, services
from learn.models import (
    AssessmentAttempt,
    AssessmentOption,
    AssessmentQuestion,
    InductionAnswer,
    InductionProgress,
    InductionQuestion,
    InductionStep,
)

# Existing skeleton lesson title → (module number, module course title).
# Mapped by TITLE, not by seed order: modules 3 and 4 are inverted relative to
# the order the skeleton lessons were created in, so an index-based mapping
# would silently file Module 3's steps under "Community Programme".
MODULE_MAP = {
    'Keys To the Kingdom': (1, 'Module 1 — Keys to the Kingdom'),
    'Repentance & Reformation': (2, 'Module 2 — Repentance / Reformation'),
    'The Secret of Living a Fulfilled Life (HAL Beginners)': (3, 'Module 3 — Secret to a Fulfilled Life'),
    'Community Programme': (4, 'Module 4 — The Sceptre Community'),
}

MODULE_TITLES = {num: title for num, title in MODULE_MAP.values()}

INTERMEDIATE_COURSE_TITLE = 'Induction Training'

ENGINE_CONFIG = {
    'enabled': True,
    'sequential_unlock': True,
    'pass_score': 70,
    'max_attempts': 0,
    'pathway_attr': 'induction_pathway',
}

LEGACY_KEY = 'legacy_induction_step_id'


class _DryRun(Exception):
    """Raised to roll back the transaction at the end of a dry run."""


class Command(BaseCommand):
    help = 'Convert InductionStep curriculum into learning Records + Relationships.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Run everything inside a transaction, report, then roll back.',
        )
        parser.add_argument(
            '--author-email', default=None,
            help='User to own created records. Defaults to the induction programme owner.',
        )
        parser.add_argument(
            '--skip-backup', action='store_true',
            help='Skip writing the legacy fixture (dry runs skip it anyway).',
        )

    # ── entry point ──────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.created = {'courses': 0, 'steps': 0, 'questions': 0, 'options': 0}
        self.reused = {'courses': 0, 'steps': 0}

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '\n  DRY RUN — every change below is rolled back at the end.\n'
            ))

        try:
            with transaction.atomic():
                self._run(options)
                if self.dry_run:
                    raise _DryRun
        except _DryRun:
            self.stdout.write(self.style.WARNING('\n  Rolled back. Nothing was written.\n'))
            return

        self.stdout.write(self.style.SUCCESS('\n  Done.\n'))

    def _run(self, options):
        programme = self._resolve_programme()
        author = self._resolve_author(options['author_email'], programme)

        if not self.dry_run and not options['skip_backup']:
            self._backup()

        self._configure_programme(programme)
        modules = self._build_module_courses(programme, author)
        self._convert_steps(programme, modules, author)
        self._carry_over_progress(programme)
        self._assert_result(programme)

    # ── 1. resolve ───────────────────────────────────────────────────────────

    def _resolve_programme(self):
        candidates = list(Record.objects.filter(
            record_family='learning',
            record_type='induction',
            deleted_at__isnull=True,
        ))
        if not candidates:
            raise CommandError(
                'No induction programme Record found '
                "(record_family='learning', record_type='induction')."
            )
        if len(candidates) > 1:
            listing = '\n'.join(f'    {r.id}  {r.title}  [{r.status}]' for r in candidates)
            raise CommandError(
                f'Found {len(candidates)} induction programmes — expected exactly one. '
                f'Resolve this by hand before migrating:\n{listing}'
            )
        programme = candidates[0]
        self.stdout.write(f'  Programme: {programme.title}  ({programme.id})')
        return programme

    def _resolve_author(self, email, programme):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if email:
            try:
                return User.objects.get(email=email)
            except User.DoesNotExist:
                raise CommandError(f'No user with email {email!r}.')

        author = programme.created_by
        if author is None:
            raise CommandError(
                'Induction programme has no created_by — pass --author-email.'
            )
        self.stdout.write(f'  Author:    {author.email}')
        return author

    def _backup(self):
        legacy = (
            list(InductionStep.objects.all())
            + list(InductionQuestion.objects.all())
            + list(InductionAnswer.objects.all())
            + list(InductionProgress.objects.all())
        )
        stamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        path = Path(__file__).resolve().parents[2] / 'fixtures'
        path.mkdir(exist_ok=True)
        target = path / f'induction_legacy_{stamp}.json'
        target.write_text(django_serializers.serialize('json', legacy, indent=2))
        self.stdout.write(f'  Backup:    {target}  ({len(legacy)} rows)')

    # ── 2. programme config ──────────────────────────────────────────────────

    def _configure_programme(self, programme):
        custom = dict(programme.custom_fields or {})
        custom['engine'] = dict(ENGINE_CONFIG)
        programme.custom_fields = custom

        perms = dict(programme.permissions_data or {})
        perms['required_level'] = 0        # induction is what Level 0 does
        programme.permissions_data = perms

        programme.save(update_fields=['custom_fields', 'permissions_data', 'updated_at'])
        self.stdout.write('  Engine config written to programme.')

    # ── 3. module courses ────────────────────────────────────────────────────

    def _build_module_courses(self, programme, author):
        """Return {module_number: course Record}."""
        self.stdout.write('\n  Modules')
        modules = {}

        # Convert the existing skeleton lessons whose titles match a module.
        for old_title, (number, new_title) in MODULE_MAP.items():
            record = Record.objects.filter(
                title=old_title,
                record_family='learning',
                deleted_at__isnull=True,
            ).exclude(record_type='course').first()

            if record is None:
                record = Record.objects.filter(
                    title=new_title, record_type='course', deleted_at__isnull=True
                ).first()

            if record is not None:
                was = record.record_type
                record.record_type = 'course'
                record.title = new_title
                record.status = 'active'
                custom = dict(record.custom_fields or {})
                custom['engine'] = {'sequential_unlock': True, 'pass_score': 70}
                record.custom_fields = custom
                record.save(update_fields=[
                    'record_type', 'title', 'status', 'custom_fields', 'updated_at'
                ])
                self.stdout.write(
                    f'    {number}. {new_title}\n'
                    f'       reused {was} record {record.id} (was {old_title!r})'
                )
                self.reused['courses'] += 1
            else:
                record = Record.objects.create(
                    tenant=programme.tenant,
                    created_by=author,
                    record_class='organizational',
                    record_family='learning',
                    record_type='course',
                    origin='system',
                    title=new_title,
                    status='active',
                    custom_fields={'engine': {'sequential_unlock': True, 'pass_score': 70}},
                    metadata={'source_app': 'learn'},
                    permissions_data={
                        'visibility': 'global', 'required_level': 0,
                        'roles_allowed': [], 'can_edit': [],
                    },
                )
                self.stdout.write(f'    {number}. {new_title}\n       created {record.id}')
                self.created['courses'] += 1

            self._attach(record, programme, number, author)
            modules[number] = record

        self._retire_intermediate_course(programme)
        return modules

    def _retire_intermediate_course(self, programme):
        """Soft-delete the 'Induction Training' course that sat between the
        programme and its lessons.

        The Activity tree is exactly three levels — programme → project →
        task — so programme → course → course → lesson cannot be enrolled in.
        Modules attach directly to the programme instead.
        """
        course = Record.objects.filter(
            title=INTERMEDIATE_COURSE_TITLE,
            record_type='course',
            record_family='learning',
            deleted_at__isnull=True,
        ).first()
        if course is None:
            return

        remaining = engine.ordered_children(course)
        if remaining:
            self.stdout.write(self.style.WARNING(
                f'    Leaving {INTERMEDIATE_COURSE_TITLE!r} in place — it still has '
                f'{len(remaining)} child record(s): '
                + ', '.join(r.title for r in remaining)
            ))
            return

        Relationship.objects.filter(
            from_record=course, relationship_type='part_of'
        ).soft_delete()
        course.soft_delete()
        self.stdout.write(f'    Retired intermediate course {INTERMEDIATE_COURSE_TITLE!r}.')

    # ── 4. steps ─────────────────────────────────────────────────────────────

    def _convert_steps(self, programme, modules, author):
        steps = list(InductionStep.objects.filter(is_active=True).order_by('sequence_order'))
        if not steps:
            raise CommandError('No active InductionStep rows to convert.')

        self.stdout.write(f'\n  Steps ({len(steps)})')

        position = {number: 0 for number in modules}
        for step in steps:
            course = modules.get(step.module)
            if course is None:
                raise CommandError(
                    f'Step {step.sequence_order} references module {step.module}, '
                    f'which has no course. Known modules: {sorted(modules)}'
                )

            position[step.module] += 1
            record = self._upsert_step_record(step, programme, author)
            self._attach(record, course, position[step.module], author, pathway=step.pathway)
            self._copy_questions(step, record)

        self.stdout.write(
            f'    {self.created["steps"]} created, {self.reused["steps"]} already present'
        )
        self.stdout.write(
            f'    {self.created["questions"]} questions, {self.created["options"]} options'
        )

    def _upsert_step_record(self, step, programme, author):
        existing = Record.objects.filter(
            record_family='learning',
            deleted_at__isnull=True,
            **{f'metadata__{LEGACY_KEY}': str(step.id)},
        ).first()

        record_type = 'lesson' if step.step_type == 'lesson' else 'quiz'
        custom = {
            'assessment_kind': step.step_type,
            'pass_score': step.pass_score,
            'is_final_assessment': step.step_type == 'final_test',
        }

        if existing is not None:
            existing.title = step.title
            existing.content = step.content
            existing.record_type = record_type
            merged = dict(existing.custom_fields or {})
            merged.update(custom)
            existing.custom_fields = merged
            existing.save(update_fields=[
                'title', 'content', 'record_type', 'custom_fields', 'updated_at'
            ])
            self.reused['steps'] += 1
            return existing

        record = Record.objects.create(
            tenant=programme.tenant,
            created_by=author,
            record_class='organizational',
            record_family='learning',
            record_type=record_type,
            origin='system',
            title=step.title,
            content=step.content,
            status='active',
            custom_fields=custom,
            metadata={'source_app': 'learn', LEGACY_KEY: str(step.id)},
            permissions_data={
                'visibility': 'global', 'required_level': 0,
                'roles_allowed': [], 'can_edit': [],
            },
        )
        self.created['steps'] += 1
        return record

    def _copy_questions(self, step, record):
        for question in step.questions.all().order_by('order'):
            target, made = AssessmentQuestion.objects.get_or_create(
                record=record,
                order=question.order,
                question_text=question.question_text,
                defaults={'question_type': 'single_choice'},
            )
            if made:
                self.created['questions'] += 1

            for answer in question.answers.all().order_by('order'):
                _, made_option = AssessmentOption.objects.get_or_create(
                    question=target,
                    order=answer.order,
                    answer_text=answer.answer_text,
                    defaults={'is_correct': answer.is_correct},
                )
                if made_option:
                    self.created['options'] += 1

    # ── shared: attach a child to a parent ───────────────────────────────────

    def _attach(self, child, parent, sequence, author, pathway=None):
        """Ensure exactly one live part_of edge from child, pointing at parent."""
        metadata = {'pathway': pathway} if pathway else {}

        edge = Relationship.objects.filter(
            from_record=child, relationship_type='part_of', deleted_at__isnull=True
        ).first()

        if edge is None:
            Relationship.objects.create(
                tenant=parent.tenant,
                created_by=author,
                from_record=child,
                to_record=parent,
                direction='directed',
                relationship_type='part_of',
                sequence_order=sequence,
                metadata=metadata,
            )
            return

        edge.to_record = parent
        edge.sequence_order = sequence
        if pathway:
            merged = dict(edge.metadata or {})
            merged['pathway'] = pathway
            edge.metadata = merged
        edge.save(update_fields=['to_record', 'sequence_order', 'metadata'])

        # Any additional live edges would make the curriculum ambiguous.
        Relationship.objects.filter(
            from_record=child, relationship_type='part_of', deleted_at__isnull=True
        ).exclude(pk=edge.pk).soft_delete()

    # ── 5. progress carry-over ───────────────────────────────────────────────

    def _carry_over_progress(self, programme):
        enrolments = list(Activity.objects.filter(
            activity_type='programme',
            linked_record=programme,
            deleted_at__isnull=True,
        ).select_related('assigned_to'))

        if not enrolments:
            self.stdout.write('\n  Progress: no existing enrolments.')
            return

        self.stdout.write(f'\n  Progress ({len(enrolments)} enrolment(s))')

        for enrolment in enrolments:
            learner = enrolment.assigned_to
            if learner is None:
                continue

            # The old task Activities point at the four skeleton lessons, which
            # are now courses. Clear them and rebuild against the real steps.
            Activity.objects.filter(
                parent_activity__parent_activity=enrolment,
                deleted_at__isnull=True,
            ).soft_delete()
            Activity.objects.filter(
                parent_activity=enrolment, deleted_at__isnull=True,
            ).soft_delete()

            engine.sync_enrolment(learner, programme, tenant=enrolment.tenant)

            legacy = {
                p.step_id: p for p in InductionProgress.objects.filter(user=learner)
            }
            if not legacy:
                self.stdout.write(f'    {learner.email}: rebuilt, no prior progress')
                continue

            steps = engine.get_steps(learner, programme)
            by_legacy_id = {
                (s.record.metadata or {}).get(LEGACY_KEY): s for s in steps
            }

            restored = scored = 0
            for step_id, progress in legacy.items():
                step = by_legacy_id.get(str(step_id))
                if step is None or step.activity is None:
                    continue

                if progress.status in ('passed', 'awaiting_steward'):
                    step.activity.status = 'completed'
                    step.activity.progress = 100
                    step.activity.save(update_fields=['status', 'progress', 'updated_at'])
                    restored += 1

                if progress.score is not None:
                    AssessmentAttempt.objects.get_or_create(
                        user=learner,
                        record=step.record,
                        attempt_number=max(progress.attempts, 1),
                        defaults={
                            'score': progress.score,
                            'passed': progress.status in ('passed', 'awaiting_steward'),
                            'responses': {},
                        },
                    )
                    scored += 1

            # Roll up so the (now-fixed) certification signal fires for anyone
            # who had already finished.
            for course_activity in Activity.objects.filter(
                parent_activity=enrolment, deleted_at__isnull=True
            ):
                services._recalculate_progress(course_activity)
            services._recalculate_progress(enrolment)
            enrolment.refresh_from_db()

            self.stdout.write(
                f'    {learner.email}: {restored} step(s) restored, '
                f'{scored} score(s) carried, programme now {enrolment.progress}%'
            )

    # ── 6. assertions ────────────────────────────────────────────────────────

    def _assert_result(self, programme):
        self.stdout.write('\n  Checks')

        expected_steps = InductionStep.objects.filter(is_active=True).count()
        expected_questions = InductionQuestion.objects.count()
        expected_options = InductionAnswer.objects.count()

        courses = engine.ordered_children(programme, ['course'])
        step_records = []
        for course in courses:
            step_records.extend(engine.ordered_children(course, engine.STEP_TYPES))

        problems = []

        if len(courses) != 4:
            problems.append(f'expected 4 module courses, found {len(courses)}')

        if len(step_records) != expected_steps:
            problems.append(
                f'expected {expected_steps} step records, found {len(step_records)}'
            )

        actual_questions = AssessmentQuestion.objects.filter(
            record__in=step_records
        ).count()
        if actual_questions != expected_questions:
            problems.append(
                f'expected {expected_questions} questions, found {actual_questions}'
            )

        actual_options = AssessmentOption.objects.filter(
            question__record__in=step_records
        ).count()
        if actual_options != expected_options:
            problems.append(
                f'expected {expected_options} options, found {actual_options}'
            )

        # Exactly one live parent edge per step, and distinct order within a course.
        for course in courses:
            edges = Relationship.objects.filter(
                to_record=course, relationship_type='part_of', deleted_at__isnull=True
            )
            orders = list(edges.values_list('sequence_order', flat=True))
            if len(orders) != len(set(orders)):
                problems.append(f'duplicate sequence_order within {course.title!r}')

        for record in step_records:
            live_edges = Relationship.objects.filter(
                from_record=record, relationship_type='part_of', deleted_at__isnull=True
            ).count()
            if live_edges != 1:
                problems.append(
                    f'{record.title!r} has {live_edges} live parent edges (expected 1)'
                )

        self.stdout.write(f'    courses:   {len(courses)}')
        self.stdout.write(f'    steps:     {len(step_records)} (expected {expected_steps})')
        self.stdout.write(f'    questions: {actual_questions} (expected {expected_questions})')
        self.stdout.write(f'    options:   {actual_options} (expected {expected_options})')

        if problems:
            raise CommandError(
                'Verification failed:\n' + '\n'.join(f'    - {p}' for p in problems)
            )

        self.stdout.write(self.style.SUCCESS('    all checks passed'))
