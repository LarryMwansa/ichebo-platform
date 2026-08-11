"""
Tests for the curriculum engine.

These lock down behaviour that four separate live bugs turned out to depend
on — see the docstrings. Each of those bugs was silent: nothing raised, the
learner simply never advanced.
"""
import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase

from activity.models import Activity
from records.models import Record, Relationship
from tenants.models import Tenant, UserPermission

from learn import engine, services
from learn.models import AssessmentAttempt, AssessmentOption, AssessmentQuestion

User = get_user_model()


class CurriculumMixin:
    """Builds a small forked programme:

        Programme (engine on, sequential, pass 70, forks on induction_pathway)
          Module 1
            L1  (all)
            Q1  (all, 2 questions)
          Module 2
            L2a (beginners)
            L2b (reconditioning)
            FINAL (all, is_final_assessment)
    """

    def build_curriculum(self):
        self.author = User.objects.create_user(
            username='author', email='author@test.local', password='p')
        self.author.competence_level = 5
        self.author.save()

        self.programme = Record.objects.create(
            created_by=self.author, record_class='organizational',
            record_family='learning', record_type='induction', origin='system',
            title='Test Induction', status='active',
            custom_fields={'engine': {
                'enabled': True, 'sequential_unlock': True, 'pass_score': 70,
                'max_attempts': 0, 'pathway_attr': 'induction_pathway',
            }},
            permissions_data={'required_level': 0, 'visibility': 'global'},
        )

        self.m1 = self._course('Module 1', 1)
        self.m2 = self._course('Module 2', 2)

        self.l1 = self._step(self.m1, 'Lesson 1', 'lesson', 1)
        self.q1 = self._step(self.m1, 'Quiz 1', 'quiz', 2)
        self.l2a = self._step(self.m2, 'Beginners Lesson', 'lesson', 1, pathway='beginners')
        self.l2b = self._step(self.m2, 'Reconditioning Lesson', 'lesson', 1, pathway='reconditioning')
        self.final = self._step(self.m2, 'Final Test', 'quiz', 2, final=True)

        self._questions(self.q1, count=2)
        self._questions(self.final, count=2)

    def _course(self, title, order):
        course = Record.objects.create(
            created_by=self.author, record_class='organizational',
            record_family='learning', record_type='course', origin='system',
            title=title, status='active',
        )
        Relationship.objects.create(
            created_by=self.author, from_record=course, to_record=self.programme,
            direction='directed', relationship_type='part_of', sequence_order=order,
        )
        return course

    def _step(self, course, title, record_type, order, pathway=None, final=False):
        custom = {
            'assessment_kind': 'final_test' if final else record_type,
            'pass_score': 70,
        }
        if final:
            custom['is_final_assessment'] = True
        step = Record.objects.create(
            created_by=self.author, record_class='organizational',
            record_family='learning', record_type=record_type, origin='system',
            title=title, status='active', custom_fields=custom,
        )
        Relationship.objects.create(
            created_by=self.author, from_record=step, to_record=course,
            direction='directed', relationship_type='part_of', sequence_order=order,
            metadata={'pathway': pathway} if pathway else {},
        )
        return step

    def _questions(self, record, count):
        for i in range(count):
            q = AssessmentQuestion.objects.create(
                record=record, question_text=f'Q{i}', order=i)
            AssessmentOption.objects.create(
                question=q, answer_text='right', is_correct=True, order=0)
            AssessmentOption.objects.create(
                question=q, answer_text='wrong', is_correct=False, order=1)

    def learner(self, pathway='beginners', level=0, name='learner'):
        user = User.objects.create_user(
            username=name, email=f'{name}@test.local', password='p')
        user.competence_level = level
        user.induction_pathway = pathway
        user.save()
        return user

    def answers(self, record, correct=True):
        return [
            str(o.id)
            for q in AssessmentQuestion.objects.filter(record=record).prefetch_related('options')
            for o in q.options.all() if o.is_correct is correct
        ]


