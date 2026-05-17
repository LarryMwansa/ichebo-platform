from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from activity.models import Activity, ActivityLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email='actor@example.com', level=1):
    return User.objects.create_user(username=email, email=email, password='testpass123',
                                    competence_level=level)


def _make_activity(user, title='Morning Prayer', activity_type='task', status='pending'):
    return Activity.objects.create(
        created_by=user,
        assigned_to=user,
        activity_type=activity_type,
        title=title,
        status=status,
    )


# ---------------------------------------------------------------------------
# Activity model tests
# ---------------------------------------------------------------------------

class ActivityModelTests(TestCase):
    def setUp(self):
        self.user = _make_user()

    def test_creation_defaults(self):
        activity = _make_activity(self.user)
        self.assertEqual(activity.status, 'pending')
        self.assertEqual(activity.progress, 0)
        self.assertIsNone(activity.due_at)
        self.assertIsNone(activity.deleted_at)
        self.assertEqual(activity.recurrence, 'none')
        self.assertEqual(activity.metadata, {})

    def test_uuid_primary_key(self):
        activity = _make_activity(self.user)
        self.assertEqual(len(str(activity.id)), 36)

    def test_str_includes_type_and_title(self):
        activity = _make_activity(self.user, activity_type='habit', title='Daily Bible')
        self.assertIn('habit', str(activity))
        self.assertIn('Daily Bible', str(activity))

    def test_soft_delete(self):
        activity = _make_activity(self.user)
        activity.deleted_at = timezone.now()
        activity.save(update_fields=['deleted_at'])
        self.assertTrue(Activity.objects.filter(id=activity.id).exists())
        self.assertFalse(Activity.objects.filter(id=activity.id, deleted_at__isnull=True).exists())

    def test_status_transition_to_completed(self):
        activity = _make_activity(self.user)
        activity.status = 'completed'
        activity.save(update_fields=['status'])
        activity.refresh_from_db()
        self.assertEqual(activity.status, 'completed')

    def test_progress_can_be_set(self):
        activity = _make_activity(self.user)
        activity.progress = 75
        activity.save(update_fields=['progress'])
        activity.refresh_from_db()
        self.assertEqual(activity.progress, 75)

    def test_due_at_can_be_set(self):
        due = timezone.now() + timezone.timedelta(days=1)
        activity = _make_activity(self.user)
        activity.due_at = due
        activity.save(update_fields=['due_at'])
        activity.refresh_from_db()
        self.assertIsNotNone(activity.due_at)

    def test_recurrence_daily(self):
        activity = Activity.objects.create(
            created_by=self.user,
            activity_type='habit',
            title='Daily habit',
            recurrence='daily',
        )
        self.assertEqual(activity.recurrence, 'daily')

    def test_kgs_pathway_stored(self):
        activity = Activity.objects.create(
            created_by=self.user,
            activity_type='goal',
            title='Formation goal',
            kgs_pathway='spiritual_formation',
        )
        activity.refresh_from_db()
        self.assertEqual(activity.kgs_pathway, 'spiritual_formation')

    def test_activity_types(self):
        for atype in ('task', 'habit', 'goal', 'event', 'programme', 'reminder'):
            a = _make_activity(self.user, activity_type=atype, title=f'{atype} title')
            self.assertEqual(a.activity_type, atype)


# ---------------------------------------------------------------------------
# ActivityLog tests
# ---------------------------------------------------------------------------

class ActivityLogTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.activity = _make_activity(self.user)

    def test_log_creation(self):
        log = ActivityLog.objects.create(
            activity=self.activity,
            created_by=self.user,
            event_type='status_changed',
            previous_value='pending',
            new_value='completed',
        )
        self.assertEqual(log.event_type, 'status_changed')
        self.assertEqual(log.previous_value, 'pending')
        self.assertEqual(log.new_value, 'completed')
        self.assertEqual(log.activity, self.activity)

    def test_multiple_logs_per_activity(self):
        # Activity creation auto-generates a 'created' log via activity/signals.py.
        # Count that baseline, then verify each manual log increments it.
        baseline = self.activity.logs.count()
        ActivityLog.objects.create(activity=self.activity, created_by=self.user,
                                   event_type='status_changed', new_value='in_progress')
        ActivityLog.objects.create(activity=self.activity, created_by=self.user,
                                   event_type='status_changed', new_value='completed')
        self.assertEqual(self.activity.logs.count(), baseline + 2)

    def test_log_uuid_primary_key(self):
        log = ActivityLog.objects.create(
            activity=self.activity, created_by=self.user, event_type='note_added',
        )
        self.assertEqual(len(str(log.id)), 36)

    def test_log_reverse_relation(self):
        ActivityLog.objects.create(
            activity=self.activity, created_by=self.user,
            event_type='status_changed', new_value='completed',
        )
        self.assertTrue(self.activity.logs.filter(event_type='status_changed').exists())


# ---------------------------------------------------------------------------
# Programme activity (learn integration pattern)
# ---------------------------------------------------------------------------

class ProgrammeActivityTests(TestCase):
    def setUp(self):
        self.user = _make_user()

    def test_programme_activity_created_with_metadata(self):
        from records.models import Record
        prog = Record.objects.create(
            created_by=self.user,
            record_class='organizational',
            record_family='learning',
            record_type='programme',
            title='Formation Programme',
            status='active',
            origin='user',
        )
        activity = Activity.objects.create(
            created_by=self.user,
            assigned_to=self.user,
            activity_type='programme',
            title='Formation Programme',
            status='pending',
            metadata={
                'source_app': 'learn',
                'programme_record_id': str(prog.id),
            },
        )
        activity.refresh_from_db()
        self.assertEqual(activity.metadata['source_app'], 'learn')
        self.assertEqual(activity.metadata['programme_record_id'], str(prog.id))
        self.assertEqual(activity.activity_type, 'programme')
