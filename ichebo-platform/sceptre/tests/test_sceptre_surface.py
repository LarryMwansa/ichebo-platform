"""
Tests for Phase H.6 — sceptre.ichebo.org surface.
Covers: middleware routing, participant access control,
steward gating, home page rendering, now-playing partial.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory

from middleware.site_router import SiteRouterMiddleware
from sceptre.auth import is_steward
from tenants.models import Tenant, UserPermission

User = get_user_model()


def _test_admin():
    """Shared admin user for created_by/granted_by FKs below. get_or_create,
    not create_user — TestSceptreAccessControl.setUp calls make_tenant()
    twice (once for the main tenant, once for the induction tenant); a
    plain create_user() call inside make_tenant would raise IntegrityError
    on the second call (duplicate username)."""
    admin, _ = User.objects.get_or_create(
        username='_test_admin_h6', defaults={'email': '_test_admin_h6@test.com'},
    )
    return admin


def make_tenant(name='Sceptre Tenant', slug='sceptre-test'):
    # Tenant requires slug (unique), path (the real field — not
    # tenant_path, which lives on UserPermission), tier, and created_by.
    return Tenant.objects.create(
        name=name, slug=slug, path=f'/global/{slug}/',
        tier='church_node', created_by=_test_admin(),
    )


def make_user(username, level=1, tenant=None, role=None):
    user = User.objects.create_user(
        username=username, password='testpass123',
        email=f'{username}@test.com',
    )
    user.competence_level = level   # real IntegerField — pass an int, not a string
    user.save()
    if tenant and role:
        # UserPermission.created_by is a required FK (on_delete=PROTECT,
        # no null=True).
        UserPermission.objects.create(
            user=user, tenant=tenant, role=role, created_by=_test_admin(),
            is_active=True, tenant_path=tenant.path,
        )
    return user


class TestSiteRouterMiddleware(TestCase):
    """Middleware sets request.site and request.urlconf correctly."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SiteRouterMiddleware(lambda r: r)

    def test_sceptre_host_sets_community_site(self):
        request = self.factory.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.middleware(request)
        self.assertEqual(request.site, 'community')
        self.assertEqual(request.urlconf, 'sceptre.urls')

    def test_app_host_sets_agency_site(self):
        request = self.factory.get('/', HTTP_HOST='app.ichebo.org')
        self.middleware(request)
        self.assertEqual(request.site, 'agency')
        self.assertFalse(hasattr(request, 'urlconf'))

    def test_unknown_host_defaults_to_agency(self):
        request = self.factory.get('/', HTTP_HOST='localhost')
        self.middleware(request)
        self.assertEqual(request.site, 'agency')

    def test_host_with_port_still_matches(self):
        """.split(':')[0] strips an explicit port before comparing."""
        request = self.factory.get('/', HTTP_HOST='sceptre.ichebo.org:8001')
        self.middleware(request)
        self.assertEqual(request.site, 'community')

    def test_host_is_case_insensitive(self):
        request = self.factory.get('/', HTTP_HOST='SCEPTRE.ICHEBO.ORG')
        self.middleware(request)
        self.assertEqual(request.site, 'community')


