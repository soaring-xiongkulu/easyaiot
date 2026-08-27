import os
import tempfile
import unittest
from datetime import datetime
from urllib.parse import urlsplit
from unittest.mock import Mock, patch

from flask import Flask

from models import db, Device, DeviceRecordingPolicy, MediaAsset, RecordFile, RecordSpace
from app.blueprints.media_asset import media_asset_bp
from app.services.media_asset_service import normalize_object_key, upsert_media_asset
from app.services.edge_event_media_service import prepare_edge_event_media
from app.services.space_file_metadata_service import upsert_record_file


class MediaAssetControlPlaneTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = os.path.join(self.temp_dir.name, 'video-test.db')
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{database_path}',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(media_asset_bp, url_prefix='/video')
        with self.app.app_context():
            db.metadata.create_all(db.engine, tables=[
                Device.__table__,
                RecordSpace.__table__,
                DeviceRecordingPolicy.__table__,
                MediaAsset.__table__,
                RecordFile.__table__,
            ])
            db.session.add(Device(
                id='camera-001',
                name='Camera 1',
                source='rtsp://camera/live',
                rtmp_stream='rtmp://main/live/camera-001',
                http_stream='http://main/live/camera-001.flv',
                manufacturer='test',
                model='test',
            ))
            db.session.add(RecordSpace(
                space_name='Camera 1',
                space_code='record-camera-001',
                bucket_name='record-camera-001',
                device_id='camera-001',
            ))
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.metadata.drop_all(db.engine, tables=[
                RecordFile.__table__,
                MediaAsset.__table__,
                DeviceRecordingPolicy.__table__,
                RecordSpace.__table__,
                Device.__table__,
            ])
        self.temp_dir.cleanup()

    def test_policy_defaults_and_update(self):
        response = self.client.get('/video/recording/policies/camera-001')
        self.assertEqual(200, response.status_code)
        self.assertEqual('continuous', response.get_json()['data']['recording_mode'])
        self.assertEqual('central_shared', response.get_json()['data']['effective_storage']['mode'])

        response = self.client.put('/video/recording/policies/camera-001', json={
            'recording_mode': 'event_only',
            'retention_hours': 72,
            'event_pre_seconds': 15,
            'event_post_seconds': 30,
            'playback_route_mode': 'proxy',
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual(72, response.get_json()['data']['retention_hours'])
        with self.app.app_context():
            self.assertEqual(72, RecordSpace.query.filter_by(device_id='camera-001').first().save_time)

    def test_existing_record_file_registers_central_asset(self):
        with self.app.app_context():
            space = RecordSpace.query.filter_by(device_id='camera-001').first()
            record = upsert_record_file(
                space_id=space.id,
                device_id='camera-001',
                object_name='camera-001/2026/08/26/segment.mp4',
                bucket_name=space.bucket_name,
                duration=37,
                event_time=datetime(2026, 8, 26, 8, 0, 0),
                file_size=1024,
            )
            self.assertIsNotNone(record.asset_id)
            asset = MediaAsset.query.get(record.asset_id)
            self.assertEqual('central', asset.storage_scope)
            self.assertEqual(37000, asset.duration_ms)
            self.assertEqual('ready', asset.status)
            self.assertEqual(0, asset.start_time.hour)

        response = self.client.get('/video/recording/assets', query_string={'device_id': 'camera-001'})
        self.assertEqual(200, response.status_code)
        item = response.get_json()['data'][0]
        self.assertEqual('/video/media/assets/' + item['asset_id'] + '/content', item['play_url'])
        self.assertNotIn('object_key', item)

    def test_edge_asset_idempotency_and_path_rejection(self):
        payload = {
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
        with self.app.app_context():
            upsert_media_asset(payload, authenticated_node_id=181)
            upsert_media_asset({**payload, 'file_size': 2048}, authenticated_node_id=181)
            self.assertEqual(1, MediaAsset.query.filter_by(id=payload['asset_id']).count())
            self.assertEqual(2048, MediaAsset.query.get(payload['asset_id']).file_size)
        with self.assertRaises(ValueError):
            normalize_object_key('../../etc/passwd')
        with self.assertRaises(ValueError):
            normalize_object_key('/mnt/edge/segment.mp4')

    def test_direct_edge_playback_uses_short_lived_signature(self):
        asset_id = '2a864dbc-497f-4e9f-9a66-8c7dc33fac0d'
        object_key = 'playbacks/live/camera-001/direct.flv'
        target = os.path.join(self.temp_dir.name, object_key)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'wb') as media_file:
            media_file.write(b'edge-video')
        with self.app.app_context():
            policy = DeviceRecordingPolicy(
                device_id='camera-001',
                recording_mode='continuous',
                retention_hours=168,
                playback_route_mode='direct',
            )
            db.session.add(policy)
            upsert_media_asset({
                'asset_id': asset_id,
                'asset_type': 'recording_segment',
                'device_id': 'camera-001',
                'source_node_id': 181,
                'storage_node_id': 181,
                'storage_scope': 'edge',
                'storage_backend': 'local',
                'object_key': object_key,
                'status': 'ready',
                'content_type': 'video/x-flv',
            }, authenticated_node_id=181)

        with patch.dict(os.environ, {
            'MEDIA_INTERNAL_TOKEN': 'unit-test-secret',
            'EDGE_RECORDING_ROOT': self.temp_dir.name,
        }), patch('app.blueprints.media_asset.get_node', return_value={
            'status': 'online',
            'mediaPublicUrl': 'http://edge.example:6000',
        }):
            response = self.client.get(f'/video/media/assets/{asset_id}/content')
            self.assertEqual(302, response.status_code)
            location = response.headers['Location']
            self.assertIn('signature=', location)
            signed_path = urlsplit(location)
            edge_response = self.client.get(signed_path.path + '?' + signed_path.query)
            self.assertEqual(200, edge_response.status_code)
            self.assertEqual(b'edge-video', edge_response.data)

            tampered = self.client.get(
                signed_path.path + '?' + signed_path.query.replace('signature=', 'signature=bad'),
            )
            self.assertEqual(403, tampered.status_code)

    def test_event_upload_ticket_creates_central_pending_asset(self):
        minio = Mock()
        minio.bucket_exists.return_value = True
        minio.presigned_put_object.return_value = 'http://minio.example/signed-put'
        asset_id = 'bc4a5fb2-2504-49d5-8edf-e8b00d204990'
        with patch.dict(os.environ, {'MEDIA_INTERNAL_TOKEN': 'unit-test-secret'}), \
                patch('app.blueprints.media_asset.get_node', return_value={'status': 'online'}), \
                patch('app.blueprints.media_asset._event_minio_client', return_value=minio):
            response = self.client.post(
                '/video/internal/media/assets/upload-ticket',
                headers={
                    'X-Node-Id': '181',
                    'X-Media-Internal-Token': 'unit-test-secret',
                },
                json={
                    'asset_id': asset_id,
                    'asset_type': 'alert_image',
                    'device_id': 'camera-001',
                    'filename': 'alert.jpg',
                    'content_type': 'image/jpeg',
                },
            )
        self.assertEqual(200, response.status_code)
        self.assertEqual('http://minio.example/signed-put', response.get_json()['data']['upload_url'])
        with self.app.app_context():
            asset = MediaAsset.query.get(asset_id)
            self.assertEqual('central', asset.storage_scope)
            self.assertEqual('uploading', asset.status)
            self.assertEqual(181, asset.source_node_id)

    def test_edge_alert_image_is_registered_and_queued_without_blocking_event(self):
        image_path = os.path.join(self.temp_dir.name, 'alert_images', 'event.jpg')
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, 'wb') as image_file:
            image_file.write(b'jpeg-data')
        with patch.dict(os.environ, {
            'RECORDING_STORAGE_MODE': 'edge_local',
            'COMPUTE_NODE_ID': '181',
            'EDGE_RECORDING_ROOT': self.temp_dir.name,
            'ALERT_IMAGES_DIR': os.path.dirname(image_path),
            'EDGE_MEDIA_SPOOL_DB': os.path.join(self.temp_dir.name, 'edge-spool.db'),
        }), patch('app.services.edge_event_media_service.flush_pending_uploads_async'), \
                patch('app.services.edge_event_media_service.flush_pending_event_reports_async'):
            with self.app.app_context():
                data = prepare_edge_event_media({
                    'device_id': 'camera-001',
                    'task_type': 'snap',
                    'time': '2026-08-26T08:00:00+00:00',
                    'image_path': image_path,
                })
                self.assertTrue(data.get('correlation_id'))
                asset = MediaAsset.query.get(data['_edge_image_asset_id'])
                self.assertEqual('edge', asset.storage_scope)
                self.assertEqual('alert_image', asset.asset_type)


if __name__ == '__main__':
    unittest.main()
