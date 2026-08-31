"""人脸库自动录入服务"""
import json
import logging
import os
import subprocess
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from app.services import face_library_service
from app.services.face_recognition_service import get_face_recognition_service
from models import Device, FaceAutoEnrollTask, FaceLibrary, FaceMatchRecord, db

logger = logging.getLogger(__name__)

FACE_AUTO_ENROLL_JOB_ID = 'face_auto_enroll_tick'
_candidate_embedding_cache: Dict[int, List[tuple[str, np.ndarray]]] = {}
_candidate_cache_lock = threading.Lock()


def _is_duplicate_candidate(library_id: int, device_id: str, embedding: np.ndarray) -> bool:
    """抑制同一批次陌生人的连续重复候选；正式库去重仍由 Milvus 完成。"""
    vector = embedding.astype(np.float32).flatten()
    norm = float(np.linalg.norm(vector))
    if norm <= 0:
        return True
    vector = vector / norm
    threshold = float(os.getenv('FACE_AUTO_CANDIDATE_SIMILARITY', '0.55'))
    same_camera_threshold = float(os.getenv('FACE_AUTO_SAME_CAMERA_SIMILARITY', '0.35'))
    with _candidate_cache_lock:
        cached = _candidate_embedding_cache.setdefault(library_id, [])
        for previous_device_id, previous in cached:
            use_threshold = same_camera_threshold if previous_device_id == str(device_id) else threshold
            if float(np.dot(vector, previous)) >= use_threshold:
                return True
        cached.append((str(device_id), vector))
        max_size = max(10, int(os.getenv('FACE_AUTO_CANDIDATE_CACHE_SIZE', '500')))
        if len(cached) > max_size:
            del cached[:-max_size]
    return False


