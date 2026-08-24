"""单节点摄像头共享源流管理测试。"""
import os
import sys
import tempfile
import threading
import time
import types
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from app.services.camera_source_manager import CameraSourceManager
from app.utils import camera_source_client
from app.utils import camera_source_shared_memory
from app.utils.camera_source_shared_memory import SharedFrameRing, SharedFrameRingReader
from services.camera_source_manager.run_service import (
    CameraSourceRequestHandler,
    _escape_prometheus_label,
)


class FakeFrame:
    """不依赖 NumPy 的测试帧。"""

    def __init__(self, width: int, height: int, value: int):
        self.shape = (height, width, 3)
        self._data = bytes([value]) * (width * height * 3)
        self.nbytes = len(self._data)

    def tobytes(self):
        return self._data


class FakeStream:
    """持续产生测试帧的源流。"""

    def __init__(self):
        self.read_failed = False
        self._released = False
        self._sequence = 0

    def isOpened(self):
        return not self._released

    def read(self):
        if self._released:
            self.read_failed = True
            return False, None
        self._sequence += 1
        time.sleep(0.002)
        return True, FakeFrame(4, 3, self._sequence % 255)

    def get(self, _prop):
        return 25.0

    def release(self):
        self._released = True


class FlakyStream(FakeStream):
    """产生一帧后模拟断流。"""

    def read(self):
        if self._sequence >= 1:
            self.read_failed = True
            return False, None
        return super().read()


class WaitingStream(FakeStream):
    """保持打开但暂时没有帧的源流。"""

    def read(self):
        time.sleep(0.002)
        return False, None


class BrokenFrame:
    """访问帧容量时触发不可恢复异常。"""

    shape = (3, 4, 3)

    @property
    def nbytes(self):
        raise RuntimeError('frame storage crashed')


class RaisingStream(FakeStream):
    """返回损坏帧的源流。"""

    def read(self):
        return True, BrokenFrame()


class FakeArray:
    """模拟 NumPy frombuffer 结果。"""

    def __init__(self, data):
        self.data = bytes(data)
        self.shape = None

    def reshape(self, shape):
        self.shape = shape
        return self

    def copy(self):
        return self


class TestSharedFrameRing(unittest.TestCase):
    def test_reader_observes_latest_complete_frame(self):
        ring = SharedFrameRing.create('CAM-001', slot_size=36, slot_count=2)
        reader = None
        try:
            ring.write_frame(FakeFrame(4, 3, 7), timestamp=12.5)
            ring.write_frame(FakeFrame(4, 3, 9), timestamp=13.5)
            reader = SharedFrameRingReader.attach(ring.descriptor())

            packet = reader.read_latest()

            self.assertIsNotNone(packet)
            self.assertEqual(packet.sequence, 2)
            self.assertEqual(packet.timestamp, 13.5)
            self.assertEqual(packet.shape, (3, 4, 3))
            self.assertEqual(packet.data, bytes([9]) * 36)
        finally:
            if reader:
                reader.close()
            ring.close(unlink=True)

    def test_capacity_shortage_falls_back_from_dev_shm(self):
        with tempfile.TemporaryDirectory() as fallback_root:
            disk_usage = types.SimpleNamespace(total=1024, used=1023, free=1)
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop('CAMERA_SOURCE_SHM_DIR', None)
                with patch.object(camera_source_shared_memory.os.path, 'isdir', return_value=True):
                    with patch.object(camera_source_shared_memory.os, 'access', return_value=True):
                        with patch.object(
                                camera_source_shared_memory.shutil,
                                'disk_usage',
                                return_value=disk_usage,
                        ):
                            with patch.object(
                                    camera_source_shared_memory,
                                    '_fallback_memory_root',
                                    return_value=fallback_root,
                            ):
                                root = camera_source_shared_memory._shared_memory_root(
                                    required_bytes=4096
                                )

        self.assertEqual(root, fallback_root)

    def test_create_reserves_backing_file_before_mmap(self):
        with tempfile.TemporaryDirectory() as memory_root:
            with patch.dict(
                    os.environ,
                    {'CAMERA_SOURCE_SHM_DIR': memory_root},
                    clear=False,
            ):
                with patch.object(
                        camera_source_shared_memory.os,
                        'posix_fallocate',
                        create=True,
                ) as fallocate:
                    ring = SharedFrameRing.create('CAM-RESERVE', slot_size=36, slot_count=2)
                    try:
                        self.assertTrue(fallocate.called)
                    finally:
                        ring.close(unlink=True)

    def test_cleanup_keeps_file_when_owner_process_cannot_be_probed(self):
        with tempfile.TemporaryDirectory() as memory_root:
            file_path = os.path.join(
                memory_root,
                'easyaiot_cam_deadbeef_12345_abcdef01',
            )
            with open(file_path, 'wb') as file_handle:
                file_handle.write(b'frame')
            old_time = time.time() - 120
            os.utime(file_path, (old_time, old_time))

            with patch.dict(
                    os.environ,
                    {'CAMERA_SOURCE_SHM_DIR': memory_root},
                    clear=False,
            ):
                with patch.object(
                        camera_source_shared_memory.os,
                        'kill',
                        side_effect=PermissionError('not permitted'),
                ):
                    removed = camera_source_shared_memory.cleanup_stale_shared_frame_files(
                        min_age_seconds=0
                    )

            self.assertEqual(removed, 0)
            self.assertTrue(os.path.exists(file_path))


