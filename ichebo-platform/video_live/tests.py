"""
video_live/tests.py

Tests for V2.7: _annotate_event logic (live/past/upcoming detection),
embed URL conversion, and the video home/schedule/watch views.
"""
from datetime import timedelta

from django.test import TestCase, Client
from django.utils import timezone

from accounts.models import User
from activity.models import Activity
from tenants.models import Tenant
from video_live.utils import get_embed_type, get_embed_url, get_youtube_id, get_vimeo_id
from video_live.views import _annotate_event, _event_qs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(email, level=1):
    u = User.objects.create_user(username=email, email=email, password='pass')
    u.competence_level = level
    u.save(update_fields=['competence_level'])
    return u


def _event(creator, title='Sunday Service', stream_url='https://youtu.be/dQw4w9WgXcQ',
           offset_minutes=0, duration=60, past=False):
    """
    Create an Activity event.
    offset_minutes > 0 → starts in the future
    offset_minutes < 0 → started in the past
    past=True → ended in the past (scheduled far enough back)
    """
    now = timezone.now()
    if past:
        start = now - timedelta(minutes=duration + 10)
    else:
        start = now + timedelta(minutes=offset_minutes)

    return Activity.objects.create(
        activity_type='event',
        title=title,
        scheduled_at=start,
        status='pending',
        created_by=creator,
        metadata={
            'stream_url': stream_url,
            'duration_minutes': duration,
            'source_app': 'video_live',
        },
    )


# ---------------------------------------------------------------------------
# Embed URL utilities
# ---------------------------------------------------------------------------

class EmbedTypeTests(TestCase):
    def test_youtube_watch_url(self):
        self.assertEqual(get_embed_type('https://www.youtube.com/watch?v=abc123'), 'youtube')

    def test_youtu_be_short_url(self):
        self.assertEqual(get_embed_type('https://youtu.be/abc123'), 'youtube')

    def test_youtube_live_url(self):
        self.assertEqual(get_embed_type('https://youtube.com/live/abc123'), 'youtube')

    def test_vimeo_url(self):
        self.assertEqual(get_embed_type('https://vimeo.com/123456789'), 'vimeo')

    def test_mp4_url(self):
        self.assertEqual(get_embed_type('https://cdn.example.com/video.mp4'), 'mp4')

    def test_unknown_url(self):
        self.assertEqual(get_embed_type('https://example.com/stream'), 'unknown')

    def test_none_returns_unknown(self):
        self.assertEqual(get_embed_type(None), 'unknown')

    def test_empty_string_returns_unknown(self):
        self.assertEqual(get_embed_type(''), 'unknown')


