"""
tenants/tests_v25.py

Tests for V2.5: TenantInvitation model, send_invitation, accept_invitation,
remove_member service functions, and the Level 1+ formation gate.
"""
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from tenants.models import Tenant, TenantInvitation, UserPermission
from tenants.service import InvitationError, accept_invitation, remove_member, send_invitation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(email, level=1):
    u = User.objects.create_user(username=email, email=email, password='pass')
    u.competence_level = level
    u.save(update_fields=['competence_level'])
    return u


def _tenant(creator, slug='church-a'):
    return Tenant.objects.create(
        created_by=creator,
        name='Church A',
        slug=slug,
        path=f'/{slug}/',
        tier='church_node',
        status='active',
    )


# ---------------------------------------------------------------------------
# TenantInvitation model
# ---------------------------------------------------------------------------

class TenantInvitationModelTests(TestCase):
    def setUp(self):
        self.steward = _user('steward@example.com', level=3)
        self.tenant = _tenant(self.steward)

    def test_token_auto_generated(self):
        inv = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='new@example.com',
            invited_by=self.steward,
        )
        self.assertTrue(len(inv.token) > 20)

    def test_expires_at_set_to_7_days(self):
        inv = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='new@example.com',
            invited_by=self.steward,
        )
        delta = inv.expires_at - inv.created_at
        self.assertAlmostEqual(delta.days, 7, delta=1)

    def test_default_status_is_pending(self):
        inv = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='new@example.com',
            invited_by=self.steward,
        )
        self.assertEqual(inv.status, 'pending')

    def test_is_expired_false_when_fresh(self):
        inv = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='new@example.com',
            invited_by=self.steward,
        )
        self.assertFalse(inv.is_expired)

    def test_is_expired_true_when_past_expiry(self):
        inv = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='new@example.com',
            invited_by=self.steward,
        )
        inv.expires_at = timezone.now() - timezone.timedelta(hours=1)
        inv.save(update_fields=['expires_at'])
        self.assertTrue(inv.is_expired)

    def test_unique_tokens(self):
        inv1 = TenantInvitation.objects.create(tenant=self.tenant, email='a@x.com', invited_by=self.steward)
        inv2 = TenantInvitation.objects.create(tenant=self.tenant, email='b@x.com', invited_by=self.steward)
        self.assertNotEqual(inv1.token, inv2.token)


# ---------------------------------------------------------------------------
# send_invitation service
# ---------------------------------------------------------------------------

class SendInvitationTests(TestCase):
    def setUp(self):
        self.steward = _user('steward@example.com', level=3)
        self.tenant = _tenant(self.steward)

    def test_creates_invitation(self):
        inv = send_invitation(self.tenant, 'member@example.com', self.steward)
        self.assertEqual(inv.status, 'pending')
        self.assertEqual(inv.email, 'member@example.com')
        self.assertEqual(inv.tenant, self.tenant)

    def test_raises_if_already_active_member(self):
        member = _user('member@example.com', level=1)
        UserPermission.objects.create(
            tenant=self.tenant, user=member,
            created_by=self.steward, granted_by=self.steward,
            tenant_path=self.tenant.path, role='disciple', level=1, is_active=True,
        )
        with self.assertRaises(InvitationError):
            send_invitation(self.tenant, 'member@example.com', self.steward)

    def test_raises_if_pending_invitation_exists(self):
        send_invitation(self.tenant, 'member@example.com', self.steward)
        with self.assertRaises(InvitationError):
            send_invitation(self.tenant, 'member@example.com', self.steward)

    def test_allows_new_invitation_after_expired(self):
        inv = send_invitation(self.tenant, 'member@example.com', self.steward)
        inv.expires_at = timezone.now() - timezone.timedelta(hours=1)
        inv.save(update_fields=['expires_at'])
        # Should not raise — old one is expired
        new_inv = send_invitation(self.tenant, 'member@example.com', self.steward)
        self.assertEqual(new_inv.status, 'pending')


# ---------------------------------------------------------------------------
# accept_invitation service — the formation gate
# ---------------------------------------------------------------------------

