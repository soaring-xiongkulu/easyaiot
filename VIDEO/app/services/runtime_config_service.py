"""
RUNTIME (C++) 配置生成与二进制路径解析。

VIDEO 仍负责编排；本模块在 executor=cpp 时写出 ini 并供 Daemon / 远程 Agent 拉起 RUNTIME。
支持 realtime / snap / patrol（本机与集群节点）。

本地 IDEA / run.py 启动时：若本机尚无 RUNTIME 二进制，默认自动触发
`RUNTIME/install_linux.sh install`（与 export 包一致，可用 RUNTIME_AUTO_INSTALL=0 或
EASYAIOT_RUNTIME_SKIP=1 关闭）。容器内不自动编译（期望宿主机挂载）。
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import List, Optional, Tuple

from models import AlgorithmTask, Device, DeviceDetectionRegion
from app.utils.service_urls import resolve_alert_hook_url, resolve_video_service_base_url

logger = logging.getLogger(__name__)

_AUTO_BUILD_LOCK = threading.Lock()
_AUTO_BUILD_DONE = False


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


def _running_in_docker() -> bool:
    raw = (os.getenv('RUNNING_IN_DOCKER') or os.getenv('VIDEO_IN_DOCKER') or '').strip().lower()
    if raw in ('1', 'true', 'yes', 'on'):
        return True
    return Path('/.dockerenv').is_file()


def _runtime_auto_install_enabled() -> bool:
    if (os.getenv('EASYAIOT_RUNTIME_SKIP') or '').strip() == '1':
        return False
    raw = (os.getenv('RUNTIME_AUTO_INSTALL') or '1').strip().lower()
    return raw in ('1', 'true', 'yes', 'on')


def apply_runtime_deploy_env() -> None:
    """把 RUNTIME/deploy.env 合并进当前进程（不覆盖已显式设置的变量）。"""
    deploy_env = _repo_root() / 'RUNTIME' / 'deploy.env'
    if not deploy_env.is_file():
        return
    try:
        for line in deploy_env.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not key:
                continue
            if key in os.environ and str(os.environ.get(key) or '').strip():
                continue
            os.environ[key] = value
    except Exception as e:
        logger.warning('读取 RUNTIME/deploy.env 失败: %s', e)


def resolve_runtime_bin(task: Optional[AlgorithmTask] = None) -> str:
    apply_runtime_deploy_env()
    if task is not None:
        custom = (getattr(task, 'runtime_bin_path', None) or '').strip()
        if custom and os.path.isfile(custom) and os.access(custom, os.X_OK):
            return custom
    env_bin = (os.getenv('RUNTIME_BIN') or '').strip()
    if env_bin and os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
        return env_bin

    root = _repo_root()
    candidates = [
        Path('/opt/easyaiot/RUNTIME/build/RUNTIME'),
        root / 'RUNTIME' / 'build' / 'RUNTIME',
        root / 'RUNTIME' / 'build' / 'Release' / 'RUNTIME',
        root / 'RUNTIME' / 'build' / 'Debug' / 'RUNTIME',
    ]
    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return str(candidates[1] if (root / 'RUNTIME').is_dir() else candidates[0])


def _runtime_bin_exists(task: Optional[AlgorithmTask] = None) -> Optional[str]:
    path = resolve_runtime_bin(task)
    if path and os.path.isfile(path) and os.access(path, os.X_OK):
        return path
    return None


def try_auto_build_runtime(*, reason: str = '') -> bool:
    """本机缺失 RUNTIME 时自动执行 install_linux.sh install。成功返回 True。"""
    global _AUTO_BUILD_DONE
    existing = _runtime_bin_exists(None)
    if existing:
        os.environ.setdefault('RUNTIME_BIN', existing)
        return True

    if not _runtime_auto_install_enabled():
        logger.info(
            'RUNTIME 二进制不存在，且已关闭自动编译（RUNTIME_AUTO_INSTALL=0 / EASYAIOT_RUNTIME_SKIP=1）'
        )
        return False

    if sys.platform != 'linux':
        logger.warning(
            '当前系统 %s 非 Linux：跳过 RUNTIME 自动编译。可用 executor=python，或自行交叉编译。',
            sys.platform,
        )
        return False

    if _running_in_docker():
        logger.warning(
            '容器内未找到 RUNTIME 二进制，跳过自动编译（请在宿主机执行 '
            'VIDEO/scripts/ensure_runtime_cpp.sh 或 RUNTIME/install_linux.sh）'
        )
        return False

    # Flask debug reloader：父进程不编译
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'false':
        return False

    root = _repo_root()
    install_sh = root / 'RUNTIME' / 'install_linux.sh'
    if not install_sh.is_file():
        logger.warning('未找到 %s，无法自动编译 RUNTIME', install_sh)
        return False

    with _AUTO_BUILD_LOCK:
        if _AUTO_BUILD_DONE:
            return bool(_runtime_bin_exists(None))
        existing = _runtime_bin_exists(None)
        if existing:
            os.environ.setdefault('RUNTIME_BIN', existing)
            _AUTO_BUILD_DONE = True
            return True

        why = f'（{reason}）' if reason else ''
        logger.info('未检测到 RUNTIME 二进制%s，自动执行: bash %s install …', why, install_sh)
        print(
            f'[VIDEO] 未检测到 RUNTIME，开始自动编译（可能需数分钟）…\n'
            f'        bash {install_sh} install\n'
            f'        关闭: RUNTIME_AUTO_INSTALL=0 或 EASYAIOT_RUNTIME_SKIP=1',
            flush=True,
        )
        try:
            completed = subprocess.run(
                ['bash', str(install_sh), 'install'],
                cwd=str(install_sh.parent),
                check=False,
            )
        except Exception as e:
            logger.error('自动编译 RUNTIME 启动失败: %s', e, exc_info=True)
            _AUTO_BUILD_DONE = True
            return False

        apply_runtime_deploy_env()
        ready = _runtime_bin_exists(None)
        _AUTO_BUILD_DONE = True
        if completed.returncode != 0 or not ready:
            logger.warning(
                'RUNTIME 自动编译失败（exit=%s）。executor=cpp 任务将不可用，'
                '可改用 executor=python，或手工执行: bash %s install',
                completed.returncode,
                install_sh,
            )
            return False

        os.environ.setdefault('RUNTIME_BIN', ready)
        lib = runtime_library_path_env()
        if lib:
            os.environ['LD_LIBRARY_PATH'] = lib
        logger.info('RUNTIME 自动编译完成: %s', ready)
        print(f'[VIDEO] RUNTIME 就绪: {ready}', flush=True)
        return True


def ensure_runtime_on_video_startup() -> None:
    """VIDEO 启动时软检查：已有则加载 env；缺失则尝试自动编译（失败只告警）。"""
    apply_runtime_deploy_env()
    existing = _runtime_bin_exists(None)
    if existing:
        os.environ.setdefault('RUNTIME_BIN', existing)
        lib = runtime_library_path_env()
        if lib and not (os.getenv('LD_LIBRARY_PATH') or '').strip():
            os.environ['LD_LIBRARY_PATH'] = lib
        logger.info('RUNTIME 已就绪: %s', existing)
        return

    if not _runtime_auto_install_enabled():
        logger.info('本机未找到 RUNTIME，自动编译已关闭，executor=cpp 任务需先手工编译')
        return

    ok = try_auto_build_runtime(reason='VIDEO 本地启动')
    if not ok and (os.getenv('EASYAIOT_RUNTIME_REQUIRED') or '').strip() == '1':
        raise RuntimeError(
            'EASYAIOT_RUNTIME_REQUIRED=1 且 RUNTIME 不可用，终止启动。'
            '请编译 RUNTIME 或关闭该开关。'
        )


def ensure_runtime_bin_ready(task: Optional[AlgorithmTask] = None) -> str:
    """Resolve and validate RUNTIME binary; raise ValueError if missing."""
    path = _runtime_bin_exists(task)
    if not path:
        if try_auto_build_runtime(reason='算法任务启动'):
            path = _runtime_bin_exists(task)
    if not path:
        expected = resolve_runtime_bin(task)
        raise ValueError(
            f'RUNTIME 二进制不存在: {expected}。'
            f'请先编译（bash RUNTIME/install_linux.sh install），'
            f'或确认未设置 RUNTIME_AUTO_INSTALL=0 / EASYAIOT_RUNTIME_SKIP=1'
        )
    if not os.access(path, os.X_OK):
        raise ValueError(f'RUNTIME 二进制不可执行: {path}')
    return path


def _parse_version_file(path: Path) -> dict:
    data = {}
    if not path.is_file():
        return data
    try:
        for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                data[key] = value
    except Exception as e:
        logger.warning('解析 VERSION 失败 %s: %s', path, e)
    return data


def read_runtime_version_info(task: Optional[AlgorithmTask] = None) -> dict:
    """读取本机 RUNTIME 版本信息（VERSION 文件 / deploy.env / 二进制旁）。"""
    apply_runtime_deploy_env()
    bin_path = _runtime_bin_exists(task)
    root = _repo_root()
    candidates = []
    if bin_path:
        bin_p = Path(bin_path)
        candidates.append(bin_p.parent / 'VERSION')
        # /opt/easyaiot/RUNTIME/bin/RUNTIME → /opt/easyaiot/RUNTIME/VERSION
        if bin_p.parent.name == 'bin':
            candidates.append(bin_p.parent.parent / 'VERSION')
    candidates.extend([
        root / 'RUNTIME' / 'build' / 'VERSION',
        root / 'RUNTIME' / 'VERSION',
        Path('/opt/easyaiot/RUNTIME/VERSION'),
        Path('/opt/easyaiot/RUNTIME/build/VERSION'),
    ])

    parsed = {}
    version_file = None
    for cand in candidates:
        parsed = _parse_version_file(cand)
        if parsed.get('version'):
            version_file = str(cand)
            break

    version = (
        parsed.get('version')
        or (os.getenv('RUNTIME_VERSION') or '').strip()
        or None
    )
    return {
        'ready': bool(bin_path),
        'binPath': bin_path,
        'version': version,
        'git': parsed.get('git') or (os.getenv('RUNTIME_GIT') or '').strip() or None,
        'builtAt': parsed.get('built_at') or (os.getenv('RUNTIME_BUILT_AT') or '').strip() or None,
        'arch': parsed.get('arch'),
        'buildMode': parsed.get('build_mode'),
        'ort': parsed.get('ort'),
        'source': parsed.get('source'),
        'versionFile': version_file,
    }


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


def _is_live_preview_rtmp(url: str) -> bool:
    """True if URL looks like SRS/ZLM preview live/ path (must not be used for AI overlay)."""
    u = (url or '').strip().lower()
    if not u:
        return False
    return '/live/' in u or u.rstrip('/').endswith('/live')


def _resolve_ai_rtmp_url(device: Device, task: AlgorithmTask) -> str:
    """
    Resolve dedicated AI detection RTMP URL (ai/ app), never preview live/.

    Priority: device.ai_rtmp_stream → task.rtmp_output_url → generate via media pool / local SRS.
    Persists generated ai_rtmp/ai_http onto the device when missing.
    """
    for raw in (
        (getattr(device, 'ai_rtmp_stream', None) or '').strip(),
        (getattr(task, 'rtmp_output_url', None) or '').strip(),
    ):
        if not raw:
            continue
        if _is_live_preview_rtmp(raw):
            logger.warning(
                '拒绝将预览 live/ 地址用作 AI 推流 device_id=%s url=%s',
                getattr(device, 'id', None),
                raw,
            )
            continue
        return raw

    try:
        from app.services.camera_service import _default_stream_urls

        _, _, ai_rtmp, ai_http = _default_stream_urls(device.id)
        ai_rtmp = (ai_rtmp or '').strip()
        ai_http = (ai_http or '').strip()
        if not ai_rtmp or _is_live_preview_rtmp(ai_rtmp):
            return ''
        # Backfill device so WEB can play ai_http_stream later
        dirty = False
        if not (getattr(device, 'ai_rtmp_stream', None) or '').strip():
            device.ai_rtmp_stream = ai_rtmp
            dirty = True
        if ai_http and not (getattr(device, 'ai_http_stream', None) or '').strip():
            device.ai_http_stream = ai_http
            dirty = True
        if dirty:
            try:
                from models import db

                db.session.add(device)
                db.session.commit()
                logger.info(
                    '已回写设备 AI 流地址 device_id=%s ai_rtmp=%s',
                    device.id,
                    ai_rtmp,
                )
            except Exception as e:
                logger.warning('回写 device.ai_rtmp_stream 失败 device_id=%s: %s', device.id, e)
                try:
                    from models import db

                    db.session.rollback()
                except Exception:
                    pass
        return ai_rtmp
    except Exception as e:
        logger.warning('生成 ai_rtmp 失败 device_id=%s: %s', getattr(device, 'id', None), e)
        return ''


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
    # realtime 默认必推独立 ai/ 检测流；禁止占用 live/ 预览地址
    rtmp_out = _resolve_ai_rtmp_url(primary, task)
    enable_rtmp = False
    if task_type == 'realtime':
        if rtmp_out:
            enable_rtmp = True
        else:
            raise ValueError(
                f'realtime 任务 {task.id} 无法解析 AI 推流地址（ai_rtmp）。'
                f'请为设备 {primary.id} 配置 ai_rtmp_stream，或确保 SRS/媒体节点可用以便自动生成 rtmp://…/ai/{primary.id}'
            )
    elif rtmp_out:
        # snap/patrol：有独立 ai 地址时也可推，但不强制
        enable_rtmp = True

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
    if task_type == 'realtime':
        logger.info(
            'RUNTIME realtime 默认推检测流 task_id=%s device_id=%s rtmp_url=%s enable_rtmp=%s',
            task.id,
            primary.id,
            rtmp_out,
            enable_rtmp,
        )
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
enable_rtmp={'true' if enable_rtmp else 'false'}
enable_draw=true
enable_alarm={'true' if task.alert_event_enabled else 'false'}

[regions]
{regions_block}
"""
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
    """Build LD_LIBRARY_PATH hint for conda + ORT SDK + CUDA (host or Docker mounts)."""
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
    # common local ORT layout (gpu preferred)
    root = _repo_root()
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
    # dedupe preserve order
    seen = set()
    out = []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return ':'.join(out)
