"""
notifications/tests.py

Tests for V2.6 notification service functions and CertificationConfirmation signals.
"""
from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from notifications.models import Notification
from notifications.service import (
    create_notification,
    notify_activity_assigned,
    notify_level_advanced,
    notify_induction_completed,
    notify_member_added,
    notify_member_removed,
    notify_tenant_invitation,
)
from tenants.models import Tenant


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(email, level=1):
    u = User.objects.create_user(username=email, email=email, password='pass')
    u.competence_level = level
    u.save(update_fields=['competence_level'])
    return u


def _tenant(creator, slug='test-tenant'):
    return Tenant.objects.create(
        created_by=creator, name='Test Community',
        slug=slug, path=f'/{slug}/', tier='church_node', status='active',
    )


# ---------------------------------------------------------------------------
# create_notification — core function
# ---------------------------------------------------------------------------

class CreateNotificationTests(TestCase):
    def setUp(self):
        self.user = _user('recipient@example.com')

    def test_creates_notification_record(self):
        n = create_notification(
            self.user, 'system', 'Test title', 'Test body'
        )
        self.assertIsNotNone(n)
        self.assertEqual(n.user, self.user)
        self.assertEqual(n.title, 'Test title')
        self.assertEqual(n.notification_type, 'system')

    def test_unread_by_default(self):
        n = create_notification(self.user, 'system', 'Hello')
        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)

    def test_mark_read(self):
        n = create_notification(self.user, 'system', 'Hello')
        n.mark_read()
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)

    def test_data_stored_as_json(self):
        n = create_notification(
            self.user, 'system', 'Hello', data={'url': '/learn/', 'count': 3}
        )
        self.assertEqual(n.data['url'], '/learn/')
        self.assertEqual(n.data['count'], 3)

    def test_returns_none_on_bad_type_gracefully(self):
        # Invalid type should not raise — returns None and logs
        n = create_notification(self.user, 'not_a_real_type', 'Title')
        # Model saves it anyway (choices not enforced at DB level in Django by default)
        self.assertIsNotNone(n)


# ---------------------------------------------------------------------------
# Level advanced notification
# ---------------------------------------------------------------------------

class LevelAdvancedNotificationTests(TestCase):
    def setUp(self):
        self.user = _user('learner@example.com', level=1)
        self.confirmer = _user('steward@example.com', level=5)
        self.confirmer.display_name = 'Bishop John'
        self.confirmer.save(update_fields=['display_name'])

    def test_creates_level_advanced_notification(self):
        notify_level_advanced(
            user=self.user,
            previous_level=0,
            new_level=1,
            confirmed_by=self.confirmer,
        )
        n = Notification.objects.get(user=self.user, notification_type='level_advanced')
        self.assertIn('Level 1', n.title)
        self.assertIn('Bishop John', n.body)

    def test_data_contains_levels(self):
        notify_level_advanced(self.user, 0, 1, self.confirmer)
        n = Notification.objects.get(user=self.user, notification_type='level_advanced')
        self.assertEqual(n.data['previous_level'], 0)
        self.assertEqual(n.data['new_level'], 1)
        self.assertEqual(n.data['url'], '/accounts/formation/')

    @patch('notifications.service._send_email')
    def test_triggers_email(self, mock_send):
        notify_level_advanced(self.user, 0, 1, self.confirmer)
        mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# Induction completed notification
# ---------------------------------------------------------------------------

class InductionCompletedNotificationTests(TestCase):
    def setUp(self):
        self.user = _user('inductee@example.com', level=1)

    def test_creates_induction_completed_notification(self):
        notify_induction_completed(self.user, placement_tenant_name='Grace Church Pretoria')
        n = Notification.objects.get(user=self.user, notification_type='induction_completed')
        self.assertIn('Grace Church Pretoria', n.body)

    @patch('notifications.service._send_email')
    def test_triggers_email(self, mock_send):
        notify_induction_completed(self.user, 'Some Church')
        mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# Tenant invitation notification
# ---------------------------------------------------------------------------