class AcceptInvitationTests(TestCase):
    def setUp(self):
        self.steward = _user('steward@example.com', level=3)
        self.tenant = _tenant(self.steward)

    def _invite(self, email='member@example.com'):
        return TenantInvitation.objects.create(
            tenant=self.tenant,
            email=email,
            invited_by=self.steward,
        )

    def test_level_1_user_can_accept(self):
        member = _user('member@example.com', level=1)
        inv = self._invite('member@example.com')
        perm = accept_invitation(inv.token, member)
        self.assertIsNotNone(perm)
        self.assertEqual(perm.tenant, self.tenant)
        self.assertEqual(perm.user, member)
        inv.refresh_from_db()
        self.assertEqual(inv.status, 'accepted')

    def test_level_0_user_cannot_accept(self):
        """Formation gate: Level 0 inductees must complete induction first."""
        inductee = _user('inductee@example.com', level=0)
        inv = self._invite('inductee@example.com')
        with self.assertRaises(InvitationError) as ctx:
            accept_invitation(inv.token, inductee)
        self.assertIn('Induction', str(ctx.exception))
        # Invitation remains pending — not consumed
        inv.refresh_from_db()
        self.assertEqual(inv.status, 'pending')

    def test_wrong_user_email_cannot_accept(self):
        """Invitation is non-transferable — only the invited email can accept."""
        other = _user('other@example.com', level=1)
        inv = self._invite('member@example.com')
        with self.assertRaises(InvitationError) as ctx:
            accept_invitation(inv.token, other)
        self.assertIn('member@example.com', str(ctx.exception))

    def test_invalid_token_raises(self):
        member = _user('member@example.com', level=1)
        with self.assertRaises(InvitationError):
            accept_invitation('not-a-real-token', member)

    def test_expired_invitation_raises(self):
        member = _user('member@example.com', level=1)
        inv = self._invite('member@example.com')
        inv.expires_at = timezone.now() - timezone.timedelta(hours=1)
        inv.save(update_fields=['expires_at'])
        with self.assertRaises(InvitationError) as ctx:
            accept_invitation(inv.token, member)
        self.assertIn('expired', str(ctx.exception).lower())

    def test_already_accepted_invitation_raises(self):
        member = _user('member@example.com', level=1)
        inv = self._invite('member@example.com')
        accept_invitation(inv.token, member)
        # Second attempt on same token
        with self.assertRaises(InvitationError):
            accept_invitation(inv.token, member)

    def test_creates_user_permission_on_accept(self):
        member = _user('member@example.com', level=1)
        inv = self._invite('member@example.com')
        accept_invitation(inv.token, member)
        self.assertTrue(
            UserPermission.objects.filter(
                tenant=self.tenant, user=member, is_active=True
            ).exists()
        )

    def test_higher_level_user_can_accept(self):
        steward = _user('senior@example.com', level=4)
        inv = self._invite('senior@example.com')
        perm = accept_invitation(inv.token, steward)
        self.assertEqual(perm.user, steward)


# ---------------------------------------------------------------------------
# remove_member service
# ---------------------------------------------------------------------------

class RemoveMemberTests(TestCase):
    def setUp(self):
        self.steward = _user('steward@example.com', level=3)
        self.tenant = _tenant(self.steward)
        self.member = _user('member@example.com', level=1)
        UserPermission.objects.create(
            tenant=self.tenant, user=self.member,
            created_by=self.steward, granted_by=self.steward,
            tenant_path=self.tenant.path, role='disciple', level=1, is_active=True,
        )

    def test_deactivates_permission(self):
        remove_member(self.tenant, self.member, removed_by=self.steward)
        self.assertFalse(
            UserPermission.objects.filter(
                tenant=self.tenant, user=self.member, is_active=True
            ).exists()
        )

    def test_does_not_delete_record(self):
        remove_member(self.tenant, self.member, removed_by=self.steward)
        self.assertTrue(
            UserPermission.objects.filter(
                tenant=self.tenant, user=self.member
            ).exists()
        )

    def test_raises_if_not_member(self):
        outsider = _user('outsider@example.com', level=1)
        with self.assertRaises(InvitationError):
            remove_member(self.tenant, outsider, removed_by=self.steward)
