from django.test import TestCase
from django.db import IntegrityError

from accounts.models import User
from tenants.models import Tenant, UserPermission


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email='admin@example.com'):
    return User.objects.create_user(username=email, email=email, password='testpass123')


def _make_tenant(creator, name='Test Church', slug='test-church', path='/test/', tier='church_node'):
    return Tenant.objects.create(
        created_by=creator,
        name=name,
        slug=slug,
        path=path,
        tier=tier,
    )


# ---------------------------------------------------------------------------
# Tenant model tests
# ---------------------------------------------------------------------------

class TenantModelTests(TestCase):
    def setUp(self):
        self.creator = _make_user()

    def test_tenant_creation_defaults(self):
        tenant = _make_tenant(self.creator)
        self.assertEqual(tenant.status, 'pending')
        self.assertEqual(tenant.affiliation, 'independent')
        self.assertFalse(tenant.is_collective)

    def test_tenant_str(self):
        tenant = _make_tenant(self.creator, name='Grace Church', path='/grace/')
        self.assertIn('Grace Church', str(tenant))
        self.assertIn('/grace/', str(tenant))

    def test_uuid_primary_key(self):
        tenant = _make_tenant(self.creator)
        self.assertEqual(len(str(tenant.id)), 36)

    def test_get_descendants(self):
        parent = _make_tenant(self.creator, name='Parent', slug='parent', path='/parent/')
        child = _make_tenant(self.creator, name='Child', slug='child', path='/parent/child/')
        grandchild = _make_tenant(self.creator, name='Grandchild', slug='gc', path='/parent/child/gc/')

        descendants = parent.get_descendants()
        self.assertIn(child, descendants)
        self.assertIn(grandchild, descendants)
        self.assertNotIn(parent, descendants)

    def test_get_ancestors(self):
        _make_tenant(self.creator, name='National', slug='national', path='/national/')
        _make_tenant(self.creator, name='District', slug='district', path='/national/district/')
        branch = _make_tenant(self.creator, name='Branch', slug='branch', path='/national/district/branch/')

        ancestors = branch.get_ancestors()
        ancestor_paths = [t.path for t in ancestors]
        self.assertIn('/national/', ancestor_paths)
        self.assertIn('/national/district/', ancestor_paths)
        self.assertNotIn('/national/district/branch/', ancestor_paths)

    def test_tenant_with_parent_fk(self):
        parent = _make_tenant(self.creator, slug='par', path='/par/')
        child = Tenant.objects.create(
            created_by=self.creator,
            parent=parent,
            name='Child Node',
            slug='child-node',
            path='/par/child/',
            tier='church_node',
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())


# ---------------------------------------------------------------------------
# UserPermission model tests
# ---------------------------------------------------------------------------

class UserPermissionTests(TestCase):
    def setUp(self):
        self.admin = _make_user(email='admin@example.com')
        self.member = _make_user(email='member@example.com')
        self.tenant = _make_tenant(self.admin)

    def _grant(self, role='disciple', level=1):
        return UserPermission.objects.create(
            tenant=self.tenant,
            user=self.member,
            created_by=self.admin,
            tenant_path=self.tenant.path,
            role=role,
            level=level,
        )

    def test_permission_creation_defaults(self):
        perm = self._grant()
        self.assertTrue(perm.is_active)
        self.assertEqual(perm.role, 'disciple')
        self.assertEqual(perm.level, 1)

    def test_uuid_primary_key(self):
        perm = self._grant()
        self.assertEqual(len(str(perm.id)), 36)

    def test_unique_together_tenant_user_role(self):
        self._grant(role='disciple')
        with self.assertRaises(IntegrityError):
            UserPermission.objects.create(
                tenant=self.tenant,
                user=self.member,
                created_by=self.admin,
                tenant_path=self.tenant.path,
                role='disciple',
                level=1,
            )

    def test_same_user_can_have_different_roles(self):
        self._grant(role='disciple')
        perm2 = UserPermission.objects.create(
            tenant=self.tenant,
            user=self.member,
            created_by=self.admin,
            tenant_path=self.tenant.path,
            role='branch-steward',
            level=3,
        )
        self.assertEqual(
            UserPermission.objects.filter(user=self.member, tenant=self.tenant).count(),
            2,
        )

    def test_permission_inactive_flag(self):
        perm = self._grant()
        perm.is_active = False
        perm.save(update_fields=['is_active'])
        perm.refresh_from_db()
        self.assertFalse(perm.is_active)

    def test_user_tenant_permissions_reverse(self):
        self._grant()
        self.assertTrue(self.member.tenant_permissions.filter(tenant=self.tenant).exists())
