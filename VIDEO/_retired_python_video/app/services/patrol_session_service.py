"""
摄像头巡检会话服务：创建/启动/停止 patrol_algorithm_service 子进程
"""
from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from models import db, PatrolSession, Device, DeviceDirectory, AlgorithmTask
from app.services import camera_service
from app.services.patrol_progress_hub import publish as publish_patrol_progress

logger = logging.getLogger(__name__)

_running_daemons: Dict[int, 'PatrolSessionDaemon'] = {}
_daemons_lock = threading.Lock()
_starting_sessions: Dict[int, threading.Lock] = {}
_starting_lock = threading.Lock()

PATROL_MAX_DEVICES = int(os.getenv('PATROL_MAX_DEVICES', '128'))
PATROL_MAX_SESSIONS = int(os.getenv('PATROL_MAX_SESSIONS', '4'))


def _video_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _log_dir(session_id: int) -> str:
    log_dir = os.path.join(_video_root(), 'logs', f'patrol_{session_id}')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _parse_id_list(raw) -> List:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _validate_devices(device_ids: List[str]) -> List[str]:
    if not device_ids:
        raise ValueError('设备列表不能为空')
    if len(device_ids) > PATROL_MAX_DEVICES:
        raise ValueError(f'单会话设备数不能超过 {PATROL_MAX_DEVICES}')
    unique = []
    seen = set()
    for did in device_ids:
        s = str(did).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        unique.append(s)
    if not unique:
        raise ValueError('设备列表不能为空')
    return unique


def create_patrol_session(data: dict) -> PatrolSession:
    device_ids = _validate_devices(data.get('device_ids') or [])
    model_ids = data.get('model_ids') or []
    if not model_ids:
        raise ValueError('模型列表不能为空')

    algorithm_task_id = data.get('algorithm_task_id')
    if algorithm_task_id:
        task = AlgorithmTask.query.get(int(algorithm_task_id))
        if not task:
            raise ValueError(f'算法任务不存在: {algorithm_task_id}')
        if not model_ids and task.model_ids:
            model_ids = _parse_id_list(task.model_ids)

    patrol_mode = 'pool'
    interval_sec = max(3, int(data.get('interval_sec') or 10))
    pool_size = max(1, min(int(data.get('pool_size') or 4), 16))

    session = PatrolSession(
        session_name=(data.get('session_name') or f'巡检-{datetime.utcnow():%m%d%H%M}').strip(),
        patrol_mode=patrol_mode,
        interval_sec=interval_sec,
        pool_size=pool_size,
        device_ids=json.dumps(device_ids),
        model_ids=json.dumps([int(x) for x in model_ids]),
        focus_device_id=None,
        algorithm_task_id=algorithm_task_id,
        alert_event_enabled=bool(data.get('alert_event_enabled', True)),
        alert_event_suppress_time=int(data.get('alert_event_suppress_time') or 5),
        face_detection_enabled=bool(data.get('face_detection_enabled', True)),
        plate_detection_enabled=bool(data.get('plate_detection_enabled', True)),
        status='stopped',
        progress_json=json.dumps({did: {} for did in device_ids}),
    )
    db.session.add(session)
    db.session.commit()
    return session


def get_patrol_session(session_id: int) -> Optional[PatrolSession]:
    return PatrolSession.query.get(session_id)


def _collect_subdirectory_ids(directory_id: int) -> List[int]:
    ids = [directory_id]
    children = DeviceDirectory.query.filter_by(parent_id=directory_id).all()
    for child in children:
        ids.extend(_collect_subdirectory_ids(child.id))
    return ids


def resolve_directory_device_ids(
    directory_id: int,
    *,
    include_children: bool = True,
) -> Tuple[List[str], str]:
    directory = DeviceDirectory.query.get(directory_id)
    if not directory:
        raise ValueError(f'目录不存在: ID={directory_id}')

    if camera_service.is_default_directory(directory):
        from app.services.gb28181_sync_service import sync_gb28181_channels_to_devices

        try:
            sync_gb28181_channels_to_devices(strict=False)
        except Exception as exc:
            logger.warning('目录巡检设备列表加载前国标同步失败: %s', exc)

    dir_ids = _collect_subdirectory_ids(directory_id) if include_children else [directory_id]
    devices = (
        Device.query.filter(Device.directory_id.in_(dir_ids))
        .order_by(Device.updated_at.desc())
        .all()
    )
    device_ids: List[str] = []
    seen = set()
    for device in devices:
        if device.id in seen:
            continue
        seen.add(device.id)
        device_ids.append(device.id)
    return device_ids, directory.name


