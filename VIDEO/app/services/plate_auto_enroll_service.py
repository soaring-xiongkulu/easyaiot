"""车牌库自动录入服务"""
import json
import logging
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from app.services import plate_library_service
from app.utils.plate_capture_service import detect_and_recognize_plates
from models import Device, PlateAutoEnrollTask, PlateLibrary, PlateMatchRecord, db

logger = logging.getLogger(__name__)

PLATE_AUTO_ENROLL_JOB_ID = 'plate_auto_enroll_tick'


def _task_to_dict(task: PlateAutoEnrollTask) -> Dict[str, Any]:
    return task.to_dict()


def _capture_frame_from_source(source: str) -> np.ndarray:
    source = (source or '').strip()
    if not source:
        raise ValueError('设备视频源为空')

    if source.lower().startswith('rtmp://'):
        ffmpeg_cmd = [
            'ffmpeg', '-i', source, '-vframes', '1', '-f', 'image2',
            '-vcodec', 'mjpeg', '-q:v', '2', 'pipe:1',
        ]
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=10)
        if process.returncode != 0 or not stdout:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
            raise RuntimeError(f'RTMP 抓帧失败: {error_msg}')
        frame = cv2.imdecode(np.frombuffer(stdout, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise RuntimeError('RTMP 图像解码失败')
        return frame

    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError('RTSP 抓帧失败')
    return frame


def get_auto_enroll_task(library_id: int) -> Optional[Dict[str, Any]]:
    PlateLibrary.query.get_or_404(library_id)
    task = PlateAutoEnrollTask.query.filter_by(library_id=library_id).first()
    return _task_to_dict(task) if task else None


def save_auto_enroll_config(
    library_id: int,
    device_ids: List[str],
    duration_minutes: int = 60,
    capture_interval_sec: int = 5,
    enroll_mode: str = 'pending',
) -> Dict[str, Any]:
    PlateLibrary.query.get_or_404(library_id)
    task = PlateAutoEnrollTask.query.filter_by(library_id=library_id).first()
    if not task:
        task = PlateAutoEnrollTask(library_id=library_id)
        db.session.add(task)
    task.device_ids = json.dumps(list(device_ids or []), ensure_ascii=False)
    task.duration_minutes = max(1, int(duration_minutes))
    task.capture_interval_sec = max(1, int(capture_interval_sec))
    mode = str(enroll_mode or 'pending').strip().lower()
    if mode not in ('pending', 'direct'):
        raise ValueError('录入模式只能是 pending 或 direct')
    task.enroll_mode = mode
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return _task_to_dict(task)


def start_auto_enroll(library_id: int) -> Dict[str, Any]:
    task = PlateAutoEnrollTask.query.filter_by(library_id=library_id).first()
    if not task:
        raise ValueError('请先完成摄像头自动录入配置并保存')
    device_ids = json.loads(task.device_ids or '[]')
    if not device_ids:
        raise ValueError('请至少绑定一个摄像头后再开启')
    now = datetime.utcnow()
    task.is_running = True
    task.started_at = now
    task.expires_at = now + timedelta(minutes=task.duration_minutes)
    task.enrolled_count = 0
    task.skipped_count = 0
    task.candidate_count = 0
    task.duplicate_count = 0
    task.rejected_count = 0
    task.capture_failed_count = 0
    task.error_count = 0
    task.last_tick_at = None
    task.updated_at = now
    db.session.commit()
    _ensure_scheduler_job()
    return _task_to_dict(task)


def stop_auto_enroll(library_id: int) -> Dict[str, Any]:
    task = PlateAutoEnrollTask.query.filter_by(library_id=library_id).first()
    if not task:
        raise ValueError('自动录入任务不存在')
    task.is_running = False
    task.updated_at = datetime.utcnow()
    db.session.commit()
    _maybe_remove_scheduler_job()
    return _task_to_dict(task)


def _ensure_scheduler_job() -> None:
    from flask import current_app
    from app.services.camera_service import scheduler

    if scheduler.get_job(PLATE_AUTO_ENROLL_JOB_ID):
        return
    if not scheduler.running:
        scheduler.start()
    app = current_app._get_current_object()

    def wrapper():
        try:
            with app.app_context():
                run_auto_enroll_tick()
                _maybe_remove_scheduler_job()
        except Exception as exc:
            logger.warning('车牌自动录入 tick 失败: %s', exc)

    scheduler.add_job(
        wrapper,
        'interval',
        seconds=5,
        id=PLATE_AUTO_ENROLL_JOB_ID,
        replace_existing=True,
    )
    logger.info('车牌库自动录入调度已启动（手动开启后生效）')


def _maybe_remove_scheduler_job() -> None:
    from app.services.camera_service import scheduler

    if PlateAutoEnrollTask.query.filter_by(is_running=True).count() > 0:
        return
    if scheduler.get_job(PLATE_AUTO_ENROLL_JOB_ID):
        scheduler.remove_job(PLATE_AUTO_ENROLL_JOB_ID)
        logger.info('车牌库自动录入调度已停止（无运行中任务）')


def _stop_expired_task(task: PlateAutoEnrollTask) -> None:
    task.is_running = False
    task.updated_at = datetime.utcnow()
    db.session.commit()


def _tick_single_task(task: PlateAutoEnrollTask) -> None:
    now = datetime.utcnow()
    if task.expires_at and now >= task.expires_at:
        _stop_expired_task(task)
        return

    interval = max(1, int(task.capture_interval_sec or 5))
    if task.last_tick_at and (now - task.last_tick_at).total_seconds() < interval:
        return

    try:
        device_ids: List[str] = json.loads(task.device_ids or '[]')
    except Exception:
        device_ids = []
    if not device_ids:
        return

    idx = int(task.last_device_index or 0) % len(device_ids)
    device_id = device_ids[idx]
    task.last_device_index = (idx + 1) % len(device_ids)
    task.last_tick_at = now

    device = Device.query.get(device_id)
    if not device or not device.source:
        task.skipped_count = (task.skipped_count or 0) + 1
        db.session.commit()
        return

    library = PlateLibrary.query.get(task.library_id)
    if not library or not library.is_enabled:
        task.skipped_count = (task.skipped_count or 0) + 1
        db.session.commit()
        return

    try:
        frame = _capture_frame_from_source(device.source)
    except Exception as exc:
        logger.warning('车牌自动录入抓帧失败 library=%s device=%s: %s', task.library_id, device_id, exc)
        task.skipped_count = (task.skipped_count or 0) + 1
        task.capture_failed_count = (task.capture_failed_count or 0) + 1
        db.session.commit()
        return

    try:
        plates = detect_and_recognize_plates(frame)
    except Exception as exc:
        logger.warning('车牌自动录入识别失败 library=%s: %s', task.library_id, exc)
        task.skipped_count = (task.skipped_count or 0) + 1
        task.error_count = (task.error_count or 0) + 1
        db.session.commit()
        return

    if not plates:
        task.skipped_count = (task.skipped_count or 0) + 1
        task.rejected_count = (task.rejected_count or 0) + 1
        db.session.commit()
        return

    best = max(plates, key=lambda p: p.get('detect_conf', 0))
    plate_no = (best.get('plate_no') or '').strip()
    if not plate_no:
        task.skipped_count = (task.skipped_count or 0) + 1
        task.rejected_count = (task.rejected_count or 0) + 1
        db.session.commit()
        return

    match_result = plate_library_service.match_plate_in_library(task.library_id, plate_no)

    rect = best.get('rect') or []
    crop_bytes = None
    crop = None
    if len(rect) >= 4:
        x1, y1, x2, y2 = [int(v) for v in rect[:4]]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 > x1 and y2 > y1:
            crop = frame[y1:y2, x1:x2]
            _, encoded = cv2.imencode('.jpg', crop)
            crop_bytes = encoded.tobytes()

    image_path = None
    if crop is not None and crop.size:
        root = os.getenv('PLATE_IMAGES_DIR') or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'plate_images',
        )
        target = os.path.join(root, 'auto_enroll', str(task.id), str(device.id))
        os.makedirs(target, exist_ok=True)
        image_path = os.path.join(target, f'{datetime.utcnow():%Y%m%d_%H%M%S_%f}_{uuid.uuid4().hex[:8]}.jpg')
        if not cv2.imwrite(image_path, crop):
            image_path = None

    try:
        from app.services.vehicle_identity_service import apply_to_record, resolve_vehicle_identity
        matched_entry = (match_result.get('entry') or {}) if match_result.get('matched') else {}
        vehicle_result = resolve_vehicle_identity(
            plate_no=plate_no, raw_plate_no=best.get('raw_plate_no') or plate_no,
            plate_color=best.get('plate_color'), confidence=best.get('detect_conf'),
            image_path=image_path, device_id=str(device.id),
            formal_plate_entry_id=matched_entry.get('id'),
        )
        if vehicle_result.get('trajectory_suppressed'):
            if image_path and os.path.isfile(image_path):
                os.remove(image_path)
            task.duplicate_count = (task.duplicate_count or 0) + 1
            task.skipped_count = (task.skipped_count or 0) + 1
            db.session.commit()
            return

        db.session.expire(task)
        if not task.is_running:
            db.session.rollback()
            if image_path and os.path.isfile(image_path):
                os.remove(image_path)
            return

        record = PlateMatchRecord(
            task_name=f'车牌库自动采集-{library.name}',
            device_id=str(device.id), device_name=device.name or str(device.id),
            library_id=library.id, library_name=library.name,
            plate_no=plate_no, plate_color=best.get('plate_color'),
            plate_image_path=image_path,
            matched=bool(match_result.get('matched')),
            matched_plate_entry_id=matched_entry.get('id'),
            matched_owner_name=matched_entry.get('owner_name'),
            detect_conf=best.get('detect_conf'), task_type='auto_enroll', status='success',
            enroll_status=(
                'enrolled' if match_result.get('matched') else
                ('pending' if vehicle_result.get('created') else 'tracked')
            ),
            bbox=json.dumps(rect[:4]) if len(rect) >= 4 else None,
        )
        apply_to_record(record, vehicle_result)
        db.session.add(record)
        if vehicle_result.get('created') and not match_result.get('matched'):
            task.candidate_count = (task.candidate_count or 0) + 1
        else:
            task.duplicate_count = (task.duplicate_count or 0) + 1

        # direct 仅保留向后兼容；默认 pending 不修改正式车牌库。
        if (task.enroll_mode or 'pending') == 'direct' and vehicle_result.get('created') and not match_result.get('matched'):
            entry = plate_library_service.add_entry(
                library_id=task.library_id, plate_no=plate_no,
                plate_color=best.get('plate_color'), image_bytes=crop_bytes, is_enabled=True,
            )
            identity = vehicle_result['identity']
            identity.business_plate_entry_id = entry.id
            identity.status = 'confirmed'
            identity.owner_name = entry.owner_name
            record.matched = True
            record.matched_plate_entry_id = entry.id
            record.enroll_status = 'enrolled'
            task.enrolled_count = (task.enrolled_count or 0) + 1
    except ValueError as exc:
        logger.info('车辆电子身份解析跳过 library=%s: %s', task.library_id, exc)
        task.skipped_count = (task.skipped_count or 0) + 1
    except Exception as exc:
        logger.error('车辆电子身份落库失败 library=%s: %s', task.library_id, exc, exc_info=True)
        task.skipped_count = (task.skipped_count or 0) + 1
        task.error_count = (task.error_count or 0) + 1

    task.updated_at = datetime.utcnow()
    db.session.commit()


def run_auto_enroll_tick() -> None:
    now = datetime.utcnow()
    tasks = PlateAutoEnrollTask.query.filter_by(is_running=True).all()
    for task in tasks:
        try:
            if task.expires_at and now >= task.expires_at:
                _stop_expired_task(task)
                continue
            _tick_single_task(task)
        except Exception as exc:
            logger.error('车牌自动录入任务执行异常 library=%s: %s', task.library_id, exc, exc_info=True)
            db.session.rollback()


tick_plate_auto_enroll_tasks = run_auto_enroll_tick