class TestCameraSourceManager(unittest.TestCase):
    def test_two_tasks_share_one_source_and_ring(self):
        open_count = 0
        open_lock = threading.Lock()

        def opener(_url, _device_id, **_kwargs):
            nonlocal open_count
            with open_lock:
                open_count += 1
            return FakeStream()

        manager = CameraSourceManager(
            stream_opener=opener,
            idle_grace_seconds=0.05,
            subscriber_timeout_seconds=1.0,
        )
        reader = None
        try:
            first = manager.subscribe(101, 'CAM-001', 'rtsp://camera/stream', wait_timeout=1.0)
            second = manager.subscribe(202, 'CAM-001', 'rtsp://camera/stream', wait_timeout=1.0)

            self.assertEqual(open_count, 1)
            self.assertEqual(first['shared_memory_name'], second['shared_memory_name'])
            self.assertEqual(manager.status('CAM-001')['subscriber_count'], 2)

            reader = SharedFrameRingReader.attach(first)
            self.assertIsNotNone(reader.read_latest())

            manager.unsubscribe(101, 'CAM-001')
            self.assertEqual(manager.status('CAM-001')['subscriber_count'], 1)
            self.assertEqual(open_count, 1)
        finally:
            if reader:
                reader.close()
            manager.close()

    def test_two_gb28181_tasks_create_only_one_play_session(self):
        opened_urls = []

        def opener(source_url, *_args, **_kwargs):
            opened_urls.append(source_url)
            return FakeStream()

        manager = CameraSourceManager(
            stream_opener=opener,
            idle_grace_seconds=0.1,
            subscriber_timeout_seconds=1.0,
        )
        resolve_mock = MagicMock(return_value='rtsp://gb28181/resolved-session')
        fake_gb28181_source = types.ModuleType('app.utils.gb28181_source')
        fake_gb28181_source.resolve_gb28181_source = resolve_mock
        try:
            with patch.dict(
                    sys.modules,
                    {'app.utils.gb28181_source': fake_gb28181_source},
            ):
                first = manager.subscribe(
                    101,
                    'CAM-GB',
                    'gb28181://34020000001320000001',
                    original_source='gb28181://34020000001320000001',
                    is_gb28181=True,
                    wait_timeout=1.0,
                )
                second = manager.subscribe(
                    202,
                    'CAM-GB',
                    'gb28181://34020000001320000001',
                    original_source='gb28181://34020000001320000001',
                    is_gb28181=True,
                    wait_timeout=1.0,
                )

            self.assertEqual(resolve_mock.call_count, 1)
            self.assertEqual(opened_urls, ['rtsp://gb28181/resolved-session'])
            self.assertEqual(first['shared_memory_name'], second['shared_memory_name'])
            self.assertEqual(manager.status('CAM-GB')['subscriber_count'], 2)
        finally:
            manager.close()

    def test_unsubscribe_token_does_not_remove_restarted_worker(self):
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: FakeStream(),
            idle_grace_seconds=0.1,
            subscriber_timeout_seconds=1.0,
        )
        try:
            manager.subscribe(
                101,
                'CAM-RESTART',
                'rtsp://camera/stream',
                subscriber_id='old-worker',
                wait_timeout=1.0,
            )
            manager.subscribe(
                101,
                'CAM-RESTART',
                'rtsp://camera/stream',
                subscriber_id='new-worker',
                wait_timeout=1.0,
            )

            manager.unsubscribe(
                101,
                'CAM-RESTART',
                subscriber_id='old-worker',
            )

            state = manager.status('CAM-RESTART')
            self.assertEqual(state['subscriber_count'], 1)
            self.assertEqual(state['subscriber_task_ids'], ['101'])
        finally:
            manager.close()

    def test_source_configuration_update_reconnects_with_new_url(self):
        opened_urls = []

        def opener(source_url, *_args, **_kwargs):
            opened_urls.append(source_url)
            return FakeStream()

        manager = CameraSourceManager(
            stream_opener=opener,
            idle_grace_seconds=0.1,
            subscriber_timeout_seconds=1.0,
        )
        try:
            manager.subscribe(
                101,
                'CAM-UPDATE',
                'rtsp://camera/old',
                subscriber_id='worker-a',
                wait_timeout=1.0,
            )
            manager.subscribe(
                202,
                'CAM-UPDATE',
                'rtsp://camera/new',
                subscriber_id='worker-b',
                wait_timeout=1.0,
            )
            deadline = time.time() + 1.0
            while time.time() < deadline and 'rtsp://camera/new' not in opened_urls:
                time.sleep(0.01)

            self.assertIn('rtsp://camera/old', opened_urls)
            self.assertIn('rtsp://camera/new', opened_urls)
        finally:
            manager.close()

    def test_last_unsubscribe_releases_source_after_grace_period(self):
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: FakeStream(),
            idle_grace_seconds=0.03,
            subscriber_timeout_seconds=1.0,
        )
        try:
            manager.subscribe(101, 'CAM-001', 'rtsp://camera/stream', wait_timeout=1.0)
            manager.unsubscribe(101, 'CAM-001')

            deadline = time.time() + 1.0
            while time.time() < deadline and manager.status('CAM-001') is not None:
                time.sleep(0.01)

            self.assertIsNone(manager.status('CAM-001'))
        finally:
            manager.close()

    def test_new_subscription_replaces_session_already_closing_for_idle(self):
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: FakeStream(),
            idle_grace_seconds=0.02,
            subscriber_timeout_seconds=1.0,
        )
        allow_old_close = threading.Event()
        old_close_started = threading.Event()
        try:
            manager.subscribe(101, 'CAM-RACE', 'rtsp://camera/stream', wait_timeout=1.0)
            old_session = manager._sessions['CAM-RACE']
            original_release = old_session._release_capture

            def blocking_release():
                if old_session._lifecycle == 'closing':
                    old_close_started.set()
                    allow_old_close.wait(timeout=1.0)
                original_release()

            old_session._release_capture = blocking_release
            manager.unsubscribe(101, 'CAM-RACE')
            self.assertTrue(old_close_started.wait(timeout=1.0))

            descriptor = manager.subscribe(
                202,
                'CAM-RACE',
                'rtsp://camera/stream',
                wait_timeout=1.0,
            )
            new_session = manager._sessions['CAM-RACE']

            self.assertIsNot(new_session, old_session)
            self.assertEqual(descriptor['subscriber_count'], 1)
            self.assertIn('202', descriptor['subscriber_task_ids'])
        finally:
            allow_old_close.set()
            manager.close()

    def test_source_reconnect_does_not_change_subscription(self):
        open_count = 0

        def opener(*_args, **_kwargs):
            nonlocal open_count
            open_count += 1
            return FlakyStream() if open_count == 1 else FakeStream()

        manager = CameraSourceManager(
            stream_opener=opener,
            idle_grace_seconds=0.1,
            subscriber_timeout_seconds=2.0,
        )
        try:
            descriptor = manager.subscribe(
                101, 'CAM-001', 'rtsp://camera/stream', wait_timeout=1.0
            )
            first_name = descriptor['shared_memory_name']
            deadline = time.time() + 2.0
            while time.time() < deadline:
                state = manager.status('CAM-001')
                if state and state['reconnect_count'] >= 1 and state['frame_count'] >= 2:
                    break
                time.sleep(0.01)

            state = manager.status('CAM-001')
            self.assertGreaterEqual(open_count, 2)
            self.assertGreaterEqual(state['reconnect_count'], 1)
            self.assertEqual(state['subscriber_count'], 1)
            self.assertEqual(state['shared_memory_name'], first_name)
        finally:
            manager.close()

    def test_open_but_stalled_source_is_reconnected(self):
        open_count = 0

        def opener(*_args, **_kwargs):
            nonlocal open_count
            open_count += 1
            return WaitingStream()

        with patch.dict(
                os.environ,
                {
                    'CAMERA_SOURCE_STALE_FRAME_SEC': '0.05',
                    'CAMERA_SOURCE_RECONNECT_DELAY_SEC': '0.01',
                },
                clear=False,
        ):
            manager = CameraSourceManager(
                stream_opener=opener,
                idle_grace_seconds=1.0,
                subscriber_timeout_seconds=2.0,
            )
            try:
                manager.subscribe(
                    101, 'CAM-STALL', 'rtsp://camera/stream', wait_timeout=0.05
                )
                deadline = time.time() + 1.0
                while time.time() < deadline and open_count < 2:
                    time.sleep(0.01)

                self.assertGreaterEqual(open_count, 2)
                self.assertGreaterEqual(
                    manager.status('CAM-STALL')['reconnect_count'],
                    1,
                )
            finally:
                manager.close()

    def test_fatal_session_state_is_retained_for_observability(self):
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: RaisingStream(),
            idle_grace_seconds=1.0,
            subscriber_timeout_seconds=2.0,
        )
        try:
            manager.subscribe(
                101,
                'CAM-FATAL',
                'rtsp://camera/stream',
                wait_timeout=0.1,
            )
            deadline = time.time() + 1.0
            state = None
            while time.time() < deadline:
                state = manager.status('CAM-FATAL')
                if state and state.get('status') == 'failed':
                    break
                time.sleep(0.01)

            self.assertIsNotNone(state)
            self.assertEqual(state['status'], 'failed')
            self.assertIn('frame storage crashed', state['error_message'])
        finally:
            manager.close()


