"""同一摄像头多算法任务隔离规则测试。"""
import ast
import math
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

try:
    import numpy  # noqa: F401
except ModuleNotFoundError:
    # 追踪器在本用例中只使用 sqrt，允许在轻量测试环境中运行。
    sys.modules['numpy'] = types.SimpleNamespace(sqrt=math.sqrt)

try:
    import requests  # noqa: F401
except ModuleNotFoundError:
    # 本用例只验证异步失败回调，不发起真实 HTTP 请求。
    sys.modules['requests'] = types.SimpleNamespace()

from app.utils.algorithm_task_identity import (
    AmbiguousAlgorithmTaskError,
    build_alert_event_groups,
    build_alert_suppression_key,
    build_task_stream_key,
    claim_due_alert_event_identities,
    parse_task_stream_key,
    resolve_alert_event_identity,
    rewrite_task_stream_url,
    select_unique_legacy_alert_task,
    should_reload_algorithm_models,
)
from app.utils.alert_images_paths import build_alert_image_filename
from app.utils.post_process_runner import build_task_context
from app.utils.parallel_inference_observability import (
    build_parallel_inference_evidence,
    build_shared_source_topology_evidence,
    format_observability_event,
)
from app.services import post_process_sink_client
from services.realtime_algorithm_service.app.utils.tracker import SimpleTracker


