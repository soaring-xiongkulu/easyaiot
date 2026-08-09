"""
RUNTIME (C++) 配置生成与二进制路径解析。

VIDEO 仍负责编排；本模块在 executor=cpp 时写出 ini 并供 Daemon / 远程 Agent 拉起 RUNTIME。
支持 realtime / snap / patrol（本机与集群节点）。
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
    """Best-effort monorepo root (host) or VIDEO parent."""
    video_root = Path(__file__).resolve().parents[2]
    sibling_runtime = video_root.parent / 'RUNTIME'
    if sibling_runtime.is_dir():
        return video_root.parent
    # Docker mount layout: /opt/easyaiot/RUNTIME
    opt = Path('/opt/easyaiot')
    if (opt / 'RUNTIME').is_dir():
        return opt
    return video_root.parent


def _is_runtime_bin(path: str) -> bool:
    """True if path looks like a usable RUNTIME binary (Windows .exe friendly)."""
    if not path or not os.path.isfile(path):
        return False
    lower = path.lower()
    if lower.endswith('.exe') or lower.endswith('.bat') or lower.endswith('.cmd'):
        return True
    return os.access(path, os.X_OK)


def resolve_runtime_bin(task: Optional[AlgorithmTask] = None) -> str:
    if task is not None:
        custom = (getattr(task, 'runtime_bin_path', None) or '').strip()
        if custom and _is_runtime_bin(custom):
            return custom
    env_bin = (os.getenv('RUNTIME_BIN') or '').strip()
    if env_bin and _is_runtime_bin(env_bin):
        return env_bin

    root = _repo_root()
    candidates = [
        Path('/opt/easyaiot/RUNTIME/build/RUNTIME'),
        root / 'RUNTIME' / 'build-win' / 'Release' / 'RUNTIME.exe',
        root / 'RUNTIME' / 'build' / 'RUNTIME',
        root / 'RUNTIME' / 'build' / 'Release' / 'RUNTIME',
        root / 'RUNTIME' / 'build' / 'Release' / 'RUNTIME.exe',
        root / 'RUNTIME' / 'build' / 'Debug' / 'RUNTIME',
        root / 'RUNTIME' / 'build' / 'Debug' / 'RUNTIME.exe',
    ]
    for path in candidates:
        if _is_runtime_bin(str(path)):
            return str(path)
    return str(candidates[1] if (root / 'RUNTIME').is_dir() else candidates[0])


def ensure_runtime_bin_ready(task: Optional[AlgorithmTask] = None) -> str:
    """Resolve and validate RUNTIME binary; raise ValueError if missing."""
    path = resolve_runtime_bin(task)
    if not path or not os.path.isfile(path):
        raise ValueError(
            f'RUNTIME 二进制不存在: {path}。请先编译（Windows: MSVC build-win；'
            f'Linux: source RUNTIME/scripts/env.sh && ./RUNTIME/scripts/build_linux.sh）'
        )
    if not _is_runtime_bin(path):
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


def _resolve_model_paths(task: AlgorithmTask, prefer_cluster: bool = False) -> Tuple[str, str]:
    root = _repo_root()
    default_onnx = root / 'RUNTIME' / 'models' / 'yolov11n.onnx'
    default_names = root / 'RUNTIME' / 'models' / 'coco.names'
    # Remote install layout
    remote_default_onnx = Path('/opt/easyaiot/RUNTIME/models/yolov11n.onnx')
    remote_default_names = Path('/opt/easyaiot/RUNTIME/models/coco.names')
    env_model = (os.getenv('RUNTIME_MODEL_PATH') or '').strip()
    env_names = (os.getenv('RUNTIME_CLASSES_PATH') or '').strip()

    model_ids = []
    raw = task.model_ids
    if raw:
        try:
            model_ids = json.loads(raw) if isinstance(raw, str) else list(raw)
        except Exception:
            model_ids = []

    if prefer_cluster and model_ids:
        try:
            import sys
            lib = str((_repo_root() / '.scripts' / 'lib').resolve())
            if lib not in sys.path:
                sys.path.insert(0, lib)
            from model_resolver import try_resolve_cluster_model_path, get_model_cluster_dir
        except Exception as e:
            logger.warning('cluster model resolver unavailable: %s', e)
            try_resolve_cluster_model_path = None  # type: ignore
            get_model_cluster_dir = None  # type: ignore
        else:
            for mid in model_ids:
                try:
                    mid_int = int(mid)
                except Exception:
                    continue
                found = try_resolve_cluster_model_path(mid_int) if try_resolve_cluster_model_path else None
                if found and str(found).lower().endswith('.onnx'):
                    names = str(default_names if default_names.is_file() else (
                        remote_default_names if remote_default_names.is_file() else (env_names or default_names)
                    ))
                    # companion .names next to weights if any
                    sibling = Path(found).with_suffix('.names')
                    if sibling.is_file():
                        names = str(sibling)
                    return str(found), names
                # Prefer onnx under cluster dir even if resolver returned .pt first
                if get_model_cluster_dir:
                    model_dir = Path(get_model_cluster_dir(mid_int))
                    if model_dir.is_dir():
                        matches = sorted(model_dir.glob('*.onnx')) + sorted(model_dir.glob('*.ONNX'))
                        if matches:
                            names = str(default_names if default_names.is_file() else (
                                remote_default_names if remote_default_names.is_file() else default_names
                            ))
                            return str(matches[0]), names
                    # Ceph may not be mounted on control plane; still emit canonical remote path
                    canonical = model_dir / 'model.onnx'
                    names = str(remote_default_names if remote_default_names.is_file() else (
                        default_names if default_names.is_file() else remote_default_names
                    ))
                    return str(canonical), names

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

    if prefer_cluster and remote_default_onnx.is_file():
        names = str(remote_default_names if remote_default_names.is_file() else (env_names or remote_default_names))
        return str(remote_default_onnx), names

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


def _bool01(val: object) -> str:
    return 'true' if bool(val) else 'false'


def _log_cpp_unsupported_fields(task: AlgorithmTask) -> None:
    """G-2.1/G-2.3: WARNING when task enables CAPs not on RUNTIME hot path."""
    gaps = []
    checks = (
        ('tracking_enabled', 'CAP-TRACKING — C++ tracker parity pending Phase 4'),
        ('motion_gate_enabled', 'CAP-MOTION-GATE — deferred to Phase 4'),
        ('pose_analysis_enabled', 'pose analysis — not in RUNTIME hot path yet'),
        ('pose_intent_enabled', 'pose intent — VIDEO/post path'),
        ('sam_supplement_enabled', 'SAM supplement — product cut; must not silent-succeed'),
        ('post_process_enabled', 'post_process — VIDEO Phase 3 absorb'),
        ('face_matching_enabled', 'face matching — VIDEO Phase 3 absorb'),
        ('plate_matching_enabled', 'plate matching — VIDEO Phase 3 absorb'),
        ('alert_notification_enabled', 'alert notification — VIDEO-side only'),
    )
    for attr, note in checks:
        if bool(getattr(task, attr, False)):
            gaps.append(f'{attr}: {note}')
    if gaps:
        logger.warning(
            'executor=cpp unsupported/deferred fields for task_id=%s: %s',
            getattr(task, 'id', None),
            '; '.join(gaps),
        )


def generate_runtime_ini(
    task: AlgorithmTask,
    log_path: str,
    *,
    prefer_cluster_model: bool = False,
    write_local: bool = True,
    remote_ini_path: Optional[str] = None,
) -> str:
    """Generate RUNTIME ini for realtime/snap/patrol; returns path (local or intended remote)."""
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

    model_path, classes_path = _resolve_model_paths(task, prefer_cluster=prefer_cluster_model)
    if write_local and not os.path.isfile(model_path):
        raise ValueError(f'ONNX 模型不存在: {model_path}')
    if prefer_cluster_model and not str(model_path).lower().endswith('.onnx'):
        raise ValueError(
            f'远程 cpp 需要 ONNX 模型，当前解析到: {model_path}。请确保模型已同步至集群且含 .onnx'
        )

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
    if write_local:
        os.makedirs(alert_image_dir, exist_ok=True)

    devices_json = _devices_json(devices)
    # Escape for ini single-line: keep as JSON, no raw newlines
    devices_json_one_line = devices_json.replace('\n', '')

    regions_block = _regions_ini_block(devices)

    hook_tt = _hook_task_type(task_type)

    # GPU default on; USE_GPU=false / RUNTIME_FORCE_CPU forces CPU
    use_gpu_env = (os.getenv('USE_GPU') or '').strip().lower()
    force_cpu_env = (os.getenv('RUNTIME_FORCE_CPU') or '').strip().lower()
    prefer_gpu = True
    force_cpu = False
    if force_cpu_env in ('1', 'true', 'yes', 'on'):
        prefer_gpu = False
        force_cpu = True
    elif use_gpu_env in ('false', '0', 'no', 'off'):
        prefer_gpu = False
    prefer_gpu_env = (os.getenv('RUNTIME_PREFER_GPU') or '').strip().lower()
    if prefer_gpu_env in ('false', '0', 'no', 'off'):
        prefer_gpu = False
    elif prefer_gpu_env in ('true', '1', 'yes', 'on'):
        prefer_gpu = True
    # Task-level prefer_gpu
    if hasattr(task, 'prefer_gpu') and task.prefer_gpu is not None:
        prefer_gpu = bool(task.prefer_gpu)
        if not prefer_gpu:
            force_cpu = True
    try:
        gpu_device_id = int(os.getenv('RUNTIME_GPU_DEVICE_ID') or '0')
    except Exception:
        gpu_device_id = 0
    if gpu_device_id < 0:
        gpu_device_id = 0

    if remote_ini_path:
        ini_path = Path(remote_ini_path)
    else:
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
prefer_gpu={'true' if prefer_gpu else 'false'}
force_cpu={'true' if force_cpu else 'false'}
gpu_device_id={gpu_device_id}

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

# Phase 2 contract: declare non-frame / deferred CAPs so RUNTIME never silently pretends support.
[unsupported]
tracking={_bool01(getattr(task, 'tracking_enabled', False))}
motion_gate={_bool01(getattr(task, 'motion_gate_enabled', False))}
pose_analysis={_bool01(getattr(task, 'pose_analysis_enabled', False))}
pose_intent={_bool01(getattr(task, 'pose_intent_enabled', False))}
sam_supplement={_bool01(getattr(task, 'sam_supplement_enabled', False))}
post_process={_bool01(getattr(task, 'post_process_enabled', False))}
face_matching={_bool01(getattr(task, 'face_matching_enabled', False))}
plate_matching={_bool01(getattr(task, 'plate_matching_enabled', False))}
alert_notification={_bool01(getattr(task, 'alert_notification_enabled', False))}
face_detection_flag={_bool01(getattr(task, 'face_detection_enabled', True))}
plate_detection_flag={_bool01(getattr(task, 'plate_detection_enabled', True))}
alert_class_names={(getattr(task, 'alert_class_names', None) or '').replace(chr(10), '')}
"""
    _log_cpp_unsupported_fields(task)
    if write_local:
        ini_path.parent.mkdir(parents=True, exist_ok=True)
        ini_path.write_text(content, encoding='utf-8')
        logger.info(
            '已生成 RUNTIME 配置: %s (task_id=%s, type=%s, devices=%s)',
            ini_path, task.id, task_type, len(devices),
        )
    else:
        # stash content for remote deploy callers
        generate_runtime_ini.last_content = content  # type: ignore[attr-defined]
        logger.info(
            '已生成 RUNTIME 远程配置内容 (task_id=%s, type=%s, remote=%s)',
            task.id, task_type, ini_path,
        )
    return str(ini_path)


