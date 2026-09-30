"""
Handbook privacy and access tests (DOC F v2.2, Parts 5.1, 6.1, 6.2, 7.4, 7.5).

Rebuilt for the ADR-022 implementation: Handbook records live in records.Record,
the workspace is server-rendered, and publishing goes through the general sync
pull. The previous suite exercised the retired /api/handbook/ API and could no
longer be imported.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from handbook.models import HandbookAccess
from records.models import Record, Relationship


def _user(email, level=0, **kwargs):
    u = User(username=email, email=email, competence_level=level, **kwargs)
    u.set_password('pass')
    u.save()
    return u


def _governance(user, record_type, status='active', title=None):
    return Record.objects.create(
        created_by=user, record_class='governance', record_family='governance',
        record_type=record_type, status=status, title=title or f'{record_type} {status}',
    )


def _key(user, title='Crown Canary Key', status='active'):
    return Record.objects.create(
        created_by=user, record_class='personal', record_family='reference',
        record_type='key', status=status, title=title,
    )


def _journal(user, title='My Dream'):
    return Record.objects.create(
        created_by=user, record_class='personal', record_family='journal',
        record_type='dream', status='active', title=title,
    )


def _synced_titles(user):
    client = APIClient()
    client.force_authenticate(user)
    resp = client.get('/api/sync/pull/')
    assert resp.status_code == 200, resp.status_code
    return {r['title'] for r in resp.data['records']}


class KeysPrivacyTest(TestCase):
    """Keys are owner-only: not visible to other users, editors or superusers (6.1)."""

    def setUp(self):
        self.owner = _user('owner@test.com', level=4)
        self.other = _user('other@test.com', level=5)
        self.editor = _user('editor@test.com', level=5)
        HandbookAccess.objects.create(user=self.editor, role=HandbookAccess.ROLE_EDITOR)
        self.admin = _user('admin@test.com', level=5, is_superuser=True, is_staff=True)
        self.key = _key(self.owner)

    def test_owner_sees_own_key_in_keys_library(self):
        self.client.force_login(self.owner)
        resp = self.client.get('/handbook/?branch=keys')
        self.assertContains(resp, 'Crown Canary Key')

    def test_other_user_does_not_see_key_in_keys_library(self):
        self.client.force_login(self.other)
        resp = self.client.get('/handbook/?branch=keys')
        self.assertNotContains(resp, 'Crown Canary Key', status_code=resp.status_code)

    def test_nobody_else_can_open_the_key(self):
        for viewer in (self.other, self.editor, self.admin):
            self.client.force_login(viewer)
            resp = self.client.get(f'/handbook/records/{self.key.pk}/')
            self.assertEqual(resp.status_code, 404, viewer.email)

    def test_owner_can_open_own_key(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(f'/handbook/records/{self.key.pk}/').status_code, 200)

    def test_key_never_synced_to_another_user(self):
        for viewer in (self.other, self.editor, self.admin):
            self.assertNotIn('Crown Canary Key', _synced_titles(viewer), viewer.email)
        self.assertIn('Crown Canary Key', _synced_titles(self.owner))

    def test_nobody_else_can_list_the_keys_links(self):
        for viewer in (self.other, self.editor, self.admin):
            self.client.force_login(viewer)
            resp = self.client.get(f'/handbook/htmx/{self.key.pk}/relationships/')
            self.assertEqual(resp.status_code, 404, viewer.email)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(f'/handbook/htmx/{self.key.pk}/relationships/').status_code, 200)


class JournalPrivacyTest(TestCase):
    """A link to a journal entry is visible only to the journal's owner (6.2)."""

    def setUp(self):
        self.host = _user('host@test.com', level=5)
        self.editor = _user('editor@test.com', level=5)
        HandbookAccess.objects.create(user=self.editor, role=HandbookAccess.ROLE_EDITOR)
        self.reader = _user('reader@test.com', level=5)
        self.journal = _journal(self.host, title='Private Dream Title')
        self.principle = _governance(self.editor, 'principle', title='Shared Principle')
        Relationship.objects.create(
            from_record=self.journal, to_record=self.principle,
            relationship_type='references', created_by=self.host,
        )

    def test_journal_not_synced_to_others(self):
        self.assertNotIn('Private Dream Title', _synced_titles(self.editor))
        self.assertNotIn('Private Dream Title', _synced_titles(self.reader))

    def test_journal_link_hidden_from_others_in_relationship_list(self):
        for viewer in (self.editor, self.reader):
            self.client.force_login(viewer)
            resp = self.client.get(f'/handbook/htmx/{self.principle.pk}/relationships/')
            self.assertEqual(resp.status_code, 200)
            self.assertNotContains(resp, 'Private Dream Title')

    def test_journal_link_visible_to_its_owner(self):
        self.client.force_login(self.host)
        resp = self.client.get(f'/handbook/htmx/{self.principle.pk}/relationships/')
        self.assertContains(resp, 'Private Dream Title')

    def test_journal_link_hidden_from_others_in_linked_records(self):
        self.client.force_login(self.editor)
        resp = self.client.get(f'/handbook/htmx/{self.principle.pk}/links/')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Private Dream Title')

    def test_journal_entry_itself_cannot_be_listed_by_others(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(f'/handbook/htmx/{self.journal.pk}/relationships/').status_code, 404)

    def test_author_cannot_link_to_someone_elses_journal(self):
        self.client.force_login(self.editor)
        resp = self.client.post('/handbook/htmx/relationship/create/', {
            'from_record_id': str(self.principle.pk),
            'to_record_id': str(self.journal.pk),
            'relationship_type': 'references',
        })
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(Relationship.objects.filter(
            from_record=self.principle, to_record=self.journal,
        ).exists())


