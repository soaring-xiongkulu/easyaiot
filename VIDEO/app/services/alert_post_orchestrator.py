"""
告警 Hook 帧后编排：在 executor=cpp 时承接原 Python run_deploy 的匹配/后处理触发。

Python 执行器仍在 run_deploy 内触发 try_send_* / enqueue_post_process；
本模块仅在 cpp 告警 hook 进入 VIDEO 后执行等价逻辑，避免双触发。
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from models import AlgorithmTask, Device, FaceLibrary

logger = logging.getLogger(__name__)

_CAPTURE_STOP_EVENT: Optional[threading.Event] = None
_CAPTURE_LOCK = threading.Lock()


def _ensure_capture_workers() -> None:
    """懒启动人脸/车牌抓取队列（cpp 任务不经 run_deploy，需在 VIDEO 侧拉起）。"""
    global _CAPTURE_STOP_EVENT
    with _CAPTURE_LOCK:
        from app.utils.face_capture_queue_service import is_running as face_running
        from app.utils.plate_capture_queue_service import is_running as plate_running
        from app.utils.face_capture_queue_service import start_face_capture_workers
        from app.utils.plate_capture_queue_service import start_plate_capture_workers

        if _CAPTURE_STOP_EVENT is None:
            _CAPTURE_STOP_EVENT = threading.Event()
        if not face_running():
            start_face_capture_workers(_CAPTURE_STOP_EVENT)
        if not plate_running():
            start_plate_capture_workers(_CAPTURE_STOP_EVENT)


def _parse_information(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    raw = alert_data.get('information')
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            logger.debug('alert information JSON 解析失败')
    return {}


def _extract_detections(alert_data: Dict[str, Any], info: Dict[str, Any]) -> List[Dict[str, Any]]:
    dets = info.get('detections')
    if isinstance(dets, list):
        return [d for d in dets if isinstance(d, dict)]
    return []


def _extract_frame_number(info: Dict[str, Any]) -> int:
    for key in ('frame_number', 'frameNumber'):
        val = info.get(key)
        if val is not None:
            try:
                return int(val)
            except (TypeError, ValueError):
                pass
    return 0


def _extract_timestamp(alert_data: Dict[str, Any], info: Dict[str, Any]) -> float:
    ts_ms = info.get('runtime_ts_ms')
    if isinstance(ts_ms, (int, float)) and ts_ms > 0:
        return float(ts_ms) / 1000.0
    raw_time = alert_data.get('time')
    if isinstance(raw_time, str) and raw_time.strip():
        from app.utils.service_urls import parse_alert_time_str
        parsed, _err = parse_alert_time_str(raw_time)
        if parsed is not None:
            return parsed.timestamp()
    return time.time()


def _load_alert_frame(image_path: Optional[str]) -> Optional[np.ndarray]:
    if not image_path or not str(image_path).strip():
        return None
    path = str(image_path).strip()
    if not os.path.isfile(path):
        logger.warning('告警帧后编排：图片不存在 path=%s', path)
        return None
    frame = cv2.imread(path)
    if frame is None:
        logger.warning('告警帧后编排：无法读取图片 path=%s', path)
    return frame


def _resolve_task(alert_event_task: Optional[Dict[str, Any]]) -> Optional[AlgorithmTask]:
    if not alert_event_task:
        return None
    task_id = alert_event_task.get('task_id')
    if not task_id:
        return None
    try:
        return AlgorithmTask.query.get(int(task_id))
    except Exception as exc:
        logger.warning('查询算法任务失败 task_id=%s: %s', task_id, exc)
        return None


def _is_cpp_executor(task: Optional[AlgorithmTask]) -> bool:
    if not task:
        return False
    ex = (getattr(task, 'executor', None) or 'python').strip().lower()
    return ex in ('cpp', 'c++', 'runtime', 'cxx')


def _resolve_face_matching_threshold(task: AlgorithmTask) -> Optional[float]:
    threshold = getattr(task, 'face_matching_threshold', None)
    if threshold is not None:
        return float(threshold)
    lib_ids = AlgorithmTask._parse_library_ids(getattr(task, 'face_library_ids', None))
    if lib_ids:
        library = FaceLibrary.query.get(lib_ids[0])
        if library is not None and getattr(library, 'similarity_threshold', None) is not None:
            return float(library.similarity_threshold)
    return None


def _try_face_matching(
    task: AlgorithmTask,
    *,
    device_id: str,
    device_name: str,
    frame: np.ndarray,
    frame_number: int,
    correlation_id: Optional[str],
    source_event: Optional[str],
) -> None:
    if not bool(getattr(task, 'face_matching_enabled', False)):
        return
    library_ids = AlgorithmTask._parse_library_ids(getattr(task, 'face_library_ids', None))
    if not library_ids:
        logger.warning('人脸匹配已开启但未配置人脸库，跳过 task_id=%s', task.id)
        return

    from app.utils.face_capture_queue_service import enqueue_face_capture, is_running
    from app.utils.service_urls import resolve_face_matching_publish_url

    if not is_running():
        logger.warning('人脸抓取队列未启动，跳过 task_id=%s frame=%s', task.id, frame_number)
        return

    enqueue_face_capture(
        frame=frame,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        task_id=int(task.id),
        task_name=getattr(task, 'task_name', '') or '',
        task_type=getattr(task, 'task_type', 'realtime') or 'realtime',
        library_ids=library_ids,
        threshold=_resolve_face_matching_threshold(task),
        publish_url=resolve_face_matching_publish_url(),
        correlation_id=correlation_id,
        source_event=source_event,
    )
    logger.info(
        'cpp 告警 hook 已入队人脸匹配: task_id=%s device_id=%s frame=%s',
        task.id,
        device_id,
        frame_number,
    )


def _try_plate_matching(
    task: AlgorithmTask,
    *,
    device_id: str,
    device_name: str,
    frame: np.ndarray,
    frame_number: int,
    correlation_id: Optional[str],
) -> None:
    if not bool(getattr(task, 'plate_matching_enabled', False)):
        return
    library_ids = AlgorithmTask._parse_library_ids(getattr(task, 'plate_library_ids', None))
    if not library_ids:
        logger.warning('车牌匹配已开启但未配置车牌库，跳过 task_id=%s', task.id)
        return

    from app.utils.plate_capture_queue_service import enqueue_plate_capture, is_running
    from app.utils.service_urls import resolve_plate_matching_publish_url

    if not is_running():
        logger.warning('车牌抓取队列未启动，跳过 task_id=%s frame=%s', task.id, frame_number)
        return

    enqueue_plate_capture(
        frame=frame,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        task_id=int(task.id),
        task_name=getattr(task, 'task_name', '') or '',
        task_type=getattr(task, 'task_type', 'realtime') or 'realtime',
        library_ids=library_ids,
        publish_url=resolve_plate_matching_publish_url(),
        correlation_id=correlation_id,
    )
    logger.info(
        'cpp 告警 hook 已入队车牌匹配: task_id=%s device_id=%s frame=%s',
        task.id,
        device_id,
        frame_number,
    )


def _try_post_process_enqueue(
    task: AlgorithmTask,
    *,
    device_id: str,
    device_name: str,
    frame_number: int,
    timestamp: float,
    detections: List[Dict[str, Any]],
    alert_image_path: Optional[str],
) -> None:
    from app.utils.post_process_runner import enqueue_post_process_request, task_needs_sink_processing

    if not task_needs_sink_processing(task):
        return
    if not detections and not alert_image_path:
        logger.debug(
            '后处理跳过：无 detections 且无 alert_image_path task_id=%s',
            task.id,
        )
        return

    enqueue_post_process_request(
        task,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        timestamp=timestamp,
        detections=detections,
        tracked_detections=detections,
        alert_image_path=alert_image_path,
    )
    logger.info(
        'cpp 告警 hook 已投递后处理入队: task_id=%s device_id=%s frame=%s',
        task.id,
        device_id,
        frame_number,
    )


def run_post_alert_orchestration(
    alert_data: Dict[str, Any],
    alert_event_task: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    同步执行 cpp 帧后编排。返回摘要供日志/测试断言。
    """
    summary = {
        'executor': None,
        'face_matching': False,
        'plate_matching': False,
        'post_process': False,
        'skipped_reason': None,
    }

    task = _resolve_task(alert_event_task)
    if not task:
        summary['skipped_reason'] = 'no_task'
        return summary

    executor = (getattr(task, 'executor', None) or 'python').strip().lower()
    summary['executor'] = executor
    if not _is_cpp_executor(task):
        summary['skipped_reason'] = 'not_cpp_executor'
        return summary

    device_id = str(alert_data.get('device_id') or '').strip()
    if not device_id:
        summary['skipped_reason'] = 'no_device_id'
        return summary

    device_name = alert_data.get('device_name') or device_id
    info = _parse_information(alert_data)
    detections = _extract_detections(alert_data, info)
    frame_number = _extract_frame_number(info)
    timestamp = _extract_timestamp(alert_data, info)
    correlation_id = (
        alert_data.get('correlation_id')
        or alert_data.get('correlationId')
        or info.get('correlation_id')
    )
    source_event = alert_data.get('event')
    image_path = alert_data.get('image_path')

    needs_matching = bool(getattr(task, 'face_matching_enabled', False)) or bool(
        getattr(task, 'plate_matching_enabled', False)
    )
    from app.utils.post_process_runner import task_needs_sink_processing
    needs_sink = task_needs_sink_processing(task)

    if not needs_matching and not needs_sink:
        summary['skipped_reason'] = 'no_post_alert_caps'
        return summary

    frame = None
    if needs_matching:
        _ensure_capture_workers()
        frame = _load_alert_frame(image_path)
        if frame is None:
            logger.warning(
                'cpp 帧后编排：无法加载告警图，跳过人脸/车牌匹配 task_id=%s',
                task.id,
            )
        else:
            _try_face_matching(
                task,
                device_id=device_id,
                device_name=device_name,
                frame=frame,
                frame_number=frame_number,
                correlation_id=correlation_id,
                source_event=source_event,
            )
            summary['face_matching'] = bool(getattr(task, 'face_matching_enabled', False)) and frame is not None
            _try_plate_matching(
                task,
                device_id=device_id,
                device_name=device_name,
                frame=frame,
                frame_number=frame_number,
                correlation_id=correlation_id,
            )
            summary['plate_matching'] = bool(getattr(task, 'plate_matching_enabled', False)) and frame is not None

    if needs_sink:
        _try_post_process_enqueue(
            task,
            device_id=device_id,
            device_name=device_name,
            frame_number=frame_number,
            timestamp=timestamp,
            detections=detections,
            alert_image_path=image_path,
        )
        summary['post_process'] = True

    return summary


def schedule_post_alert_orchestration(
    alert_data: Dict[str, Any],
    alert_event_task: Optional[Dict[str, Any]],
) -> None:
    """异步调度，避免阻塞 hook HTTP 响应。"""
    payload = dict(alert_data)
    task_snapshot = dict(alert_event_task) if alert_event_task else None

    def _run():
        try:
            run_post_alert_orchestration(payload, task_snapshot)
        except Exception as exc:
            logger.error('cpp 帧后编排异常: %s', exc, exc_info=True)

    threading.Thread(
        target=_run,
        daemon=True,
        name='alert-post-orchestrator',
    ).start()