def generate_runtime_ini_content(
    task: AlgorithmTask,
    log_path: str,
    *,
    prefer_cluster_model: bool = True,
    remote_ini_path: Optional[str] = None,
) -> Tuple[str, str]:
    """Return (remote_ini_path, ini_content) without requiring local model file."""
    path = generate_runtime_ini(
        task,
        log_path,
        prefer_cluster_model=prefer_cluster_model,
        write_local=False,
        remote_ini_path=remote_ini_path or f'/opt/easyaiot/RUNTIME/config/task_{task.id}.ini',
    )
    content = getattr(generate_runtime_ini, 'last_content', '') or ''
    if not content:
        raise ValueError('生成 RUNTIME ini 内容失败')
    return path, content


REMOTE_RUNTIME_BIN = '/opt/easyaiot/RUNTIME/bin/RUNTIME'
REMOTE_RUNTIME_LD_LIBRARY_PATH = (
    '/opt/easyaiot/RUNTIME/lib:/usr/local/cuda/lib64:/usr/local/cuda/lib'
    ':/usr/lib/x86_64-linux-gnu:/usr/lib/aarch64-linux-gnu'
)


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
    """Build LD_LIBRARY_PATH (Linux) or PATH-prepend list (Windows) for RUNTIME deps."""
    root = _repo_root()
    if os.name == 'nt':
        parts = []
        existing = (os.getenv('PATH') or '').strip()
        vendor = root / 'RUNTIME' / 'vendor' / 'win-x64'
        candidates = [
            root / 'RUNTIME' / 'build-win' / 'Release',
            vendor / 'conda-pkgs' / 'libprotobuf' / 'Library' / 'bin',
            vendor / 'conda-pkgs' / 'opencv' / 'Library' / 'bin',
            vendor / 'conda-pkgs' / 'ffmpeg' / 'Library' / 'bin',
            vendor / 'conda-pkgs' / 'jsoncpp' / 'Library' / 'bin',
            vendor / 'conda-pkgs' / 'ffmpeg4' / 'Library' / 'bin',
            vendor / '_conda_ffmpeg4' / 'Library' / 'bin',
            vendor / 'onnxruntime' / 'lib',
        ]
        conda = (os.getenv('CONDA_PREFIX') or '').strip()
        if conda:
            candidates.append(Path(conda) / 'Library' / 'bin')
        for p in candidates:
            if p.is_dir():
                parts.append(str(p))
        # preserve existing PATH last
        if existing:
            parts.append(existing)
        seen = set()
        out = []
        for p in parts:
            if p and p not in seen:
                seen.add(p)
                out.append(p)
        return os.pathsep.join(out)

    parts = []
    existing = (os.getenv('LD_LIBRARY_PATH') or '').strip()
    if existing:
        parts.append(existing)
    for mounted in (
        '/opt/easyaiot/runtime-conda-lib',
        '/opt/easyaiot/ort-lib',
        '/opt/easyaiot/cuda-lib',
    ):
        if os.path.isdir(mounted):
            parts.append(mounted)
    conda = (os.getenv('CONDA_PREFIX') or '').strip()
    if conda:
        parts.append(os.path.join(conda, 'lib'))
    for arch in ('x64', 'aarch64'):
        for name in (
            f'onnxruntime-linux-{arch}-gpu-1.23.2',
            f'onnxruntime-linux-{arch}-1.23.2',
        ):
            ort = root / '.deps' / name / 'lib'
            if ort.is_dir():
                parts.append(str(ort))
                break
        else:
            continue
        break
    for cuda_path in (
        '/usr/local/cuda/lib64',
        '/usr/local/cuda/lib',
        '/usr/lib/x86_64-linux-gnu',
        '/usr/lib/aarch64-linux-gnu',
    ):
        if os.path.isdir(cuda_path):
            parts.append(cuda_path)
    seen = set()
    out = []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return ':'.join(out)