def build_session_stats_payload(session: PatrolSession) -> dict:
    data = session.to_dict()
    device_ids = data.get('device_ids') or []
    progress = data.get('progress') or {}
    done = sum(1 for did in device_ids if progress.get(did, {}).get('last_patrol_at'))
    return {
        **data,
        'completed_devices': done,
        'total_devices': len(device_ids),
        'completion_ratio': (done / len(device_ids)) if device_ids else 0,
    }


def broadcast_patrol_session(session_id: int, event_type: str = 'progress') -> None:
    session = PatrolSession.query.get(session_id)
    if not session:
        return
    publish_patrol_progress(session_id, event_type, build_session_stats_payload(session))


def update_patrol_progress(session_id: int, progress: dict, *, total_patrols: int = None,
                           total_detections: int = None) -> None:
    session = PatrolSession.query.get(session_id)
    if not session:
        return
    session.progress_json = json.dumps(progress, ensure_ascii=False)
    session.last_patrol_time = datetime.utcnow()
    if total_patrols is not None:
        session.total_patrols = total_patrols
    if total_detections is not None:
        session.total_detections = total_detections
    db.session.commit()


class PatrolSessionDaemon:
    """巡检会话守护进程"""

    def __init__(self, session_id: int, log_path: str):
        self._session_id = session_id
        self._log_path = log_path
        self._process = None
        self._running = True
        threading.Thread(target=self._daemon_loop, daemon=True).start()

    def _log_file(self) -> str:
        os.makedirs(self._log_path, exist_ok=True)
        return os.path.join(self._log_path, datetime.now().strftime('%Y-%m-%d.log'))

    def _build_env(self) -> dict:
        env = os.environ.copy()
        video_env = os.getenv('VIDEO_ENV', '').strip()
        if video_env:
            env['VIDEO_ENV'] = video_env
        for key in (
            'DATABASE_URL', 'GATEWAY_URL', 'GB28181_SERVICE_URL', 'JWT_TOKEN', 'JAVA_BACKEND_URL',
            'GB28181_HTTP_READ_TIMEOUT', 'GB28181_PLAY_PROTOCOL', 'GB28181_HEVC_RTSP_FIRST',
            'GB28181_OPENCV_RTMP_FALLBACK_RTSP', 'POD_IP', 'HOST_IP', 'AI_SERVICE_URL',
            'USE_GPU', 'GPU_IDS', 'GPU_POLICY', 'INFER_GPU_POLICY',
            'KAFKA_BOOTSTRAP_SERVERS', 'MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY',
            'MINIO_SECURE',
        ):
            val = os.getenv(key)
            if val is not None and val != '':
                env[key] = val
        env['PYTHONUNBUFFERED'] = '1'
        env['PATROL_SESSION_ID'] = str(self._session_id)
        env['LOG_PATH'] = self._log_path
        video_service_port = os.getenv('FLASK_RUN_PORT', '6000')
        env['VIDEO_SERVICE_PORT'] = video_service_port
        gateway = os.getenv('JAVA_BACKEND_URL', os.getenv('GATEWAY_URL', 'http://localhost:48080')).rstrip('/')
        env['VIDEO_CONTROL_URL'] = f'{gateway}/admin-api/video'
        env['VIDEO_HEARTBEAT_URL'] = f'{env["VIDEO_CONTROL_URL"]}/patrol/heartbeat'
        kafka = env.get('KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
        if 'Kafka' in kafka or 'kafka-server' in kafka:
            env['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
        else:
            env['KAFKA_BOOTSTRAP_SERVERS'] = kafka
        return env

    def _get_deploy_args(self) -> Tuple[Optional[list], Optional[str], Optional[dict]]:
        video_root = _video_root()
        deploy_dir = os.path.join(video_root, 'services', 'patrol_algorithm_service')
        script = os.path.join(deploy_dir, 'run_deploy.py')
        if not os.path.exists(script):
            logger.error('巡检脚本不存在: %s', script)
            return None, None, None
        python_exec = sys.executable
        return [python_exec, script], deploy_dir, self._build_env()

    def _daemon_loop(self):
        log_path = self._log_file()
        while self._running:
            try:
                cmds, cwd, env = self._get_deploy_args()
                if not cmds:
                    time.sleep(10)
                    continue
                with open(log_path, 'a', encoding='utf-8') as f_log:
                    f_log.write(f'\n# 启动 patrol session {self._session_id} {datetime.now().isoformat()}\n')
                    f_log.flush()
                    self._process = subprocess.Popen(
                        cmds,
                        cwd=cwd,
                        env=env,
                        stdout=f_log,
                        stderr=subprocess.STDOUT,
                        preexec_fn=os.setsid,
                    )
                    self._process.wait()
                if not self._running:
                    break
                logger.warning('巡检进程退出 session_id=%s，5s 后重启', self._session_id)
                time.sleep(5)
            except Exception as exc:
                logger.error('巡检守护进程异常 session_id=%s: %s', self._session_id, exc, exc_info=True)
                time.sleep(5)

    def stop(self):
        self._running = False
        if self._process and self._process.poll() is None:
            try:
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                self._process.wait(timeout=10)
            except Exception:
                try:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                except Exception:
                    pass
        self._process = None


def _running_session_count() -> int:
    with _daemons_lock:
        return sum(
            1 for d in _running_daemons.values()
            if d._running and d._process and d._process.poll() is None
        )


def start_patrol_session(session_id: int) -> Tuple[bool, str]:
    session = PatrolSession.query.get(session_id)
    if not session:
        return False, '巡检会话不存在'
    if session.status == 'running':
        with _daemons_lock:
            daemon = _running_daemons.get(session_id)
            if daemon and daemon._process and daemon._process.poll() is None:
                return True, '巡检已在运行'

    if _running_session_count() >= PATROL_MAX_SESSIONS:
        return False, f'同时运行的巡检会话不能超过 {PATROL_MAX_SESSIONS} 个'

    with _starting_lock:
        if session_id not in _starting_sessions:
            _starting_sessions[session_id] = threading.Lock()
        lock = _starting_sessions[session_id]
    if not lock.acquire(blocking=False):
        return True, '巡检正在启动中'

    try:
        stop_patrol_session(session_id, update_status=False)
        log_path = _log_dir(session_id)
        daemon = PatrolSessionDaemon(session_id, log_path)
        with _daemons_lock:
            _running_daemons[session_id] = daemon
        session.status = 'running'
        session.exception_reason = None
        session.service_log_path = log_path
        db.session.commit()
        broadcast_patrol_session(session_id, 'status')
        return True, '巡检已启动'
    except Exception as exc:
        session.status = 'error'
        session.exception_reason = str(exc)
        db.session.commit()
        return False, str(exc)
    finally:
        lock.release()


def stop_patrol_session(session_id: int, update_status: bool = True) -> Tuple[bool, str]:
    with _daemons_lock:
        daemon = _running_daemons.pop(session_id, None)
    if daemon:
        try:
            daemon.stop()
        except Exception as exc:
            logger.warning('停止巡检守护进程失败 session_id=%s: %s', session_id, exc)

    session = PatrolSession.query.get(session_id)
    if session and update_status:
        session.status = 'stopped'
        session.service_process_id = None
        db.session.commit()
        broadcast_patrol_session(session_id, 'status')
    return True, '巡检已停止'


def receive_patrol_heartbeat(data: dict) -> bool:
    session_id = data.get('session_id') or data.get('patrol_session_id')
    if not session_id:
        return False
    session = PatrolSession.query.get(int(session_id))
    if not session:
        return False
    session.service_last_heartbeat = datetime.utcnow()
    if data.get('server_ip'):
        session.service_server_ip = data['server_ip']
    if data.get('process_id'):
        session.service_process_id = data['process_id']
    if data.get('progress') is not None:
        session.progress_json = json.dumps(data['progress'], ensure_ascii=False)
    if data.get('total_patrols') is not None:
        session.total_patrols = int(data['total_patrols'])
    if data.get('total_detections') is not None:
        session.total_detections = int(data['total_detections'])
    if session.status != 'stopped':
        session.status = 'running'
    db.session.commit()
    broadcast_patrol_session(int(session_id), 'progress')
    return True
