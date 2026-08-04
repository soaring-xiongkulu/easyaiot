"""FFmpeg 守护进程注册表清理逻辑单元测试。"""

import threading

from app.utils.ffmpeg_process_registry import stop_registered_process


class FakeDaemon:
    """用于验证停止调用的最小守护进程替身。"""

    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


def test_stop_registered_process_handles_daemon_object():
    """注册表保存的是守护对象，删除设备时不得按字典访问。"""
    daemon = FakeDaemon()
    registry = {'camera-1': daemon}

    stopped = stop_registered_process(registry, threading.Lock(), 'camera-1')

    assert stopped is True
    assert daemon.stopped is True
    assert 'camera-1' not in registry


def test_stop_registered_process_is_idempotent_for_missing_device():
    registry = {}

    stopped = stop_registered_process(registry, threading.Lock(), 'missing')

    assert stopped is False
    assert registry == {}


def test_stop_registered_process_removes_stale_entry_when_stop_fails():
    class FailingDaemon:
        def stop(self):
            raise ProcessLookupError('process already exited')

    daemon = FailingDaemon()
    registry = {'camera-1': daemon}

    try:
        stop_registered_process(registry, threading.Lock(), 'camera-1')
    except ProcessLookupError as exc:
        assert str(exc) == 'process already exited'
    else:
        raise AssertionError('停止失败时应向上抛出异常')

    assert 'camera-1' not in registry