class TestSceptreAccessControl(TestCase):
    """Participant and steward gates, including the real 0a/visitor vs
    0b/seeker boundary (Doc J §5.1/§5.2, v1.3)."""

    def setUp(self):
        self.tenant = make_tenant()
        self.participant = make_user('part_h6', level=1, tenant=self.tenant, role='disciple')
        self.steward = make_user('stew_h6', level=3, tenant=self.tenant, role='branch-steward')
        # 0a/visitor — competence_level 0, no induction-tenant UserPermission at all.
        # accounts/signals.py auto-places every new user into the induction
        # tenant on creation, so a genuine 0a state must be simulated by
        # removing that auto-created UserPermission afterward — confirmed
        # against real dev data while building Task 3/4.
        self.visitor = make_user('visitor_h6', level=0)
        UserPermission.objects.filter(user=self.visitor, tenant__tier='induction').delete()
        # 0b/seeker — competence_level 0, but placed in an induction-tier tenant.
        self.induction_tenant = make_tenant(slug='induction-h6')
        self.induction_tenant.tier = 'induction'
        self.induction_tenant.save(update_fields=['tier'])
        self.seeker = make_user('seeker_h6', level=0, tenant=self.induction_tenant, role='seeker')
        self.client = Client()

    def test_participant_can_access_home(self):
        self.client.login(username='part_h6', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org', follow=True)
        self.assertNotEqual(response.status_code, 403)
        self.assertNotEqual(response.status_code, 500)

    def test_unauthenticated_redirected_to_login(self):
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 302)

    def test_visitor_0a_gets_403(self):
        """A pure visitor — no induction placement at all — must not
        reach this surface. Their front door is join.ichebo.org."""
        self.client.login(username='visitor_h6', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 403)

    def test_seeker_0b_can_access_home(self):
        """A seeker — placed in induction, competence_level still 0 —
        is the lowest level that should reach this surface."""
        self.client.login(username='seeker_h6', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org', follow=True)
        self.assertNotEqual(response.status_code, 403)
        self.assertNotEqual(response.status_code, 500)

    def test_steward_view_rejects_participant(self):
        self.client.login(username='part_h6', password='testpass123')
        response = self.client.get(
            '/steward/members/', HTTP_HOST='sceptre.ichebo.org'
        )
        self.assertEqual(response.status_code, 403)

    def test_steward_can_access_steward_view(self):
        self.client.login(username='stew_h6', password='testpass123')
        response = self.client.get(
            '/steward/members/', HTTP_HOST='sceptre.ichebo.org', follow=True
        )
        self.assertNotEqual(response.status_code, 403)

    def test_login_page_resolves_under_sceptre_urlconf(self):
        """sceptre/urls.py must include django.contrib.auth.urls itself —
        request.urlconf makes it the *root* resolver for sceptre.ichebo.org,
        so it doesn't inherit ics_project.urls' /accounts/login/ route.
        Found via a real browser session (force_login/c.login bypass this
        path entirely, which is exactly why it shipped broken initially)."""
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        login_url = response.get('Location')
        login_response = self.client.get(login_url, HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(login_response.status_code, 200)


class TestIsSteward(TestCase):
    """is_steward helper function."""

    def setUp(self):
        self.tenant = make_tenant(name='Stew T', slug='stewt')

    def test_level_3_is_steward(self):
        user = make_user('s_l3', level=3)
        self.assertTrue(is_steward(user))

    def test_level_1_not_steward(self):
        user = make_user('s_l1', level=1)
        self.assertFalse(is_steward(user))

    def test_level_1_with_steward_role_is_steward(self):
        user = make_user('s_role', level=1, tenant=self.tenant, role='branch-steward')
        self.assertTrue(is_steward(user))

    def test_level_1_with_admin_role_is_steward(self):
        """role__in=UserPermission.STEWARD_ROLES includes 'admin' — a
        role__endswith='-steward' suffix match would silently exclude it."""
        user = make_user('s_admin', level=1, tenant=self.tenant, role='admin')
        self.assertTrue(is_steward(user))


class TestParticipantHomeTemplate(TestCase):
    """Participant home renders without error."""

    def setUp(self):
        self.tenant = make_tenant(name='Home T', slug='homet')
        self.user = make_user('home_user', level=1, tenant=self.tenant, role='disciple')
        self.client = Client()

    def test_home_renders_200(self):
        self.client.login(username='home_user', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 200)

    def test_home_contains_quick_tiles(self):
        self.client.login(username='home_user', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertContains(response, 'Community')
        self.assertContains(response, 'Learn')
        self.assertContains(response, 'Bible')
        self.assertContains(response, 'Support')

    def test_offline_channel_state_renders(self):
        """No ChannelConfig/ChannelSlot/BroadcastSchedule configured for
        this tenant — resolve_now_playing falls through to offline."""
        self.client.login(username='home_user', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertContains(response, 'Channel offline')

    def test_steward_nav_hidden_from_participant(self):
        self.client.login(username='home_user', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        # Real template text is "Community Management" (title case) — CSS
        # text-transform: uppercase only changes the *display*, not the
        # underlying HTML assertContains checks. "Manage" is the trigger
        # button's own label and is the more direct signal either way.
        self.assertNotContains(response, 'Community Management')
        self.assertNotContains(response, 'Manage')

    def test_steward_nav_visible_to_steward(self):
        steward = make_user('home_stew', level=3, tenant=self.tenant, role='branch-steward')
        self.client.login(username='home_stew', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertContains(response, 'Community Management')
        self.assertContains(response, 'Manage')


class TestNowPlayingPartial(TestCase):
    """GET /now-playing/ — the HTMX-polled partial."""

    def setUp(self):
        self.tenant = make_tenant(name='Now Playing T', slug='nowplayingt')
        self.user = make_user('np_user', level=1, tenant=self.tenant, role='disciple')
        self.client = Client()

    def test_partial_returns_200(self):
        self.client.login(username='np_user', password='testpass123')
        response = self.client.get('/now-playing/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 200)

    def test_partial_requires_participant_gate(self):
        visitor = make_user('np_visitor', level=0)
        UserPermission.objects.filter(user=visitor, tenant__tier='induction').delete()
        self.client.login(username='np_visitor', password='testpass123')
        response = self.client.get('/now-playing/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 403)
