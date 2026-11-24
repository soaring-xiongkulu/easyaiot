#!/usr/bin/env python3
import unittest
from datetime import datetime, timedelta, timezone

from flask import Flask

from app.services import edge_compute_service
from models import EdgeComputeCommand, EdgeComputeMetric, EdgeComputeNode, db


class EdgeComputeServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI='sqlite://',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.metadata.create_all(db.engine, tables=[
            EdgeComputeNode.__table__,
            EdgeComputeMetric.__table__,
            EdgeComputeCommand.__table__,
        ])

    def tearDown(self):
        db.session.remove()
        db.metadata.drop_all(db.engine, tables=[
            EdgeComputeCommand.__table__,
            EdgeComputeMetric.__table__,
            EdgeComputeNode.__table__,
        ])
        self.context.pop()

    def test_enrollment_does_not_reissue_enabled_node_secret(self):
        first = edge_compute_service.enroll_node({
            'fingerprint': 'rk3588-fingerprint',
            'name': 'rk3588-01',
            'socModel': 'RK3588',
        })
        with self.assertRaisesRegex(FileExistsError, '已纳管'):
            edge_compute_service.enroll_node({
                'fingerprint': 'rk3588-fingerprint',
                'name': 'impersonator',
            })

        repeated = edge_compute_service.enroll_node({
            'fingerprint': 'rk3588-fingerprint',
            'agentToken': first['agentToken'],
        })
        self.assertFalse(repeated['created'])
        self.assertEqual(repeated['agentToken'], first['agentToken'])

    def test_disabled_node_can_reenroll_with_rotated_secret(self):
        first = edge_compute_service.enroll_node({'fingerprint': 'box-reinstalled'})
        edge_compute_service.delete_node(first['nodeId'])
        recovered = edge_compute_service.enroll_node({'fingerprint': 'box-reinstalled'})
        self.assertEqual(recovered['nodeId'], first['nodeId'])
        self.assertNotEqual(recovered['agentToken'], first['agentToken'])

    def test_status_filter_uses_heartbeat_window_for_items_and_total(self):
        now = datetime.now(timezone.utc)
        online = EdgeComputeNode(
            fingerprint='online', name='online', mqtt_username='edge-node-1',
            mqtt_client_id='easyaiot-edge-1', agent_token='a', status='online',
            last_heartbeat_at=now,
        )
        stale = EdgeComputeNode(
            fingerprint='stale', name='stale', mqtt_username='edge-node-2',
            mqtt_client_id='easyaiot-edge-2', agent_token='b', status='online',
            last_heartbeat_at=now - timedelta(seconds=edge_compute_service.OFFLINE_AFTER_SECONDS + 1),
        )
        db.session.add_all((online, stale))
        db.session.commit()

        online_page = edge_compute_service.list_nodes(status='online')
        offline_page = edge_compute_service.list_nodes(status='offline')
        self.assertEqual(online_page['total'], 1)
        self.assertEqual([item['name'] for item in online_page['list']], ['online'])
        self.assertEqual(offline_page['total'], 1)
        self.assertEqual([item['name'] for item in offline_page['list']], ['stale'])


if __name__ == '__main__':
    unittest.main()
