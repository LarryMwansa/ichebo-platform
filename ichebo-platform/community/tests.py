from django.test import TestCase, Client

from accounts.models import User
from notifications.models import Notification
from records.models import Record
from tenants.models import Tenant, UserPermission

from .services import resolve_steward_for_tenant
from .views import _find_live_session


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


# ---------------------------------------------------------------------------
# Live service room — tenant-scoped, with in-service ministry panel
# See .docs/plans/community-live-service-room-plan.md
# ---------------------------------------------------------------------------

class FindLiveSessionTests(TestCase):
    """_find_live_session is backed by BroadcastSchedule only — the legacy
    Activity URL-embed fallback it used to also check was retired
    2026-06-24 (video-direction-v2-plan.md): production had zero rows using
    that pattern, and video_live's app surface (the only place that could
    create new ones) was deleted in the same pass."""

    def setUp(self):
        self.steward = _make_user('live-find-steward@example.com', level=3)
        self.tenant_a = _make_tenant('live-find-a', self.steward)
        self.tenant_b = _make_tenant('live-find-b', self.steward)

    def test_returns_none_for_null_tenant(self):
        self.assertIsNone(_find_live_session(None))

    def test_returns_none_when_nothing_scheduled(self):
        self.assertIsNone(_find_live_session(self.tenant_a))

    def test_finds_live_broadcast_schedule(self):
        from django.utils import timezone
        from video_live.models import BroadcastSchedule

        broadcast = BroadcastSchedule.objects.create(
            tenant=self.tenant_a, created_by=self.steward, title='Sunday Service',
            scheduled_at=timezone.now(), status='live',
        )
        session = _find_live_session(self.tenant_a)
        self.assertIsNotNone(session)
        self.assertTrue(session['is_live'])
        self.assertEqual(session['source'], 'broadcast')
        self.assertEqual(session['broadcast_id'], str(broadcast.id))

    def test_does_not_leak_across_tenants(self):
        from django.utils import timezone
        from video_live.models import BroadcastSchedule

        BroadcastSchedule.objects.create(
            tenant=self.tenant_a, created_by=self.steward, title='Tenant A Service',
            scheduled_at=timezone.now(), status='live',
        )
        self.assertIsNone(_find_live_session(self.tenant_b))


class LiveServiceRoomFlowTests(TestCase):

    def setUp(self):
        self.steward = _make_user('live-flow-steward@example.com', level=3)
        self.member = _make_user('live-flow-member@example.com', level=1)
        self.tenant = _make_tenant('live-flow', self.steward)
        _grant(self.tenant, self.member, 'disciple', 1, self.steward)
        _grant(self.tenant, self.steward, 'branch-steward', 3, self.steward)

    def _create_live_broadcast(self):
        from django.utils import timezone
        from video_live.models import BroadcastSchedule
        return BroadcastSchedule.objects.create(
            tenant=self.tenant, created_by=self.steward, title='Live Service',
            scheduled_at=timezone.now(), status='live',
        )

    def test_room_view_requires_level_1(self):
        seeker = _make_user('live-seeker@example.com', level=0)
        client = Client()
        client.force_login(seeker)
        resp = client.get('/community/live/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'community/seeker_gate.html')

    def test_room_view_renders_live_session(self):
        broadcast = self._create_live_broadcast()
        client = Client()
        client.force_login(self.member)
        resp = client.get('/community/live/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Live Service')

    def test_member_can_raise_live_request_scoped_to_broadcast(self):
        broadcast = self._create_live_broadcast()
        client = Client()
        client.force_login(self.member)
        resp = client.post('/community/htmx/live/request/', {
            'broadcast_id': str(broadcast.id), 'kind': 'prayer', 'content': 'Pray for me',
        })
        self.assertEqual(resp.status_code, 200)

        record = Record.objects.get(record_type='live_request', created_by=self.member)
        self.assertEqual(record.custom_fields['broadcast_id'], str(broadcast.id))
        self.assertEqual(record.status, 'submitted')

    def test_raising_live_request_notifies_steward_not_all_members(self):
        broadcast = self._create_live_broadcast()
        other_member = _make_user('live-flow-other@example.com', level=1)
        _grant(self.tenant, other_member, 'disciple', 1, self.steward)

        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/live/request/', {
            'broadcast_id': str(broadcast.id), 'kind': 'question', 'content': 'X',
        })

        self.assertTrue(
            Notification.objects.filter(
                user=self.steward, notification_type='live_request_raised',
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                user=other_member, notification_type='live_request_raised',
            ).exists()
        )

    def test_invalid_kind_rejected(self):
        broadcast = self._create_live_broadcast()
        client = Client()
        client.force_login(self.member)
        resp = client.post('/community/htmx/live/request/', {
            'broadcast_id': str(broadcast.id), 'kind': 'not-a-real-kind', 'content': 'X',
        })
        self.assertContains(resp, 'form-error')
        self.assertFalse(Record.objects.filter(record_type='live_request').exists())

    def test_steward_queue_scoped_to_broadcast_id(self):
        broadcast = self._create_live_broadcast()
        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/live/request/', {
            'broadcast_id': str(broadcast.id), 'kind': 'prayer', 'content': 'This session',
        })

        # A request tagged to a different (old) session must not appear.
        Record.objects.create(
            tenant=self.tenant, created_by=self.member, record_class='personal',
            record_family='community', record_type='live_request', title='question',
            content='Old session', status='submitted',
            custom_fields={'broadcast_id': 'some-other-id', 'session_date': '2026-01-01'},
        )

        steward_client = Client()
        steward_client.force_login(self.steward)
        resp = steward_client.get(f'/community/htmx/live/queue/?broadcast_id={broadcast.id}')
        self.assertContains(resp, 'This session')
        self.assertNotContains(resp, 'Old session')

    def test_non_steward_cannot_access_queue(self):
        broadcast = self._create_live_broadcast()
        client = Client()
        client.force_login(self.member)
        resp = client.get(f'/community/htmx/live/queue/?broadcast_id={broadcast.id}')
        self.assertEqual(resp.status_code, 403)

    def test_steward_can_respond_then_complete(self):
        broadcast = self._create_live_broadcast()
        client = Client()
        client.force_login(self.member)
        client.post('/community/htmx/live/request/', {
            'broadcast_id': str(broadcast.id), 'kind': 'prayer', 'content': 'X',
        })
        record = Record.objects.get(record_type='live_request', created_by=self.member)

        steward_client = Client()
        steward_client.force_login(self.steward)

        resp = steward_client.post(
            f'/community/htmx/live/{record.id}/respond/', {'action': 'respond'},
        )
        self.assertEqual(resp.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, 'active')

        resp = steward_client.post(
            f'/community/htmx/live/{record.id}/respond/', {'action': 'complete'},
        )
        self.assertEqual(resp.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, 'completed')
