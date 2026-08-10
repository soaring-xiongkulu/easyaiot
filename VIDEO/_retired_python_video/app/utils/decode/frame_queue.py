"""
解码帧队列 — 解码快于推理时的缓冲层，带时间戳与丢帧统计。
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional

import numpy as np

from .shared_memory import FrameHeader


@dataclass
class QueuedFrame:
    header: FrameHeader
    frame: np.ndarray
    enqueue_time_ns: int = field(default_factory=time.time_ns)

    @property
    def queue_delay_ms(self) -> float:
        return (time.time_ns() - self.enqueue_time_ns) / 1_000_000


@dataclass
class FrameQueueStats:
    total_frames: int = 0
    dropped_frames: int = 0
    current_size: int = 0
    max_capacity: int = 0
    avg_queue_delay_ms: float = 0.0
    min_queue_delay_ms: float = 0.0
    max_queue_delay_ms: float = 0.0


class FrameQueue:
    """线程安全 FIFO；满时丢弃最旧帧，保证解码线程不被推理阻塞。"""

    def __init__(self, max_size: int = 5):
        self.max_size = max(1, int(max_size))
        self._queue: Deque[QueuedFrame] = deque(maxlen=self.max_size)
        self._lock = threading.Lock()
        self._stats = FrameQueueStats(max_capacity=self.max_size)
        self._delay_history: List[float] = []
        self._dequeue_count = 0

    def enqueue(self, header: FrameHeader, frame: np.ndarray) -> bool:
        with self._lock:
            is_full = len(self._queue) >= self.max_size
            if is_full:
                self._stats.dropped_frames += 1
            q_frame = QueuedFrame(
                header=header,
                frame=frame.copy(),
                enqueue_time_ns=time.time_ns(),
            )
            self._queue.append(q_frame)
            self._stats.total_frames += 1
            self._stats.current_size = len(self._queue)
            return not is_full

    def dequeue(self) -> Optional[QueuedFrame]:
        with self._lock:
            if not self._queue:
                return None
            q_frame = self._queue.popleft()
            self._dequeue_count += 1
            self._stats.current_size = len(self._queue)
            self._record_delay(q_frame.queue_delay_ms)
            return q_frame

    def dequeue_latest(self) -> Optional[QueuedFrame]:
        """取最新帧并清空队列（推理跟不上时用）。"""
        with self._lock:
            if not self._queue:
                return None
            q_frame = self._queue[-1]
            skipped = max(0, len(self._queue) - 1)
            self._stats.dropped_frames += skipped
            self._queue.clear()
            self._dequeue_count += 1
            self._stats.current_size = 0
            self._record_delay(q_frame.queue_delay_ms)
            return q_frame

    def peek(self) -> Optional[QueuedFrame]:
        with self._lock:
            return self._queue[0] if self._queue else None

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def clear(self) -> None:
        with self._lock:
            self._queue.clear()
            self._stats.current_size = 0

    def get_stats(self) -> FrameQueueStats:
        with self._lock:
            return FrameQueueStats(
                total_frames=self._stats.total_frames,
                dropped_frames=self._stats.dropped_frames,
                current_size=self._stats.current_size,
                max_capacity=self.max_size,
                avg_queue_delay_ms=self._stats.avg_queue_delay_ms,
                min_queue_delay_ms=self._stats.min_queue_delay_ms,
                max_queue_delay_ms=self._stats.max_queue_delay_ms,
            )

    def _record_delay(self, delay_ms: float) -> None:
        self._delay_history.append(delay_ms)
        if len(self._delay_history) > 100:
            self._delay_history = self._delay_history[-100:]
        self._stats.avg_queue_delay_ms = sum(self._delay_history) / len(self._delay_history)
        self._stats.min_queue_delay_ms = min(self._delay_history)
        self._stats.max_queue_delay_ms = max(self._delay_history)
