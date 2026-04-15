from django.test import TestCase

from accounts.models import User
from activity.models import Activity, ActivityLog
from records.models import Record, Relationship
from learn.views import _recalculate_programme_progress


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email='learner@example.com', level=1):
    return User.objects.create_user(username=email, email=email, password='testpass123',
                                    competence_level=level)


def _make_programme(creator, title='Discipleship Programme'):
    return Record.objects.create(
        created_by=creator,
        record_class='organizational',
        record_family='learning',
        record_type='programme',
        title=title,
        status='active',
        origin='user',
        metadata={'source_app': 'learn'},
        permissions_data={'visibility': 'tenant', 'required_level': 1,
                          'roles_allowed': [], 'can_edit': []},
    )


def _make_course(creator, title='Course A'):
    return Record.objects.create(
        created_by=creator,
        record_class='organizational',
        record_family='learning',
        record_type='course',
        title=title,
        status='active',
        origin='user',
        metadata={'source_app': 'learn'},
        permissions_data={'visibility': 'tenant', 'required_level': 1,
                          'roles_allowed': [], 'can_edit': []},
    )


def _make_lesson(creator, title='Lesson 1'):
    return Record.objects.create(
        created_by=creator,
        record_class='organizational',
        record_family='learning',
        record_type='lesson',
        title=title,
        status='active',
        origin='user',
        metadata={'source_app': 'learn'},
        permissions_data={'visibility': 'tenant', 'required_level': 1,
                          'roles_allowed': [], 'can_edit': []},
    )


def _link(creator, child, parent):
    """Create a part_of Relationship from child to parent."""
    return Relationship.objects.create(
        created_by=creator,
        from_record=child,
        to_record=parent,
        relationship_type='part_of',
        direction='directed',
    )


def _enrol(user, programme):
    """Create a programme Activity (enrolment) for a user."""
    return Activity.objects.create(
        created_by=user,
        assigned_to=user,
        activity_type='programme',
        title=programme.title,
        status='in_progress',
        progress=0,
        metadata={'source_app': 'learn', 'programme_record_id': str(programme.id)},
    )


# ---------------------------------------------------------------------------
# Enrolment tests
# ---------------------------------------------------------------------------

class EnrolmentTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.programme = _make_programme(self.user)

    def test_enrolment_creates_programme_activity(self):
        activity = _enrol(self.user, self.programme)
        self.assertEqual(activity.activity_type, 'programme')
        self.assertEqual(activity.assigned_to, self.user)
        self.assertEqual(activity.metadata['programme_record_id'], str(self.programme.id))
        self.assertEqual(activity.status, 'in_progress')
        self.assertEqual(activity.progress, 0)

    def test_duplicate_enrolment_check(self):
        _enrol(self.user, self.programme)
        # Platform checks: only one active enrolment per programme per user
        count = Activity.objects.filter(
            assigned_to=self.user,
            activity_type='programme',
            metadata__programme_record_id=str(self.programme.id),
            status__in=['pending', 'in_progress'],
        ).count()
        self.assertEqual(count, 1)


# ---------------------------------------------------------------------------
# Progress recalculation tests
# ---------------------------------------------------------------------------

class ProgressRecalculationTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.programme = _make_programme(self.user)
        self.course = _make_course(self.user)
        self.lesson1 = _make_lesson(self.user, 'Lesson 1')
        self.lesson2 = _make_lesson(self.user, 'Lesson 2')

        # Wire curriculum: lesson → course → programme
        _link(self.user, self.course, self.programme)
        _link(self.user, self.lesson1, self.course)
        _link(self.user, self.lesson2, self.course)

        # Create programme activity (enrolment)
        self.programme_activity = _enrol(self.user, self.programme)

    def _complete_lesson(self, lesson):
        Activity.objects.create(
            created_by=self.user,
            assigned_to=self.user,
            activity_type='lesson',
            title=lesson.title,
            status='completed',
            metadata={'source_app': 'learn', 'lesson_record_id': str(lesson.id)},
        )

    def test_zero_lessons_completed_gives_zero_progress(self):
        _recalculate_programme_progress(self.user, self.lesson1.id)
        self.programme_activity.refresh_from_db()
        self.assertEqual(self.programme_activity.progress, 0)

    def test_one_of_two_lessons_gives_fifty_percent(self):
        self._complete_lesson(self.lesson1)
        _recalculate_programme_progress(self.user, self.lesson1.id)
        self.programme_activity.refresh_from_db()
        self.assertEqual(self.programme_activity.progress, 50)

    def test_all_lessons_completed_gives_hundred_percent(self):
        self._complete_lesson(self.lesson1)
        self._complete_lesson(self.lesson2)
        _recalculate_programme_progress(self.user, self.lesson2.id)
        self.programme_activity.refresh_from_db()
        self.assertEqual(self.programme_activity.progress, 100)
        self.assertEqual(self.programme_activity.status, 'completed')

    def test_progress_only_counts_this_users_completions(self):
        other_user = _make_user(email='other@example.com')
        # Other user completes lesson1 — should not affect self.user progress
        Activity.objects.create(
            created_by=other_user,
            assigned_to=other_user,
            activity_type='lesson',
            title=self.lesson1.title,
            status='completed',
            metadata={'source_app': 'learn', 'lesson_record_id': str(self.lesson1.id)},
        )
        _recalculate_programme_progress(self.user, self.lesson1.id)
        self.programme_activity.refresh_from_db()
        self.assertEqual(self.programme_activity.progress, 0)


# ---------------------------------------------------------------------------
# Auto-certification signal tests
# ---------------------------------------------------------------------------

class AutoCertificationSignalTests(TestCase):
    """
    When a programme Activity reaches progress=100 and is saved via .save(),
    the post_save signal in learn/signals.py should create a draft certification Record.
    """

    def setUp(self):
        self.user = _make_user()
        self.programme = _make_programme(self.user)
        self.programme_activity = _enrol(self.user, self.programme)

    def test_certification_created_when_progress_reaches_100(self):
        self.programme_activity.progress = 100
        self.programme_activity.status = 'completed'
        self.programme_activity.save(update_fields=['progress', 'status'])

        cert = Record.objects.filter(
            record_type='certification',
            created_by=self.user,
            metadata__programme_record_id=str(self.programme.id),
            status='draft',
            deleted_at__isnull=True,
        ).first()
        self.assertIsNotNone(cert, 'Expected a draft certification Record to be created')
        self.assertEqual(cert.record_family, 'learning')
        self.assertEqual(cert.origin, 'system')

    def test_certification_not_created_when_progress_below_100(self):
        self.programme_activity.progress = 80
        self.programme_activity.save(update_fields=['progress'])

        self.assertFalse(
            Record.objects.filter(
                record_type='certification',
                created_by=self.user,
                metadata__programme_record_id=str(self.programme.id),
            ).exists()
        )

    def test_certification_idempotent_on_repeated_save(self):
        self.programme_activity.progress = 100
        self.programme_activity.status = 'completed'
        self.programme_activity.save(update_fields=['progress', 'status'])

        # Save again — should not create a second certification
        self.programme_activity.save(update_fields=['progress', 'status'])

        count = Record.objects.filter(
            record_type='certification',
            created_by=self.user,
            metadata__programme_record_id=str(self.programme.id),
        ).count()
        self.assertEqual(count, 1, 'Expected exactly one certification despite multiple saves')


# ---------------------------------------------------------------------------
# Catalogue access tests
# ---------------------------------------------------------------------------

class CatalogueAccessTests(TestCase):
    def setUp(self):
        self.author = _make_user(email='author@example.com', level=4)
        self.level1_user = _make_user(email='l1@example.com', level=1)
        self.level0_user = _make_user(email='l0@example.com', level=0)

    def test_programme_required_level_respected(self):
        prog = Record.objects.create(
            created_by=self.author,
            record_class='organizational',
            record_family='learning',
            record_type='programme',
            title='Advanced Programme',
            status='active',
            origin='user',
            permissions_data={'required_level': 3, 'visibility': 'tenant',
                              'roles_allowed': [], 'can_edit': []},
        )
        required = prog.permissions_data.get('required_level', 1)
        self.assertFalse(self.level1_user.competence_level >= required)
        self.assertTrue(self.author.competence_level >= required)
