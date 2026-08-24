"""单节点摄像头共享拉流与解码管理。"""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Callable, Dict, Optional

from app.utils.camera_source_shared_memory import (
    SharedFrameCapacityError,
    SharedFrameRing,
    cleanup_stale_shared_frame_files,
)
from app.utils.parallel_inference_observability import (
    build_shared_source_topology_evidence,
    format_observability_event,
)


logger = logging.getLogger(__name__)


class CameraSourceSessionClosing(RuntimeError):
    """源流会话已经进入关闭阶段，不能再接受新订阅。"""


def _default_stream_opener(source_url: str, device_id: str, **kwargs):
    """延迟导入解码依赖，便于控制面和轻量测试启动。"""
    from app.utils.decode.stream_adapter import open_device_stream

    return open_device_stream(
        source_url,
        device_id,
        task_id='camera_source_manager',
        open_timeout_msec=int(kwargs.get('open_timeout_msec', 5000)),
        read_timeout_msec=int(kwargs.get('read_timeout_msec', 2500)),
        queue_max_override=1,
    )


class CameraSourceSession:
    """一个摄像头的唯一源流会话。"""

    def __init__(
            self,
            *,
            device_id: str,
            source_url: str,
            stream_opener: Callable,
            slot_count: int,
            idle_grace_seconds: float,
            subscriber_timeout_seconds: float,
            original_source: Optional[str] = None,
            is_gb28181: bool = False,
    ):
        self.device_id = str(device_id)
        self.configured_source_url = str(source_url)
        self.source_url = str(source_url)
        self.original_source = original_source
        self.is_gb28181 = bool(is_gb28181)
        self._stream_opener = stream_opener
        self._slot_count = max(2, int(slot_count))
        self._idle_grace_seconds = max(0.0, float(idle_grace_seconds))
        self._subscriber_timeout_seconds = max(1.0, float(subscriber_timeout_seconds))
        self._lock = threading.RLock()
        self._ready_condition = threading.Condition(self._lock)
        self._stop_event = threading.Event()
        self._lifecycle = 'active'
        # key 为 Worker 实例订阅令牌，value 为 (task_id, 最后心跳时间)。
        self._subscribers: Dict[str, tuple[str, float]] = {}
        self._idle_since: Optional[float] = None
        self._ring: Optional[SharedFrameRing] = None
        self._capture = None
        self._status = 'starting'
        self._error_message: Optional[str] = None
        self._fatal_error: Optional[str] = None
        self._last_frame_time = 0.0
        self._last_frame_monotonic = 0.0
        self._frame_count = 0
        self._fps_window_started = time.monotonic()
        self._fps_window_frames = 0
        self._decode_fps = 0.0
        self._reconnect_count = 0
        self._connected_monotonic = 0.0
        self._gray_bad_streak = 0
        self._gb_use_alternate_next = False
        self._gray_reconnect_enabled = (
            (os.getenv('AI_RTSP_GRAY_RECONNECT') or '1').strip().lower()
            not in ('0', 'false', 'no', 'off')
        )
        self._gray_streak_required = max(
            1, int(os.getenv('AI_RTSP_GRAY_STREAK', '20') or '20')
        )
        self._gray_warmup_seconds = max(
            0.0, float(os.getenv('AI_RTSP_GRAY_WARMUP_SEC', '15') or '15')
        )
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name=f'camera_source_{self.device_id}',
        )
        self._thread_started = False
        self._last_logged_task_ids = None

    def _log_subscription_topology_locked(self, reason: str) -> None:
        """订阅任务集合发生变化时输出共享源并行拓扑。"""
        task_ids = sorted({
            task_id for task_id, _last_seen in self._subscribers.values()
        })
        topology_key = tuple(task_ids)
        if topology_key == self._last_logged_task_ids:
            return
        self._last_logged_task_ids = topology_key
        evidence = build_shared_source_topology_evidence(
            device_id=self.device_id,
            task_ids=task_ids,
            subscriber_count=len(self._subscribers),
            reason=reason,
        )
        logger.info(format_observability_event('PARALLEL_SOURCE_TOPOLOGY', evidence))

    @property
    def stopped(self) -> bool:
        with self._lock:
            return self._lifecycle == 'stopped'

    def subscribe(
            self,
            task_id: int,
            *,
            subscriber_id: Optional[str],
            wait_timeout: float,
    ) -> Dict:
        normalized_task_id = str(task_id)
        subscriber_key = str(subscriber_id or normalized_task_id)
        with self._ready_condition:
            if self._lifecycle != 'active':
                raise CameraSourceSessionClosing(
                    f'设备 {self.device_id} 的共享源流会话正在关闭'
                )
            self._subscribers[subscriber_key] = (
                normalized_task_id,
                time.monotonic(),
            )
            self._log_subscription_topology_locked('subscribe')
            self._idle_since = None
            if not self._thread_started:
                self._thread_started = True
                self._thread.start()
            deadline = time.monotonic() + max(0.0, float(wait_timeout))
            while self._ring is None and not self._stop_event.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._ready_condition.wait(timeout=min(remaining, 0.2))
            return self._descriptor_locked()

    def unsubscribe(self, task_id: int, *, subscriber_id: Optional[str] = None) -> None:
        with self._lock:
            if subscriber_id:
                self._subscribers.pop(str(subscriber_id), None)
            else:
                normalized_task_id = str(task_id)
                subscriber_keys = [
                    key
                    for key, (registered_task_id, _last_seen) in self._subscribers.items()
                    if registered_task_id == normalized_task_id
                ]
                for subscriber_key in subscriber_keys:
                    self._subscribers.pop(subscriber_key, None)
            if not self._subscribers and self._idle_since is None:
                self._idle_since = time.monotonic()
            self._log_subscription_topology_locked('unsubscribe')

    def _expire_subscribers_locked(self, now: float) -> None:
        expired = [
            subscriber_id
            for subscriber_id, (_task_id, last_seen) in self._subscribers.items()
            if now - last_seen > self._subscriber_timeout_seconds
        ]
        for subscriber_id in expired:
            self._subscribers.pop(subscriber_id, None)
        if expired:
            self._log_subscription_topology_locked('subscriber_expired')
        if not self._subscribers and self._idle_since is None:
            self._idle_since = now

    def _should_stop_for_idle(self) -> bool:
        now = time.monotonic()
        with self._lock:
            self._expire_subscribers_locked(now)
            if self._subscribers:
                return False
            if self._idle_since is None:
                self._idle_since = now
            if now - self._idle_since < self._idle_grace_seconds:
                return False
            # 在锁内先进入 closing，阻止空闲判断完成后又接受新订阅。
            self._lifecycle = 'closing'
            self._stop_event.set()
            return True

    def _descriptor_locked(self) -> Dict:
        result = self._ring.descriptor() if self._ring else {
            'source_id': f'source_{self.device_id}',
            'device_id': self.device_id,
            'shared_memory_name': None,
            'shared_memory_path': None,
            'frame_format': 'bgr24',
            'width': 0,
            'height': 0,
            'channels': 3,
            'slot_size': 0,
            'slot_count': self._slot_count,
            'latest_sequence': 0,
            'latest_timestamp': 0.0,
        }
        result.update({
            'status': self._status,
            'subscriber_count': len(self._subscribers),
            'subscriber_task_ids': sorted({
                task_id for task_id, _last_seen in self._subscribers.values()
            }),
            'decode_fps': round(self._decode_fps, 2),
            'frame_count': self._frame_count,
            'last_frame_time': self._last_frame_time or None,
            'reconnect_count': self._reconnect_count,
            'error_message': self._error_message,
        })
        return result

    def status(self) -> Dict:
        with self._lock:
            self._expire_subscribers_locked(time.monotonic())
            return self._descriptor_locked()

    def _set_status(self, status: str, error_message: Optional[str] = None) -> None:
        with self._ready_condition:
            self._status = status
            self._error_message = error_message
            self._ready_condition.notify_all()

    def _resolve_source_url(self) -> str:
        if not self.is_gb28181 or not self.original_source:
            return self.source_url
        try:
            from app.utils.gb28181_source import resolve_gb28181_source

            resolved = resolve_gb28181_source(self.original_source, logger=logger)
            if resolved:
                self.source_url = resolved
        except Exception as exc:
            logger.warning('共享源流重新解析 GB28181 地址失败 device_id=%s: %s', self.device_id, exc)
        return self.source_url

    def update_source(
            self,
            source_url: str,
            *,
            original_source: Optional[str],
            is_gb28181: bool,
    ) -> None:
        """更新设备源配置并触发当前 Capture 重连。"""
        normalized_source_url = str(source_url)
        with self._ready_condition:
            if self._lifecycle != 'active':
                raise CameraSourceSessionClosing(
                    f'设备 {self.device_id} 的共享源流会话正在关闭'
                )
            if (
                    self.configured_source_url == normalized_source_url
                    and self.original_source == original_source
                    and self.is_gb28181 == bool(is_gb28181)
            ):
                return
            self.configured_source_url = normalized_source_url
            self.source_url = normalized_source_url
            self.original_source = original_source
            self.is_gb28181 = bool(is_gb28181)
            self._status = 'source_waiting'
            self._error_message = '摄像头源配置已更新，正在重新连接'
        self._release_capture()

    def _open_capture(self):
        source_url = self._resolve_source_url()
        if self.is_gb28181 and self.original_source and self._gb_use_alternate_next:
            self._gb_use_alternate_next = False
            try:
                from app.utils.gb28181_source import resolve_gb28181_alternate_pull_url

                alternate_url = resolve_gb28181_alternate_pull_url(
                    self.original_source,
                    source_url,
                    logger=logger,
                )
                if alternate_url:
                    source_url = alternate_url
                    self.source_url = alternate_url
            except Exception as exc:
                logger.warning(
                    '共享源流预选 GB28181 备用地址失败 device_id=%s: %s',
                    self.device_id,
                    exc,
                )
        capture = self._stream_opener(
            source_url,
            self.device_id,
            open_timeout_msec=int(os.getenv('RTSP_OPEN_TIMEOUT_MSEC', '5000')),
            read_timeout_msec=int(os.getenv('RTSP_READ_TIMEOUT_MSEC', '2500')),
        )
        if capture is not None and capture.isOpened():
            return capture
        if not self.is_gb28181 or not self.original_source:
            return capture

        try:
            from app.utils.gb28181_source import resolve_gb28181_alternate_pull_url

            alternate_url = resolve_gb28181_alternate_pull_url(
                self.original_source,
                source_url,
                logger=logger,
            )
        except Exception as exc:
            logger.warning('共享源流解析 GB28181 备用地址失败 device_id=%s: %s', self.device_id, exc)
            return capture
        if not alternate_url or alternate_url == source_url:
            return capture
        if capture is not None:
            try:
                capture.release()
            except Exception:
                pass
        self.source_url = alternate_url
        return self._stream_opener(
            alternate_url,
            self.device_id,
            open_timeout_msec=int(os.getenv('RTSP_OPEN_TIMEOUT_MSEC', '5000')),
            read_timeout_msec=int(os.getenv('RTSP_READ_TIMEOUT_MSEC', '2500')),
        )

    def _release_capture(self) -> None:
        capture = self._capture
        self._capture = None
        if capture is not None:
            try:
                capture.release()
            except Exception:
                pass

    def _replace_ring(self, frame) -> None:
        old_ring = self._ring
        self._ring = SharedFrameRing.create(
            self.device_id,
            slot_size=int(frame.nbytes),
            slot_count=self._slot_count,
        )
        if old_ring is not None:
            old_ring.close(unlink=True)

    def _write_frame(self, frame, frame_timestamp: float) -> None:
        with self._ready_condition:
            if self._ring is None:
                self._replace_ring(frame)
            try:
                self._ring.write_frame(frame, timestamp=frame_timestamp)
            except SharedFrameCapacityError:
                # 分辨率升高时发布新一代共享帧环，订阅者会在心跳时重新附加。
                self._replace_ring(frame)
                self._ring.write_frame(frame, timestamp=frame_timestamp)
            self._frame_count += 1
            self._fps_window_frames += 1
            self._last_frame_time = frame_timestamp
            self._last_frame_monotonic = time.monotonic()
            now = time.monotonic()
            elapsed = now - self._fps_window_started
            if elapsed >= 1.0:
                self._decode_fps = self._fps_window_frames / elapsed
                self._fps_window_started = now
                self._fps_window_frames = 0
            self._status = 'streaming'
            self._error_message = None
            self._ready_condition.notify_all()

    def _is_flat_corrupt_frame(self, frame) -> bool:
        """识别 RTSP 解码失败后的典型中灰塌缩帧。"""
        if not self._gray_reconnect_enabled:
            return False
        if not self.source_url.lower().startswith('rtsp://'):
            return False
        if time.monotonic() - self._connected_monotonic < self._gray_warmup_seconds:
            return False
        try:
            # 抽样即可识别整屏塌缩，避免每帧对 1080P 全图重复统计。
            sampled_frame = frame[::16, ::16]
            frame_mean = float(sampled_frame.mean())
            frame_std = float(sampled_frame.std())
            mean_low = float(os.getenv('AI_RTSP_GRAY_MEAN_LO', '80') or '80')
            mean_high = float(os.getenv('AI_RTSP_GRAY_MEAN_HI', '180') or '180')
            std_max = float(os.getenv('AI_RTSP_GRAY_STD_MAX', '4') or '4')
            return mean_low <= frame_mean <= mean_high and frame_std < std_max
        except Exception:
            return False

    def _run(self) -> None:
        reconnect_delay = max(0.1, float(os.getenv('CAMERA_SOURCE_RECONNECT_DELAY_SEC', '1')))
        stale_frame_seconds = max(
            0.05,
            float(os.getenv('CAMERA_SOURCE_STALE_FRAME_SEC', '8')),
        )
        try:
            while not self._stop_event.is_set():
                if self._should_stop_for_idle():
                    break
                if self._capture is None or not self._capture.isOpened():
                    self._set_status('source_waiting')
                    try:
                        self._capture = self._open_capture()
                        if self._capture is None or not self._capture.isOpened():
                            raise RuntimeError('源流未成功打开')
                        self._connected_monotonic = time.monotonic()
                        self._gray_bad_streak = 0
                        # Capture 打开不代表已经收到首帧，保持等待状态直到成功发布。
                        self._set_status('source_waiting')
                    except Exception as exc:
                        self._reconnect_count += 1
                        self._set_status('source_waiting', str(exc))
                        self._release_capture()
                        self._stop_event.wait(reconnect_delay)
                        continue

                capture = self._capture
                if capture is None:
                    continue
                try:
                    ret, frame = capture.read()
                except Exception as exc:
                    self._reconnect_count += 1
                    self._set_status('source_waiting', f'源流读取异常: {exc}')
                    self._release_capture()
                    self._stop_event.wait(reconnect_delay)
                    continue
                if not ret or frame is None:
                    last_frame_reference = (
                        self._last_frame_monotonic or self._connected_monotonic
                    )
                    source_stalled = (
                        last_frame_reference > 0
                        and time.monotonic() - last_frame_reference >= stale_frame_seconds
                    )
                    if (
                            getattr(capture, 'read_failed', False)
                            or not capture.isOpened()
                            or source_stalled
                    ):
                        self._reconnect_count += 1
                        if self.is_gb28181:
                            self._gb_use_alternate_next = True
                        error_message = '源流超过时限没有新帧' if source_stalled else '源流读取失败'
                        self._set_status('source_waiting', error_message)
                        self._release_capture()
                        self._stop_event.wait(reconnect_delay)
                    else:
                        time.sleep(0.005)
                    continue
                if self._is_flat_corrupt_frame(frame):
                    self._gray_bad_streak += 1
                    if self._gray_bad_streak >= self._gray_streak_required:
                        self._reconnect_count += 1
                        self._set_status('source_waiting', '连续帧疑似解码灰屏')
                        self._release_capture()
                        self._gray_bad_streak = 0
                        self._stop_event.wait(reconnect_delay)
                    continue
                self._gray_bad_streak = 0
                self._write_frame(frame, time.time())
        except Exception as exc:
            logger.error('共享源流线程异常 device_id=%s: %s', self.device_id, exc, exc_info=True)
            self._fatal_error = str(exc)
            self._set_status('failed', str(exc))
        finally:
            with self._ready_condition:
                self._lifecycle = 'closing'
                self._stop_event.set()
            self._release_capture()
            ring = self._ring
            self._ring = None
            if ring is not None:
                ring.close(unlink=True)
            with self._ready_condition:
                self._status = 'failed' if self._fatal_error else 'stopped'
                if self._fatal_error:
                    self._error_message = self._fatal_error
                self._lifecycle = 'stopped'
                self._ready_condition.notify_all()

    def close(self) -> None:
        with self._ready_condition:
            if self._lifecycle == 'stopped':
                return
            self._lifecycle = 'closing'
            self._stop_event.set()
        self._release_capture()
        if self._thread_started and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        elif not self._thread_started:
            with self._ready_condition:
                self._status = 'stopped'
                self._lifecycle = 'stopped'


