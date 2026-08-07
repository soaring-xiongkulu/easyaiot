"""
RUNTIME (C++) 配置生成与二进制路径解析。

VIDEO 仍负责编排；本模块只在 executor=cpp 时写出 ini 并供 Daemon 拉起 RUNTIME。
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from models import AlgorithmTask, Device
from app.utils.service_urls import resolve_alert_hook_url, resolve_video_service_base_url

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    # VIDEO/app/services -> VIDEO -> repo
    return Path(__file__).resolve().parents[3]


def resolve_runtime_bin(task: Optional[AlgorithmTask] = None) -> str:
    if task is not None:
        custom = (getattr(task, 'runtime_bin_path', None) or '').strip()
        if custom and os.path.isfile(custom) and os.access(custom, os.X_OK):
            return custom
    env_bin = (os.getenv('RUNTIME_BIN') or '').strip()
    if env_bin and os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
        return env_bin

    root = _repo_root()
    candidates = [
        root / 'RUNTIME' / 'build' / 'RUNTIME',
        root / 'RUNTIME' / 'build' / 'Release' / 'RUNTIME.exe',
        root / 'RUNTIME' / 'build' / 'Debug' / 'RUNTIME.exe',
        root / 'RUNTIME' / 'build' / 'RUNTIME.exe',
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    # Return preferred Linux path even if missing — Daemon will fail with clear log
    return str(candidates[0])


def _first_device(task: AlgorithmTask) -> Optional[Device]:
    devices = list(getattr(task, 'devices', None) or [])
    if devices:
        return devices[0]
    return None


def _resolve_rtsp_url(device: Device) -> str:
    for attr in ('source', 'rtsp_direct'):
        val = (getattr(device, attr, None) or '').strip()
        if val.startswith('rtsp://') or val.startswith('rtsps://'):
            return val
    # fallback: source may be non-rtsp but still usable by FFmpeg
    return (device.source or '').strip()


def _resolve_model_paths(task: AlgorithmTask) -> Tuple[str, str]:
    """Return (onnx_model_path, classes_path). Prefer ONNX under VIDEO data or RUNTIME/models."""
    root = _repo_root()
    default_onnx = root / 'RUNTIME' / 'models' / 'yolo11n.onnx'
    default_names = root / 'RUNTIME' / 'models' / 'coco.names'
    env_model = (os.getenv('RUNTIME_MODEL_PATH') or '').strip()
    env_names = (os.getenv('RUNTIME_CLASSES_PATH') or '').strip()

    model_ids = []
    raw = task.model_ids
    if raw:
        try:
            model_ids = json.loads(raw) if isinstance(raw, str) else list(raw)
        except Exception:
            model_ids = []

    video_root = Path(__file__).resolve().parents[2]
    for mid in model_ids:
        try:
            mid_int = int(mid)
        except Exception:
            continue
        model_dir = video_root / 'data' / 'models' / str(mid_int)
        if model_dir.is_dir():
            for pattern in ('*.onnx', '*.ONNX'):
                matches = sorted(model_dir.glob(pattern))
                if matches:
                    names = default_names if default_names.is_file() else (env_names or str(default_names))
                    return str(matches[0]), str(names)

    onnx = env_model or str(default_onnx)
    names = env_names or str(default_names)
    return onnx, names


def _control_port(task: AlgorithmTask) -> int:
    custom = getattr(task, 'runtime_control_port', None)
    if custom and 8000 <= int(custom) <= 9000:
        return int(custom)
    # 8000 + (task_id % 1000) keeps within 8000-8999
    return 8000 + (int(task.id) % 1000)


def runtime_config_dir() -> Path:
    env_dir = (os.getenv('RUNTIME_CONFIG_DIR') or '').strip()
    if env_dir:
        path = Path(env_dir)
    else:
        path = _repo_root() / 'RUNTIME' / 'config'
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_runtime_ini(task: AlgorithmTask, log_path: str) -> str:
    """Generate RUNTIME ini for a realtime task; returns absolute path."""
    if (getattr(task, 'task_type', None) or 'realtime') != 'realtime':
        raise ValueError('executor=cpp 当前仅支持 realtime 任务')

    device = _first_device(task)
    if device is None:
        raise ValueError(f'任务 {task.id} 未绑定设备，无法生成 RUNTIME 配置')

    rtsp_url = _resolve_rtsp_url(device)
    if not rtsp_url:
        raise ValueError(f'设备 {device.id} 无可用 RTSP/source 地址')

    model_path, classes_path = _resolve_model_paths(task)
    video_base = resolve_video_service_base_url().rstrip('/')
    alert_hook = resolve_alert_hook_url()
    heartbeat = f'{video_base}/video/algorithm/heartbeat/realtime'
    control_port = _control_port(task)
    conf = float(task.detect_conf if task.detect_conf is not None else 0.5)
    cooldown = int(task.alert_event_suppress_time or 30)
    algo_name = (task.model_names or 'detection').split(',')[0].strip() or 'detection'
    rtmp_out = (getattr(device, 'ai_rtmp_stream', None) or task.rtmp_output_url or '').strip()

    ini_path = runtime_config_dir() / f'task_{task.id}.ini'
    content = f"""# Auto-generated by VIDEO for executor=cpp — do not edit by hand while task is running
[video]
rtsp_url={rtsp_url}
rtmp_url={rtmp_out}
width=1920
height=1080
fps=25

[ai]
enable=true
model_path={model_path}
classes_path={classes_path}
threads=2

[alarm]
enable={'true' if task.alert_event_enabled else 'false'}
hook_url={alert_hook}
confidence_threshold={conf}
cooldown_time={cooldown}

[task]
id={task.id}
control_port={control_port}

[video_task]
device_id={device.id}
device_name={device.name or device.id}
task_type=realtime
algorithm_name={algo_name}
alert_hook_url={alert_hook}
heartbeat_url={heartbeat}
heartbeat_interval_sec=10
log_path={log_path}
headless=true

[features]
enable_rtmp={'true' if rtmp_out else 'false'}
enable_draw=true
enable_alarm={'true' if task.alert_event_enabled else 'false'}

[regions]
"""
    ini_path.write_text(content, encoding='utf-8')
    logger.info('已生成 RUNTIME 配置: %s (task_id=%s, device=%s)', ini_path, task.id, device.id)
    return str(ini_path)


def normalize_executor(value) -> str:
    v = (str(value) if value is not None else 'python').strip().lower()
    if v in ('cpp', 'c++', 'runtime', 'cxx'):
        return 'cpp'
    return 'python'
