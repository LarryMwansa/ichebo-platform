from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from handbook.models import (
    HandbookAccess, HandbookRecord,
    BRANCH_KEYS, BRANCH_REFERENCE, BRANCH_MANDATE,
)


def _make_user(email, **kwargs):
    u = User(username=email, email=email, **kwargs)
    u.set_password('pass')
    u.save()
    return u


def _make_record(branch, record_type, user, status=HandbookRecord.STATUS_ACTIVE, title='Test'):
    return HandbookRecord.objects.create(
        branch=branch,
        record_type=record_type,
        title=title,
        created_by=user,
        status=status,
    )


class KeysLibraryPrivacyTest(TestCase):
    """
    Keys are personal. They are never visible to other users, never published
    to the network, and accessible without HandbookAccess.
    """

    def setUp(self):
        self.owner = _make_user('owner@test.com')
        self.other = _make_user('other@test.com')
        self.editor = _make_user('editor@test.com')
        HandbookAccess.objects.create(user=self.editor, role=HandbookAccess.ROLE_EDITOR)
        self.client = APIClient()

    # ── Creation ─────────────────────────────────────────────────────────────

    def test_any_user_can_create_key_record_without_handbook_access(self):
        """No HandbookAccess required to create a key record."""
        self.client.force_authenticate(self.owner)
        resp = self.client.post('/api/handbook/records/', {
            'branch': BRANCH_KEYS, 'record_type': 'key',
            'title': 'Crown', 'content': 'Symbol of authority',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['branch'], BRANCH_KEYS)
        self.assertEqual(HandbookRecord.objects.filter(branch=BRANCH_KEYS, created_by=self.owner).count(), 1)

    # ── Isolation ────────────────────────────────────────────────────────────

    def test_key_record_not_visible_to_other_user_in_list(self):
        """A user cannot see another user's key records in the list endpoint."""
        _make_record(BRANCH_KEYS, 'key', self.owner, title='My Key')
        self.client.force_authenticate(self.other)
        resp = self.client.get('/api/handbook/records/?branch=keys')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)

    def test_key_record_not_visible_to_editor_in_list(self):
        """Even an editor cannot see another user's key records."""
        _make_record(BRANCH_KEYS, 'key', self.owner, title='My Key')
        self.client.force_authenticate(self.editor)
        resp = self.client.get('/api/handbook/records/?branch=keys')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)

    def test_owner_can_see_own_key_in_list(self):
        _make_record(BRANCH_KEYS, 'key', self.owner, title='My Key')
        self.client.force_authenticate(self.owner)
        resp = self.client.get('/api/handbook/records/?branch=keys')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_other_user_cannot_fetch_key_record_detail(self):
        record = _make_record(BRANCH_KEYS, 'key', self.owner)
        self.client.force_authenticate(self.other)
        resp = self.client.get(f'/api/handbook/records/{record.id}/')
        self.assertEqual(resp.status_code, 404)

    def test_other_user_cannot_patch_key_record(self):
        record = _make_record(BRANCH_KEYS, 'key', self.owner, status=HandbookRecord.STATUS_DRAFT)
        self.client.force_authenticate(self.other)
        resp = self.client.patch(f'/api/handbook/records/{record.id}/', {'title': 'Stolen'}, format='json')
        self.assertEqual(resp.status_code, 404)

    def test_owner_can_fetch_and_patch_own_key(self):
        record = _make_record(BRANCH_KEYS, 'key', self.owner, status=HandbookRecord.STATUS_DRAFT)
        self.client.force_authenticate(self.owner)
        resp = self.client.get(f'/api/handbook/records/{record.id}/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.patch(f'/api/handbook/records/{record.id}/', {'title': 'Updated'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['title'], 'Updated')

    # ── Publishing blocked ────────────────────────────────────────────────────

    def test_key_record_cannot_be_published(self):
        """Keys are personal — publish endpoint must reject them."""
        record = _make_record(BRANCH_KEYS, 'key', self.owner, status=HandbookRecord.STATUS_DRAFT)
        self.client.force_authenticate(self.owner)
        resp = self.client.post(f'/api/handbook/records/{record.id}/publish/')
        self.assertEqual(resp.status_code, 400)

    def test_key_record_cannot_be_locked_via_lock_endpoint(self):
        record = _make_record(BRANCH_KEYS, 'key', self.owner, status=HandbookRecord.STATUS_ACTIVE)
        self.client.force_authenticate(self.editor)
        resp = self.client.post(f'/api/handbook/records/{record.id}/lock/')
        self.assertEqual(resp.status_code, 400)

    # ── Publish feed excludes keys ────────────────────────────────────────────

    def test_publish_feed_excludes_key_records(self):
        """Keys must never appear in the sync publish feed."""
        _make_record(BRANCH_KEYS, 'key', self.owner, status=HandbookRecord.STATUS_ACTIVE, title='My Key')
        _make_record(BRANCH_REFERENCE, 'principle', self.editor, status=HandbookRecord.STATUS_ACTIVE, title='A Principle')
        self.client.force_authenticate(self.editor)
        resp = self.client.get('/api/handbook/publish-feed/')
        self.assertEqual(resp.status_code, 200)
        titles = [r['title'] for r in resp.data]
        self.assertNotIn('My Key', titles)
        self.assertIn('A Principle', titles)

    # ── History scoped to owner ───────────────────────────────────────────────

    def test_history_of_key_record_only_accessible_by_owner(self):
        record = _make_record(BRANCH_KEYS, 'key', self.owner)
        self.client.force_authenticate(self.other)
        resp = self.client.get(f'/api/handbook/records/{record.id}/history/')
        self.assertEqual(resp.status_code, 404)
        self.client.force_authenticate(self.owner)
        resp = self.client.get(f'/api/handbook/records/{record.id}/history/')
        self.assertEqual(resp.status_code, 200)

    # ── Relationship privacy ──────────────────────────────────────────────────

    def test_other_user_cannot_view_key_record_relationships(self):
        record = _make_record(BRANCH_KEYS, 'key', self.owner)
        self.client.force_authenticate(self.other)
        resp = self.client.get(f'/api/handbook/records/{record.id}/relationships/')
        self.assertEqual(resp.status_code, 404)

    def test_owner_can_add_has_symbol_relationship_to_reference_record(self):
        """Owner can link their key to a shared Reference Library record via has_symbol."""
        key = _make_record(BRANCH_KEYS, 'key', self.owner, status=HandbookRecord.STATUS_DRAFT)
        ref = _make_record(BRANCH_REFERENCE, 'principle', self.editor, status=HandbookRecord.STATUS_ACTIVE, title='Authority')
        self.client.force_authenticate(self.owner)
        resp = self.client.post(f'/api/handbook/records/{key.id}/relationships/', {
            'relationship_type': 'has_symbol',
            'to_record': str(ref.id),
            'direction': 'bidirectional',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