class CameraSourceManager:
    """节点级摄像头源流会话管理器。"""

    def __init__(
            self,
            *,
            stream_opener: Optional[Callable] = None,
            slot_count: Optional[int] = None,
            idle_grace_seconds: Optional[float] = None,
            subscriber_timeout_seconds: Optional[float] = None,
    ):
        self._stream_opener = stream_opener or _default_stream_opener
        cleanup_stale_shared_frame_files()
        self._slot_count = int(slot_count or os.getenv('CAMERA_SOURCE_RING_SLOTS', '2'))
        self._idle_grace_seconds = float(
            idle_grace_seconds
            if idle_grace_seconds is not None
            else os.getenv('CAMERA_SOURCE_IDLE_GRACE_SEC', '15')
        )
        self._subscriber_timeout_seconds = float(
            subscriber_timeout_seconds
            if subscriber_timeout_seconds is not None
            else os.getenv('CAMERA_SOURCE_SUBSCRIBER_TIMEOUT_SEC', '45')
        )
        self._max_sources = max(
            1,
            int(os.getenv('CAMERA_SOURCE_MAX_SOURCES', '64')),
        )
        self._lock = threading.RLock()
        self._sessions: Dict[str, CameraSourceSession] = {}
        self._failure_tombstones: Dict[str, tuple[float, Dict]] = {}
        self._failure_ttl_seconds = max(
            1.0,
            float(os.getenv('CAMERA_SOURCE_FAILURE_TTL_SEC', '300')),
        )
        self._closed = False
        self._sweeper_stop = threading.Event()
        self._sweeper = threading.Thread(
            target=self._sweep_sessions,
            daemon=True,
            name='camera_source_sweeper',
        )
        self._sweeper.start()

    def subscribe(
            self,
            task_id: int,
            device_id: str,
            source_url: str,
            *,
            original_source: Optional[str] = None,
            is_gb28181: bool = False,
            subscriber_id: Optional[str] = None,
            wait_timeout: float = 5.0,
    ) -> Dict:
        if self._closed:
            raise RuntimeError('CameraSourceManager 已关闭')
        if not device_id or not source_url:
            raise ValueError('device_id 和 source_url 不能为空')
        try:
            normalized_task_id = int(task_id)
        except (TypeError, ValueError) as exc:
            raise ValueError('task_id 必须是正整数') from exc
        if normalized_task_id <= 0:
            raise ValueError('task_id 必须是正整数')
        normalized_device_id = str(device_id)
        while True:
            with self._lock:
                session = self._sessions.get(normalized_device_id)
                if session is None or session.stopped:
                    active_source_count = sum(
                        1 for item in self._sessions.values() if not item.stopped
                    )
                    if active_source_count >= self._max_sources:
                        raise RuntimeError(
                            f'共享摄像头源数量达到上限: {self._max_sources}'
                        )
                    session = CameraSourceSession(
                        device_id=normalized_device_id,
                        source_url=str(source_url),
                        stream_opener=self._stream_opener,
                        slot_count=self._slot_count,
                        idle_grace_seconds=self._idle_grace_seconds,
                        subscriber_timeout_seconds=self._subscriber_timeout_seconds,
                        original_source=original_source,
                        is_gb28181=is_gb28181,
                    )
                    self._sessions[normalized_device_id] = session
                    self._failure_tombstones.pop(normalized_device_id, None)
                elif (
                        session.configured_source_url != str(source_url)
                        or session.original_source != original_source
                        or session.is_gb28181 != bool(is_gb28181)
                ):
                    try:
                        session.update_source(
                            str(source_url),
                            original_source=original_source,
                            is_gb28181=is_gb28181,
                        )
                    except CameraSourceSessionClosing:
                        if self._sessions.get(normalized_device_id) is session:
                            self._sessions.pop(normalized_device_id, None)
                        continue
            try:
                return session.subscribe(
                    normalized_task_id,
                    subscriber_id=subscriber_id,
                    wait_timeout=wait_timeout,
                )
            except CameraSourceSessionClosing:
                # 空闲回收已经决定关闭旧会话，替换后重试订阅。
                with self._lock:
                    if self._sessions.get(normalized_device_id) is session:
                        self._sessions.pop(normalized_device_id, None)

    def unsubscribe(
            self,
            task_id: int,
            device_id: str,
            *,
            subscriber_id: Optional[str] = None,
    ) -> None:
        with self._lock:
            session = self._sessions.get(str(device_id))
        if session is not None:
            session.unsubscribe(task_id, subscriber_id=subscriber_id)

    def status(self, device_id: Optional[str] = None):
        now = time.monotonic()
        with self._lock:
            self._expire_failure_tombstones_locked(now)
            if device_id is not None:
                session = self._sessions.get(str(device_id))
                if session is not None and not session.stopped:
                    return session.status()
                tombstone = self._failure_tombstones.get(str(device_id))
                return dict(tombstone[1]) if tombstone else None
            sessions = list(self._sessions.values())
            tombstones = [dict(item[1]) for item in self._failure_tombstones.values()]
        active_states = [session.status() for session in sessions if not session.stopped]
        active_device_ids = {str(item.get('device_id')) for item in active_states}
        return active_states + [
            item for item in tombstones
            if str(item.get('device_id')) not in active_device_ids
        ]

    def _expire_failure_tombstones_locked(self, now: float) -> None:
        expired_device_ids = [
            device_id
            for device_id, (expires_at, _state) in self._failure_tombstones.items()
            if expires_at <= now
        ]
        for device_id in expired_device_ids:
            self._failure_tombstones.pop(device_id, None)

    def _sweep_sessions(self) -> None:
        while not self._sweeper_stop.wait(0.05):
            stopped_sessions = []
            with self._lock:
                for device_id, session in list(self._sessions.items()):
                    if session.stopped:
                        terminal_state = session.status()
                        if terminal_state.get('status') == 'failed':
                            self._failure_tombstones[device_id] = (
                                time.monotonic() + self._failure_ttl_seconds,
                                terminal_state,
                            )
                        stopped_sessions.append(session)
                        self._sessions.pop(device_id, None)
                self._expire_failure_tombstones_locked(time.monotonic())
            for session in stopped_sessions:
                session.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._sweeper_stop.set()
        if self._sweeper.is_alive():
            self._sweeper.join(timeout=1.0)
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
            self._failure_tombstones.clear()
        for session in sessions:
            session.close()
