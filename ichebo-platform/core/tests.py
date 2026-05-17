"""
core/tests.py

Exit-criterion tests for Phase E.4a (POST /api/sync/push/) and
E.4b (GET /api/sync/pull/) as specified in DOC C §9.

E.4a exit criterion:
  Sending the same payload twice returns "success" both times with no
  duplicate data in the cloud store.

E.4b exit criterion:
  Returns only data scoped to the requesting tenant.
  has_more pagination works correctly.
"""

import uuid
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from activity.models import Activity
from records.models import Record
from tenants.models import Tenant, UserPermission
from core.models import SyncChangelog


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(email=None, competence_level=0):
    email = email or f'user-{uuid.uuid4().hex[:8]}@test.com'
    return User.objects.create_user(
        username=email, email=email, password='testpass123',
        competence_level=competence_level,
    )


def _make_tenant(creator, name=None):
    name = name or f'Tenant-{uuid.uuid4().hex[:6]}'
    slug = name.lower().replace(' ', '-').replace('_', '-')
    return Tenant.objects.create(
        name=name, slug=slug, tier='church_node',
        path=f'/{slug}/', created_by=creator, status='active',
    )


def _make_record(user, tenant=None, title='Test Record'):
    return Record.objects.create(
        title=title,
        record_type='note',
        record_family='journal',
        record_class='personal',
        created_by=user,
        tenant=tenant,
        status='active',
    )


def _make_activity(user, tenant=None, title='Test Activity'):
    return Activity.objects.create(
        title=title,
        activity_type='task',
        created_by=user,
        assigned_to=user,
        tenant=tenant,
        status='pending',
    )


def _auth(client, user):
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')


# ── E.4a — Push endpoint ──────────────────────────────────────────────────────

class PushIdempotencyTests(APITestCase):
    """
    E.4a exit criterion: sending the same payload twice returns "success"
    both times with no duplicate data.
    """

    def setUp(self):
        self.user = _make_user()
        self.tenant = _make_tenant(self.user)
        _auth(self.client, self.user)
        self.device_id = str(uuid.uuid4())
        self.url = '/api/sync/push/'

    def _push(self, entries):
        return self.client.post(
            self.url,
            {'device_id': self.device_id, 'entries': entries},
            format='json',
        )

    def _record_entry(self, entity_id=None, operation='CREATE'):
        entity_id = entity_id or str(uuid.uuid4())
        payload = {
            'id': entity_id,
            'title': 'Pushed Record',
            'record_type': 'note',
            'record_family': 'journal',
            'record_class': 'personal',
            'status': 'active',
            'tenant': str(self.tenant.pk),
        }
        return {
            'entity_type': 'record',
            'entity_id': entity_id,
            'operation': operation,
            'changed_at': timezone.now().isoformat(),
            'payload_hash': SyncChangelog.compute_hash(payload),
            'payload': payload,
        }

    def test_push_create_record_returns_success(self):
        entry = self._record_entry()
        resp = self._push([entry])
        self.assertEqual(resp.status_code, 200)
        result = resp.data['results'][0]
        self.assertEqual(result['status'], 'success')

    def test_push_same_payload_twice_both_succeed(self):
        """E.4a: idempotent — second push of same entry returns success."""
        entry = self._record_entry()
        resp1 = self._push([entry])
        resp2 = self._push([entry])
        self.assertEqual(resp1.data['results'][0]['status'], 'success')
        self.assertEqual(resp2.data['results'][0]['status'], 'success')

    def test_push_idempotent_no_duplicate_changelog_entries(self):
        """E.4a: no duplicate SyncChangelog rows after repeated push."""
        entry = self._record_entry()
        self._push([entry])
        self._push([entry])
        count = SyncChangelog.objects.filter(
            device_id=self.device_id,
            entity_id=entry['entity_id'],
            operation='CREATE',
        ).count()
        self.assertEqual(count, 1)

    def test_push_idempotent_no_duplicate_records(self):
        """E.4a: no duplicate Record rows after repeated push."""
        entry = self._record_entry()
        self._push([entry])
        self._push([entry])
        count = Record.objects.filter(pk=entry['entity_id']).count()
        self.assertEqual(count, 1)

    def test_push_delete_sets_deleted_at(self):
        record = _make_record(self.user, self.tenant)
        entry = self._record_entry(entity_id=str(record.pk), operation='DELETE')
        resp = self._push([entry])
        self.assertEqual(resp.data['results'][0]['status'], 'success')
        record.refresh_from_db()
        self.assertIsNotNone(record.deleted_at)

    def test_push_delete_idempotent(self):
        """Deleting an already-deleted entity returns success, not error."""
        record = _make_record(self.user, self.tenant)
        entry = self._record_entry(entity_id=str(record.pk), operation='DELETE')
        self._push([entry])
        resp = self._push([entry])
        self.assertEqual(resp.data['results'][0]['status'], 'success')

    def test_push_unknown_entity_type_rejected(self):
        entry = self._record_entry()
        entry['entity_type'] = 'banana'
        resp = self._push([entry])
        result = resp.data['results'][0]
        self.assertEqual(result['status'], 'rejected')
        self.assertIn('reason', result)

    def test_push_invalid_entity_id_rejected(self):
        entry = self._record_entry()
        entry['entity_id'] = 'not-a-uuid'
        resp = self._push([entry])
        self.assertEqual(resp.data['results'][0]['status'], 'rejected')

    def test_push_batch_mixed_results(self):
        """Batch can return different statuses per entry independently."""
        good = self._record_entry()
        bad = self._record_entry()
        bad['entity_type'] = 'nope'
        resp = self._push([good, bad])
        statuses = [r['status'] for r in resp.data['results']]
        self.assertIn('success', statuses)
        self.assertIn('rejected', statuses)

    def test_push_creates_changelog_entry(self):
        entry = self._record_entry()
        self._push([entry])
        self.assertTrue(
            SyncChangelog.objects.filter(
                entity_type='record',
                entity_id=entry['entity_id'],
                operation='CREATE',
                device_id=self.device_id,
            ).exists()
        )

    def test_push_requires_authentication(self):
        self.client.credentials()
        entry = self._record_entry()
        resp = self._push([entry])
        self.assertEqual(resp.status_code, 401)

    def test_push_activity_create(self):
        entity_id = str(uuid.uuid4())
        payload = {
            'id': entity_id,
            'title': 'Pushed Activity',
            'activity_type': 'task',
            'status': 'pending',
            'tenant': str(self.tenant.pk),
        }
        entry = {
            'entity_type': 'activity',
            'entity_id': entity_id,
            'operation': 'CREATE',
            'changed_at': timezone.now().isoformat(),
            'payload_hash': SyncChangelog.compute_hash(payload),
            'payload': payload,
        }
        resp = self._push([entry])
        self.assertEqual(resp.data['results'][0]['status'], 'success')


