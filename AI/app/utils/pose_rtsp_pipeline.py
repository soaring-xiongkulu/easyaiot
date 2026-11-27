"""
RTSP 姿态推流管道：固定帧率推流 + 异步姿态推理叠画。
"""
from __future__ import annotations

import logging
import os
import queue
import threading
import time
from typing import Optional

import numpy as np

from app.utils.pose_inference import predict_pose_frame

logger = logging.getLogger(__name__)


class PoseRtspStreamPipeline:
    """读帧 → 叠姿态 overlay → 固定速率推流；推理在独立线程异步执行。"""

    def __init__(
        self,
        *,
        reader,
        ffmpeg_process,
        model,
        stop_event: threading.Event,
        conf: float = 0.25,
        extract_interval: int = 5,
        output_fps: Optional[float] = None,
        log_interval: int = 150,
    ):
        self.reader = reader
        self.ffmpeg_process = ffmpeg_process
        self.model = model
        self.stop_event = stop_event
        self.conf = float(conf)
        self.extract_interval = max(1, int(extract_interval))
        self.log_interval = max(1, int(log_interval))

        src_fps = float(reader.fps or 25)
        cap_fps = int(os.getenv('STREAM_OUTPUT_FPS', os.getenv('AI_OUTPUT_FPS', '25')))
        self.output_fps = max(1, min(int(output_fps or src_fps), cap_fps))

        self._overlay_lock = threading.Lock()
        self._latest_plotted: Optional[np.ndarray] = None

        self._output_lock = threading.Lock()
        self._output_frame: Optional[np.ndarray] = None

        self._detect_queue: queue.Queue = queue.Queue(maxsize=1)
        self._push_stop = threading.Event()
        self._push_failure = threading.Event()
        self._push_error: Optional[str] = None

    def run(self) -> None:
        detect_thread = threading.Thread(
            target=self._pose_worker,
            daemon=True,
            name='rtsp-pose-detect',
        )
        push_thread = threading.Thread(
            target=self._fixed_rate_push_worker,
            daemon=True,
            name='rtsp-pose-push',
        )
        detect_thread.start()
        push_thread.start()
        logger.info(
            'RTSP 姿态管道启动: output_fps=%s overlay_interval=%s conf=%.2f',
            self.output_fps,
            self.extract_interval,
            self.conf,
        )
        try:
            self._read_loop()
        finally:
            self._push_stop.set()
            detect_thread.join(timeout=3)
            push_thread.join(timeout=3)
        if self._push_error:
            raise RuntimeError(self._push_error)

    def _fail_push(self, message: str) -> None:
        if self.stop_event.is_set() or self._push_stop.is_set():
            return
        self._push_error = message
        self._push_failure.set()
        logger.error(message)

    def _enqueue_pose(self, frame: np.ndarray, frame_number: int) -> None:
        payload = {'frame': frame.copy(), 'frame_number': frame_number}
        while not self._detect_queue.empty():
            try:
                self._detect_queue.get_nowait()
            except queue.Empty:
                break
        try:
            self._detect_queue.put(payload, timeout=0.05)
        except queue.Full:
            pass

    def _pose_worker(self) -> None:
        while not self.stop_event.is_set():
            try:
                payload = self._detect_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            frame = payload['frame']
            frame_number = payload['frame_number']
            try:
                plotted = predict_pose_frame(self.model, frame, conf=self.conf)
                with self._overlay_lock:
                    self._latest_plotted = plotted
                if frame_number == 1 or frame_number % self.log_interval == 0:
                    logger.info('RTSP 姿态推理 frame=%s conf=%.2f', frame_number, self.conf)
            except Exception as exc:
                logger.warning('RTSP 姿态推理失败 frame=%s: %s', frame_number, exc)

    def _apply_overlay(self, frame: np.ndarray) -> np.ndarray:
        with self._overlay_lock:
            plotted = self._latest_plotted
        if plotted is not None:
            return plotted
        return frame

    def _read_loop(self) -> None:
        frame_number = 0
        while (
            self.reader.alive
            and not self.stop_event.is_set()
            and not self._push_failure.is_set()
        ):
            frame = self.reader.read()
            if frame is None:
                time.sleep(0.02)
                continue

            frame_number += 1
            if frame_number == 1 or frame_number % self.extract_interval == 0:
                self._enqueue_pose(frame, frame_number)

            annotated = np.ascontiguousarray(self._apply_overlay(frame))
            with self._output_lock:
                self._output_frame = annotated

    def _fixed_rate_push_worker(self) -> None:
        interval = 1.0 / self.output_fps
        last_push_time = time.perf_counter()
        last_frame: Optional[np.ndarray] = None
        push_count = 0
        flush_every = max(1, int(os.getenv('AI_PUSH_FLUSH_EVERY', '5')))

        while not self.stop_event.is_set() and not self._push_stop.is_set():
            target_time = last_push_time + interval
            now = time.perf_counter()
            sleep_duration = target_time - now
            if sleep_duration > 0:
                time.sleep(sleep_duration)
            elif sleep_duration < -interval * 2:
                last_push_time = time.perf_counter()
                time.sleep(interval)
            last_push_time = time.perf_counter()

            proc = self.ffmpeg_process
            if proc is None:
                self._fail_push('RTSP 姿态推流进程未启动')
                break
            return_code = proc.poll()
            if return_code is not None:
                self._fail_push(f'RTSP 姿态推流进程已退出，exit={return_code}')
                break
            if proc.stdin is None:
                self._fail_push('RTSP 姿态推流进程缺少标准输入管道')
                break

            with self._output_lock:
                frame = self._output_frame
            if frame is not None:
                last_frame = frame
            if last_frame is None:
                time.sleep(0.005)
                continue

            try:
                proc.stdin.write(last_frame.tobytes())
                if push_count % flush_every == 0:
                    proc.stdin.flush()
                push_count += 1
            except BrokenPipeError:
                self._fail_push('RTSP 姿态推流管道已断开，请检查 SRS 发布地址与服务状态')
                break
            except Exception as exc:
                self._fail_push(f'RTSP 姿态推帧失败: {exc}')
                break