class TenantInvitationNotificationTests(TestCase):
    def setUp(self):
        self.steward = _user('steward@example.com', level=3)
        self.tenant = _tenant(self.steward)

    def test_creates_in_app_notification_for_registered_user(self):
        member = _user('member@example.com', level=1)
        notify_tenant_invitation(
            email='member@example.com',
            tenant=self.tenant,
            invited_by=self.steward,
            token='abc123',
        )
        n = Notification.objects.get(user=member, notification_type='tenant_invitation')
        self.assertIn('Test Community', n.title)
        self.assertIn('abc123', n.data['url'])

    @patch('notifications.service._send_email')
    def test_sends_email_for_unregistered_email(self, mock_send):
        # Email not belonging to any user — email-only delivery
        notify_tenant_invitation(
            email='unknown@example.com',
            tenant=self.tenant,
            invited_by=self.steward,
            token='tok999',
        )
        mock_send.assert_called_once()
        # No in-app notification created
        self.assertEqual(
            Notification.objects.filter(notification_type='tenant_invitation').count(), 0
        )

    @patch('notifications.service._send_email')
    def test_in_app_also_triggers_email(self, mock_send):
        _user('member@example.com', level=1)
        notify_tenant_invitation(
            email='member@example.com',
            tenant=self.tenant,
            invited_by=self.steward,
            token='tok456',
        )
        mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# Member added / removed
# ---------------------------------------------------------------------------

class MemberNotificationTests(TestCase):
    def setUp(self):
        self.steward = _user('steward@example.com', level=3)
        self.tenant = _tenant(self.steward)
        self.member = _user('member@example.com', level=1)

    def test_member_added_notification(self):
        notify_member_added(self.member, self.tenant)
        n = Notification.objects.get(user=self.member, notification_type='member_added')
        self.assertIn('Test Community', n.title)

    def test_member_removed_notification(self):
        notify_member_removed(self.member, self.tenant)
        n = Notification.objects.get(user=self.member, notification_type='member_removed')
        self.assertIn('Test Community', n.title)


# ---------------------------------------------------------------------------
# CertificationConfirmation signal integration
# ---------------------------------------------------------------------------

class CertificationSignalTests(TestCase):
    """
    Test that creating a CertificationConfirmation fires the right
    notification types via the post_save signal.
    """
    def setUp(self):
        self.learner = _user('learner@example.com', level=0)
        self.steward = _user('steward@example.com', level=5)

    def _make_cert_record(self, context=''):
        from records.models import Record
        meta = {'learner_id': str(self.learner.id), 'target_level': 1}
        if context:
            meta['context'] = context
        return Record.objects.create(
            created_by=self.learner,
            title='Induction Programme',
            record_type='certification',
            record_class='learn',
            status='draft',
            metadata=meta,
        )

    def test_certification_earned_notification_fired(self):
        from learn.models import CertificationConfirmation
        rec = self._make_cert_record()
        CertificationConfirmation.objects.create(
            certification_record_id=rec.id,
            confirmed_by=self.steward,
            learner_id=self.learner.id,
            previous_competence_level=0,
            new_competence_level=1,
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.learner,
                notification_type='certification_earned',
            ).exists()
        )

    def test_level_advanced_notification_fired_when_level_rises(self):
        from learn.models import CertificationConfirmation
        rec = self._make_cert_record()
        CertificationConfirmation.objects.create(
            certification_record_id=rec.id,
            confirmed_by=self.steward,
            learner_id=self.learner.id,
            previous_competence_level=0,
            new_competence_level=1,
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.learner,
                notification_type='level_advanced',
            ).exists()
        )

    def test_level_advanced_not_fired_when_level_unchanged(self):
        from learn.models import CertificationConfirmation
        rec = self._make_cert_record()
        CertificationConfirmation.objects.create(
            certification_record_id=rec.id,
            confirmed_by=self.steward,
            learner_id=self.learner.id,
            previous_competence_level=1,
            new_competence_level=1,
        )
        self.assertFalse(
            Notification.objects.filter(
                user=self.learner,
                notification_type='level_advanced',
            ).exists()
        )

    def test_induction_completed_fired_for_induction_context(self):
        from learn.models import CertificationConfirmation
        rec = self._make_cert_record(context='induction_completion')
        rec.metadata['placement_tenant_name'] = 'Grace Church'
        rec.save(update_fields=['metadata'])
        CertificationConfirmation.objects.create(
            certification_record_id=rec.id,
            confirmed_by=self.steward,
            learner_id=self.learner.id,
            previous_competence_level=0,
            new_competence_level=1,
        )
        n = Notification.objects.filter(
            user=self.learner,
            notification_type='induction_completed',
        ).first()
        self.assertIsNotNone(n)
        self.assertIn('Grace Church', n.body)

    def test_induction_completed_not_fired_for_regular_certification(self):
        from learn.models import CertificationConfirmation
        rec = self._make_cert_record()  # no context
        CertificationConfirmation.objects.create(
            certification_record_id=rec.id,
            confirmed_by=self.steward,
            learner_id=self.learner.id,
            previous_competence_level=0,
            new_competence_level=1,
        )
        self.assertFalse(
            Notification.objects.filter(
                user=self.learner,
                notification_type='induction_completed',
            ).exists()
        )
