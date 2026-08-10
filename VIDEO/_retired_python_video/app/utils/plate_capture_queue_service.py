"""
车牌抓取独立队列：与主算法检测/告警链路解耦，避免 ONNX 车牌识别拖慢实时任务。

主链路仅 copy 帧并入队；专用 Worker 线程执行 detect+OCR → Kafka 投递。
"""
import logging
import os
import queue
import threading
from concurrent import futures
from datetime import datetime
from typing import Any, Dict, Optional

import cv2
import numpy as np
import requests

from app.utils.plate_capture_service import detect_and_recognize_plates

logger = logging.getLogger(__name__)

PLATE_CAPTURE_QUEUE_SIZE = int(os.getenv('PLATE_CAPTURE_QUEUE_SIZE', '8'))
PLATE_CAPTURE_WORKER_THREADS = int(os.getenv('PLATE_CAPTURE_WORKER_THREADS', '1'))
PLATE_CAPTURE_KEEP_LATEST = os.getenv('PLATE_CAPTURE_KEEP_LATEST', 'true').lower() in ('1', 'true', 'yes')
PLATE_CAPTURE_KEEP_LATEST_THRESHOLD = int(
    os.getenv('PLATE_CAPTURE_KEEP_LATEST_THRESHOLD', str(max(2, PLATE_CAPTURE_QUEUE_SIZE // 2)))
)

_queue: Optional[queue.Queue] = None
_executor: Optional[futures.ThreadPoolExecutor] = None
_stop_event: Optional[threading.Event] = None
_running = False
_lock = threading.Lock()


def is_running() -> bool:
    return _running


def _video_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _save_plate_crop_image(
    frame: np.ndarray,
    task_id: int,
    device_id: str,
    frame_number: int,
    detection: Dict[str, Any],
) -> Optional[str]:
    try:
        rect = detection.get('rect') or []
        if len(rect) < 4:
            return None
        x1, y1, x2, y2 = [int(v) for v in rect[:4]]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return None
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        images_root = os.getenv('PLATE_IMAGES_DIR', os.path.join(_video_root(), 'data', 'plate_images'))
        plate_dir = os.path.join(images_root, f'task_{task_id}', device_id, 'matching')
        os.makedirs(plate_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plate_no = (detection.get('plate_no') or 'unknown').replace('/', '_')
        image_filename = f"{timestamp}_frame{frame_number}_{plate_no}.jpg"
        image_path = os.path.join(plate_dir, image_filename)
        cv2.imwrite(image_path, crop)
        return image_path
    except Exception as exc:
        logger.error("保存车牌裁剪图失败: %s", exc, exc_info=True)
        return None


def _publish_plate_matching(payload: Dict[str, Any], publish_url: str) -> None:
    try:
        response = requests.post(
            publish_url,
            json=payload,
            timeout=5,
            headers={'Content-Type': 'application/json'},
        )
        if response.status_code == 200:
            logger.info(
                "车牌匹配消息已投递: device_id=%s, task_id=%s, plate_no=%s",
                payload.get('deviceId'),
                payload.get('taskId'),
                payload.get('plateNo'),
            )
        else:
            logger.warning(
                "车牌匹配消息投递失败: status=%s, body=%s",
                response.status_code,
                response.text,
            )
    except requests.exceptions.RequestException as exc:
        logger.warning("车牌匹配消息投递异常: %s", exc)


def _process_task(task: Dict[str, Any]) -> None:
    frame = task.get('frame')
    if frame is None:
        return

    try:
        plate_detections = detect_and_recognize_plates(frame)
    except Exception as exc:
        logger.warning("固定车牌识别模型推理失败: %s", exc)
        return

    if not plate_detections:
        return

    device_id = task['device_id']
    frame_number = task['frame_number']
    task_id = task['task_id']
    publish_url = task['publish_url']

    for det in plate_detections:
        plate_path = _save_plate_crop_image(frame, task_id, device_id, frame_number, det)
        payload = {
            'taskId': task_id,
            'taskName': task.get('task_name', ''),
            'taskType': task.get('task_type', 'realtime'),
            'deviceId': device_id,
            'deviceName': task.get('device_name', device_id),
            'plateNo': det.get('plate_no'),
            'plateColor': det.get('plate_color'),
            'plateImagePath': plate_path,
            'detectConf': det.get('detect_conf'),
            'rect': det.get('rect'),
            'landmarks': det.get('landmarks'),
        }
        correlation_id = task.get('correlation_id')
        if correlation_id:
            payload['correlationId'] = correlation_id
        _publish_plate_matching(payload, publish_url)


def _plate_capture_worker(worker_id: int) -> None:
    logger.info("🚗 车牌抓取 Worker %s 启动（独立队列）", worker_id)
    consecutive_errors = 0
    max_consecutive_errors = 10

    while _stop_event is not None and not _stop_event.is_set():
        try:
            if _queue is None:
                break
            try:
                task = _queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                _process_task(task)
                consecutive_errors = 0
            except Exception as exc:
                consecutive_errors += 1
                logger.error(
                    "车牌抓取 Worker %s 处理异常: %s (连续错误: %s)",
                    worker_id,
                    exc,
                    consecutive_errors,
                    exc_info=True,
                )
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("车牌抓取 Worker %s 连续错误过多，暂停 5 秒", worker_id)
                    threading.Event().wait(5)
                    consecutive_errors = 0
            finally:
                _queue.task_done()
        except Exception as exc:
            logger.error("车牌抓取 Worker %s 异常: %s", worker_id, exc, exc_info=True)
            threading.Event().wait(1)

    logger.info("🚗 车牌抓取 Worker %s 停止", worker_id)


def enqueue_plate_capture(
    *,
    frame: np.ndarray,
    device_id: str,
    device_name: str,
    frame_number: int,
    task_id: int,
    task_name: str,
    task_type: str,
    library_ids: list,
    publish_url: str,
    correlation_id: Optional[str] = None,
) -> bool:
    """非阻塞入队；队列满时可选丢弃旧任务保留最新，不影响主算法线程。"""
    if not _running or _queue is None:
        return False

    task = {
        'device_id': device_id,
        'device_name': device_name,
        'frame_number': frame_number,
        'task_id': task_id,
        'task_name': task_name,
        'task_type': task_type,
        'library_ids': library_ids,
        'publish_url': publish_url,
        'frame': frame.copy(),
    }
    if correlation_id:
        task['correlation_id'] = correlation_id

    drained = 0
    if PLATE_CAPTURE_KEEP_LATEST and _queue.qsize() >= PLATE_CAPTURE_KEEP_LATEST_THRESHOLD:
        while True:
            try:
                _queue.get_nowait()
                _queue.task_done()
                drained += 1
            except queue.Empty:
                break
        if drained > 0 and frame_number % 50 == 0:
            logger.info(
                "🔄 车牌抓取队列积压，丢弃 %s 个旧任务，保留最新帧 %s",
                drained,
                frame_number,
            )

    try:
        _queue.put(task, timeout=0.05)
        return True
    except queue.Full:
        if PLATE_CAPTURE_KEEP_LATEST:
            while True:
                try:
                    _queue.get_nowait()
                    _queue.task_done()
                    drained += 1
                except queue.Empty:
                    break
            try:
                _queue.put(task, timeout=0.05)
                if drained > 0:
                    logger.debug(
                        "🔄 车牌抓取队列满，清空 %s 个旧任务后入队帧 %s",
                        drained,
                        frame_number,
                    )
                return True
            except queue.Full:
                pass
        logger.warning(
            "⚠️ 车牌抓取队列已满，丢弃帧 %s（队列大小: %s）",
            frame_number,
            PLATE_CAPTURE_QUEUE_SIZE,
        )
        return False


def start_plate_capture_workers(stop_event: threading.Event) -> None:
    global _queue, _executor, _stop_event, _running

    with _lock:
        if _running:
            return

        _stop_event = stop_event
        _queue = queue.Queue(maxsize=PLATE_CAPTURE_QUEUE_SIZE)
        _executor = futures.ThreadPoolExecutor(
            max_workers=PLATE_CAPTURE_WORKER_THREADS,
            thread_name_prefix='plate_capture_worker',
        )
        for worker_id in range(1, PLATE_CAPTURE_WORKER_THREADS + 1):
            _executor.submit(_plate_capture_worker, worker_id)
        _running = True
        logger.info(
            "🚗 车牌抓取队列已启动: queue=%s, workers=%s, keep_latest=%s",
            PLATE_CAPTURE_QUEUE_SIZE,
            PLATE_CAPTURE_WORKER_THREADS,
            PLATE_CAPTURE_KEEP_LATEST,
        )


def stop_plate_capture_workers(timeout: float = 5.0) -> None:
    global _queue, _executor, _stop_event, _running

    with _lock:
        if not _running:
            return

        _running = False
        if _executor:
            logger.info("🛑 等待车牌抓取 Worker 结束...")
            try:
                _executor.shutdown(wait=True, cancel_futures=True)
            except TypeError:
                _executor.shutdown(wait=True)
            _executor = None
            logger.info("✅ 车牌抓取 Worker 已结束")

        _queue = None
        _stop_event = None