# ── E.4b — Pull endpoint ──────────────────────────────────────────────────────

class PullTenantScopingTests(APITestCase):
    """
    E.4b exit criterion:
      1. Returns only data scoped to the requesting tenant.
      2. has_more pagination works correctly.
    """

    def setUp(self):
        # Two users in different tenants
        self.user_a = _make_user(email='alice@test.com')
        self.user_b = _make_user(email='bob@test.com')

        self.tenant_a = _make_tenant(self.user_a, 'Alpha Church')
        self.tenant_b = _make_tenant(self.user_b, 'Beta Church')

        # Give user_a membership in tenant_a only
        UserPermission.objects.create(
            tenant=self.tenant_a,
            user=self.user_a,
            created_by=self.user_a,
            granted_by=self.user_a,
            role='disciple',
        )

        # Give user_b membership in tenant_b only
        UserPermission.objects.create(
            tenant=self.tenant_b,
            user=self.user_b,
            created_by=self.user_b,
            granted_by=self.user_b,
            role='disciple',
        )

        self.url = '/api/sync/pull/'

    def test_pull_returns_own_records_only(self):
        """User A cannot see User B's records via pull."""
        _make_record(self.user_a, self.tenant_a, 'Alpha Record')
        _make_record(self.user_b, self.tenant_b, 'Beta Record')

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        titles = [r['title'] for r in resp.data['records']]
        self.assertIn('Alpha Record', titles)
        self.assertNotIn('Beta Record', titles)

    def test_pull_returns_own_activities_only(self):
        """User A cannot see User B's activities via pull."""
        _make_activity(self.user_a, self.tenant_a, 'Alpha Task')
        _make_activity(self.user_b, self.tenant_b, 'Beta Task')

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)

        titles = [a['title'] for a in resp.data['activities']]
        self.assertIn('Alpha Task', titles)
        self.assertNotIn('Beta Task', titles)

    def test_pull_since_filters_correctly(self):
        """Only records updated after 'since' are returned."""
        old_record = _make_record(self.user_a, self.tenant_a, 'Old Record')
        since_mark = timezone.now()
        new_record = _make_record(self.user_a, self.tenant_a, 'New Record')

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url, {'since': since_mark.isoformat()})

        titles = [r['title'] for r in resp.data['records']]
        self.assertIn('New Record', titles)
        self.assertNotIn('Old Record', titles)

    def test_pull_no_since_returns_all(self):
        """Without since= the pull returns everything in scope."""
        _make_record(self.user_a, self.tenant_a, 'Record One')
        _make_record(self.user_a, self.tenant_a, 'Record Two')

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)

        titles = [r['title'] for r in resp.data['records']]
        self.assertIn('Record One', titles)
        self.assertIn('Record Two', titles)

    def test_pull_excludes_soft_deleted_records(self):
        """Soft-deleted records do not appear in the pull response."""
        record = _make_record(self.user_a, self.tenant_a, 'Deleted Record')
        record.deleted_at = timezone.now()
        record.save(update_fields=['deleted_at'])

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)

        titles = [r['title'] for r in resp.data['records']]
        self.assertNotIn('Deleted Record', titles)

    def test_pull_response_has_required_keys(self):
        """Response always contains the required envelope keys."""
        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)

        self.assertIn('since', resp.data)
        self.assertIn('retrieved_at', resp.data)
        self.assertIn('has_more', resp.data)
        self.assertIn('records', resp.data)
        self.assertIn('activities', resp.data)
        self.assertIn('relationships', resp.data)
        self.assertIn('notifications', resp.data)

    def test_pull_has_more_false_when_under_limit(self):
        """has_more is False when results fit within the page size."""
        _make_record(self.user_a, self.tenant_a, 'Solo Record')

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)

        self.assertFalse(resp.data['has_more'])

    def test_pull_has_more_true_when_over_limit(self):
        """has_more is True when any entity type exceeds PULL_PAGE_SIZE."""
        from core.views.sync import PULL_PAGE_SIZE
        # Create one more than the page limit
        for i in range(PULL_PAGE_SIZE + 1):
            _make_record(self.user_a, self.tenant_a, f'Record {i}')

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)

        self.assertTrue(resp.data['has_more'])
        # The response itself is capped at PULL_PAGE_SIZE
        self.assertEqual(len(resp.data['records']), PULL_PAGE_SIZE)

    def test_pull_tenant_id_param_scopes_further(self):
        """tenant_id query param restricts to that tenant only."""
        # Give user_a access to both tenants
        UserPermission.objects.create(
            tenant=self.tenant_b,
            user=self.user_a,
            created_by=self.user_b,
            granted_by=self.user_b,
            role='disciple',
        )
        _make_record(self.user_a, self.tenant_a, 'Alpha Only')
        _make_record(self.user_b, self.tenant_b, 'Beta Only')

        _auth(self.client, self.user_a)
        resp = self.client.get(self.url, {'tenant_id': str(self.tenant_a.pk)})

        titles = [r['title'] for r in resp.data['records']]
        self.assertIn('Alpha Only', titles)
        self.assertNotIn('Beta Only', titles)

    def test_pull_requires_authentication(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_pull_retrieved_at_is_iso8601(self):
        """retrieved_at in response is a valid ISO-8601 string."""
        from datetime import datetime
        _auth(self.client, self.user_a)
        resp = self.client.get(self.url)
        # Should parse without error
        dt = datetime.fromisoformat(resp.data['retrieved_at'].replace('Z', '+00:00'))
        self.assertIsNotNone(dt)


# ── E.4 — SyncChangelog model invariants ──────────────────────────────────────

class SyncChangelogTests(APITestCase):
    """
    Verify the append-only changelog model and its signal integration.
    """

    def setUp(self):
        self.user = _make_user()
        self.tenant = _make_tenant(self.user)

    def test_changelog_entry_created_on_record_save(self):
        """post_save signal appends a changelog entry when a Record is created."""
        before = SyncChangelog.objects.count()
        _make_record(self.user, self.tenant)
        after = SyncChangelog.objects.count()
        self.assertGreater(after, before)

    def test_changelog_entry_created_on_activity_save(self):
        before = SyncChangelog.objects.count()
        _make_activity(self.user, self.tenant)
        after = SyncChangelog.objects.count()
        self.assertGreater(after, before)

    def test_changelog_entry_created_on_user_save(self):
        before = SyncChangelog.objects.count()
        _make_user()
        after = SyncChangelog.objects.count()
        self.assertGreater(after, before)

    def test_changelog_records_correct_entity_type(self):
        _make_record(self.user, self.tenant, 'Typed Record')
        entry = SyncChangelog.objects.filter(entity_type='record').last()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.operation, 'CREATE')

    def test_changelog_update_operation_logged(self):
        record = _make_record(self.user, self.tenant)
        record.title = 'Updated Title'
        record.save(update_fields=['title'])
        updates = SyncChangelog.objects.filter(
            entity_id=record.pk, operation='UPDATE'
        )
        self.assertTrue(updates.exists())

    def test_payload_hash_is_sha256_hex(self):
        """payload_hash is always a 64-char hex string (SHA-256)."""
        _make_record(self.user, self.tenant)
        entry = SyncChangelog.objects.filter(entity_type='record').last()
        self.assertEqual(len(entry.payload_hash), 64)
        int(entry.payload_hash, 16)  # must be valid hex

    def test_compute_hash_deterministic(self):
        """Same payload always produces same hash regardless of key order."""
        payload = {'b': 2, 'a': 1, 'id': 'x'}
        h1 = SyncChangelog.compute_hash(payload)
        h2 = SyncChangelog.compute_hash({'a': 1, 'id': 'x', 'b': 2})
        self.assertEqual(h1, h2)