class EmbedUrlTests(TestCase):
    def test_youtube_watch_becomes_embed(self):
        url = get_embed_url('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        self.assertIn('youtube.com/embed/dQw4w9WgXcQ', url)

    def test_youtu_be_becomes_embed(self):
        url = get_embed_url('https://youtu.be/dQw4w9WgXcQ')
        self.assertIn('youtube.com/embed/dQw4w9WgXcQ', url)

    def test_vimeo_becomes_player(self):
        url = get_embed_url('https://vimeo.com/987654321')
        self.assertIn('player.vimeo.com/video/987654321', url)

    def test_mp4_returned_as_is(self):
        raw = 'https://cdn.example.com/sermon.mp4'
        self.assertEqual(get_embed_url(raw), raw)

    def test_unknown_returned_as_is(self):
        raw = 'https://example.com/stream'
        self.assertEqual(get_embed_url(raw), raw)


class YoutubeIdTests(TestCase):
    def test_watch_url(self):
        self.assertEqual(get_youtube_id('https://www.youtube.com/watch?v=abc123'), 'abc123')

    def test_short_url(self):
        self.assertEqual(get_youtube_id('https://youtu.be/abc123'), 'abc123')

    def test_embed_url(self):
        self.assertEqual(get_youtube_id('https://www.youtube.com/embed/abc123'), 'abc123')

    def test_live_url(self):
        self.assertEqual(get_youtube_id('https://youtube.com/live/abc123'), 'abc123')

    def test_invalid_returns_none(self):
        self.assertIsNone(get_youtube_id('https://example.com'))


# ---------------------------------------------------------------------------
# _annotate_event — live / past / upcoming detection
# ---------------------------------------------------------------------------

class AnnotateEventTests(TestCase):
    def setUp(self):
        self.creator = _user('creator@example.com')

    def test_upcoming_event_is_not_live_not_past(self):
        ev = _event(self.creator, offset_minutes=60)
        result = _annotate_event(ev)
        self.assertFalse(result['is_live'])
        self.assertFalse(result['is_past'])

    def test_currently_broadcasting_event_is_live(self):
        # Started 10 minutes ago, duration 60 min → currently live
        ev = _event(self.creator, offset_minutes=-10, duration=60)
        result = _annotate_event(ev)
        self.assertTrue(result['is_live'])
        self.assertFalse(result['is_past'])

    def test_finished_event_is_past(self):
        ev = _event(self.creator, past=True, duration=60)
        result = _annotate_event(ev)
        self.assertFalse(result['is_live'])
        self.assertTrue(result['is_past'])

    def test_event_starting_right_now_is_live(self):
        # scheduled_at is now — should be inside the window
        ev = _event(self.creator, offset_minutes=0, duration=60)
        result = _annotate_event(ev)
        self.assertTrue(result['is_live'])

    def test_annotate_returns_correct_embed_url(self):
        ev = _event(self.creator, stream_url='https://youtu.be/abc123')
        result = _annotate_event(ev)
        self.assertIn('youtube.com/embed/abc123', result['embed_url'])
        self.assertEqual(result['embed_type'], 'youtube')

    def test_annotate_returns_duration(self):
        ev = _event(self.creator, duration=90)
        result = _annotate_event(ev)
        self.assertEqual(result['duration'], 90)

    def test_annotate_returns_id_and_title(self):
        ev = _event(self.creator, title='Midweek Service')
        result = _annotate_event(ev)
        self.assertEqual(result['id'], ev.id)
        self.assertEqual(result['title'], 'Midweek Service')

    def test_event_without_scheduled_at_is_neither_live_nor_past(self):
        ev = Activity.objects.create(
            activity_type='event', title='No Date',
            created_by=self.creator, status='pending',
            metadata={'stream_url': 'https://youtu.be/abc', 'duration_minutes': 60},
        )
        result = _annotate_event(ev)
        self.assertFalse(result['is_live'])
        self.assertFalse(result['is_past'])


# ---------------------------------------------------------------------------
# _event_qs — query filter
# ---------------------------------------------------------------------------

class EventQuerysetTests(TestCase):
    def setUp(self):
        self.creator = _user('creator@example.com')

    def test_excludes_events_without_stream_url(self):
        Activity.objects.create(
            activity_type='event', title='No Stream',
            created_by=self.creator, status='pending',
            metadata={},
        )
        self.assertEqual(_event_qs().count(), 0)

    def test_excludes_deleted_events(self):
        ev = _event(self.creator)
        ev.deleted_at = timezone.now()
        ev.save(update_fields=['deleted_at'])
        self.assertEqual(_event_qs().count(), 0)

    def test_excludes_non_event_activities(self):
        Activity.objects.create(
            activity_type='task', title='A Task',
            created_by=self.creator, status='pending',
            metadata={'stream_url': 'https://youtu.be/abc'},
        )
        self.assertEqual(_event_qs().count(), 0)

    def test_includes_valid_events(self):
        _event(self.creator, title='Event 1')
        _event(self.creator, title='Event 2', offset_minutes=120)
        self.assertEqual(_event_qs().count(), 2)

    def test_no_tenant_arg_returns_all_tenants_unscoped(self):
        """Default (no tenant passed) preserves existing global behaviour for
        the steward-facing schedule/VOD/manage views."""
        tenant_a = Tenant.objects.create(
            name='T1', slug='video-t1', tier='church_node', path='/global/video-t1/',
            status='active', created_by=self.creator,
        )
        tenant_b = Tenant.objects.create(
            name='T2', slug='video-t2', tier='church_node', path='/global/video-t2/',
            status='active', created_by=self.creator,
        )
        ev_a = _event(self.creator, title='A')
        ev_a.tenant = tenant_a
        ev_a.save(update_fields=['tenant'])
        ev_b = _event(self.creator, title='B')
        ev_b.tenant = tenant_b
        ev_b.save(update_fields=['tenant'])

        self.assertEqual(_event_qs().count(), 2)

    def test_tenant_arg_scopes_to_that_tenant_only(self):
        tenant_a = Tenant.objects.create(
            name='T3', slug='video-t3', tier='church_node', path='/global/video-t3/',
            status='active', created_by=self.creator,
        )
        tenant_b = Tenant.objects.create(
            name='T4', slug='video-t4', tier='church_node', path='/global/video-t4/',
            status='active', created_by=self.creator,
        )
        ev_a = _event(self.creator, title='A')
        ev_a.tenant = tenant_a
        ev_a.save(update_fields=['tenant'])
        ev_b = _event(self.creator, title='B')
        ev_b.tenant = tenant_b
        ev_b.save(update_fields=['tenant'])

        scoped = _event_qs(tenant=tenant_a)
        self.assertEqual(scoped.count(), 1)
        self.assertEqual(scoped.first().title, 'A')


# ---------------------------------------------------------------------------
# View tests — HTTP responses
# ---------------------------------------------------------------------------

class VideoViewTests(TestCase):
    def setUp(self):
        self.user = _user('viewer@example.com', level=1)
        self.client = Client()
        self.client.login(username='viewer@example.com', password='pass')

    def test_home_returns_200(self):
        response = self.client.get('/video/')
        self.assertEqual(response.status_code, 200)

    def test_live_returns_200(self):
        response = self.client.get('/video/live/')
        self.assertEqual(response.status_code, 200)

    def test_schedule_returns_200(self):
        response = self.client.get('/video/schedule/')
        self.assertEqual(response.status_code, 200)

    def test_vod_returns_200(self):
        response = self.client.get('/video/vod/')
        self.assertEqual(response.status_code, 200)

    def test_watch_returns_200_for_valid_event(self):
        ev = _event(self.user)
        response = self.client.get(f'/video/watch/{ev.id}/')
        self.assertEqual(response.status_code, 200)

    def test_watch_returns_404_for_deleted_event(self):
        ev = _event(self.user)
        ev.deleted_at = timezone.now()
        ev.save(update_fields=['deleted_at'])
        response = self.client.get(f'/video/watch/{ev.id}/')
        self.assertEqual(response.status_code, 404)

    def test_manage_redirects_level_1_user(self):
        response = self.client.get('/video/manage/')
        self.assertEqual(response.status_code, 302)

    def test_manage_accessible_to_level_3(self):
        steward = _user('steward@example.com', level=3)
        self.client.login(username='steward@example.com', password='pass')
        response = self.client.get('/video/manage/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_redirects_to_login(self):
        self.client.logout()
        response = self.client.get('/video/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_home_shows_live_event_in_context(self):
        ev = _event(self.user, title='Live Now', offset_minutes=-10, duration=60)
        response = self.client.get('/video/')
        live_ids = [e['id'] for e in response.context['live']]
        self.assertIn(ev.id, live_ids)

    def test_home_shows_upcoming_event_in_context(self):
        ev = _event(self.user, title='Coming Up', offset_minutes=120)
        response = self.client.get('/video/')
        upcoming_ids = [e['id'] for e in response.context['upcoming']]
        self.assertIn(ev.id, upcoming_ids)

    def test_home_shows_past_event_in_vod(self):
        ev = _event(self.user, title='Past Service', past=True)
        response = self.client.get('/video/')
        vod_ids = [e['id'] for e in response.context['recent_vod']]
        self.assertIn(ev.id, vod_ids)
