from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from accounts.models import User
from records.models import Record

from .engine_client import post_with_retry
from .models import TranscodeJob
from .tasks import reconcile_stuck_transcode_jobs, reconcile_transcode_job


def _make_user(email='media-test@example.com'):
    return User.objects.create_user(username=email, email=email, password='Tr0ub4dor&3xample!')


class PostWithRetryTests(TestCase):

    @patch('media.engine_client.time.sleep')
    @patch('media.engine_client.requests.post')
    def test_succeeds_on_first_attempt_no_sleep(self, mock_post, mock_sleep):
        mock_post.return_value = Mock(status_code=200, raise_for_status=lambda: None)
        resp = post_with_retry('http://engine/x')
        self.assertEqual(mock_post.call_count, 1)
        mock_sleep.assert_not_called()
        self.assertIsNotNone(resp)

    @patch('media.engine_client.time.sleep')
    @patch('media.engine_client.requests.post')
    def test_retries_then_succeeds(self, mock_post, mock_sleep):
        ok = Mock(status_code=200, raise_for_status=lambda: None)
        mock_post.side_effect = [requests.ConnectionError('boom'), ok]
        resp = post_with_retry('http://engine/x')
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once()
        self.assertIsNotNone(resp)

    @patch('media.engine_client.time.sleep')
    @patch('media.engine_client.requests.post')
    def test_raises_after_max_attempts(self, mock_post, mock_sleep):
        mock_post.side_effect = requests.ConnectionError('boom')
        with self.assertRaises(requests.ConnectionError):
            post_with_retry('http://engine/x')
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)


class ReconcileTranscodeJobTests(TestCase):

    def setUp(self):
        self.user = _make_user()
        self.record = Record.objects.create(
            created_by=self.user,
            record_class='organizational',
            record_family='media',
            record_type='teaching_video',
            title='Sermon',
            status='draft',
            custom_fields={'transcoding_status': 'processing'},
        )
        self.job = TranscodeJob.objects.create(
            record=self.record, job_id='engine-job-123', status='processing',
        )

    @patch('media.tasks.requests.get')
    def test_reconciles_completed_job_from_engine_poll(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {
                'status': 'complete', 'progress_pct': 100,
                'video_url': 'https://cdn/x/index.m3u8',
                'thumbnail_url': 'https://cdn/x/thumb.jpg',
                'duration_seconds': 120,
            },
        )
        reconcile_transcode_job(str(self.job.id))

        self.job.refresh_from_db()
        self.record.refresh_from_db()
        self.assertEqual(self.job.status, 'complete')
        self.assertEqual(self.record.status, 'active')
        self.assertEqual(self.record.custom_fields['video_url'], 'https://cdn/x/index.m3u8')
        self.assertEqual(self.record.custom_fields['duration_seconds'], 120)

    @patch('media.tasks.requests.get')
    def test_leaves_still_processing_job_untouched(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200, raise_for_status=lambda: None,
            json=lambda: {'status': 'processing', 'progress_pct': 40},
        )
        reconcile_transcode_job(str(self.job.id))

        self.job.refresh_from_db()
        self.record.refresh_from_db()
        self.assertEqual(self.job.status, 'processing')
        self.assertEqual(self.record.status, 'draft')

    @patch('media.tasks.requests.get')
    def test_job_not_found_on_engine_leaves_record_untouched(self, mock_get):
        mock_get.return_value = Mock(status_code=404)
        reconcile_transcode_job(str(self.job.id))

        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'draft')

    @patch('media.tasks.reconcile_transcode_job.delay')
    def test_finds_only_stuck_draft_jobs(self, mock_delay):
        from django.utils import timezone
        # Make this job look old enough to count as stuck.
        TranscodeJob.objects.filter(id=self.job.id).update(
            created_at=timezone.now() - timezone.timedelta(minutes=10)
        )
        reconcile_stuck_transcode_jobs()
        mock_delay.assert_called_once_with(str(self.job.id))