class OrderingTests(CurriculumMixin, TestCase):
    def setUp(self):
        self.build_curriculum()

    def test_steps_follow_sequence_order_not_creation_order(self):
        steps = engine.get_steps(self.learner(), self.programme)
        self.assertEqual([s.title for s in steps],
                         ['Lesson 1', 'Quiz 1', 'Beginners Lesson', 'Final Test'])

    def test_reordering_the_edge_reorders_the_curriculum(self):
        edge = Relationship.objects.get(from_record=self.q1)
        edge.sequence_order = 0
        edge.save(update_fields=['sequence_order'])

        steps = engine.get_steps(self.learner(), self.programme)
        self.assertEqual([s.title for s in steps[:2]], ['Quiz 1', 'Lesson 1'])


class PathwayTests(CurriculumMixin, TestCase):
    def setUp(self):
        self.build_curriculum()

    def test_each_pathway_sees_only_its_own_branch(self):
        beginner = [s.title for s in engine.get_steps(
            self.learner('beginners', name='b'), self.programme)]
        recon = [s.title for s in engine.get_steps(
            self.learner('reconditioning', name='r'), self.programme)]

        self.assertIn('Beginners Lesson', beginner)
        self.assertNotIn('Reconditioning Lesson', beginner)
        self.assertIn('Reconditioning Lesson', recon)
        self.assertNotIn('Beginners Lesson', recon)
        # Shared steps appear on both.
        for shared in ('Lesson 1', 'Quiz 1', 'Final Test'):
            self.assertIn(shared, beginner)
            self.assertIn(shared, recon)

    def test_enrolment_only_creates_tasks_for_the_learners_pathway(self):
        """Bug B4.

        enrol_in_programme used to enrol a forked learner in BOTH branches.
        They could only ever complete their own, so the programme Activity
        stuck below 100%, the certification signal never fired, and nobody
        was ever advanced.
        """
        user = self.learner('beginners')
        services.enrol_in_programme(user, self.programme)

        titles = set(
            Activity.objects
            .filter(assigned_to=user, activity_type='task', deleted_at__isnull=True)
            .values_list('title', flat=True)
        )
        self.assertIn('Beginners Lesson', titles)
        self.assertNotIn('Reconditioning Lesson', titles)


class UnlockTests(CurriculumMixin, TestCase):
    def setUp(self):
        self.build_curriculum()
        self.user = self.learner()
        engine.ensure_enrolled(self.user, self.programme)

    def steps(self):
        return engine.get_steps(self.user, self.programme)

    def test_only_the_first_step_starts_unlocked(self):
        steps = self.steps()
        self.assertTrue(steps[0].unlocked)
        self.assertFalse(any(s.unlocked for s in steps[1:]))

    def test_completing_a_step_unlocks_the_next(self):
        engine.mark_lesson_complete(self.user, self.steps()[0])
        steps = self.steps()
        self.assertEqual(steps[0].status, 'passed')
        self.assertTrue(steps[1].unlocked)
        self.assertFalse(steps[2].unlocked)

    def test_locked_step_cannot_be_completed(self):
        with self.assertRaises(engine.EngineError):
            engine.mark_lesson_complete(self.user, self.steps()[1])

    def test_sequential_unlock_off_unlocks_everything(self):
        custom = dict(self.programme.custom_fields)
        custom['engine'] = {**custom['engine'], 'sequential_unlock': False}
        self.programme.custom_fields = custom
        self.programme.save(update_fields=['custom_fields'])

        self.assertTrue(all(s.unlocked for s in self.steps()))

    def test_step_inserted_mid_curriculum_does_not_strand_existing_learners(self):
        """The drift bug the stored-status model had.

        InductionProgress rows were written once at enrolment and only the
        immediately-following step was ever unlocked, so a step added later
        stayed locked forever for anyone already enrolled. Unlock is derived
        now, so a new step slots in and the chain still resolves.
        """
        engine.mark_lesson_complete(self.user, self.steps()[0])

        inserted = self._step(self.m1, 'Inserted Lesson', 'lesson', 3)
        engine.sync_enrolment(self.user, self.programme)

        steps = self.steps()
        titles = [s.title for s in steps]
        self.assertIn('Inserted Lesson', titles)

        # Everything after the completed step is reachable in turn, and the
        # new one is not silently skipped.
        by_title = {s.title: s for s in steps}
        self.assertTrue(by_title['Quiz 1'].unlocked)
        self.assertIsNotNone(by_title['Inserted Lesson'].activity)