class SyncGovernanceTest(TestCase):
    """The sync pull publishes only published governance records, Mandate from Level 4 (5.1, 7.2)."""

    def setUp(self):
        self.author = _user('author@test.com', level=5)
        HandbookAccess.objects.create(user=self.author, role=HandbookAccess.ROLE_AUTHOR)
        self.l3 = _user('l3@test.com', level=3)
        self.l4 = _user('l4@test.com', level=4)
        _governance(self.author, 'principle', status='draft', title='Draft Principle')
        _governance(self.author, 'principle', status='active', title='Active Principle')
        _governance(self.author, 'mandate', status='active', title='Active Mandate')
        _governance(self.author, 'mandate', status='locked', title='Locked Mandate')

    def test_drafts_are_not_published(self):
        self.assertNotIn('Draft Principle', _synced_titles(self.l3))
        self.assertNotIn('Draft Principle', _synced_titles(self.l4))

    def test_level_3_gets_reference_but_not_mandate(self):
        titles = _synced_titles(self.l3)
        self.assertIn('Active Principle', titles)
        self.assertNotIn('Active Mandate', titles)
        self.assertNotIn('Locked Mandate', titles)

    def test_level_4_gets_mandate(self):
        titles = _synced_titles(self.l4)
        self.assertIn('Active Mandate', titles)
        self.assertIn('Locked Mandate', titles)

    def test_below_level_3_gets_no_governance(self):
        l2 = _user('l2@test.com', level=2)
        self.assertFalse({'Active Principle', 'Active Mandate'} & _synced_titles(l2))

    def test_author_still_syncs_own_drafts(self):
        self.assertIn('Draft Principle', _synced_titles(self.author))


class HandbookReaderAccessTest(TestCase):
    """No anonymous access; Reference from Level 3, Mandate from Level 4 (5.1, 7.5)."""

    def setUp(self):
        author = _user('author@test.com', level=5)
        self.principle = _governance(author, 'principle', title='Visible Principle')
        self.mandate = _governance(author, 'mandate', title='Guarded Mandate')
        self.draft = _governance(author, 'principle', status='draft', title='Unpublished Principle')

    def test_anonymous_redirected_to_login(self):
        self.assertEqual(self.client.get('/handbook/').status_code, 302)
        self.assertEqual(self.client.get(f'/handbook/records/{self.principle.pk}/').status_code, 302)

    def test_below_level_3_has_no_handbook(self):
        self.client.force_login(_user('l1@test.com', level=1))
        self.assertEqual(self.client.get('/handbook/').status_code, 403)
        self.assertEqual(self.client.get(f'/handbook/records/{self.principle.pk}/').status_code, 404)

    def test_level_3_reads_reference_not_mandate(self):
        self.client.force_login(_user('l3@test.com', level=3))
        self.assertEqual(self.client.get(f'/handbook/records/{self.principle.pk}/').status_code, 200)
        self.assertEqual(self.client.get(f'/handbook/records/{self.mandate.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/handbook/?branch=mandate').status_code, 403)

    def test_level_4_reads_mandate(self):
        self.client.force_login(_user('l4@test.com', level=4))
        self.assertEqual(self.client.get(f'/handbook/records/{self.mandate.pk}/').status_code, 200)

    def test_readers_without_a_grant_do_not_see_drafts(self):
        self.client.force_login(_user('l5@test.com', level=5))
        self.assertEqual(self.client.get(f'/handbook/records/{self.draft.pk}/').status_code, 404)


class GraphOfflineTest(TestCase):
    """The knowledge graph is offline until rescoped (7.5, D16)."""

    def setUp(self):
        owner = _user('owner@test.com', level=4)
        _journal(owner, title='Graph Leak Canary')
        _key(owner, title='Graph Key Canary')

    def test_anonymous_cannot_reach_graph(self):
        self.assertEqual(self.client.get('/handbook/htmx/graph/data/').status_code, 302)
        self.assertEqual(self.client.get('/handbook/graph/').status_code, 302)

    def test_graph_data_returns_nothing(self):
        self.client.force_login(_user('viewer@test.com', level=5))
        resp = self.client.get('/handbook/htmx/graph/data/')
        self.assertEqual(resp.json(), {'nodes': [], 'links': []})
        self.assertNotContains(resp, 'Canary')


class HtmlEscapingTest(TestCase):
    """Record titles are escaped in hand-built HTMX fragments."""

    def test_relationship_list_escapes_titles(self):
        author = _user('author@test.com', level=5)
        a = _governance(author, 'principle', title='Plain')
        b = _governance(author, 'concept', title='<script>alert(1)</script>')
        Relationship.objects.create(from_record=a, to_record=b, relationship_type='references', created_by=author)
        self.client.force_login(author)
        resp = self.client.get(f'/handbook/htmx/{a.pk}/relationships/')
        self.assertNotContains(resp, '<script>alert(1)</script>')
        self.assertContains(resp, '&lt;script&gt;')
