"""CameraSourceManager 进程监督测试。"""
import os
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services import algorithm_task_launcher_service as launcher


class TestCameraSourceManagerWatchdog(unittest.TestCase):
    def tearDown(self):
        launcher._camera_source_watchdog_stop.set()
        watchdog_thread = launcher._camera_source_watchdog_thread
        if watchdog_thread is not None and watchdog_thread.is_alive():
            watchdog_thread.join(timeout=2.0)
        launcher._camera_source_watchdog_thread = None

    def test_watchdog_requests_restart_after_health_failure(self):
        restart_requested = threading.Event()

        def ensure_manager():
            restart_requested.set()
            return True, 'restarted'

        with patch.dict(
                os.environ,
                {
                    'CAMERA_SOURCE_MODE': 'shared',
                    'CAMERA_SOURCE_WATCHDOG_INTERVAL_SEC': '1',
                },
                clear=False,
        ):
            with patch.object(
                    launcher,
                    '_camera_source_manager_healthy',
                    return_value=False,
            ):
                with patch.object(
                        launcher,
                        'ensure_camera_source_manager',
                        side_effect=ensure_manager,
                ):
                    launcher._start_camera_source_watchdog()
                    self.assertTrue(restart_requested.wait(timeout=2.0))

    def test_stop_manager_terminates_child_and_closes_log(self):
        process = Mock()
        process.poll.return_value = None
        log_handle = Mock()
        launcher._camera_source_process = process
        launcher._camera_source_log_handle = log_handle

        launcher.stop_camera_source_manager()

        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5.0)
        log_handle.close.assert_called_once_with()
        self.assertIsNone(launcher._camera_source_process)
        self.assertIsNone(launcher._camera_source_log_handle)

    def test_remote_realtime_worker_is_forced_to_direct_mode(self):
        with patch.dict(
                os.environ,
                {
                    'CAMERA_SOURCE_MODE': 'shared',
                    'CAMERA_SOURCE_MANAGER_URL': 'http://control-node:6010',
                    'CAMERA_SOURCE_MANAGER_TOKEN': 'secret',
                },
                clear=False,
        ):
            with patch(
                    'app.utils.node_remote_tools.apply_remote_toolchain_env',
            ):
                env = launcher._build_task_deploy_env(
                    101,
                    'realtime',
                    '/tmp/task-101',
                    '203.0.113.20',
                )

        self.assertEqual(env['CAMERA_SOURCE_MODE'], 'direct')
        self.assertEqual(env['CAMERA_SOURCE_REMOTE_WORKER'], 'true')
        self.assertNotIn('CAMERA_SOURCE_MANAGER_URL', env)
        self.assertNotIn('CAMERA_SOURCE_MANAGER_TOKEN', env)

    def test_remote_worker_rewrites_loopback_control_plane_urls_and_disables_gpu(self):
        task = SimpleNamespace(
            task_type='realtime',
            prefer_gpu=False,
            motion_gate_enabled=False,
            motion_gate_config=None,
        )
        with patch.dict(
                os.environ,
                {
                    # RFC 5737 TEST-NET 地址，避免测试固化真实部署信息。
                    'EASYAIOT_PLATFORM_HOST': '198.51.100.10',
                    'DATABASE_URL': 'postgresql://user:pass@localhost:5432/video',
                    'GATEWAY_URL': 'http://127.0.0.1:48080',
                    'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
                    'USE_GPU': 'true',
                    'CUDA_VISIBLE_DEVICES': '0',
                },
                clear=False,
        ):
            with patch('app.utils.node_remote_tools.apply_remote_toolchain_env'):
                env = launcher._build_task_deploy_env(
                    102,
                    'realtime',
                    '/tmp/task-102',
                    '203.0.113.20',
                    task=task,
                )

        self.assertEqual(
            env['DATABASE_URL'],
            'postgresql://user:pass@198.51.100.10:5432/video',
        )
        self.assertEqual(env['GATEWAY_URL'], 'http://198.51.100.10:48080')
        self.assertEqual(env['KAFKA_BOOTSTRAP_SERVERS'], '198.51.100.10:9092')
        self.assertEqual(env['VIDEO_SERVICE_URL'], 'http://198.51.100.10:6000')
        self.assertEqual(env['USE_GPU'], 'false')
        self.assertEqual(env['ORT_EXECUTION_PROVIDERS'], 'CPUExecutionProvider')
        self.assertNotIn('CUDA_VISIBLE_DEVICES', env)

    def test_ensure_manager_restarts_after_managed_process_exit(self):
        exited_process = Mock()
        exited_process.poll.return_value = 1
        restarted_process = Mock()
        restarted_process.poll.return_value = None
        restarted_process.pid = 43210
        launcher._camera_source_process = exited_process

        with tempfile.TemporaryDirectory() as video_root:
            with patch.dict(os.environ, {'CAMERA_SOURCE_MODE': 'shared'}, clear=False):
                with patch.object(launcher, '_start_camera_source_watchdog'):
                    with patch.object(
                            launcher,
                            '_camera_source_manager_healthy',
                            side_effect=[False, False, True],
                    ):
                        with patch.object(launcher, '_get_video_root', return_value=video_root):
                            with patch.object(launcher, '_resolve_camera_source_python', return_value='python'):
                                with patch.object(
                                        launcher.subprocess,
                                        'Popen',
                                        return_value=restarted_process,
                                ) as popen:
                                    ok, _message = launcher.ensure_camera_source_manager()

        self.assertTrue(ok)
        popen.assert_called_once()
        self.assertIs(launcher._camera_source_process, restarted_process)
        launcher.stop_camera_source_manager()


if __name__ == '__main__':
    unittest.main()