def _task_to_dict(task: FaceAutoEnrollTask) -> Dict[str, Any]:
    device_ids: List[str] = []
    try:
        device_ids = json.loads(task.device_ids or '[]')
    except Exception:
        device_ids = []
    device_names = []
    for did in device_ids:
        dev = Device.query.get(did)
        device_names.append(dev.name if dev else did)
    data = task.to_dict()
    data['device_ids'] = device_ids
    data['device_names'] = device_names
    return data


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
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise RuntimeError('RTMP 抓帧超时')
        if process.returncode != 0 or not stdout:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
            raise RuntimeError(f'RTMP 抓帧失败: {error_msg}')
        frame = cv2.imdecode(np.frombuffer(stdout, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise RuntimeError('RTMP 图像解码失败')
        return frame

    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if hasattr(cv2, 'CAP_PROP_OPEN_TIMEOUT_MSEC'):
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
    if hasattr(cv2, 'CAP_PROP_READ_TIMEOUT_MSEC'):
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError('RTSP 抓帧失败')
    return frame


def _next_auto_person_name(library_id: int, prefix: str) -> str:
    prefix = (prefix or '摄像头自动录入').strip()
    from models import FaceEntry
    seq = FaceEntry.query.filter(
        FaceEntry.library_id == library_id,
        FaceEntry.person_name.like(f'{prefix}-%'),
    ).count() + 1
    return f'{prefix}-{seq:03d}'


def _save_pending_candidate(task, device, library, crop_info, match_result) -> FaceMatchRecord:
    root = os.getenv('FACE_IMAGES_DIR') or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'data', 'face_images',
    )
    target = os.path.join(root, 'auto_enroll', str(task.id), str(device.id))
    os.makedirs(target, exist_ok=True)
    path = os.path.join(target, f'{datetime.utcnow():%Y%m%d_%H%M%S_%f}_{uuid.uuid4().hex[:8]}.jpg')
    if not cv2.imwrite(path, crop_info['crop']):
        raise RuntimeError('候选人脸图片保存失败')
    best = match_result.get('best_match') or {}
    formal_entry_id = best.get('face_entry_id') if match_result.get('matched') else None
    formal_person_id = None
    if formal_entry_id:
        from models import FaceEntry
        formal_entry = FaceEntry.query.get(int(formal_entry_id))
        formal_person_id = formal_entry.person_id if formal_entry else None
    from app.services.face_identity_service import apply_to_record, resolve_identity
    identity_result = resolve_identity(
        embedding=crop_info['embedding'], image_path=path,
        device_id=str(device.id), formal_person_id=formal_person_id,
        quality_score=crop_info.get('quality_score'),
    )
    if identity_result.get('trajectory_suppressed'):
        try:
            os.remove(path)
        except OSError:
            pass
        return None
    # 解析特征期间 stop 可能由另一个请求提交；落轨迹前再次刷新任务状态。
    db.session.expire(task)
    if not task.is_running:
        db.session.rollback()
        try:
            os.remove(path)
        except OSError:
            pass
        return None
    matched = bool(match_result.get('matched'))
    record = FaceMatchRecord(
        task_id=None,
        task_name=f'人脸库自动采集-{library.name}',
        device_id=str(device.id),
        device_name=device.name or str(device.id),
        library_id=library.id,
        library_name=library.name,
        face_image_path=path,
        matched=matched,
        matched_person_name=best.get('person_name') if matched else None,
        matched_person_code=best.get('person_code') if matched else None,
        matched_face_entry_id=formal_entry_id,
        similarity=best.get('similarity'),
        threshold=float(library.similarity_threshold or 0.55),
        candidates=json.dumps(match_result.get('candidates') or [], ensure_ascii=False),
        task_type='auto_enroll',
        status='success',
        enroll_status=(
            'enrolled' if matched else
            ('pending' if identity_result.get('created') else 'tracked')
        ),
        bbox=json.dumps([0, 0, crop_info['crop'].shape[1], crop_info['crop'].shape[0]]),
    )
    apply_to_record(record, identity_result)
    db.session.add(record)
    return record


def get_auto_enroll_task(library_id: int) -> Optional[Dict[str, Any]]:
    FaceLibrary.query.get_or_404(library_id)
    task = FaceAutoEnrollTask.query.filter_by(library_id=library_id).first()
    return _task_to_dict(task) if task else None


def save_auto_enroll_config(
    library_id: int,
    device_ids: List[str],
    duration_minutes: int = 60,
    capture_interval_sec: int = 5,
    person_name_prefix: str = '摄像头自动录入',
    enroll_mode: str = 'pending',
) -> Dict[str, Any]:
    FaceLibrary.query.get_or_404(library_id)
    task = FaceAutoEnrollTask.query.filter_by(library_id=library_id).first()
    if not task:
        task = FaceAutoEnrollTask(library_id=library_id)
        db.session.add(task)
    task.device_ids = json.dumps(list(device_ids or []), ensure_ascii=False)
    task.duration_minutes = max(1, int(duration_minutes))
    task.capture_interval_sec = max(1, int(capture_interval_sec))
    task.person_name_prefix = (person_name_prefix or '摄像头自动录入').strip()
    mode = str(enroll_mode or 'pending').strip().lower()
    if mode not in ('pending', 'direct'):
        raise ValueError('录入模式只能是 pending 或 direct')
    task.enroll_mode = mode
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return _task_to_dict(task)


def start_auto_enroll(library_id: int) -> Dict[str, Any]:
    task = FaceAutoEnrollTask.query.filter_by(library_id=library_id).first()
    if not task:
        raise ValueError('请先完成摄像头自动录入配置并保存')
    device_ids = json.loads(task.device_ids or '[]')
    if not device_ids:
        raise ValueError('请至少绑定一个摄像头后再开启')
    valid_devices = Device.query.filter(
        Device.id.in_([str(item) for item in device_ids]),
        Device.source.isnot(None),
    ).count()
    if valid_devices <= 0:
        raise ValueError('绑定的摄像头不存在或均未配置视频源')
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
    with _candidate_cache_lock:
        _candidate_embedding_cache[library_id] = []
    db.session.commit()
    _ensure_scheduler_job()
    return _task_to_dict(task)


def stop_auto_enroll(library_id: int) -> Dict[str, Any]:
    task = FaceAutoEnrollTask.query.filter_by(library_id=library_id).first()
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

    if scheduler.get_job(FACE_AUTO_ENROLL_JOB_ID):
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
            logger.warning('人脸自动录入 tick 失败: %s', exc)

    scheduler.add_job(
        wrapper,
        'interval',
        seconds=1,
        id=FACE_AUTO_ENROLL_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info('人脸库自动录入调度已启动（手动开启后生效）')


def _maybe_remove_scheduler_job() -> None:
    from app.services.camera_service import scheduler

    if FaceAutoEnrollTask.query.filter_by(is_running=True).count() > 0:
        return
    if scheduler.get_job(FACE_AUTO_ENROLL_JOB_ID):
        scheduler.remove_job(FACE_AUTO_ENROLL_JOB_ID)
        logger.info('人脸库自动录入调度已停止（无运行中任务）')


def _stop_expired_task(task: FaceAutoEnrollTask) -> None:
    task.is_running = False
    task.updated_at = datetime.utcnow()
    db.session.commit()


def _tick_single_task(task: FaceAutoEnrollTask) -> None:
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

    library = FaceLibrary.query.get(task.library_id)
    if not library or not library.is_enabled:
        task.skipped_count = (task.skipped_count or 0) + 1
        db.session.commit()
        return

    try:
        frame = _capture_frame_from_source(device.source)
    except Exception as exc:
        logger.warning('自动录入抓帧失败 library=%s device=%s: %s', task.library_id, device_id, exc)
        task.skipped_count = (task.skipped_count or 0) + 1
        task.capture_failed_count = (task.capture_failed_count or 0) + 1
        db.session.commit()
        return

    service = get_face_recognition_service()
    crop_info = service.extract_and_crop_largest_face(
        frame, allow_full_frame_fallback=False, enforce_quality=True,
    )
    if not crop_info:
        task.skipped_count = (task.skipped_count or 0) + 1
        task.rejected_count = (task.rejected_count or 0) + 1
        db.session.commit()
        return

    _, encoded = cv2.imencode('.jpg', crop_info['crop'])
    crop_bytes = encoded.tobytes()
    threshold = float(library.similarity_threshold or 0.55)

    try:
        match_result = face_library_service.match_face_in_library(
            library_id=task.library_id,
            image_bytes=crop_bytes,
            threshold=threshold,
            top_k=1,
        )
    except Exception as exc:
        logger.warning('自动录入匹配失败 library=%s: %s', task.library_id, exc)
        task.skipped_count = (task.skipped_count or 0) + 1
        db.session.commit()
        return

    # stop 接口可能在抓帧/推理期间被调用；写数据前强制刷新，禁止停止后继续入库。
    db.session.expire(task)
    if not task.is_running:
        return

    if (task.enroll_mode or 'pending') == 'pending':
        try:
            record = _save_pending_candidate(task, device, library, crop_info, match_result)
            if record is None:
                task.duplicate_count = (task.duplicate_count or 0) + 1
                task.skipped_count = (task.skipped_count or 0) + 1
            elif record.identity_resolution == 'new' and not record.matched:
                task.candidate_count = (task.candidate_count or 0) + 1
            else:
                task.duplicate_count = (task.duplicate_count or 0) + 1
                task.skipped_count = (task.skipped_count or 0) + 1
        except Exception as exc:
            logger.error('自动采集候选保存失败 library=%s: %s', task.library_id, exc, exc_info=True)
            task.error_count = (task.error_count or 0) + 1
            task.skipped_count = (task.skipped_count or 0) + 1
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return

    if match_result.get('matched'):
        _save_pending_candidate(task, device, library, crop_info, match_result)
        task.duplicate_count = (task.duplicate_count or 0) + 1
        task.skipped_count = (task.skipped_count or 0) + 1
        db.session.commit()
        return

    person_name = _next_auto_person_name(task.library_id, task.person_name_prefix)
    try:
        entry = face_library_service.add_entry(
            library_id=task.library_id,
            person_name=person_name,
            image_bytes=crop_bytes,
            is_enabled=True,
        )
        _save_pending_candidate(task, device, library, crop_info, {
            'matched': True,
            'best_match': {
                'person_name': entry.person_name,
                'person_code': entry.person_code,
                'face_entry_id': entry.id,
                'similarity': 1.0,
            },
            'candidates': [],
        })
        task.enrolled_count = (task.enrolled_count or 0) + 1
    except ValueError as exc:
        logger.info('自动录入跳过 library=%s: %s', task.library_id, exc)
        task.skipped_count = (task.skipped_count or 0) + 1
    except Exception as exc:
        logger.error('自动录入入库失败 library=%s: %s', task.library_id, exc, exc_info=True)
        task.skipped_count = (task.skipped_count or 0) + 1
        task.error_count = (task.error_count or 0) + 1

    task.updated_at = datetime.utcnow()
    db.session.commit()


def run_auto_enroll_tick() -> None:
    """调度器周期调用：处理所有运行中的自动录入任务"""
    now = datetime.utcnow()
    tasks = FaceAutoEnrollTask.query.filter_by(is_running=True).all()
    for task in tasks:
        try:
            if task.expires_at and now >= task.expires_at:
                _stop_expired_task(task)
                continue
            _tick_single_task(task)
        except Exception as exc:
            logger.error('自动录入任务执行异常 library=%s: %s', task.library_id, exc, exc_info=True)
            db.session.rollback()


# run.py 调度器引用的别名
tick_auto_enroll_tasks = run_auto_enroll_tick


def restore_auto_enroll_jobs() -> int:
    """服务重启后恢复仍在有效期内的任务，并关闭已经过期的脏状态。"""
    now = datetime.utcnow()
    tasks = FaceAutoEnrollTask.query.filter_by(is_running=True).all()
    active = 0
    for task in tasks:
        if task.expires_at and task.expires_at <= now:
            task.is_running = False
        else:
            active += 1
    db.session.commit()
    if active:
        _ensure_scheduler_job()
    return active
