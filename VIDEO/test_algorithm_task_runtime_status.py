"""算法任务控制面与 Worker 运行状态一致性测试。"""
import unittest
from datetime import datetime
from types import SimpleNamespace

from app.utils.algorithm_task_runtime import (
    mark_stream_runtime_stopped,
    resolve_frame_runtime_status,
    resolve_heartbeat_server_ip,
    resolve_heartbeat_stream_state,
    resolve_task_run_status_from_heartbeat,
)


class TestAlgorithmTaskRuntimeStatus(unittest.TestCase):
    """验证启停、心跳和推流状态不会互相覆盖为错误状态。"""

    def test_enabled_stopped_task_becomes_running_after_worker_heartbeat(self):
        self.assertEqual(
            resolve_task_run_status_from_heartbeat(is_enabled=True),
            'running',
        )

    def test_disabled_task_stays_stopped_after_stale_worker_heartbeat(self):
        self.assertEqual(
            resolve_task_run_status_from_heartbeat(is_enabled=False),
            'stopped',
        )

    def test_remote_worker_loopback_does_not_replace_edge_host(self):
        self.assertEqual(
            resolve_heartbeat_server_ip(
                '127.0.0.1',
                '192.0.2.20',
                node_id=5,
            ),
            '192.0.2.20',
        )

    def test_local_worker_can_report_loopback(self):
        self.assertEqual(
            resolve_heartbeat_server_ip('127.0.0.1', '', node_id=None),
            '127.0.0.1',
        )

    def test_live_publisher_keeps_publishing_status_on_each_frame(self):
        self.assertEqual(
            resolve_frame_runtime_status('shared', publisher_running=True),
            'publishing',
        )

    def test_direct_fallback_keeps_degraded_status_even_when_publishing(self):
        self.assertEqual(
            resolve_frame_runtime_status('direct_fallback', publisher_running=True),
            'degraded',
        )

    def test_disabled_task_heartbeat_cannot_reactivate_stream_runtime(self):
        self.assertEqual(
            resolve_heartbeat_stream_state(
                is_enabled=False,
                source_mode='shared',
                status='publishing',
            ),
            ('pending', 'stopped'),
        )

    def test_stop_marks_runtime_stopped_and_preserves_last_activity(self):
        last_frame_time = datetime(2026, 8, 12, 15, 20, 13)
        stopped_at = datetime(2026, 8, 12, 15, 21, 41)
        runtime = SimpleNamespace(
            source_mode='shared',
            status='publishing',
            last_frame_time=last_frame_time,
            error_message='旧错误',
            updated_at=None,
        )

        mark_stream_runtime_stopped(runtime, stopped_at)

        self.assertEqual(runtime.source_mode, 'pending')
        self.assertEqual(runtime.status, 'stopped')
        self.assertEqual(runtime.last_frame_time, last_frame_time)
        self.assertIsNone(runtime.error_message)
        self.assertEqual(runtime.updated_at, stopped_at)


if __name__ == '__main__':
    unittest.main()
