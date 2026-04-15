from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from activity.models import Activity, ActivityLog
from paraclete.service import build_digest, ParacleteDigest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email='paraclete@example.com', level=0):
    return User.objects.create_user(username=email, email=email, password='testpass123',
                                    competence_level=level)


# ---------------------------------------------------------------------------
# Digest shape tests
# ---------------------------------------------------------------------------

class DigestShapeTests(TestCase):
    """Verify build_digest() returns the correct ParacleteDigest structure."""

    def test_returns_paraclete_digest_instance(self):
        user = _make_user(level=0)
        digest = build_digest(user)
        self.assertIsInstance(digest, ParacleteDigest)

    def test_digest_user_id_matches(self):
        user = _make_user(level=1)
        digest = build_digest(user)
        self.assertEqual(digest.user_id, str(user.id))

    def test_digest_competence_level_matches(self):
        for level in (0, 1, 3):
            user = _make_user(email=f'level{level}@example.com', level=level)
            digest = build_digest(user)
            self.assertEqual(digest.competence_level, level)

    def test_digest_has_generated_at(self):
        user = _make_user()
        digest = build_digest(user)
        self.assertIsNotNone(digest.generated_at)
        self.assertTrue(digest.generated_at.startswith(str(timezone.now().year)))

    def test_digest_has_discipline_prompt(self):
        user = _make_user()
        digest = build_digest(user)
        # Falls back to 'Press into the Lord today.' when no prompts exist
        self.assertIsInstance(digest.discipline_prompt, str)
        self.assertTrue(len(digest.discipline_prompt) > 0)


# ---------------------------------------------------------------------------
# Level 0 (seeker) digest
# ---------------------------------------------------------------------------

class Level0DigestTests(TestCase):
    def setUp(self):
        self.user = _make_user(email='seeker@example.com', level=0)

    def test_level0_returns_early_with_only_prompt(self):
        digest = build_digest(self.user)
        self.assertEqual(digest.competence_level, 0)
        self.assertEqual(digest.pending_count, 0)
        self.assertEqual(digest.overdue_count, 0)
        self.assertEqual(digest.due_today, [])
        self.assertEqual(digest.overdue_items, [])
        self.assertEqual(digest.active_enrolments, [])
        self.assertIsNone(digest.next_lesson)
        self.assertIsNone(digest.dar_today)
        self.assertIsNone(digest.team_pending_count)


# ---------------------------------------------------------------------------
# Level 1 digest — activity surface
# ---------------------------------------------------------------------------

class Level1DigestTests(TestCase):
    def setUp(self):
        self.user = _make_user(email='level1@example.com', level=1)

    def test_pending_count_zero_with_no_activities(self):
        digest = build_digest(self.user)
        self.assertEqual(digest.pending_count, 0)
        self.assertEqual(digest.overdue_count, 0)

    def test_pending_count_includes_personal_tasks(self):
        Activity.objects.create(
            created_by=self.user,
            assigned_to=self.user,
            activity_type='task',
            title='Personal task',
            status='pending',
        )
        digest = build_digest(self.user)
        self.assertEqual(digest.pending_count, 1)

    def test_overdue_count_for_past_due_activities(self):
        Activity.objects.create(
            created_by=self.user,
            assigned_to=self.user,
            activity_type='task',
            title='Overdue task',
            status='pending',
            due_at=timezone.now() - timezone.timedelta(days=1),
        )
        digest = build_digest(self.user)
        self.assertEqual(digest.overdue_count, 1)
        self.assertEqual(len(digest.overdue_items), 1)
        self.assertEqual(digest.overdue_items[0].title, 'Overdue task')

    def test_completed_activities_not_in_pending_count(self):
        Activity.objects.create(
            created_by=self.user,
            activity_type='task',
            title='Done task',
            status='completed',
        )
        digest = build_digest(self.user)
        self.assertEqual(digest.pending_count, 0)

    def test_due_today_list(self):
        today_noon = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
        Activity.objects.create(
            created_by=self.user,
            assigned_to=self.user,
            activity_type='task',
            title='Today task',
            status='pending',
            due_at=today_noon,
        )
        digest = build_digest(self.user)
        titles = [item.title for item in digest.due_today]
        self.assertIn('Today task', titles)

    def test_no_team_counts_for_level1(self):
        digest = build_digest(self.user)
        self.assertIsNone(digest.team_pending_count)
        self.assertIsNone(digest.team_overdue_count)

    def test_active_enrolments_empty_with_no_programmes(self):
        digest = build_digest(self.user)
        self.assertEqual(digest.active_enrolments, [])

    def test_reminder_in_pending_reminders(self):
        upcoming = timezone.now() + timezone.timedelta(hours=2)
        Activity.objects.create(
            created_by=self.user,
            activity_type='reminder',
            title='Check in with mentor',
            status='pending',
            due_at=upcoming,
        )
        digest = build_digest(self.user)
        reminder_titles = [r.title for r in digest.pending_reminders]
        self.assertIn('Check in with mentor', reminder_titles)


# ---------------------------------------------------------------------------
# Level 3+ digest — team counts
# ---------------------------------------------------------------------------

class Level3DigestTests(TestCase):
    def setUp(self):
        self.user = _make_user(email='steward@example.com', level=3)
        from tenants.models import Tenant, UserPermission
        self.tenant = Tenant.objects.create(
            created_by=self.user, name='Branch', slug='branch',
            path='/branch/', tier='church_node',
        )
        UserPermission.objects.create(
            tenant=self.tenant, user=self.user, created_by=self.user,
            tenant_path=self.tenant.path, role='branch-steward', level=3,
        )

    def test_team_counts_populated_for_level3(self):
        # Create a team activity in the tenant
        Activity.objects.create(
            created_by=self.user,
            tenant=self.tenant,
            activity_type='task',
            title='Team task',
            status='pending',
        )
        digest = build_digest(self.user)
        self.assertIsNotNone(digest.team_pending_count)
        self.assertGreaterEqual(digest.team_pending_count, 1)

    def test_team_overdue_count(self):
        Activity.objects.create(
            created_by=self.user,
            tenant=self.tenant,
            activity_type='task',
            title='Overdue team task',
            status='pending',
            due_at=timezone.now() - timezone.timedelta(days=2),
        )
        digest = build_digest(self.user)
        self.assertIsNotNone(digest.team_overdue_count)
        self.assertGreaterEqual(digest.team_overdue_count, 1)


# ---------------------------------------------------------------------------
# DAR (Daily Activity Report) lookup
# ---------------------------------------------------------------------------

class DARTests(TestCase):
    def setUp(self):
        self.user = _make_user(email='dar@example.com', level=1)

    def test_dar_today_none_when_no_record_written(self):
        digest = build_digest(self.user)
        self.assertIsNone(digest.dar_today)

    def test_dar_today_returned_when_record_exists(self):
        from records.models import Record
        Record.objects.create(
            created_by=self.user,
            record_class='personal',
            record_family='journal',
            record_type='note',
            title='DAR - Today',
            status='active',
            origin='user',
            metadata={'dar': True},
        )
        digest = build_digest(self.user)
        self.assertIsNotNone(digest.dar_today)
        self.assertEqual(digest.dar_today.title, 'DAR - Today')
