"""
RUNTIME (C++) 配置生成与二进制路径解析。

VIDEO 仍负责编排；本模块在 executor=cpp 时写出 ini 并供 Daemon 拉起 RUNTIME。
支持 realtime / snap / patrol 三种任务类型（本机）。
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

from models import AlgorithmTask, Device, DeviceDetectionRegion
from app.utils.service_urls import resolve_alert_hook_url, resolve_video_service_base_url

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
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
        root / 'RUNTIME' / 'build' / 'Release' / 'RUNTIME',
        root / 'RUNTIME' / 'build' / 'Debug' / 'RUNTIME',
    ]
    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return str(candidates[0])


def ensure_runtime_bin_ready(task: Optional[AlgorithmTask] = None) -> str:
    """Resolve and validate RUNTIME binary; raise ValueError if missing."""
    path = resolve_runtime_bin(task)
    if not path or not os.path.isfile(path):
        raise ValueError(
            f'RUNTIME 二进制不存在: {path}。请先编译（source RUNTIME/scripts/env.sh && ./RUNTIME/scripts/build_linux.sh）'
        )
    if not os.access(path, os.X_OK):
        raise ValueError(f'RUNTIME 二进制不可执行: {path}')
    return path


def _task_devices(task: AlgorithmTask) -> List[Device]:
    return list(getattr(task, 'devices', None) or [])


def _resolve_rtsp_url(device: Device) -> str:
    for attr in ('source', 'rtsp_direct'):
        val = (getattr(device, attr, None) or '').strip()
        if val.startswith('rtsp://') or val.startswith('rtsps://') or val.startswith('rtmp://'):
            return val
    return (device.source or '').strip()


def _resolve_model_paths(task: AlgorithmTask) -> Tuple[str, str]:
    root = _repo_root()
    default_onnx = root / 'RUNTIME' / 'models' / 'yolov11n.onnx'
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
    return 8000 + (int(task.id) % 1000)


def runtime_config_dir() -> Path:
    env_dir = (os.getenv('RUNTIME_CONFIG_DIR') or '').strip()
    if env_dir:
        path = Path(env_dir)
    else:
        path = _repo_root() / 'RUNTIME' / 'config'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _regions_ini_block(devices: List[Device]) -> str:
    lines: List[str] = []
    for device in devices:
        try:
            regions = DeviceDetectionRegion.query.filter_by(
                device_id=device.id, is_enabled=True
            ).order_by(DeviceDetectionRegion.sort_order.asc()).all()
        except Exception as e:
            logger.warning('load regions for %s failed: %s', device.id, e)
            continue
        for region in regions:
            try:
                pts = json.loads(region.points) if region.points else []
            except Exception:
                pts = []
            if not pts or len(pts) < 3:
                continue
            # Keep normalized 0-1 coords as JSON array
            key = f'{device.id}_{region.region_name or region.id}'.replace(' ', '_')
            lines.append(f'{key}={json.dumps(pts, ensure_ascii=False)}')
    return '\n'.join(lines)


def _devices_json(devices: List[Device]) -> str:
    items = []
    for d in devices:
        url = _resolve_rtsp_url(d)
        if not url:
            continue
        items.append({
            'device_id': d.id,
            'device_name': d.name or d.id,
            'rtsp_url': url,
        })
    return json.dumps(items, ensure_ascii=False)


def _heartbeat_url(task_type: str, video_base: str) -> str:
    base = video_base.rstrip('/')
    if task_type == 'patrol':
        return f'{base}/video/algorithm/heartbeat/patrol'
    return f'{base}/video/algorithm/heartbeat/realtime'


def _hook_task_type(task_type: str) -> str:
    """Value written to ini / sent in alerts (snap -> snapshot for hook compat)."""
    if task_type == 'snap':
        return 'snapshot'
    return task_type or 'realtime'


def generate_runtime_ini(task: AlgorithmTask, log_path: str) -> str:
    """Generate RUNTIME ini for realtime/snap/patrol; returns absolute path."""
    task_type = (getattr(task, 'task_type', None) or 'realtime').strip().lower()
    if task_type == 'snapshot':
        task_type = 'snap'
    if task_type not in ('realtime', 'snap', 'patrol'):
        raise ValueError(f'executor=cpp 不支持任务类型: {task_type}')

    devices = _task_devices(task)
    if not devices:
        raise ValueError(f'任务 {task.id} 未绑定设备，无法生成 RUNTIME 配置')

    primary = devices[0]
    rtsp_url = _resolve_rtsp_url(primary)
    if not rtsp_url:
        raise ValueError(f'设备 {primary.id} 无可用 RTSP/source 地址')

    for d in devices:
        if not _resolve_rtsp_url(d):
            raise ValueError(f'设备 {d.id} 无可用 RTSP/source 地址')

    model_path, classes_path = _resolve_model_paths(task)
    if not os.path.isfile(model_path):
        raise ValueError(f'ONNX 模型不存在: {model_path}')

    video_base = resolve_video_service_base_url().rstrip('/')
    alert_hook = resolve_alert_hook_url()
    heartbeat = _heartbeat_url(task_type, video_base)
    control_port = _control_port(task)
    conf = float(task.detect_conf if task.detect_conf is not None else 0.5)
    cooldown = int(task.alert_event_suppress_time or 30)
    algo_name = (task.model_names or 'detection').split(',')[0].strip() or 'detection'
    rtmp_out = (getattr(primary, 'ai_rtmp_stream', None) or task.rtmp_output_url or '').strip()

    frame_skip = int(getattr(task, 'extract_interval', None) or getattr(task, 'frame_skip', None) or 8)
    if frame_skip <= 0:
        frame_skip = 8

    cron = (getattr(task, 'cron_expression', None) or '').strip()
    patrol_mode = (getattr(task, 'patrol_mode', None) or 'pool').strip() or 'pool'
    patrol_interval = max(3, int(getattr(task, 'patrol_interval_sec', None) or 10))
    patrol_pool = max(1, min(int(getattr(task, 'patrol_pool_size', None) or 4), 16))

    log_dir = os.path.dirname(log_path) if log_path else str(runtime_config_dir())
    alert_image_dir = os.path.join(log_dir, 'alerts')
    os.makedirs(alert_image_dir, exist_ok=True)

    devices_json = _devices_json(devices)
    # Escape for ini single-line: keep as JSON, no raw newlines
    devices_json_one_line = devices_json.replace('\n', '')

    regions_block = _regions_ini_block(devices)

    hook_tt = _hook_task_type(task_type)

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
frame_skip={frame_skip}

[alarm]
enable={'true' if task.alert_event_enabled else 'false'}
hook_url={alert_hook}
confidence_threshold={conf}
cooldown_time={cooldown}
image_dir={alert_image_dir}

[task]
id={task.id}
control_port={control_port}

[video_task]
device_id={primary.id}
device_name={primary.name or primary.id}
task_type={hook_tt}
algorithm_name={algo_name}
alert_hook_url={alert_hook}
heartbeat_url={heartbeat}
heartbeat_interval_sec={'15' if task_type == 'patrol' else '10'}
log_path={log_path}
alert_image_dir={alert_image_dir}
headless=true
frame_skip={frame_skip}
cron_expression={cron}
patrol_mode={patrol_mode}
patrol_interval_sec={patrol_interval}
patrol_pool_size={patrol_pool}
devices_json={devices_json_one_line}

[features]
enable_rtmp={'true' if rtmp_out and task_type == 'realtime' else 'false'}
enable_draw=true
enable_alarm={'true' if task.alert_event_enabled else 'false'}

[regions]
{regions_block}
"""
    ini_path.write_text(content, encoding='utf-8')
    logger.info(
        '已生成 RUNTIME 配置: %s (task_id=%s, type=%s, devices=%s)',
        ini_path, task.id, task_type, len(devices),
    )
    return str(ini_path)


def normalize_executor(value) -> str:
    if value is None or str(value).strip() == '':
        return 'cpp'
    v = str(value).strip().lower()
    if v in ('cpp', 'c++', 'runtime', 'cxx'):
        return 'cpp'
    if v in ('python', 'py'):
        return 'python'
    return 'cpp'


def runtime_library_path_env() -> str:
    """Build LD_LIBRARY_PATH hint for conda + ORT SDK."""
    parts = []
    existing = (os.getenv('LD_LIBRARY_PATH') or '').strip()
    if existing:
        parts.append(existing)
    conda = (os.getenv('CONDA_PREFIX') or '').strip()
    if conda:
        parts.append(os.path.join(conda, 'lib'))
    # common local ORT layout
    ort = _repo_root() / '.deps' / 'onnxruntime-linux-x64-1.23.2' / 'lib'
    if ort.is_dir():
        parts.append(str(ort))
    # dedupe preserve order
    seen = set()
    out = []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return ':'.join(out)
