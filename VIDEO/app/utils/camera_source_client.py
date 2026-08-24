"""实时算法 Worker 的共享摄像头源流客户端。"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.utils.camera_source_shared_memory import SharedFrameRingReader


logger = logging.getLogger(__name__)


def camera_source_mode() -> str:
    """读取共享源流模式，支持 shared 与 direct。"""
    mode = (os.getenv('CAMERA_SOURCE_MODE') or 'shared').strip().lower()
    return 'shared' if mode == 'shared' else 'direct'


def camera_source_fallback_direct_enabled() -> bool:
    raw_value = (os.getenv('CAMERA_SOURCE_FALLBACK_DIRECT') or 'true').strip().lower()
    return raw_value not in ('0', 'false', 'no', 'off')


def camera_source_manager_url() -> str:
    explicit_url = (os.getenv('CAMERA_SOURCE_MANAGER_URL') or '').strip().rstrip('/')
    if explicit_url:
        return explicit_url
    port = int(os.getenv('CAMERA_SOURCE_MANAGER_PORT', '6010'))
    return f'http://127.0.0.1:{port}'


def _request_json(
        method: str,
        path: str,
        *,
        payload: Optional[Dict] = None,
        query: Optional[Dict] = None,
        timeout: float = 2.0,
) -> Dict:
    url = f'{camera_source_manager_url()}{path}'
    if query:
        url = f'{url}?{urlencode(query)}'
    request_data = None
    headers = {}
    control_token = (os.getenv('CAMERA_SOURCE_MANAGER_TOKEN') or '').strip()
    if control_token:
        headers['X-Camera-Source-Token'] = control_token
    if payload is not None:
        request_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request = Request(url, data=request_data, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode('utf-8'))
    if body.get('status') != 'ok':
        raise RuntimeError(body.get('error') or 'CameraSourceManager 请求失败')
    return body


def get_camera_source_status(device_id: Optional[str] = None):
    """查询节点级共享源流运行状态。"""
    query = {'device_id': device_id} if device_id else None
    return _request_json('GET', '/status', query=query, timeout=1.0).get('data')


class SharedCameraStream:
    """兼容 VideoCapture 读取接口的共享帧订阅。"""

    is_shared_camera_stream = True

    def __init__(
            self,
            *,
            task_id: int,
            device_id: str,
            source_url: str,
            original_source: Optional[str] = None,
            is_gb28181: bool = False,
            open_timeout_msec: int = 5000,
            read_timeout_msec: int = 2500,
    ):
        self.task_id = int(task_id)
        self.subscriber_id = uuid.uuid4().hex
        self.device_id = str(device_id)
        self.source_url = str(source_url)
        self.original_source = original_source
        self.is_gb28181 = bool(is_gb28181)
        self.open_timeout_msec = max(100, int(open_timeout_msec))
        self.read_timeout_msec = max(100, int(read_timeout_msec))
        self.queue_max = 1
        self.read_failed = False
        self._reader: Optional[SharedFrameRingReader] = None
        self._descriptor: Optional[Dict] = None
        self._last_sequence = 0
        self.last_frame_timestamp = 0.0
        self._last_frame_monotonic = time.monotonic()
        self._last_heartbeat_monotonic = 0.0
        self._last_heartbeat_attempt_monotonic = 0.0
        self._last_manager_success_monotonic = time.monotonic()
        self._released = False
        self._lock = threading.RLock()
        try:
            self._subscribe(wait_timeout=self.open_timeout_msec / 1000.0)
        except Exception:
            # 请求超时可能发生在 Manager 已登记订阅之后，尽量回滚幽灵订阅。
            self._best_effort_unsubscribe()
            raise

    def _subscription_payload(self, wait_timeout: float) -> Dict:
        return {
            'task_id': self.task_id,
            'subscriber_id': self.subscriber_id,
            'device_id': self.device_id,
            'source_url': self.source_url,
            'original_source': self.original_source,
            'is_gb28181': self.is_gb28181,
            'sampling_fps': 0,
            'wait_timeout': max(0.0, float(wait_timeout)),
        }

    def _subscribe(self, *, wait_timeout: float) -> None:
        body = _request_json(
            'POST',
            '/subscribe',
            payload=self._subscription_payload(wait_timeout),
            timeout=max(1.0, wait_timeout + 1.0),
        )
        descriptor = body.get('data') or {}
        shared_memory_name = descriptor.get('shared_memory_name')
        with self._lock:
            self._descriptor = descriptor
            self._last_heartbeat_monotonic = time.monotonic()
            self._last_heartbeat_attempt_monotonic = self._last_heartbeat_monotonic
            self._last_manager_success_monotonic = self._last_heartbeat_monotonic
            self.read_failed = False
            descriptor_status = str(descriptor.get('status') or '')
            if descriptor_status == 'failed':
                self.read_failed = True
                raise RuntimeError(
                    descriptor.get('error_message')
                    or f'CameraSourceManager 源流失败: device_id={self.device_id}'
                )
            if not shared_memory_name:
                # Manager 已接受订阅但摄像头尚未产生首帧，保持 shared pending。
                return

            stale_seconds = self._stale_seconds()
            latest_timestamp = float(descriptor.get('latest_timestamp') or 0.0)
            if (
                    self._reader is None
                    and (
                        descriptor_status != 'streaming'
                        or latest_timestamp <= 0
                        or time.time() - latest_timestamp > stale_seconds
                    )
            ):
                # 断流期间 Manager 会保留旧环，不能把最后一帧当成新鲜首帧重放。
                return

            reader_name = (
                self._reader.descriptor.get('shared_memory_name')
                if self._reader is not None else None
            )
            if self._reader is None or reader_name != shared_memory_name:
                new_reader = SharedFrameRingReader.attach(descriptor)
                old_reader = self._reader
                self._reader = new_reader
                self._last_sequence = 0
                if old_reader is not None:
                    old_reader.close()

    def _stale_seconds(self) -> float:
        return max(
            self.read_timeout_msec / 1000.0 * 2.0,
            float(os.getenv('CAMERA_SOURCE_STALE_FRAME_SEC', '8')),
        )

    def _heartbeat_if_due(self) -> None:
        heartbeat_interval = max(
            1.0,
            float(os.getenv('CAMERA_SOURCE_HEARTBEAT_INTERVAL_SEC', '5')),
        )
        now = time.monotonic()
        if now - self._last_heartbeat_attempt_monotonic < heartbeat_interval:
            return
        self._last_heartbeat_attempt_monotonic = now
        try:
            self._subscribe(wait_timeout=0.2)
        except Exception as exc:
            # 控制面短暂失败时仍继续消费现有 mmap 数据，避免心跳拖死数据面。
            logger.warning(
                '共享源流心跳失败，继续读取现有帧: task_id=%s, device_id=%s, error=%s',
                self.task_id,
                self.device_id,
                exc,
            )

    def isOpened(self) -> bool:
        # 没有 Reader 但 Manager 已接受订阅时属于 source_waiting，而不是打开失败。
        return not self._released and not self.read_failed

    def is_ready(self) -> bool:
        """共享源已经有新鲜帧，可无中断替换独立拉流。"""
        if self._released or self.read_failed:
            return False
        self._heartbeat_if_due()
        with self._lock:
            if (
                    time.monotonic() - self._last_manager_success_monotonic
                    > self._stale_seconds()
            ):
                self.read_failed = True
                return False
            descriptor = self._descriptor or {}
            return bool(
                self._reader is not None
                and not self.read_failed
                and descriptor.get('status') == 'streaming'
                and float(descriptor.get('latest_timestamp') or 0.0) > 0
                and time.time() - float(descriptor.get('latest_timestamp') or 0.0)
                <= self._stale_seconds()
            )

    def read(self):
        if self._released:
            self.read_failed = True
            return False, None
        try:
            self._heartbeat_if_due()
            with self._lock:
                reader = self._reader
                last_sequence = self._last_sequence
            if reader is None:
                if (
                        time.monotonic() - self._last_manager_success_monotonic
                        > self._stale_seconds()
                ):
                    self.read_failed = True
                return False, None
            packet = reader.read_latest(after_sequence=last_sequence)
            if packet is None:
                frame_stale = (
                    time.monotonic() - self._last_frame_monotonic > self._stale_seconds()
                )
                manager_stale = (
                    time.monotonic() - self._last_manager_success_monotonic
                    > self._stale_seconds()
                )
                if frame_stale and manager_stale:
                    self.read_failed = True
                return False, None

            import numpy as np

            frame = np.frombuffer(packet.data, dtype=np.uint8).reshape(packet.shape).copy()
            with self._lock:
                self._last_sequence = packet.sequence
                self.last_frame_timestamp = packet.timestamp
                self._last_frame_monotonic = time.monotonic()
                self.read_failed = False
            return True, frame
        except Exception as exc:
            logger.debug('读取共享源流失败 device_id=%s: %s', self.device_id, exc)
            if (
                    time.monotonic() - self._last_frame_monotonic > self._stale_seconds()
                    and time.monotonic() - self._last_manager_success_monotonic
                    > self._stale_seconds()
            ):
                self.read_failed = True
            return False, None

    def get(self, prop):
        try:
            import cv2

            if prop == cv2.CAP_PROP_FPS and self._descriptor:
                return float(self._descriptor.get('decode_fps') or 0.0)
        except Exception:
            pass
        return 0.0

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        with self._lock:
            reader = self._reader
            self._reader = None
        if reader is not None:
            reader.close()
        self._best_effort_unsubscribe()

    def _best_effort_unsubscribe(self) -> None:
        try:
            _request_json(
                'POST',
                '/unsubscribe',
                payload={
                    'task_id': self.task_id,
                    'device_id': self.device_id,
                    'subscriber_id': self.subscriber_id,
                },
                timeout=0.8,
            )
        except Exception:
            pass


def open_shared_camera_stream(
        source_url: str,
        device_id: str,
        *,
        task_id: int,
        original_source: Optional[str] = None,
        is_gb28181: bool = False,
        open_timeout_msec: int = 5000,
        read_timeout_msec: int = 2500,
) -> SharedCameraStream:
    """订阅节点级 CameraSourceManager 的共享帧。"""
    return SharedCameraStream(
        task_id=task_id,
        device_id=device_id,
        source_url=source_url,
        original_source=original_source,
        is_gb28181=is_gb28181,
        open_timeout_msec=open_timeout_msec,
        read_timeout_msec=read_timeout_msec,
    )


def open_task_camera_stream(
        source_url: str,
        device_id: str,
        *,
        task_id: int,
        original_source: Optional[str] = None,
        is_gb28181: bool = False,
        open_timeout_msec: int = 5000,
        read_timeout_msec: int = 2500,
        queue_max_override: Optional[int] = None,
) -> Tuple[object, str]:
    """优先共享拉流，失败时按开关降级为任务独立拉流。"""
    if camera_source_mode() == 'shared':
        try:
            return open_shared_camera_stream(
                source_url,
                device_id,
                task_id=task_id,
                original_source=original_source,
                is_gb28181=is_gb28181,
                open_timeout_msec=open_timeout_msec,
                read_timeout_msec=read_timeout_msec,
            ), 'shared'
        except Exception as exc:
            logger.warning(
                '订阅共享源流失败，准备按配置降级: task_id=%s, device_id=%s, error=%s',
                task_id,
                device_id,
                exc,
            )
            if not camera_source_fallback_direct_enabled():
                raise

    from app.utils.decode.stream_adapter import open_device_stream

    direct_source_url = source_url
    if is_gb28181 and original_source:
        from app.utils.gb28181_source import resolve_gb28181_source

        resolved_source_url = resolve_gb28181_source(original_source, logger=logger)
        if resolved_source_url:
            direct_source_url = resolved_source_url

    direct_stream = open_device_stream(
        direct_source_url,
        device_id,
        task_id=str(task_id),
        open_timeout_msec=open_timeout_msec,
        read_timeout_msec=read_timeout_msec,
        queue_max_override=queue_max_override,
    )
    if (
            is_gb28181
            and original_source
            and direct_stream is not None
            and not direct_stream.isOpened()
    ):
        try:
            from app.utils.gb28181_source import resolve_gb28181_alternate_pull_url

            alternate_url = resolve_gb28181_alternate_pull_url(
                original_source,
                direct_source_url,
                logger=logger,
            )
            if alternate_url and alternate_url != direct_source_url:
                direct_stream.release()
                direct_stream = open_device_stream(
                    alternate_url,
                    device_id,
                    task_id=str(task_id),
                    open_timeout_msec=open_timeout_msec,
                    read_timeout_msec=read_timeout_msec,
                    queue_max_override=queue_max_override,
                )
        except Exception as exc:
            logger.warning('GB28181 独立拉流备用地址打开失败 device_id=%s: %s', device_id, exc)

    return direct_stream, 'direct_fallback' if camera_source_mode() == 'shared' else 'direct'


def is_shared_camera_stream(stream) -> bool:
    return bool(getattr(stream, 'is_shared_camera_stream', False))
