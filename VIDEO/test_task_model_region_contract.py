import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.algo_mqtt_bus import (
    build_infer_event,
    inject_post_bypass_info,
    post_delivery_mode,
    post_fail_closed,
    post_failover_open,
    post_ingress_enabled,
    post_in_bypass,
    should_publish_infer_event,
)


class TaskModelRegionContractTest(unittest.TestCase):
    def test_legacy_region_migration_uses_join_table_task_id_column(self):
        run_source = (Path(__file__).resolve().parent / 'run.py').read_text(encoding='utf-8')
        unique_task_sql = run_source.split('WITH unique_task AS (', 1)[1].split('UPDATE device_detection_region', 1)[0]
        self.assertIn('MIN(task_id) AS task_id', unique_task_sql)
        self.assertIn('COUNT(DISTINCT task_id)', unique_task_sql)
        self.assertNotIn('algorithm_task_id', unique_task_sql)

    def test_region_hit_config_columns_and_legacy_backfill_are_migrated(self):
        run_source = (Path(__file__).resolve().parent / 'run.py').read_text(encoding='utf-8')
        self.assertIn("('hit_mode', 'VARCHAR(50)')", run_source)
        self.assertIn("('min_overlap_ratio', 'DOUBLE PRECISION')", run_source)
        self.assertIn('task.post_pipeline', run_source)
        self.assertIn("step.get('plugin') == 'region_gate'", run_source)

    def test_build_event_preserves_detection_model_ids(self):
        event = build_infer_event(
            task_id=1,
            task_type='realtime',
            device_id='cam',
            detections=[
                {'model_id': 11, 'bbox': [1, 2, 3, 4], 'class_name': 'person', 'confidence': 0.9},
                {'model_id': -1, 'bbox': [5, 6, 7, 8], 'class_name': 'car', 'confidence': 0.8},
            ],
            model_ids=[-1, 11],
        )
        self.assertEqual([11, -1], [item['model_id'] for item in event['detections']])

    def test_build_event_omits_unknown_model_instead_of_null(self):
        event = build_infer_event(
            task_id=1,
            task_type='realtime',
            device_id='cam',
            detections=[{'bbox': [1, 2, 3, 4], 'class_name': 'person', 'confidence': 0.9}],
        )
        self.assertNotIn('model_id', event['detections'][0])

    def test_build_event_omits_reserved_zero_model_id(self):
        event = build_infer_event(
            task_id=1,
            task_type='realtime',
            device_id='cam',
            detections=[{'model_id': 0, 'bbox': [1, 2, 3, 4], 'class_name': 'person'}],
            model_ids=[0, -1],
        )
        self.assertNotIn('model_id', event['detections'][0])
        self.assertEqual([-1], event['model_ids'])

    def test_post_ingress_is_independent_from_alert_transport(self):
        with patch.dict(os.environ, {
            'POST_ENABLED': 'true',
            'POST_INGRESS_TRANSPORT': 'mqtt',
            'POST_FAIL_STRATEGY': 'closed',
            'ALGO_BUS_TRANSPORT': 'http',
        }, clear=False), patch('app.utils.algo_mqtt_bus.post_is_ready', return_value=True):
            self.assertTrue(post_ingress_enabled())
            self.assertFalse(post_failover_open())
            self.assertTrue(should_publish_infer_event())

    def test_post_delivery_mode_matrix(self):
        cases = [
            ({'POST_ENABLED': 'false'}, True, 'direct'),
            ({'POST_ENABLED': 'true', 'POST_INGRESS_TRANSPORT': 'mqtt', 'POST_FAIL_STRATEGY': 'closed'}, True, 'infer'),
            ({'POST_ENABLED': 'true', 'POST_INGRESS_TRANSPORT': 'mqtt', 'POST_FAIL_STRATEGY': 'open'}, False, 'bypass'),
            ({'POST_ENABLED': 'true', 'POST_INGRESS_TRANSPORT': 'mqtt', 'POST_FAIL_STRATEGY': 'closed'}, False, 'drop'),
            ({'POST_ENABLED': 'true', 'POST_INGRESS_TRANSPORT': 'off', 'POST_FAIL_STRATEGY': 'open'}, True, 'bypass'),
            ({'POST_ENABLED': 'true', 'POST_INGRESS_TRANSPORT': 'off', 'POST_FAIL_STRATEGY': 'closed'}, True, 'drop'),
        ]
        for env, ready, expected in cases:
            with self.subTest(env=env, ready=ready), \
                    patch.dict(os.environ, env, clear=False), \
                    patch('app.utils.algo_mqtt_bus.post_is_ready', return_value=ready):
                self.assertEqual(expected, post_delivery_mode())
                self.assertEqual(expected == 'infer', should_publish_infer_event())
                self.assertEqual(expected == 'bypass', post_in_bypass())
                self.assertEqual(expected == 'drop', post_fail_closed())

    def test_fail_open_bypass_marker_is_explicit_and_preserves_information(self):
        output = inject_post_bypass_info({'information': '{"existing":1}'})
        info = __import__('json').loads(output['information'])
        self.assertEqual(1, info['existing'])
        self.assertIs(True, info['post_bypass'])
        self.assertEqual('post_unready', info['post_bypass_reason'])


if __name__ == '__main__':
    unittest.main()
