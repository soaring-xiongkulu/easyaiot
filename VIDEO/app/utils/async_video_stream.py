"""
OpenCV 网络流异步解码：后台线程持续 VideoCapture.read()，主线程从缓冲取帧。
供 realtime_algorithm_service、stream_forward_service、snapshot_algorithm_service 等共用。

环境变量：
- AI_RTSP_ASYNC_READ（默认开启）。
- AI_RTSP_ASYNC_QUEUE_MAX（默认 1）：异步缓冲深度；1 表示只保留「最新一帧」（追实时）；
  大于 1 时为 FIFO，恢复解码突增时可按序播放，减轻画面/OSD 突然跳几秒。
"""
from __future__ import annotations

import os
import threading
from collections import deque
from typing import Optional

import cv2


def async_rtsp_queue_max() -> int:
    """异步解码侧 FIFO 缓冲帧数；1 表示仅保留最新帧（与旧行为一致）。"""
    raw = (os.getenv("AI_RTSP_ASYNC_QUEUE_MAX", "1") or "1").strip()
    try:
        v = int(raw)
    except ValueError:
        return 1
    return max(1, min(v, 600))


class AsyncVideoStream:
    """
    后台线程持续调用 VideoCapture.read() 解码。

    queue_max==1：主线程始终取最新帧（中间帧丢弃），低延迟、追实时。
    queue_max>1：解码帧进入定长 FIFO，主线程按序取帧；队列满时丢弃最旧帧（上限延迟）。
    """

    def __init__(self, capture: cv2.VideoCapture, queue_max: Optional[int] = None):
        self._cap = capture
        qm = async_rtsp_queue_max() if queue_max is None else queue_max
        try:
            self.queue_max = max(1, int(qm))
        except (TypeError, ValueError):
            self.queue_max = 1

        self._lock = threading.Lock()
        self._frame = None
        self._queue: Optional[deque] = None
        if self.queue_max > 1:
            self._queue = deque(maxlen=self.queue_max)

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.read_failed = False
        self._consecutive_read_failures = 0
        try:
            self._read_fail_streak_limit = max(
                1,
                int((os.getenv("AI_RTSP_READ_FAIL_STREAK", "30") or "30").strip()),
            )
        except ValueError:
            self._read_fail_streak_limit = 30

    def isOpened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def set(self, prop, value):
        return self._cap.set(prop, value)

    def read(self):
        """与 cv2.VideoCapture.read 一致，返回 (ret, frame)。"""
        if self.read_failed:
            return False, None
        with self._lock:
            if self._queue is not None:
                if len(self._queue) == 0:
                    return False, None
                return True, self._queue.popleft().copy()
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def start(self):
        self._running = True
        self.read_failed = False
        self._consecutive_read_failures = 0
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        return self

    def _update_loop(self):
        try:
            while self._running:
                ret, frame = self._cap.read()
                if not ret or frame is None:
                    if self._running:
                        self._consecutive_read_failures += 1
                        if self._consecutive_read_failures >= self._read_fail_streak_limit:
                            self.read_failed = True
                            break
                    continue
                self._consecutive_read_failures = 0
                with self._lock:
                    if self._queue is not None:
                        self._queue.append(frame)
                    else:
                        self._frame = frame
        except Exception:
            if self._running:
                self.read_failed = True

    def release(self):
        self._running = False
        cap = self._cap
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        self._cap = None
        with self._lock:
            self._frame = None
            if self._queue is not None:
                self._queue.clear()


def async_rtsp_read_enabled() -> bool:
    """是否对 rtsp/rtmp 使用异步拉流（默认开启）。"""
    v = (os.getenv("AI_RTSP_ASYNC_READ", "1") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")