class TestMultiAlgorithmTaskIsolation(unittest.TestCase):
    """验证任务流和告警抑制均包含任务维度。"""

    def test_realtime_worker_defines_instance_id_for_inference_evidence(self):
        source_path = (
            Path(__file__).parent
            / 'services'
            / 'realtime_algorithm_service'
            / 'run_deploy.py'
        )
        module = ast.parse(source_path.read_text(encoding='utf-8'))
        assigned_names = {
            target.id
            for node in ast.walk(module)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            if isinstance(target, ast.Name)
        }

        self.assertIn('WORKER_INSTANCE', assigned_names)

    def test_same_device_uses_distinct_task_stream_keys(self):
        task_a = build_task_stream_key(101, 'CAM-001')
        task_b = build_task_stream_key(202, 'CAM-001')

        self.assertEqual(task_a, 't101_CAM-001')
        self.assertEqual(task_b, 't202_CAM-001')
        self.assertNotEqual(task_a, task_b)

    def test_task_stream_url_keeps_protocol_and_uses_task_key(self):
        rtmp_url = rewrite_task_stream_url(
            'rtmp://video.example:1935/ai/CAM-001',
            202,
            'CAM-001',
        )
        http_url = rewrite_task_stream_url(
            'http://video.example:8080/ai/CAM-001.flv',
            202,
            'CAM-001',
        )

        self.assertEqual(rtmp_url, 'rtmp://video.example:1935/ai/t202_CAM-001')
        self.assertEqual(http_url, 'http://video.example:8080/ai/t202_CAM-001.flv')

    def test_special_device_id_generates_stable_safe_key(self):
        first = build_task_stream_key(202, '厂区入口/一号')
        second = build_task_stream_key(202, '厂区入口/一号')

        self.assertEqual(first, second)
        self.assertRegex(first, r'^t202_[A-Za-z0-9._-]+_[0-9a-f]{8}$')

    def test_task_stream_key_exposes_task_identity(self):
        self.assertEqual(parse_task_stream_key('t202_CAM-001'), (202, 'CAM-001'))
        self.assertEqual(parse_task_stream_key('CAM-001'), (None, None))

    def test_alert_suppression_key_isolated_by_task(self):
        task_a = build_alert_suppression_key(101, 'CAM-001', 'realtime')
        task_b = build_alert_suppression_key(202, 'CAM-001', 'realtime')

        self.assertEqual(task_a, ('101', 'CAM-001', 'realtime'))
        self.assertEqual(task_b, ('202', 'CAM-001', 'realtime'))
        self.assertNotEqual(task_a, task_b)

    def test_alert_suppression_key_isolated_by_model_and_class(self):
        person = build_alert_suppression_key(
            101,
            'CAM-001',
            'realtime',
            event_identity='1:person',
        )
        detection = build_alert_suppression_key(
            101,
            'CAM-001',
            'realtime',
            event_identity='32:detection',
        )

        self.assertNotEqual(person, detection)

    def test_due_event_claims_do_not_cross_suppress_models(self):
        state = {('CAM-001', '1:person'): 99.0}

        claimed = claim_due_alert_event_identities(
            state,
            'CAM-001',
            ['1:person', '32:detection'],
            current_time=100.0,
            suppress_interval=5.0,
        )

        self.assertEqual(claimed, ['32:detection'])
        self.assertEqual(state[('CAM-001', '32:detection')], 100.0)

    def test_alert_event_groups_split_models_and_remove_duplicate_tracks(self):
        groups = build_alert_event_groups([
            {
                'model_id': 1,
                'track_id': 7,
                'class_name': 'person',
                'bbox': [1, 2, 30, 40],
                'confidence': 0.91,
                'is_cached': False,
            },
            {
                'model_id': 1,
                'track_id': 7,
                'class_name': 'person',
                'bbox': [1, 2, 30, 40],
                'confidence': 0.91,
                'is_cached': True,
            },
            {
                'model_id': 32,
                'track_id': 8,
                'class_name': 'detection',
                'bbox': [50, 60, 90, 100],
                'confidence': 0.73,
                'is_cached': False,
            },
        ])

        self.assertEqual(list(groups), ['1:person', '32:detection'])
        self.assertEqual(len(groups['1:person']), 1)
        self.assertEqual(len(groups['32:detection']), 1)

    def test_alert_event_groups_normalize_equivalent_class_names(self):
        groups = build_alert_event_groups([
            {'model_id': 1, 'class_name': 'Safety Helmet', 'bbox': [1, 2, 3, 4]},
            {'model_id': 1, 'class_name': 'safety-helmet', 'bbox': [5, 6, 7, 8]},
        ])

        self.assertEqual(list(groups), ['1:safety_helmet'])

    def test_legacy_alert_resolves_model_class_identity(self):
        identity = resolve_alert_event_identity({
            'object': 'person',
            'model_ids': [1],
        })

        self.assertEqual(identity, '1:person')

    def test_snapshot_task_type_is_normalized(self):
        key = build_alert_suppression_key(202, 'CAM-001', 'snapshot')

        self.assertEqual(key, ('202', 'CAM-001', 'snap'))

    def test_legacy_alert_can_resolve_only_one_candidate_task(self):
        candidate = {'task_id': 101}

        resolved = select_unique_legacy_alert_task([candidate], 'CAM-001', 'realtime')

        self.assertIs(resolved, candidate)

    def test_legacy_alert_rejects_ambiguous_candidate_tasks(self):
        with self.assertRaises(AmbiguousAlgorithmTaskError):
            select_unique_legacy_alert_task(
                [{'task_id': 101}, {'task_id': 202}],
                'CAM-001',
                'realtime',
            )

    def test_tracker_keeps_model_identity_for_overlapping_boxes(self):
        tracker = SimpleTracker(similarity_threshold=0.1)
        first_frame = tracker.update([
            {'model_id': 11, 'bbox': [0, 0, 100, 100], 'class_id': 0, 'class_name': 'person', 'confidence': 0.9},
            {'model_id': 22, 'bbox': [0, 0, 100, 100], 'class_id': 0, 'class_name': 'helmet', 'confidence': 0.8},
        ], 1, current_time=1.0)
        second_frame = tracker.update([
            {'model_id': 22, 'bbox': [1, 1, 101, 101], 'class_id': 0, 'class_name': 'helmet', 'confidence': 0.85},
            {'model_id': 11, 'bbox': [1, 1, 101, 101], 'class_id': 0, 'class_name': 'person', 'confidence': 0.95},
        ], 2, current_time=2.0)

        first_ids = {item['model_id']: item['track_id'] for item in first_frame}
        second_ids = {
            item['model_id']: item['track_id']
            for item in second_frame
            if not item['is_cached']
        }
        self.assertEqual(first_ids, second_ids)

    def test_tracker_returns_new_detection_only_once(self):
        tracker = SimpleTracker(similarity_threshold=0.1)

        tracked = tracker.update([
            {
                'model_id': 32,
                'bbox': [0, 0, 100, 100],
                'class_id': 0,
                'class_name': 'detection',
                'confidence': 0.8,
            },
        ], 1, current_time=1.0)

        self.assertEqual(len(tracked), 1)
        self.assertFalse(tracked[0]['is_cached'])

    def test_post_process_context_preserves_detection_model_identity(self):
        task = SimpleNamespace(
            id=9,
            task_name='多模型任务',
            task_code='multi-model',
            task_type='realtime',
            model_ids='[32, 1]',
            tracking_enabled=False,
            alert_class_names='["detection", "person"]',
            pose_analysis_enabled=True,
            pose_intent_enabled=False,
        )

        context = build_task_context(
            task,
            device_id='CAM-006',
            device_name='06摄像头',
            frame_number=120,
            timestamp=100.0,
            detections=[{
                'model_id': 32,
                'class_id': 0,
                'class_name': 'detection',
                'confidence': 0.8,
                'bbox': [1, 2, 30, 40],
            }],
        )

        self.assertEqual(context['detections'][0]['model_id'], 32)

    def test_alert_image_filename_is_unique_per_event(self):
        captured_at = datetime(2026, 8, 13, 11, 30, 0)
        model_one = build_alert_image_filename(
            captured_at,
            120,
            {'model_id': 1, 'track_id': 0, 'class_name': 'person'},
            event_id='event-one',
        )
        model_two = build_alert_image_filename(
            captured_at,
            120,
            {'model_id': 2, 'track_id': 0, 'class_name': 'person'},
            event_id='event-two',
        )

        self.assertNotEqual(model_one, model_two)
        self.assertNotIn('/', model_one)

    def test_alert_image_filename_sanitizes_model_class(self):
        filename = build_alert_image_filename(
            datetime(2026, 8, 13, 11, 30, 0),
            120,
            {'model_id': 32, 'track_id': 0, 'class_name': '../unsafe/class'},
            event_id='event-id',
        )

        self.assertNotIn('..', filename)
        self.assertNotIn('/', filename)

    def test_post_process_async_failure_releases_caller_slot(self):
        failures = []

        class ImmediateThread:
            def __init__(self, target, daemon):
                self.target = target

            def start(self):
                self.target()

        with patch.object(
                post_process_sink_client,
                'publish_post_process_request',
                return_value=False,
        ):
            with patch.object(post_process_sink_client.threading, 'Thread', ImmediateThread):
                post_process_sink_client.publish_post_process_request_async(
                    {'task_id': 9},
                    on_failure=lambda: failures.append('released'),
                )

        self.assertEqual(failures, ['released'])

    def test_task_hot_reload_skips_unchanged_models(self):
        self.assertFalse(
            should_reload_algorithm_models(
                loaded_model_ids=[1, 32],
                configured_model_ids=[32, 1],
            )
        )

    def test_task_hot_reload_detects_model_set_change(self):
        self.assertTrue(
            should_reload_algorithm_models(
                loaded_model_ids=[1, 32],
                configured_model_ids=[1, 33],
            )
        )

    def test_parallel_inference_evidence_contains_worker_and_model_progress(self):
        evidence = build_parallel_inference_evidence(
            task_id=6,
            process_id=102,
            worker_instance='6-102-test',
            device_id='CAM-006',
            source_mode='shared',
            frame_number=1200,
            model_stats=[{
                'model_id': 1,
                'inference_count': 30,
                'success_count': 30,
                'hit_frame_count': 12,
                'detection_count': 12,
                'error_count': 0,
                'last_frame_number': 1200,
                'last_duration_ms': 23.5,
            }],
            observed_at_epoch_ms=1000,
        )

        self.assertEqual(evidence['task_id'], 6)
        self.assertEqual(evidence['source_mode'], 'shared')
        self.assertEqual(evidence['active_model_ids'], [1])
        self.assertEqual(evidence['models'][0]['inference_count'], 30)
        self.assertEqual(evidence['observed_at_epoch_ms'], 1000)

    def test_shared_source_topology_evidence_lists_two_tasks(self):
        evidence = build_shared_source_topology_evidence(
            device_id='CAM-006',
            task_ids=['9', '6', '6'],
            subscriber_count=2,
            reason='subscribe',
            observed_at_epoch_ms=1000,
        )
        line = format_observability_event('PARALLEL_SOURCE_TOPOLOGY', evidence)

        self.assertEqual(evidence['task_ids'], ['6', '9'])
        self.assertTrue(evidence['parallel_task_execution_expected'])
        self.assertIn('[PARALLEL_SOURCE_TOPOLOGY]', line)


if __name__ == '__main__':
    unittest.main()
