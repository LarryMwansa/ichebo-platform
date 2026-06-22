from django.test import TestCase, Client

from accounts.models import User
from notifications.models import Notification
from records.models import Record
from tenants.models import Tenant, UserPermission

from .services import resolve_steward_for_tenant


def _make_user(email, level=1):
    return User.objects.create_user(
        username=email, email=email, password='Tr0ub4dor&3xample!', competence_level=level,
    )


def _make_tenant(slug, created_by):
    return Tenant.objects.create(
        name=f'Tenant {slug}', slug=slug, tier='church_node',
        path=f'/global/{slug}/', status='active', created_by=created_by,
    )


def _grant(tenant, user, role, level, created_by):
    return UserPermission.objects.create(
        tenant=tenant, user=user, created_by=created_by, tenant_path=tenant.path,
        role=role, level=level, is_active=True,
    )


# ---------------------------------------------------------------------------
# Steward routing
# ---------------------------------------------------------------------------

class ResolveStewardForTenantTests(TestCase):

    def test_finds_active_steward_role(self):
        steward = _make_user('steward1@example.com', level=3)
        tenant = _make_tenant('t1', steward)
        _grant(tenant, steward, 'branch-steward', 3, steward)

        self.assertEqual(resolve_steward_for_tenant(tenant).id, steward.id)

    def test_falls_back_to_coordinator_user_when_no_steward_role(self):
        coordinator = _make_user('coord@example.com', level=3)
        tenant = _make_tenant('t2', coordinator)
        tenant.coordinator_user = coordinator
        tenant.save(update_fields=['coordinator_user'])

        self.assertEqual(resolve_steward_for_tenant(tenant).id, coordinator.id)

    def test_returns_none_when_neither_resolves(self):
        someone = _make_user('someone@example.com', level=3)
        tenant = _make_tenant('t3', someone)

        self.assertIsNone(resolve_steward_for_tenant(tenant))

    def test_returns_none_for_null_tenant(self):
        self.assertIsNone(resolve_steward_for_tenant(None))

    def test_ignores_inactive_steward_permission(self):
        steward = _make_user('steward2@example.com', level=3)
        tenant = _make_tenant('t4', steward)
        perm = _grant(tenant, steward, 'branch-steward', 3, steward)
        perm.is_active = False
        perm.save(update_fields=['is_active'])

        self.assertIsNone(resolve_steward_for_tenant(tenant))


# ---------------------------------------------------------------------------
# Support request flow — full HTTP path
# ---------------------------------------------------------------------------