class ScoringTests(CurriculumMixin, TestCase):
    def setUp(self):
        self.build_curriculum()
        self.user = self.learner()
        engine.ensure_enrolled(self.user, self.programme)
        engine.mark_lesson_complete(
            self.user, engine.get_steps(self.user, self.programme)[0])

    def quiz_step(self):
        return engine.get_step(self.user, self.programme, self.q1.id)

    def test_all_wrong_fails_and_records_the_attempt(self):
        result = engine.score_assessment(
            self.user, self.quiz_step(), self.answers(self.q1, correct=False))

        self.assertEqual(result['score'], 0)
        self.assertFalse(result['passed'])
        self.assertEqual(AssessmentAttempt.objects.filter(
            user=self.user, record=self.q1).count(), 1)
        self.assertEqual(self.quiz_step().status, 'in_progress')

    def test_all_correct_passes_and_unlocks_the_next_step(self):
        result = engine.score_assessment(
            self.user, self.quiz_step(), self.answers(self.q1))

        self.assertEqual(result['score'], 100)
        self.assertTrue(result['passed'])
        self.assertEqual(self.quiz_step().status, 'passed')

        steps = engine.get_steps(self.user, self.programme)
        self.assertTrue(steps[2].unlocked)

    def test_half_right_is_below_the_pass_mark(self):
        questions = list(AssessmentQuestion.objects.filter(record=self.q1).order_by('order'))
        chosen = [
            str(questions[0].options.get(is_correct=True).id),
            str(questions[1].options.get(is_correct=False).id),
        ]
        result = engine.score_assessment(self.user, self.quiz_step(), chosen)

        self.assertEqual(result['score'], 50)
        self.assertFalse(result['passed'])

    def test_attempt_numbers_increment(self):
        engine.score_assessment(self.user, self.quiz_step(), self.answers(self.q1, correct=False))
        second = engine.score_assessment(self.user, self.quiz_step(), self.answers(self.q1))
        self.assertEqual(second['attempt'].attempt_number, 2)

    def test_max_attempts_is_enforced_when_set(self):
        custom = dict(self.programme.custom_fields)
        custom['engine'] = {**custom['engine'], 'max_attempts': 1}
        self.programme.custom_fields = custom
        self.programme.save(update_fields=['custom_fields'])

        engine.score_assessment(self.user, self.quiz_step(), self.answers(self.q1, correct=False))
        with self.assertRaises(engine.EngineError):
            engine.score_assessment(self.user, self.quiz_step(), self.answers(self.q1))

    def test_locked_assessment_cannot_be_submitted(self):
        final = engine.get_step(self.user, self.programme, self.final.id)
        with self.assertRaises(engine.EngineError):
            engine.score_assessment(self.user, final, self.answers(self.final))


