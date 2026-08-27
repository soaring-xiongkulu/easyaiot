import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.services.edge_media_spool_service import (
    enqueue_asset_report,
    enqueue_center_upload,
    enqueue_event_report,
    flush_pending_event_reports,
    flush_pending_reports,
    flush_pending_uploads,
    spool_status,
)


class EdgeMediaSpoolTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            'EDGE_MEDIA_SPOOL_DB': os.path.join(self.temp_dir.name, 'media-spool.db'),
            'MEDIA_ASSET_REPORT_URL': 'http://main/video/internal/media/assets/report-batch',
            'MEDIA_ASSET_UPLOAD_TICKET_URL': 'http://main/video/internal/media/assets/upload-ticket',
            'MEDIA_ASSET_UPLOAD_COMPLETE_URL': 'http://main/video/internal/media/assets/upload-complete',
            'MEDIA_INTERNAL_TOKEN': 'test-token',
            'COMPUTE_NODE_ID': '181',
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp_dir.cleanup()

    def _payload(self):
        return {
            'asset_id': '31825f9b-e30c-49ba-99a8-7de95b8c6f3a',
            'asset_type': 'recording_segment',
            'device_id': 'camera-001',
            'source_node_id': 181,
            'storage_node_id': 181,
            'storage_scope': 'edge',
            'storage_backend': 'local',
            'object_key': 'playbacks/live/camera-001/segment.flv',
            'status': 'ready',
        }

    @patch('app.services.edge_media_spool_service.requests.post')
    def test_successful_report_is_removed(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {'code': 0, 'data': []}
        post.return_value = response
        enqueue_asset_report(self._payload())
        self.assertEqual(1, spool_status()['pending_count'])
        result = flush_pending_reports()
        self.assertEqual(1, result['sent'])
        self.assertEqual(0, spool_status()['pending_count'])
        self.assertEqual('181', post.call_args.kwargs['headers']['X-Node-Id'])

    @patch('app.services.edge_media_spool_service.requests.post')
    def test_failed_report_stays_for_retry(self, post):
        post.side_effect = OSError('main offline')
        enqueue_asset_report(self._payload())
        result = flush_pending_reports()
        self.assertEqual(0, result['sent'])
        status = spool_status()
        self.assertEqual(1, status['pending_count'])
        self.assertGreaterEqual(status['retry_count'], 1)
        self.assertIn('main offline', status['last_error'])

    @patch('app.services.edge_media_spool_service.requests.put')
    @patch('app.services.edge_media_spool_service.requests.post')
    def test_event_media_upload_and_completion_are_reliable(self, post, put):
        media_path = os.path.join(self.temp_dir.name, 'event.jpg')
        with open(media_path, 'wb') as media_file:
            media_file.write(b'event-image')
        ticket = Mock()
        ticket.raise_for_status.return_value = None
        ticket.json.return_value = {'code': 0, 'data': {'upload_url': 'http://minio/upload'}}
        completed = Mock()
        completed.raise_for_status.return_value = None
        completed.json.return_value = {'code': 0, 'data': {'linked': True}}
        post.side_effect = [ticket, completed]
        put_response = Mock()
        put_response.raise_for_status.return_value = None
        put.return_value = put_response
        payload = {
            'asset_id': '0e650ca2-bb2a-4bf3-8465-92a106566f05',
            'asset_type': 'alert_image',
            'device_id': 'camera-001',
            'filename': 'event.jpg',
            'content_type': 'image/jpeg',
            'correlation_id': 'event-001',
        }
        enqueue_center_upload(payload, media_path)
        self.assertEqual(1, spool_status()['upload_pending_count'])
        result = flush_pending_uploads()
        self.assertEqual(1, result['sent'])
        self.assertEqual(0, spool_status()['upload_pending_count'])
        self.assertEqual('test-token', post.call_args_list[0].kwargs['headers']['X-Media-Internal-Token'])

    @patch('app.services.edge_media_spool_service.requests.post')
    def test_event_metadata_is_reported_idempotently(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {'code': 0, 'data': [{'alert_id': 1}]}
        post.return_value = response
        payload = {
            'correlation_id': 'event-001',
            'device_id': 'camera-001',
            'device_name': 'Camera 1',
            'object': 'person',
            'event': 'person',
            'image_path': '/edge/secret.jpg',
        }
        enqueue_event_report(payload)
        enqueue_event_report(payload)
        self.assertEqual(1, spool_status()['event_pending_count'])
        result = flush_pending_event_reports()
        self.assertEqual(1, result['sent'])
        sent = post.call_args.kwargs['json']['items'][0]
        self.assertIsNone(sent['image_path'])
        self.assertNotIn('/edge/', str(sent))


if __name__ == '__main__':
    unittest.main()