class SupportRequestFlowTests(TestCase):

    def setUp(self):
        self.steward = _make_user('steward@example.com', level=3)
        self.member = _make_user('member@example.com', level=1)
        self.tenant = _make_tenant('sceptre', self.steward)
        _grant(self.tenant, self.member, 'disciple', 1, self.steward)
        _grant(self.tenant, self.steward, 'branch-steward', 3, self.steward)

    def test_member_can_create_support_request(self):
        client = Client()
        client.force_login(self.member)
        resp = client.post('/community/htmx/support/create/', {
            'title': 'Need prayer', 'content': 'Going through a hard time',
        })
        self.assertEqual(resp.status_code, 200)

        record = Record.objects.get(record_type='support_request', created_by=self.member)
        self.assertEqual(record.status, 'submitted')
        self.assertEqual(record.tenant_id, self.tenant.id)
        self.assertEqual(record.custom_fields['assigned_steward_id'], str(self.steward.id))

    def test_creating_request_notifies_assigned_steward(self):
        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/support/create/', {'title': 'X', 'content': 'Y'})

        self.assertTrue(
            Notification.objects.filter(
                user=self.steward, notification_type='support_request_created',
            ).exists()
        )

    def test_missing_fields_rejected(self):
        client = Client()
        client.force_login(self.member)
        resp = client.post('/community/htmx/support/create/', {'title': '', 'content': ''})
        self.assertContains(resp, 'form-error')
        self.assertFalse(Record.objects.filter(record_type='support_request').exists())

    def test_needs_routing_when_no_steward_assigned(self):
        orphan_tenant = _make_tenant('orphan', self.steward)
        lone_member = _make_user('lone@example.com', level=1)
        _grant(orphan_tenant, lone_member, 'disciple', 1, self.steward)

        client = Client()
        client.force_login(lone_member)
        resp = client.post('/community/htmx/support/create/', {'title': 'Help', 'content': 'No steward here'})
        self.assertEqual(resp.status_code, 200)

        record = Record.objects.get(record_type='support_request', created_by=lone_member)
        self.assertIsNone(record.custom_fields['assigned_steward_id'])
        # No notification should be created — there's no recipient to notify.
        self.assertFalse(
            Notification.objects.filter(notification_type='support_request_created').exists()
        )

    def test_steward_can_acknowledge_then_resolve(self):
        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/support/create/', {'title': 'X', 'content': 'Y'})
        record = Record.objects.get(record_type='support_request', created_by=self.member)

        steward_client = Client()
        steward_client.force_login(self.steward)

        resp = steward_client.post(
            f'/community/htmx/support/{record.id}/acknowledge/', {'action': 'acknowledge'},
        )
        self.assertEqual(resp.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, 'active')
        self.assertIsNotNone(record.custom_fields['acknowledged_at'])
        self.assertTrue(
            Notification.objects.filter(
                user=self.member, notification_type='support_request_acknowledged',
            ).exists()
        )

        resp = steward_client.post(
            f'/community/htmx/support/{record.id}/acknowledge/', {'action': 'resolve'},
        )
        self.assertEqual(resp.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, 'completed')
        self.assertIsNotNone(record.custom_fields['resolved_at'])

    def test_non_steward_cannot_acknowledge(self):
        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/support/create/', {'title': 'X', 'content': 'Y'})
        record = Record.objects.get(record_type='support_request', created_by=self.member)

        # The member themselves (Level 1, not a steward) tries to acknowledge their own request.
        resp = client.post(
            f'/community/htmx/support/{record.id}/acknowledge/', {'action': 'acknowledge'},
        )
        self.assertEqual(resp.status_code, 403)
        record.refresh_from_db()
        self.assertEqual(record.status, 'submitted')

    def test_queue_view_requires_level_3(self):
        client = Client()
        client.force_login(self.member)
        resp = client.get('/community/support/')
        self.assertEqual(resp.status_code, 403)

    def test_queue_view_scoped_to_steward_tenant(self):
        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/support/create/', {'title': 'In scope', 'content': 'Y'})

        other_steward = _make_user('other-steward@example.com', level=3)
        other_tenant = _make_tenant('other', other_steward)
        _grant(other_tenant, other_steward, 'branch-steward', 3, other_steward)
        other_member = _make_user('other-member@example.com', level=1)
        _grant(other_tenant, other_member, 'disciple', 1, other_steward)
        other_client = Client()
        other_client.force_login(other_member)
        other_client.post('/community/htmx/support/create/', {'title': 'Out of scope', 'content': 'Z'})

        steward_client = Client()
        steward_client.force_login(self.steward)
        resp = steward_client.get('/community/support/')
        self.assertContains(resp, 'In scope')
        self.assertNotContains(resp, 'Out of scope')

    def test_my_requests_only_shows_own_requests(self):
        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/support/create/', {'title': 'Mine', 'content': 'Y'})

        other_member = _make_user('other2@example.com', level=1)
        _grant(self.tenant, other_member, 'disciple', 1, self.steward)
        other_client = Client()
        other_client.force_login(other_member)
        other_client.post('/community/htmx/support/create/', {'title': 'Not mine', 'content': 'Z'})

        resp = client.get('/community/htmx/support/mine/')
        self.assertContains(resp, 'Mine')
        self.assertNotContains(resp, 'Not mine')
