"""
RTSP 推理管道：推流与检测分离，固定帧率推流 + overlay 缓存叠框（对齐 VIDEO 算法任务）。
"""
from __future__ import annotations

import logging
import os
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Set

import numpy as np

from app.utils.algorithm_detection_draw import draw_algorithm_detections
from app.utils.stream_detect_utils import run_stream_detection


class RtspStreamPipeline:
    """读帧 → 叠 overlay 缓存 → 固定速率推流；检测在独立线程异步执行。"""

    def __init__(
        self,
        *,
        reader,
        ffmpeg_process,
        model,
        detect_config: Dict[str, Any],
        stop_event: threading.Event,
        class_ids: Optional[Set[int]] = None,
        extract_interval: int = 5,
        output_fps: Optional[float] = None,
        log_interval: int = 150,
    ):
        self.reader = reader
        self.ffmpeg_process = ffmpeg_process
        self.model = model
        self.detect_config = detect_config
        self.stop_event = stop_event
        self.class_ids = class_ids
        self.extract_interval = max(1, int(extract_interval))
        self.log_interval = max(1, int(log_interval))

        src_fps = float(reader.fps or 25)
        cap_fps = int(os.getenv('STREAM_OUTPUT_FPS', os.getenv('AI_OUTPUT_FPS', '25')))
        self.output_fps = max(1, min(int(output_fps or src_fps), cap_fps))

        self._overlay_lock = threading.Lock()
        self._latest_overlay: Optional[List[Dict[str, Any]]] = None

        self._output_lock = threading.Lock()
        self._output_frame: Optional[np.ndarray] = None

        self._detect_queue: queue.Queue = queue.Queue(maxsize=1)
        self._push_stop = threading.Event()
        self._push_failure = threading.Event()
        self._push_error: Optional[str] = None

    def run(self) -> None:
        detect_thread = threading.Thread(
            target=self._detection_worker,
            daemon=True,
            name='rtsp-overlay-detect',
        )
        push_thread = threading.Thread(
            target=self._fixed_rate_push_worker,
            daemon=True,
            name='rtsp-fixed-push',
        )
        detect_thread.start()
        push_thread.start()
        logging.info(
            'RTSP 异步管道启动: output_fps=%s overlay_interval=%s conf=%.2f imgsz=%s',
            self.output_fps,
            self.extract_interval,
            float(self.detect_config.get('conf', 0.5)),
            self.detect_config.get('imgsz'),
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
        logging.error(message)

    def _enqueue_detection(self, frame: np.ndarray, frame_number: int) -> None:
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

    def _detection_worker(self) -> None:
        while not self.stop_event.is_set():
            try:
                payload = self._detect_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            frame = payload['frame']
            frame_number = payload['frame_number']
            try:
                detections = run_stream_detection(
                    self.model,
                    frame,
                    conf=float(self.detect_config['conf']),
                    iou=float(self.detect_config['iou']),
                    imgsz=int(self.detect_config['imgsz']),
                    infer_device=str(self.detect_config.get('infer_device', 'cpu')),
                    class_ids=self.class_ids,
                )
                with self._overlay_lock:
                    self._latest_overlay = detections
                if frame_number == 1 or frame_number % self.log_interval == 0:
                    logging.info(
                        'RTSP overlay检测 frame=%s detections=%s conf=%.2f imgsz=%s',
                        frame_number,
                        len(detections),
                        float(self.detect_config['conf']),
                        self.detect_config.get('imgsz'),
                    )
            except Exception as exc:
                logging.warning('RTSP overlay检测失败 frame=%s: %s', frame_number, exc)

    def _apply_overlay(self, frame: np.ndarray) -> np.ndarray:
        with self._overlay_lock:
            overlay = self._latest_overlay
        if overlay:
            return draw_algorithm_detections(frame, overlay)
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
                self._enqueue_detection(frame, frame_number)

            annotated = np.ascontiguousarray(self._apply_overlay(frame))
            with self._output_lock:
                self._output_frame = annotated

    def _fixed_rate_push_worker(self) -> None:
        """固定帧率推帧：AI 处理慢时重复上一帧，避免卡顿快进。"""
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
                self._fail_push('RTSP 推流进程未启动')
                break
            return_code = proc.poll()
            if return_code is not None:
                self._fail_push(f'RTSP 推流进程已退出，exit={return_code}')
                break
            if proc.stdin is None:
                self._fail_push('RTSP 推流进程缺少标准输入管道')
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
                self._fail_push('RTSP 推流管道已断开，请检查 SRS 发布地址与服务状态')
                break
            except Exception as exc:
                self._fail_push(f'RTSP 固定推帧失败: {exc}')
                break
