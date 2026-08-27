import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from flask import Flask

from sqlalchemy import text

from models import Device, DeviceRecordingPolicy, MediaAsset, Playback, db
from app.services.edge_storage_maintenance_service import cleanup_edge_storage


class EdgeStorageMaintenanceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(self.temp_dir.name, 'db.sqlite')}",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.tables = [Device.__table__, DeviceRecordingPolicy.__table__, MediaAsset.__table__,
                       Playback.__table__]
        with self.app.app_context():
            db.metadata.create_all(db.engine, tables=self.tables)
            db.session.execute(text(
                'CREATE TABLE alert (id INTEGER PRIMARY KEY, record_asset_id VARCHAR(36))'
            ))
            db.session.add(Device(
                id='camera-cleanup', name='cleanup', source='rtsp://test',
                rtmp_stream='rtmp://test/live', http_stream='http://test/live.flv',
                manufacturer='test', model='test',
            ))
            db.session.add(DeviceRecordingPolicy(
                device_id='camera-cleanup', recording_mode='continuous', retention_hours=1,
                event_pre_seconds=10, event_post_seconds=20,
            ))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.session.execute(text('DROP TABLE IF EXISTS alert'))
            db.session.commit()
            db.metadata.drop_all(db.engine, tables=reversed(self.tables))
        self.temp_dir.cleanup()

    def test_expired_unprotected_segment_is_deleted(self):
        media_path = os.path.join(self.temp_dir.name, 'playbacks', 'old.flv')
        os.makedirs(os.path.dirname(media_path), exist_ok=True)
        with open(media_path, 'wb') as media_file:
            media_file.write(b'old-video')
        asset_id = 'ad706a55-b948-4109-858b-2fd7ed8976bf'
        with patch.dict(os.environ, {
            'RECORDING_STORAGE_MODE': 'edge_local',
            'EDGE_RECORDING_ROOT': self.temp_dir.name,
            'EDGE_MEDIA_SPOOL_DB': os.path.join(self.temp_dir.name, 'spool.db'),
        }):
            with self.app.app_context():
                db.session.add(MediaAsset(
                    id=asset_id,
                    asset_type='recording_segment',
                    device_id='camera-cleanup',
                    source_node_id=181,
                    storage_node_id=181,
                    storage_scope='edge',
                    storage_backend='local',
                    object_key='playbacks/old.flv',
                    status='ready',
                    start_time=datetime.now(timezone.utc) - timedelta(hours=2),
                    end_time=datetime.now(timezone.utc) - timedelta(hours=2) + timedelta(seconds=30),
                    file_size=9,
                ))
                db.session.commit()
                result = cleanup_edge_storage()
                self.assertEqual(1, result['deleted'])
                self.assertFalse(os.path.exists(media_path))
                self.assertEqual('deleted', MediaAsset.query.get(asset_id).status)


if __name__ == '__main__':
    unittest.main()
