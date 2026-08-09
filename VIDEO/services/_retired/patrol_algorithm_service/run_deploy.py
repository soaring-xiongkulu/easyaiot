#!/usr/bin/env python3
"""
摄像头巡检算法服务：rotate / pool 模式，复用 stream_adapter 与 algo_model_detect。
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import cv2
import numpy as np
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, video_root)
_repo_root = os.path.abspath(os.path.join(video_root, '..'))
_lib_root = os.path.join(_repo_root, '.scripts', 'lib')
for _p in (_lib_root,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.utils.video_env import load_video_env

load_video_env(override=True)

import app.utils.nvidia_lib_path  # noqa: F401

from models import Device, PatrolSession, AlgorithmTask
from app.utils.gb28181_source import resolve_gb28181_source
from app.utils.decode.stream_adapter import is_async_stream, open_device_stream, stream_mode_label
from app.utils.onnx_inference import ONNXInference
from app.utils.algo_model_detect import run_model_detection
from app.utils.alert_images_paths import resolve_alert_images_root
from app.utils.patrol_snap_upload import upload_patrol_frame_to_snap_space
from app.utils.service_urls import resolve_alert_hook_url

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('patrol_algorithm_service')

PATROL_SESSION_ID = int(os.getenv('PATROL_SESSION_ID', '0'))
TASK_ID = int(os.getenv('TASK_ID', '0'))
PATROL_SAVE_SNAP = os.getenv('PATROL_SAVE_SNAP', '1').strip().lower() not in ('0', 'false', 'no', 'off')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
VIDEO_SERVICE_PORT = os.getenv('VIDEO_SERVICE_PORT', '6000')
ALERT_HOOK_URL = resolve_alert_hook_url()
YOLO_IMG_SIZE = int(os.getenv('YOLO_IMG_SIZE', '416'))
YOLO_WORKER_THREADS = int(os.getenv('YOLO_WORKER_THREADS', '2'))
DETECTION_QUEUE_SIZE = int(os.getenv('DETECTION_QUEUE_SIZE', '50'))
PATROL_CONNECT_TIMEOUT_SEC = float(os.getenv('PATROL_CONNECT_TIMEOUT_SEC', '8'))
PATROL_READ_WARMUP_FRAMES = int(os.getenv('PATROL_READ_WARMUP_FRAMES', '3'))

engine = create_engine(DATABASE_URL.replace('postgres://', 'postgresql://', 1))
SessionLocal = sessionmaker(bind=engine)
db_session = scoped_session(SessionLocal)

stop_event = threading.Event()
session_config: Optional[PatrolRuntimeConfig] = None
device_streams: Dict[str, dict] = {}
yolo_models: Dict[int, Any] = {}
yolo_model_devices: Dict[int, str] = {}
detection_queue: 'queue.Queue' = None  # type: ignore
progress_lock = threading.Lock()
device_progress: Dict[str, dict] = {}
total_patrols = 0
total_detections = 0
last_alert_time: Dict[str, float] = {}
alert_lock = threading.Lock()

import queue  # noqa: E402


@dataclass
class PatrolRuntimeConfig:
    name: str
    patrol_mode: str
    interval_sec: int
    pool_size: int
    focus_device_id: Optional[str]
    model_ids: List[int]
    alert_event_enabled: bool
    alert_event_suppress_time: int
    alert_class_names: List[str]
    face_detection_enabled: bool
    plate_detection_enabled: bool
    detect_conf: float = 0.5
    session_id: Optional[int] = None
    task_id: Optional[int] = None


def _load_alert_class_names_from_task(task_id: Optional[int]) -> List[str]:
    if not task_id:
        return []
    task = db_session.query(AlgorithmTask).filter_by(id=int(task_id)).first()
    if not task:
        return []
    from app.utils.alert_class_filter import parse_alert_class_names
    return parse_alert_class_names(task.alert_class_names)


def _parse_json_list(raw) -> List:
    if not raw:
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _get_detect_conf() -> float:
    if session_config is not None:
        task_conf = getattr(session_config, 'detect_conf', None)
        if task_conf is not None:
            try:
                return float(task_conf)
            except (TypeError, ValueError):
                pass
    try:
        return float(os.getenv('PATROL_DETECT_CONF', os.getenv('YOLO_DETECT_CONF', '0.5')))
    except ValueError:
        return 0.5


def _load_detect_conf_from_task(task_id: Optional[int]) -> float:
    if not task_id:
        return 0.5
    task = db_session.query(AlgorithmTask).filter_by(id=int(task_id)).first()
    if not task or task.detect_conf is None:
        return 0.5
    try:
        return float(task.detect_conf)
    except (TypeError, ValueError):
        return 0.5


def _config_from_session(session: PatrolSession) -> PatrolRuntimeConfig:
    return PatrolRuntimeConfig(
        name=session.session_name,
        patrol_mode=(session.patrol_mode or 'pool').lower(),
        interval_sec=max(3, int(session.interval_sec or 10)),
        pool_size=max(1, int(session.pool_size or 4)),
        focus_device_id=session.focus_device_id,
        model_ids=[int(x) for x in _parse_json_list(session.model_ids)],
        alert_event_enabled=bool(session.alert_event_enabled),
        alert_event_suppress_time=int(session.alert_event_suppress_time or 5),
        alert_class_names=_load_alert_class_names_from_task(session.algorithm_task_id),
        face_detection_enabled=bool(session.face_detection_enabled),
        plate_detection_enabled=bool(session.plate_detection_enabled),
        detect_conf=_load_detect_conf_from_task(session.algorithm_task_id),
        session_id=session.id,
    )


def _config_from_task(task: AlgorithmTask) -> PatrolRuntimeConfig:
    model_ids = []
    if task.model_ids:
        try:
            model_ids = [int(x) for x in json.loads(task.model_ids)]
        except Exception:
            pass
    from app.utils.alert_class_filter import parse_alert_class_names
    return PatrolRuntimeConfig(
        name=task.task_name,
        patrol_mode=(task.patrol_mode or 'pool').lower(),
        interval_sec=max(3, int(task.patrol_interval_sec or 10)),
        pool_size=max(1, int(task.patrol_pool_size or 4)),
        focus_device_id=task.focus_device_id,
        model_ids=model_ids,
        alert_event_enabled=bool(task.alert_event_enabled),
        alert_event_suppress_time=int(task.alert_event_suppress_time or 5),
        alert_class_names=parse_alert_class_names(task.alert_class_names),
        face_detection_enabled=bool(task.face_detection_enabled),
        plate_detection_enabled=bool(task.plate_detection_enabled),
        detect_conf=float(task.detect_conf) if task.detect_conf is not None else 0.5,
        task_id=task.id,
    )


def load_patrol_config() -> bool:
    global session_config, device_streams, device_progress, yolo_models, yolo_model_devices

    session_config = None
    device_ids: List[str] = []
    model_ids: List[int] = []

    if PATROL_SESSION_ID:
        session = db_session.query(PatrolSession).filter_by(id=PATROL_SESSION_ID).first()
        if not session:
            logger.error('巡检会话 %s 不存在', PATROL_SESSION_ID)
            return False
        session_config = _config_from_session(session)
        device_ids = _parse_json_list(session.device_ids)
        model_ids = session_config.model_ids
    elif TASK_ID:
        task = db_session.query(AlgorithmTask).filter_by(id=TASK_ID).first()
        if not task or task.task_type != 'patrol':
            logger.error('巡检任务 %s 不存在或类型不是 patrol', TASK_ID)
            return False
        session_config = _config_from_task(task)
        db_session.refresh(task)
        device_ids = [d.id for d in (task.devices or [])]
        model_ids = session_config.model_ids
    else:
        logger.error('PATROL_SESSION_ID 或 TASK_ID 未设置')
        return False

    device_streams.clear()
    for device_id in device_ids:
        device = db_session.query(Device).filter_by(id=device_id).first()
        if not device or not device.source:
            logger.warning('设备 %s 无可用源，跳过', device_id)
            continue
        rtsp_url = resolve_gb28181_source(device.source, logger=logger)
        if not rtsp_url:
            logger.warning('设备 %s 无法解析流地址，跳过', device_id)
            continue
        device_streams[device_id] = {
            'rtsp_url': rtsp_url,
            'device_name': device.name or device_id,
            'is_gb28181': device.source.strip().lower().startswith('gb28181://'),
            'original_source': device.source,
        }

    if not device_streams:
        logger.error('没有可用的巡检设备流')
        return False

    yolo_models.clear()
    yolo_model_devices.clear()
    models = _load_models(model_ids)
    if not models:
        logger.error('模型加载失败')
        return False
    yolo_models.update(models)

    with progress_lock:
        device_progress = {did: device_progress.get(did, {}) for did in device_streams.keys()}

    logger.info(
        '巡检配置加载成功: %s mode=%s devices=%s models=%s interval=%ss pool=%s',
        session_config.name,
        session_config.patrol_mode,
        len(device_streams),
        list(yolo_models.keys()),
        session_config.interval_sec,
        session_config.pool_size,
    )
    return True


def load_patrol_session() -> bool:
    """兼容旧函数名。"""
    return load_patrol_config()


def _load_models(model_ids: List[int]) -> Dict[int, Any]:
    models: Dict[int, Any] = {}
    ai_url = os.getenv('AI_SERVICE_URL', 'http://localhost:5000')
    jwt = os.getenv('JWT_TOKEN', '')

    for model_id in model_ids:
        try:
            resp = requests.get(
                f'{ai_url}/model/{model_id}',
                headers={'X-Authorization': f'Bearer {jwt}'},
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning('获取模型 %s 失败: HTTP %s', model_id, resp.status_code)
                continue
            body = resp.json()
            if body.get('code') != 0:
                continue
            info = body.get('data') or {}
            model_path = info.get('onnx_model_path') or info.get('model_path')
            if not model_path:
                continue
            local_path = _ensure_local_model(model_id, model_path, ai_url, jwt)
            if not local_path or not os.path.exists(local_path):
                logger.warning('模型 %s 本地路径不可用: %s', model_id, local_path)
                continue
            if str(local_path).lower().endswith('.onnx'):
                onnx = ONNXInference(
                    local_path,
                    conf_threshold=_get_detect_conf(),
                    iou_threshold=0.45,
                    api_class_names=info.get('classNames') or info.get('class_names'),
                )
                models[model_id] = onnx
                yolo_model_devices[model_id] = 'onnx'
            else:
                from ultralytics import YOLO
                models[model_id] = YOLO(local_path)
                yolo_model_devices[model_id] = 'cpu'
            logger.info('模型 %s 加载成功: %s', model_id, local_path)
        except Exception as exc:
            logger.error('加载模型 %s 失败: %s', model_id, exc, exc_info=True)
    return models


def _ensure_local_model(model_id: int, model_path: str, ai_url: str, jwt: str) -> Optional[str]:
    try:
        from model_resolver import try_resolve_cluster_model_path
        cluster_path = try_resolve_cluster_model_path(model_id)
        if cluster_path:
            logger.info('使用集群共享模型: model_id=%s path=%s', model_id, cluster_path)
            return cluster_path
    except ImportError:
        pass
    if model_path.startswith('/') and not model_path.startswith('/api'):
        return model_path if os.path.exists(model_path) else None
    storage = os.path.join(video_root, 'data', 'models', str(model_id))
    os.makedirs(storage, exist_ok=True)
    filename = os.path.basename(model_path.split('?')[0]) or f'model_{model_id}.onnx'
    local = os.path.join(storage, filename)
    if os.path.exists(local) and os.path.getsize(local) > 0:
        return local
    if model_path.startswith('/api/'):
        url = f'{ai_url.rstrip("/")}{model_path}' if not model_path.startswith('http') else model_path
    elif model_path.startswith('http'):
        url = model_path
    else:
        return model_path if os.path.exists(model_path) else None
    try:
        r = requests.get(url, headers={'X-Authorization': f'Bearer {jwt}'}, timeout=120, stream=True)
        r.raise_for_status()
        with open(local, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return local
    except Exception as exc:
        logger.warning('下载模型 %s 失败: %s', model_id, exc)
        return None


def _release_cap(cap) -> None:
    if cap is None:
        return
    try:
        cap.release()
    except Exception:
        pass


def capture_frame(device_id: str) -> Optional[np.ndarray]:
    info = device_streams.get(device_id)
    if not info:
        return None
    url = info['rtsp_url']
    cap = None
    try:
        cap = open_device_stream(
            url,
            device_id,
            task_id=f'patrol_{PATROL_SESSION_ID}',
            open_timeout_msec=int(os.getenv('RTSP_OPEN_TIMEOUT_MSEC', '5000')),
            read_timeout_msec=int(os.getenv('RTSP_READ_TIMEOUT_MSEC', '2500')),
        )
        if not cap.isOpened():
            return None
        logger.info('设备 %s 拉流: %s', device_id, stream_mode_label(cap))
        deadline = time.time() + PATROL_CONNECT_TIMEOUT_SEC
        frame = None
        reads = 0
        while time.time() < deadline and reads < max(PATROL_READ_WARMUP_FRAMES, 5):
            if stop_event.is_set():
                break
            ret, img = cap.read()
            reads += 1
            if is_async_stream(cap) and not ret and getattr(cap, 'read_failed', False):
                break
            if ret and img is not None and img.size > 0:
                frame = img
                if reads >= PATROL_READ_WARMUP_FRAMES:
                    break
            time.sleep(0.05)
        return frame
    except Exception as exc:
        logger.warning('设备 %s 抓帧失败: %s', device_id, exc)
        return None
    finally:
        _release_cap(cap)


def _update_device_progress(device_id: str, *, result: str, detection_count: int = 0, error: str = None):
    global total_patrols, total_detections
    now_iso = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    with progress_lock:
        total_patrols += 1
        if detection_count:
            total_detections += detection_count
        entry = device_progress.setdefault(device_id, {})
        entry.update({
            'last_patrol_at': now_iso,
            'last_result': result,
            'detection_count': detection_count,
            'error': error,
        })


def _get_patrol_algorithm_task() -> Optional[AlgorithmTask]:
    """获取巡检关联的算法任务（用于 iot-sink 后处理/姿态分析）。"""
    task_id = TASK_ID
    if not task_id and PATROL_SESSION_ID:
        session = db_session.query(PatrolSession).filter_by(id=PATROL_SESSION_ID).first()
        if session and session.algorithm_task_id:
            task_id = session.algorithm_task_id
    elif not task_id and session_config and session_config.task_id:
        task_id = session_config.task_id
    if not task_id:
        return None
    return db_session.query(AlgorithmTask).filter_by(id=int(task_id)).first()


def _save_alert_image(frame: np.ndarray, device_id: str, detection: dict) -> Optional[str]:
    try:
        root = resolve_alert_images_root()
        out_dir = os.path.join(root, f'patrol_{PATROL_SESSION_ID}', device_id)
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(out_dir, f'{ts}_{uuid.uuid4().hex[:8]}.jpg')
        cv2.imwrite(path, frame)
        return path
    except Exception as exc:
        logger.warning('保存告警图失败 device=%s: %s', device_id, exc)
        return None


def _send_alert(device_id: str, device_name: str, frame: np.ndarray, detections: List[dict]):
    from app.utils.alert_class_filter import filter_detections_for_alert

    detections = filter_detections_for_alert(
        detections,
        session_config.alert_class_names if session_config else None,
    )
    if not session_config or not session_config.alert_event_enabled or not detections:
        return
    now = time.time()
    with alert_lock:
        suppress = float(session_config.alert_event_suppress_time or 5)
        last = last_alert_time.get(device_id, 0)
        if suppress > 0 and now - last < suppress:
            return
        last_alert_time[device_id] = now

    counts: Dict[str, int] = {}
    for d in detections:
        cn = d.get('class_name', 'unknown')
        counts[cn] = counts.get(cn, 0) + 1
    primary = max(counts.items(), key=lambda x: x[1])[0] if counts else 'unknown'
    image_path = _save_alert_image(frame, device_id, detections[0])
    alert_data = {
        'object': primary,
        'event': session_config.name,
        'device_id': device_id,
        'device_name': device_name,
        'task_type': 'patrol',
        'face_detection_enabled': bool(session_config.face_detection_enabled),
        'plate_detection_enabled': bool(session_config.plate_detection_enabled),
        'time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'information': json.dumps({
            'total_count': len(detections),
            'object_counts': counts,
            'task_type': 'patrol',
            'patrol_session_id': session_config.session_id,
            'patrol_task_id': session_config.task_id,
        }, ensure_ascii=False),
        'image_path': image_path,
    }
    try:
        requests.post(ALERT_HOOK_URL, json=alert_data, timeout=5)
        logger.info('设备 %s 巡检告警: %s', device_id, counts)
    except Exception as exc:
        logger.warning('发送告警失败 device=%s: %s', device_id, exc)


def _run_detection(frame: np.ndarray) -> List[dict]:
    all_dets: List[dict] = []
    for model_id, model in yolo_models.items():
        infer_device = yolo_model_devices.get(model_id, 'cpu')
        try:
            dets = run_model_detection(
                model,
                frame,
                conf=_get_detect_conf(),
                imgsz=YOLO_IMG_SIZE,
                infer_device=infer_device if infer_device != 'onnx' else 'cpu',
            )
            all_dets.extend(dets)
        except Exception as exc:
            logger.error('模型 %s 检测失败: %s', model_id, exc)
    return all_dets


def _process_patrol_device(device_id: str):
    info = device_streams.get(device_id, {})
    device_name = info.get('device_name', device_id)
    frame = capture_frame(device_id)
    if frame is None or frame.size == 0:
        _update_device_progress(device_id, result='error', error='capture_failed')
        return
    if PATROL_SAVE_SNAP and session_config:
        upload_patrol_frame_to_snap_space(
            device_id,
            frame,
            task_id=session_config.task_id,
            session_id=session_config.session_id,
        )
    detections = _run_detection(frame)
    _update_device_progress(device_id, result='ok', detection_count=len(detections))
    if detections:
        task = _get_patrol_algorithm_task()
        from app.utils.post_process_runner import enqueue_post_process_request, task_needs_sink_processing
        if task and task_needs_sink_processing(task):
            alert_image_path = _save_alert_image(frame, device_id, detections[0])
            try:
                enqueue_post_process_request(
                    task,
                    device_id=device_id,
                    device_name=device_name,
                    frame_number=int(time.time()),
                    timestamp=time.time(),
                    detections=detections,
                    tracked_detections=detections,
                    alert_image_path=alert_image_path,
                )
            except Exception as exc:
                logger.warning('巡检后处理入队失败 device=%s: %s', device_id, exc)
        else:
            _send_alert(device_id, device_name, frame, detections)


def _devices_due(now: float, interval: float, device_ids: Optional[List[str]] = None) -> List[str]:
    targets = device_ids if device_ids is not None else list(device_streams.keys())
    due = []
    with progress_lock:
        for device_id in targets:
            if device_id not in device_streams:
                continue
            entry = device_progress.get(device_id, {})
            last_str = entry.get('last_patrol_at')
            if not last_str:
                due.append(device_id)
                continue
            try:
                last_ts = datetime.strptime(last_str, '%Y-%m-%dT%H:%M:%SZ').timestamp()
            except Exception:
                due.append(device_id)
                continue
            if now - last_ts >= interval:
                due.append(device_id)
    return due


def _run_patrol_batch(device_ids: List[str]):
    if not device_ids:
        return
    threads = []
    for device_id in device_ids:
        t = threading.Thread(target=_process_patrol_device, args=(device_id,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=PATROL_CONNECT_TIMEOUT_SEC + 15)


def patrol_scheduler_worker():
    cfg = session_config
    if not cfg:
        return
    mode = (cfg.patrol_mode or 'pool').lower()
    interval = cfg.interval_sec
    pool_size = cfg.pool_size
    device_list = list(device_streams.keys())
    rotate_idx = 0
    focus_id = cfg.focus_device_id if cfg.focus_device_id in device_streams else None
    background_ids = [d for d in device_list if d != focus_id] if focus_id else device_list
    focus_interval = max(3, interval // 2)
    bg_pool = max(1, pool_size - 1) if focus_id else pool_size

    logger.info(
        '巡检调度启动 mode=%s interval=%ss pool=%s focus=%s devices=%s',
        mode, interval, pool_size, focus_id, len(device_list),
    )

    while not stop_event.is_set():
        try:
            if mode == 'rotate':
                if not device_list:
                    stop_event.wait(1)
                    continue
                device_id = device_list[rotate_idx % len(device_list)]
                rotate_idx += 1
                _process_patrol_device(device_id)
                stop_event.wait(interval / max(1, len(device_list)))
            elif mode == 'hybrid' and focus_id:
                now = time.time()
                focus_due = _devices_due(now, focus_interval, [focus_id])
                if focus_due:
                    _process_patrol_device(focus_id)
                bg_due = _devices_due(now, interval, background_ids)
                if bg_due:
                    _run_patrol_batch(bg_due[:bg_pool])
                if not focus_due and not bg_due:
                    stop_event.wait(0.5)
                else:
                    stop_event.wait(0.3)
            else:
                now = time.time()
                due = _devices_due(now, interval)
                if not due:
                    stop_event.wait(0.5)
                    continue
                _run_patrol_batch(due[:pool_size])
                stop_event.wait(0.3)
        except Exception as exc:
            logger.error('巡检调度异常: %s', exc, exc_info=True)
            stop_event.wait(2)


def send_heartbeat():
    try:
        url = os.getenv('VIDEO_HEARTBEAT_URL', '').strip()
        if not url:
            port = os.getenv('VIDEO_SERVICE_PORT', '6000')
            url = f'http://localhost:{port}/video/patrol/heartbeat'
        with progress_lock:
            payload = {
                'session_id': session_config.session_id if session_config else PATROL_SESSION_ID or None,
                'patrol_session_id': session_config.session_id if session_config else PATROL_SESSION_ID or None,
                'task_id': session_config.task_id if session_config else TASK_ID or None,
                'process_id': os.getpid(),
                'server_ip': os.getenv('HOST_IP') or os.getenv('POD_IP') or '127.0.0.1',
                'progress': dict(device_progress),
                'total_patrols': total_patrols,
                'total_detections': total_detections,
            }
        requests.post(url, json=payload, timeout=5)
    except Exception as exc:
        logger.debug('心跳上报失败: %s', exc)


def heartbeat_worker():
    while not stop_event.is_set():
        send_heartbeat()
        stop_event.wait(15)


def signal_handler(sig, frame):
    logger.info('收到停止信号，退出巡检服务')
    stop_event.set()
    sys.exit(0)


def main():
    if not PATROL_SESSION_ID and not TASK_ID:
        logger.error('PATROL_SESSION_ID 或 TASK_ID 未设置')
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    retry = int(os.getenv('TASK_CONFIG_RETRY_INTERVAL', '10'))
    while not stop_event.is_set():
        if load_patrol_config():
            break
        logger.error('%ss 后重试加载巡检配置', retry)
        stop_event.wait(retry)

    if stop_event.is_set():
        return

    threading.Thread(target=heartbeat_worker, daemon=True).start()
    patrol_scheduler_worker()


if __name__ == '__main__':
    main()
