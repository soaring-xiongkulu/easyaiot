import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen


AGENT_PATH = Path(__file__).resolve().parents[1] / '.scripts' / 'media-cluster' / 'edge_media_agent.py'
SPEC = importlib.util.spec_from_file_location('easyaiot_edge_media_agent', AGENT_PATH)
agent_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent_module)


class EdgeMediaStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.store = agent_module.EdgeMediaStore(str(self.root))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dvr_is_durably_queued_and_serialized_for_control_plane(self):
        segment = self.root / 'playbacks' / 'device-a' / 'segment.mp4'
        segment.parent.mkdir(parents=True)
        segment.write_bytes(b'0123456789')

        created = self.store.add_dvr(
            {'stream': 'device-a', 'task_id': 7, 'file_path': str(segment), 'duration': 1.5},
            node_id=5,
            generation=3,
        )

        pending = self.store.pending()
        self.assertEqual(1, len(pending))
        report = self.store.as_report(pending[0], node_id=5, generation=3)
        self.assertEqual(created['asset_id'], report['asset_id'])
        self.assertEqual('device-a', report['device_id'])
        self.assertEqual('edge', report['storage_scope'])
        self.assertEqual('playbacks/device-a/segment.mp4', report['object_key'])
        self.assertEqual(1500, report['duration_ms'])
        self.assertEqual(10, report['file_size'])

        self.store.mark_reported([created['asset_id']])
        self.assertEqual(0, len(self.store.pending()))
        self.assertEqual({'reported': 1}, self.store.status()['asset_reports'])

    def test_container_path_is_mapped_to_configured_recording_root(self):
        segment = self.root / 'playbacks' / 'device-b' / 'segment.flv'
        segment.parent.mkdir(parents=True)
        segment.write_bytes(b'flv')

        resolved = self.store.resolve_srs_path('/mnt/easyaiot-media/playbacks/device-b/segment.flv')

        self.assertEqual(segment.resolve(), resolved)

    def test_path_outside_recording_root_is_rejected(self):
        with tempfile.NamedTemporaryFile() as outside:
            with self.assertRaises(ValueError):
                self.store.resolve_srs_path(outside.name)

    def test_alert_is_durably_queued_without_leaking_edge_paths(self):
        image = self.root / 'alert_images' / 'task_4' / 'event.jpg'
        image.parent.mkdir(parents=True)
        image.write_bytes(b'jpeg-data')

        queued = self.store.enqueue_alert(
            {
                'device_id': 'device-a',
                'task_id': 4,
                'task_type': 'realtime',
                'time': '2026-08-26T14:30:00Z',
                'correlation_id': 'edge-event-1',
                'image_path': str(image),
            },
            node_id=5,
            generation=2,
            pre_seconds=10,
            post_seconds=10,
            clip_settle_seconds=1,
        )

        self.assertEqual('edge-event-1', queued['correlation_id'])
        reports = self.store.pending_event_reports()
        self.assertEqual(1, len(reports))
        payload = json.loads(reports[0]['payload_json'])
        self.assertIsNone(payload['image_path'])
        self.assertIsNone(payload['record_path'])
        self.assertEqual(1, len(self.store.pending_uploads()))
        with self.store.connect() as conn:
            clip_count = conn.execute('SELECT COUNT(*) FROM event_clip_spool').fetchone()[0]
        self.assertEqual(1, clip_count)

    def test_missing_alert_image_does_not_drop_event(self):
        queued = self.store.enqueue_alert(
            {
                'device_id': 'device-a',
                'task_type': 'snap',
                'time': '2026-08-26T14:30:00Z',
                'correlation_id': 'edge-event-no-image',
                'image_path': str(self.root / 'already-cleaned.jpg'),
            },
            node_id=5,
            generation=2,
            pre_seconds=10,
            post_seconds=10,
            clip_settle_seconds=1,
        )

        self.assertEqual('edge-event-no-image', queued['correlation_id'])
        self.assertIsNone(queued['image_asset_id'])
        self.assertEqual(1, len(self.store.pending_event_reports()))


class EdgeMediaAuthTest(unittest.TestCase):
    def setUp(self):
        self.old_env = dict(os.environ)
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ.update({
            'EDGE_RECORDING_ROOT': self.temp_dir.name,
            'COMPUTE_NODE_ID': '5',
            'RECORDING_STORAGE_GENERATION': '2',
            'MEDIA_INTERNAL_TOKEN': 'test-token',
            'MEDIA_ASSET_REPORT_URL': 'http://127.0.0.1:9/report',
        })
        self.agent = agent_module.EdgeMediaAgent()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)
        self.temp_dir.cleanup()

    def test_internal_header_and_short_lived_signature_are_accepted(self):
        self.assertTrue(self.agent.authorized({'X-Media-Internal-Token': 'test-token'}))
        expires = int(agent_module.time.time()) + 60
        signature = agent_module.hmac.new(
            b'test-token', f'asset-1:{expires}'.encode(), agent_module.hashlib.sha256
        ).hexdigest()
        self.assertTrue(self.agent.authorized(
            {}, 'asset-1', {'expires': [str(expires)], 'signature': [signature]}
        ))
        self.assertFalse(self.agent.authorized(
            {}, 'asset-1', {'expires': [str(expires)], 'signature': ['bad']}
        ))

    def test_runtime_http_alert_hook_returns_success_and_queues_event(self):
        image = Path(self.temp_dir.name) / 'alert_images' / 'event.jpg'
        image.parent.mkdir(parents=True)
        image.write_bytes(b'jpeg-data')
        self.agent.flush_event_media_async = lambda: None
        server = agent_module.Server(('127.0.0.1', 0), self.agent)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            request = Request(
                f'http://127.0.0.1:{server.server_port}/video/alert/hook',
                data=json.dumps({
                    'device_id': 'device-a',
                    'task_id': 4,
                    'task_type': 'realtime',
                    'time': '2026-08-26T14:30:00Z',
                    'correlation_id': 'edge-event-http-1',
                    'image_path': str(image),
                }).encode(),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urlopen(request, timeout=5) as response:
                body = json.loads(response.read())
            self.assertEqual(200, response.status)
            self.assertEqual(0, body['code'])
            self.assertEqual('queued', body['data']['status'])
            self.assertEqual(1, len(self.agent.store.pending_event_reports()))
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