class CertificationGateTests(CurriculumMixin, TestCase):
    def setUp(self):
        self.build_curriculum()
        self.user = self.learner()
        engine.ensure_enrolled(self.user, self.programme)

        self.steward = User.objects.create_user(
            username='steward', email='steward@test.local', password='p')
        self.steward.competence_level = 3
        self.steward.save()

        self.induction_tenant = Tenant.objects.create(
            name='Induction', slug='induction-t', tier='induction',
            path='/induction-t/', status='active', created_by=self.author)
        self.home = Tenant.objects.create(
            name='Home Community', slug='home-c', tier='branch',
            path='/home-c/', status='active', created_by=self.author)
        UserPermission.objects.get_or_create(
            user=self.user, tenant=self.induction_tenant, role='seeker',
            defaults=dict(created_by=self.steward, granted_by=self.steward,
                          tenant_path=self.induction_tenant.path, level=0, is_active=True))

    def finish_programme(self):
        for _ in range(20):
            steps = engine.get_steps(self.user, self.programme)
            nxt = engine.get_current_step(steps)
            if nxt is None:
                return
            if nxt.is_assessment:
                engine.score_assessment(self.user, nxt, self.answers(nxt.record))
            else:
                engine.mark_lesson_complete(self.user, nxt)

    def test_finishing_creates_exactly_one_draft_certification(self):
        """Bug B1.

        learn/signals.py filtered record_type='programme'. Induction is
        record_type='induction', so the signal hit DoesNotExist and returned
        silently — no inductee ever got a certification, which is why the old
        code wrote competence_level directly instead.
        """
        self.finish_programme()

        certs = Record.objects.filter(
            record_type='certification', created_by=self.user,
            status='draft', deleted_at__isnull=True)
        self.assertEqual(certs.count(), 1)

        metadata = certs.first().metadata
        self.assertEqual(metadata['context'], 'induction_completion')
        # Not the programme's required_level of 0 — that would make
        # confirm_certification_record reject the confirmation.
        self.assertEqual(metadata['target_level'], 1)

    def test_learner_stays_level_0_until_a_steward_confirms(self):
        self.finish_programme()
        self.user.refresh_from_db()
        self.assertEqual(self.user.competence_level, 0)

        final = engine.get_step(self.user, self.programme, self.final.id)
        self.assertEqual(final.status, 'awaiting_steward')

    def test_confirming_without_a_placement_community_is_refused(self):
        """Bug B2.

        Placement deactivated the induction permission unconditionally but
        only created the replacement if a tenant was passed — advancing the
        learner to Level 1 with no community at all.
        """
        self.finish_programme()
        cert = engine.awaiting_confirmation(self.user, self.programme)

        with self.assertRaises(services.CertificationError):
            services.confirm_certification_record(
                cert_record=cert, confirmed_by=self.steward, placement_tenant_id=None)

        self.user.refresh_from_db()
        cert.refresh_from_db()
        self.assertEqual(self.user.competence_level, 0)
        self.assertEqual(cert.status, 'draft')
        self.assertTrue(
            UserPermission.objects.filter(user=self.user, is_active=True).exists())

    def test_confirming_with_a_placement_advances_and_places(self):
        """Bug B3 also lives here.

        Placement built a UserPermission without created_by or tenant_path
        (both NOT NULL) and with role='member', which is not in ROLE_CHOICES,
        so it raised IntegrityError every time — induction placement had
        never once completed.
        """
        self.finish_programme()
        cert = engine.awaiting_confirmation(self.user, self.programme)

        services.confirm_certification_record(
            cert_record=cert, confirmed_by=self.steward,
            placement_tenant_id=self.home.id)

        self.user.refresh_from_db()
        self.assertEqual(self.user.competence_level, 1)
        self.assertIsNotNone(self.user.induction_completed_at)

        active = UserPermission.objects.filter(user=self.user, is_active=True)
        self.assertEqual([p.tenant_id for p in active], [self.home.id])
        self.assertFalse(
            UserPermission.objects.filter(
                user=self.user, tenant=self.induction_tenant, is_active=True).exists())


class CompetenceLevelWriteGuardTests(TestCase):
    """competence_level has exactly one authorised writer.

    The induction code used to set it with a bare .update(), skipping the
    certification record, the audit row and tenant placement. This fails the
    build if another assignment reappears anywhere in learn/ or sceptre/.
    """

    ALLOWED = {'learn/services.py'}

    def test_only_services_assigns_competence_level(self):
        root = Path(__file__).resolve().parent.parent
        pattern = re.compile(r'\.competence_level\s*=(?!=)')
        offenders = []

        for app in ('learn', 'sceptre'):
            for path in (root / app).rglob('*.py'):
                if 'test' in path.name or '/migrations/' in str(path):
                    continue
                relative = str(path.relative_to(root))
                if relative in self.ALLOWED:
                    continue
                for number, line in enumerate(path.read_text().splitlines(), 1):
                    if pattern.search(line) and not line.strip().startswith('#'):
                        offenders.append(f'{relative}:{number}: {line.strip()}')

        self.assertEqual(offenders, [], (
            'competence_level must only be written by '
            'learn.services.confirm_certification_record:\n' + '\n'.join(offenders)
        ))
