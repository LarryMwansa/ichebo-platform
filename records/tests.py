from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from records.models import Record, Relationship
from governance.services import create_new_version


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email='author@example.com', level=0):
    return User.objects.create_user(username=email, email=email, password='testpass123',
                                    competence_level=level)


def _make_record(user, title='Test Record', record_type='note', record_family='journal',
                 record_class='personal', status='active', version=None):
    return Record.objects.create(
        created_by=user,
        record_class=record_class,
        record_family=record_family,
        record_type=record_type,
        title=title,
        status=status,
        version=version,
        origin='user',
    )


# ---------------------------------------------------------------------------
# Record model tests
# ---------------------------------------------------------------------------

class RecordModelTests(TestCase):
    def setUp(self):
        self.user = _make_user()

    def test_record_creation_defaults(self):
        rec = _make_record(self.user)
        self.assertEqual(rec.status, 'active')
        self.assertIsNone(rec.deleted_at)
        self.assertIsNone(rec.locked_by)
        self.assertEqual(rec.tags, [])
        self.assertEqual(rec.metadata, {})

    def test_uuid_primary_key(self):
        rec = _make_record(self.user)
        self.assertEqual(len(str(rec.id)), 36)

    def test_str_includes_type_and_title(self):
        rec = _make_record(self.user, record_type='note', title='Daily Reflection')
        self.assertIn('note', str(rec))
        self.assertIn('Daily Reflection', str(rec))

    def test_soft_delete_leaves_row_in_db(self):
        rec = _make_record(self.user)
        rec.deleted_at = timezone.now()
        rec.save(update_fields=['deleted_at'])
        # Row still exists
        self.assertTrue(Record.objects.filter(id=rec.id).exists())
        # But can be filtered out
        self.assertFalse(Record.objects.filter(id=rec.id, deleted_at__isnull=True).exists())

    def test_record_families_and_types_stored(self):
        gov = _make_record(self.user, record_family='governance', record_type='edict',
                           record_class='governance')
        self.assertEqual(gov.record_family, 'governance')
        self.assertEqual(gov.record_type, 'edict')

    def test_metadata_json_stored(self):
        rec = Record.objects.create(
            created_by=self.user,
            record_class='personal',
            record_family='journal',
            record_type='note',
            title='With metadata',
            metadata={'dar': True, 'source_app': 'test'},
            origin='user',
        )
        rec.refresh_from_db()
        self.assertTrue(rec.metadata['dar'])
        self.assertEqual(rec.metadata['source_app'], 'test')


# ---------------------------------------------------------------------------
# Relationship model tests
# ---------------------------------------------------------------------------

class RelationshipModelTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.rec_a = _make_record(self.user, title='A')
        self.rec_b = _make_record(self.user, title='B')

    def test_create_relationship_between_records(self):
        rel = Relationship.objects.create(
            created_by=self.user,
            from_record=self.rec_a,
            to_record=self.rec_b,
            relationship_type='relates_to',
            direction='directed',
        )
        self.assertEqual(rel.from_record, self.rec_a)
        self.assertEqual(rel.to_record, self.rec_b)
        self.assertEqual(rel.relationship_type, 'relates_to')

    def test_part_of_relationship(self):
        lesson = _make_record(self.user, record_type='lesson', title='Lesson 1',
                              record_family='learning', record_class='organizational')
        course = _make_record(self.user, record_type='course', title='Course A',
                              record_family='learning', record_class='organizational')
        Relationship.objects.create(
            created_by=self.user,
            from_record=lesson,
            to_record=course,
            relationship_type='part_of',
            direction='directed',
        )
        self.assertTrue(
            Relationship.objects.filter(
                from_record=lesson, to_record=course, relationship_type='part_of'
            ).exists()
        )

    def test_uuid_primary_key(self):
        rel = Relationship.objects.create(
            created_by=self.user,
            from_record=self.rec_a,
            to_record=self.rec_b,
            relationship_type='references',
            direction='directed',
        )
        self.assertEqual(len(str(rel.id)), 36)

    def test_soft_delete_relationship(self):
        rel = Relationship.objects.create(
            created_by=self.user,
            from_record=self.rec_a,
            to_record=self.rec_b,
            relationship_type='relates_to',
            direction='directed',
        )
        rel.deleted_at = timezone.now()
        rel.save(update_fields=['deleted_at'])
        self.assertTrue(Relationship.objects.filter(id=rel.id).exists())
        self.assertFalse(Relationship.objects.filter(id=rel.id, deleted_at__isnull=True).exists())


# ---------------------------------------------------------------------------
# Version chain (supersede) tests
# ---------------------------------------------------------------------------

class VersionChainTests(TestCase):
    def setUp(self):
        self.user = _make_user(level=5)

    def _make_gov_record(self, version=1):
        return Record.objects.create(
            created_by=self.user,
            record_class='governance',
            record_family='governance',
            record_type='edict',
            title='Original Edict',
            status='active',
            version=version,
            origin='user',
            metadata={'source_app': 'governance'},
        )

    def test_supersede_creates_new_draft_version(self):
        old = self._make_gov_record(version=1)
        new = create_new_version(old, self.user)

        self.assertEqual(new.status, 'draft')
        self.assertEqual(new.version, 2)
        self.assertEqual(new.previous_version, old)
        self.assertEqual(new.record_type, old.record_type)
        self.assertEqual(new.title, old.title)

    def test_supersede_marks_old_record_as_superseded(self):
        old = self._make_gov_record(version=1)
        new = create_new_version(old, self.user)

        old.refresh_from_db()
        self.assertEqual(old.status, 'superseded')
        self.assertEqual(old.superseded_by, new)

    def test_supersede_increments_version_number(self):
        v1 = self._make_gov_record(version=1)
        v2 = create_new_version(v1, self.user)
        v3 = create_new_version(v2, self.user)

        self.assertEqual(v2.version, 2)
        self.assertEqual(v3.version, 3)

    def test_supersede_copies_content_to_new_version(self):
        old = Record.objects.create(
            created_by=self.user,
            record_class='governance',
            record_family='governance',
            record_type='edict',
            title='Original',
            content='Important content',
            summary='Brief summary',
            status='active',
            version=1,
            origin='user',
            tags=['theology', 'governance'],
        )
        new = create_new_version(old, self.user)

        self.assertEqual(new.content, 'Important content')
        self.assertEqual(new.summary, 'Brief summary')
        self.assertEqual(new.tags, ['theology', 'governance'])
