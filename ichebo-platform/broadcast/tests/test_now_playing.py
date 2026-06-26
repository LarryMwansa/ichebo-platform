"""
Tests for Phase H.7 — Ichebo Channel.
Covers: now-playing resolution (all five fallback levels), the API
endpoint's auth/validation behaviour and response shape.
"""
import uuid
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from tenants.models import Tenant
from video_live.models import BroadcastSchedule

from broadcast.models import ChannelConfig, ChannelSlot
from broadcast.services import resolve_now_playing


def _make_user(email, level=1):
    return User.objects.create_user(
        username=email, email=email, password='Tr0ub4dor&3xample!', competence_level=level,
    )


def _make_tenant(slug, created_by):
    return Tenant.objects.create(
        name=f'Tenant {slug}', slug=slug, tier='church_node',
        path=f'/global/{slug}/', status='active', created_by=created_by,
    )


class TestNowPlayingResolution(TestCase):
    """resolve_now_playing — all five fallback levels, against real rows."""

    def setUp(self):
        self.user = _make_user('channel-owner@example.com', level=5)
        self.tenant = _make_tenant('channel-test', self.user)
        self.now = timezone.now()

    def test_offline_when_nothing_configured(self):
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'offline')
        self.assertEqual(result['source'], 'offline')
        self.assertIsNone(result['video_url'])

    def test_loop_default(self):
        video_id = uuid.uuid4()
        ChannelConfig.objects.create(
            tenant=self.tenant, loop_default_video_id=video_id,
            created_by=self.user,
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'vod')
        self.assertEqual(result['source'], 'loop')
        self.assertEqual(result['_video_id'], str(video_id))

    def test_fallback_playlist_rotation(self):
        v1, v2 = str(uuid.uuid4()), str(uuid.uuid4())
        config = ChannelConfig.objects.create(
            tenant=self.tenant, fallback_playlist=[v1, v2],
            fallback_position=0, created_by=self.user,
        )
        result1 = resolve_now_playing(self.tenant)
        self.assertEqual(result1['source'], 'fallback')
        self.assertEqual(result1['_video_id'], v1)

        config.refresh_from_db()
        self.assertEqual(config.fallback_position, 1)

        result2 = resolve_now_playing(self.tenant)
        self.assertEqual(result2['_video_id'], v2)

    def test_live_broadcast_overrides_fallback(self):
        ChannelConfig.objects.create(
            tenant=self.tenant, loop_default_video_id=uuid.uuid4(),
            created_by=self.user,
        )
        broadcast = BroadcastSchedule.objects.create(
            tenant=self.tenant, created_by=self.user, title='Test Live Service',
            scheduled_at=self.now, status='live',
            hls_url='https://media.ichebo.org/test-stream/index.m3u8',
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['source'], 'live')
        self.assertEqual(result['title'], 'Test Live Service')
        self.assertEqual(result['hls_url'], broadcast.hls_url)
        self.assertTrue(result['is_live'])

    def test_scheduled_slot_takes_priority_over_everything(self):
        ChannelConfig.objects.create(
            tenant=self.tenant, loop_default_video_id=uuid.uuid4(),
            created_by=self.user,
        )
        BroadcastSchedule.objects.create(
            tenant=self.tenant, created_by=self.user, title='Should Be Overridden',
            scheduled_at=self.now, status='live',
        )
        ChannelSlot.objects.create(
            tenant=self.tenant, title='Sunday Teaching', content_type='vod',
            scheduled_start=self.now - timedelta(minutes=30),
            scheduled_end=self.now + timedelta(minutes=30),
            created_by=self.user,
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['source'], 'scheduled')
        self.assertEqual(result['title'], 'Sunday Teaching')

    def test_past_slot_does_not_resolve(self):
        ChannelSlot.objects.create(
            tenant=self.tenant, title='Past Slot', content_type='vod',
            scheduled_start=self.now - timedelta(hours=2),
            scheduled_end=self.now - timedelta(hours=1),
            created_by=self.user,
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'offline')

    def test_future_slot_does_not_resolve(self):
        ChannelSlot.objects.create(
            tenant=self.tenant, title='Future Slot', content_type='vod',
            scheduled_start=self.now + timedelta(hours=1),
            scheduled_end=self.now + timedelta(hours=2),
            created_by=self.user,
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'offline')

    def test_soft_deleted_slot_is_excluded(self):
        """ChannelSlot uses SoftDeleteMixin — a deleted slot must not resolve,
        even if its scheduled window is currently active."""
        slot = ChannelSlot.objects.create(
            tenant=self.tenant, title='Deleted Slot', content_type='vod',
            scheduled_start=self.now - timedelta(minutes=10),
            scheduled_end=self.now + timedelta(minutes=10),
            created_by=self.user,
        )
        slot.soft_delete()
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'offline')


class TestNowPlayingAPIEndpoint(TestCase):
    """GET /api/broadcast/now/ — auth, validation, response shape."""

    def setUp(self):
        self.user = _make_user('api-channel-owner@example.com', level=5)
        self.tenant = _make_tenant('api-channel-test', self.user)
        self.client = Client()

    def test_requires_authentication(self):
        """DRF returns 403, not 401, here — confirmed directly against
        this project's REST_FRAMEWORK config: only SessionAuthentication
        and TokenAuthentication are configured, neither of which sets a
        WWW-Authenticate challenge header, so DRF's 401-vs-403 fallback
        rule lands on 403. (The original H.7 plan asserted 401 — checked
        against the real app and found that to be wrong before writing
        this test, rather than copying it.)"""
        url = reverse('broadcast-now-playing')
        response = self.client.get(url, {'tenant_id': str(self.tenant.id)})
        self.assertEqual(response.status_code, 403)

    def test_missing_tenant_id_returns_400(self):
        self.client.force_login(self.user)
        url = reverse('broadcast-now-playing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_unknown_tenant_id_returns_404(self):
        self.client.force_login(self.user)
        url = reverse('broadcast-now-playing')
        response = self.client.get(url, {'tenant_id': str(uuid.uuid4())})
        self.assertEqual(response.status_code, 404)

    def test_malformed_tenant_id_returns_404_not_500(self):
        self.client.force_login(self.user)
        url = reverse('broadcast-now-playing')
        response = self.client.get(url, {'tenant_id': 'not-a-real-uuid'})
        self.assertEqual(response.status_code, 404)

    def test_valid_request_returns_200_with_full_schema(self):
        self.client.force_login(self.user)
        url = reverse('broadcast-now-playing')
        response = self.client.get(url, {'tenant_id': str(self.tenant.id)})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for field in ['content_type', 'source', 'title', 'video_url',
                      'hls_url', 'is_live', 'thumbnail_url', 'ends_at',
                      'next_scheduled']:
            self.assertIn(field, data, f'Missing field: {field}')
        self.assertEqual(data['content_type'], 'offline')