class TestCameraSourceFallback(unittest.TestCase):
    def test_manager_failed_descriptor_falls_back_to_direct_stream(self):
        direct_stream = object()
        fake_adapter = types.SimpleNamespace(
            open_device_stream=lambda *_args, **_kwargs: direct_stream
        )

        def request_json(_method, path, **_kwargs):
            if path == '/subscribe':
                return {
                    'status': 'ok',
                    'data': {
                        'status': 'failed',
                        'error_message': 'shared frame capacity exhausted',
                    },
                }
            return {'status': 'ok'}

        with patch.dict(
                os.environ,
                {'CAMERA_SOURCE_MODE': 'shared', 'CAMERA_SOURCE_FALLBACK_DIRECT': 'true'},
                clear=False,
        ):
            with patch.object(camera_source_client, '_request_json', side_effect=request_json):
                with patch.dict(
                        sys.modules,
                        {'app.utils.decode.stream_adapter': fake_adapter},
                ):
                    stream, mode = camera_source_client.open_task_camera_stream(
                        'rtsp://camera/stream', 'CAM-CAPACITY', task_id=101
                    )

        self.assertIs(stream, direct_stream)
        self.assertEqual(mode, 'direct_fallback')

    def test_shared_failure_falls_back_to_direct_stream(self):
        direct_stream = object()
        fake_adapter = types.SimpleNamespace(
            open_device_stream=lambda *_args, **_kwargs: direct_stream
        )
        with patch.dict(
                os.environ,
                {'CAMERA_SOURCE_MODE': 'shared', 'CAMERA_SOURCE_FALLBACK_DIRECT': 'true'},
                clear=False,
        ):
            with patch.object(
                    camera_source_client,
                    'open_shared_camera_stream',
                    side_effect=RuntimeError('manager unavailable'),
            ):
                with patch.dict(
                        sys.modules,
                        {'app.utils.decode.stream_adapter': fake_adapter},
                ):
                    stream, mode = camera_source_client.open_task_camera_stream(
                        'rtsp://camera/stream', 'CAM-001', task_id=101
                    )

        self.assertIs(stream, direct_stream)
        self.assertEqual(mode, 'direct_fallback')

    def test_shared_failure_is_raised_when_fallback_disabled(self):
        with patch.dict(
                os.environ,
                {'CAMERA_SOURCE_MODE': 'shared', 'CAMERA_SOURCE_FALLBACK_DIRECT': 'false'},
                clear=False,
        ):
            with patch.object(
                    camera_source_client,
                    'open_shared_camera_stream',
                    side_effect=RuntimeError('manager unavailable'),
            ):
                with self.assertRaisesRegex(RuntimeError, 'manager unavailable'):
                    camera_source_client.open_task_camera_stream(
                        'rtsp://camera/stream', 'CAM-001', task_id=101
                    )


class TestCameraSourceHttpIntegration(unittest.TestCase):
    def test_non_loopback_control_requires_matching_token(self):
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: FakeStream(),
        )
        CameraSourceRequestHandler.manager = manager
        CameraSourceRequestHandler.require_token = True
        CameraSourceRequestHandler.control_token = 'internal-secret'
        server = ThreadingHTTPServer(('127.0.0.1', 0), CameraSourceRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            manager_url = f'http://127.0.0.1:{server.server_port}'
            with patch.dict(
                    os.environ,
                    {
                        'CAMERA_SOURCE_MANAGER_URL': manager_url,
                        'CAMERA_SOURCE_MANAGER_TOKEN': 'wrong-secret',
                    },
                    clear=False,
            ):
                with self.assertRaises(HTTPError) as error_context:
                    camera_source_client.get_camera_source_status()
                self.assertEqual(error_context.exception.code, 401)
                error_context.exception.close()

            with patch.dict(
                    os.environ,
                    {
                        'CAMERA_SOURCE_MANAGER_URL': manager_url,
                        'CAMERA_SOURCE_MANAGER_TOKEN': 'internal-secret',
                    },
                    clear=False,
            ):
                self.assertEqual(camera_source_client.get_camera_source_status(), [])
        finally:
            CameraSourceRequestHandler.require_token = False
            CameraSourceRequestHandler.control_token = ''
            server.shutdown()
            server.server_close()
            manager.close()

    def test_prometheus_label_escaping(self):
        self.assertEqual(
            _escape_prometheus_label('CAM\\"\n001'),
            'CAM\\\\\\"\\n001',
        )

    def test_source_waiting_keeps_shared_pending_without_direct_fallback(self):
        direct_open_count = 0
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: WaitingStream(),
            idle_grace_seconds=0.2,
            subscriber_timeout_seconds=2.0,
        )
        CameraSourceRequestHandler.manager = manager
        server = ThreadingHTTPServer(('127.0.0.1', 0), CameraSourceRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        stream = None

        def direct_opener(*_args, **_kwargs):
            nonlocal direct_open_count
            direct_open_count += 1
            return FakeStream()

        fake_adapter = types.SimpleNamespace(open_device_stream=direct_opener)
        try:
            with patch.dict(
                    os.environ,
                    {
                        'CAMERA_SOURCE_MODE': 'shared',
                        'CAMERA_SOURCE_MANAGER_URL': f'http://127.0.0.1:{server.server_port}',
                    },
                    clear=False,
            ):
                with patch.dict(
                        sys.modules,
                        {'app.utils.decode.stream_adapter': fake_adapter},
                ):
                    stream, mode = camera_source_client.open_task_camera_stream(
                        'rtsp://camera/stream',
                        'CAM-PENDING',
                        task_id=101,
                        open_timeout_msec=100,
                    )

            self.assertEqual(mode, 'shared')
            self.assertTrue(stream.isOpened())
            self.assertFalse(stream.read_failed)
            self.assertEqual(direct_open_count, 0)
            self.assertEqual(
                manager.status('CAM-PENDING')['subscriber_count'],
                1,
            )
        finally:
            if stream:
                stream.release()
            server.shutdown()
            server.server_close()
            manager.close()

    def test_worker_subscribes_and_reads_frame_through_http_control(self):
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: FakeStream(),
            idle_grace_seconds=0.05,
            subscriber_timeout_seconds=2.0,
        )
        CameraSourceRequestHandler.manager = manager
        server = ThreadingHTTPServer(('127.0.0.1', 0), CameraSourceRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        stream = None
        fake_numpy = types.SimpleNamespace(
            uint8='uint8',
            frombuffer=lambda data, dtype=None: FakeArray(data),
        )
        try:
            with patch.dict(
                    os.environ,
                    {
                        'CAMERA_SOURCE_MODE': 'shared',
                        'CAMERA_SOURCE_MANAGER_URL': f'http://127.0.0.1:{server.server_port}',
                    },
                    clear=False,
            ):
                stream = camera_source_client.open_shared_camera_stream(
                    'rtsp://camera/stream',
                    'CAM-001',
                    task_id=101,
                    open_timeout_msec=1000,
                )
                with patch.dict(sys.modules, {'numpy': fake_numpy}):
                    deadline = time.time() + 1.0
                    result = (False, None)
                    while time.time() < deadline and not result[0]:
                        result = stream.read()
                        time.sleep(0.005)

            self.assertTrue(result[0])
            self.assertEqual(result[1].shape, (3, 4, 3))
            self.assertEqual(manager.status('CAM-001')['subscriber_count'], 1)
        finally:
            if stream:
                stream.release()
            server.shutdown()
            server.server_close()
            manager.close()

    def test_heartbeat_failure_does_not_block_available_shared_frame(self):
        manager = CameraSourceManager(
            stream_opener=lambda *_args, **_kwargs: FakeStream(),
            idle_grace_seconds=0.05,
            subscriber_timeout_seconds=2.0,
        )
        CameraSourceRequestHandler.manager = manager
        server = ThreadingHTTPServer(('127.0.0.1', 0), CameraSourceRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        stream = None
        fake_numpy = types.SimpleNamespace(
            uint8='uint8',
            frombuffer=lambda data, dtype=None: FakeArray(data),
        )
        try:
            with patch.dict(
                    os.environ,
                    {
                        'CAMERA_SOURCE_MANAGER_URL': f'http://127.0.0.1:{server.server_port}',
                    },
                    clear=False,
            ):
                stream = camera_source_client.open_shared_camera_stream(
                    'rtsp://camera/stream',
                    'CAM-HEARTBEAT',
                    task_id=101,
                    open_timeout_msec=1000,
                )
                stream._last_heartbeat_monotonic = 0
                stream._last_heartbeat_attempt_monotonic = 0
                with patch.object(
                        camera_source_client,
                        '_request_json',
                        side_effect=TimeoutError('control plane timeout'),
                ):
                    with patch.dict(sys.modules, {'numpy': fake_numpy}):
                        result = stream.read()

            self.assertTrue(result[0])
            self.assertIsNotNone(result[1])
            self.assertFalse(stream.read_failed)
        finally:
            if stream:
                stream.release()
            server.shutdown()
            server.server_close()
            manager.close()


if __name__ == '__main__':
    unittest.main()
