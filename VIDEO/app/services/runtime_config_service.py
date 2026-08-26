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
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from models import AlgorithmTask, Device, DeviceDetectionRegion
from app.utils.gb28181_source import (
    resolve_gb28181_alternate_pull_url,
    resolve_gb28181_source,
)
from app.utils.algorithm_task_identity import rewrite_task_stream_url
from app.utils.service_urls import resolve_video_service_base_url

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
        if lib:
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
    source = (device.source or '').strip()
    if source.lower().startswith('gb28181://'):
        return resolve_gb28181_source(source, logger=logger) or ''
    return source


def _device_has_active_cpp_realtime_algo(device_id: str) -> bool:
    """设备是否绑定启用的 cpp realtime 算法任务（forward 需改拉子码流）。"""
    if not device_id:
        return False
    try:
        tasks = (
            AlgorithmTask.query
            .filter(
                AlgorithmTask.is_enabled.is_(True),
                AlgorithmTask.task_type == 'realtime',
            )
            .all()
        )
    except Exception as e:
        logger.warning('query algo for forward substream failed device=%s: %s', device_id, e)
        return False
    for task in tasks:
        if normalize_executor(getattr(task, 'executor', None)) != 'cpp':
            continue
        for bound in (getattr(task, 'devices', None) or []):
            if getattr(bound, 'id', None) == device_id:
                return True
    return False


def _is_substream_rtsp_url(url: str) -> bool:
    u = (url or '').strip()
    if not u:
        return False
    m = re.search(r'/Streaming/Channels/(\d+)(?:\?|$)', u, re.I)
    if m:
        return int(m.group(1)) % 10 >= 2
    qs = parse_qs(urlparse(u).query, keep_blank_values=True)
    for key in ('subtype',):
        for val in qs.get(key) or []:
            try:
                if int(val) >= 1:
                    return True
            except (TypeError, ValueError):
                pass
    if re.search(r'/\d+/2(?:/|$|\?)', u):
        return True
    if re.search(r'/media/video2(?:/|$|\?)', u, re.I):
        return True
    if re.search(r'/stream2(?:/|$|&|\?)', u, re.I):
        return True
    return False


def _derive_substream_rtsp_url(main_url: str) -> Optional[str]:
    """从主码流 URL 推导子码流 URL；无法识别时返回 None。"""
    u = (main_url or '').strip()
    if not u or _is_substream_rtsp_url(u):
        return u or None

    m = re.search(r'(/Streaming/Channels/)(\d+)(\b)', u, re.I)
    if m:
        sid = int(m.group(2))
        if sid % 10 == 1:
            return u[:m.start(2)] + str(sid + 1) + u[m.end(2):]
        return u

    parsed = urlparse(u)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    if 'subtype' in qs:
        try:
            subtype = int((qs['subtype'] or ['0'])[0])
        except (TypeError, ValueError):
            return None
        if subtype == 0:
            qs['subtype'] = ['1']
            pairs = [(k, v) for k, vals in qs.items() for v in vals]
            return urlunparse(parsed._replace(query=urlencode(pairs)))
        return u

    m2 = re.search(r'^(rtsp://[^/]+/\d+)/1(\?.*)?$', u, re.I)
    if m2:
        return f'{m2.group(1)}/2' + (m2.group(2) or '')

    if re.search(r'/media/video1\b', u, re.I):
        return re.sub(r'/media/video1\b', '/media/video2', u, flags=re.I)

    if re.search(r'/stream1\b', u, re.I):
        return re.sub(r'/stream1\b', '/stream2', u, flags=re.I)

    return None


def resolve_algo_rtsp_url(device: Device) -> str:
    """
    算法 realtime（AI ai/）RTSP：与 VIDEO 一致使用主码流，保证叠框清晰、坐标准确。
    forward copy 与 AI 解码争用主码流时，NVR 通常可承受单路双连接。
    """
    url = _resolve_rtsp_url(device)
    source = (getattr(device, 'source', None) or '').strip()
    if (
        source.lower().startswith('gb28181://')
        and url.lower().startswith(('rtmp://', 'rtmps://'))
    ):
        rtsp_url = resolve_gb28181_alternate_pull_url(
            source,
            url,
            prefer_schemes=('rtsp', 'rtsps'),
            logger=logger,
        )
        if rtsp_url:
            return rtsp_url
    return url


def _resolve_available_device_urls(
    devices: List[Device],
) -> Tuple[List[Device], Dict[str, str]]:
    available: List[Device] = []
    resolved: Dict[str, str] = {}
    for device in devices:
        url = resolve_algo_rtsp_url(device)
        if not url:
            logger.warning(
                '跳过无可用视频流的设备 device_id=%s name=%s',
                getattr(device, 'id', None),
                getattr(device, 'name', None),
            )
            continue
        available.append(device)
        resolved[str(device.id)] = url
    return available, resolved


def resolve_forward_rtsp_url(device: Device) -> str:
    """
    推流转发（原画 live/）RTSP：始终主码流，保证预览 OSD 最低延迟。
    有 AI 任务时由算法走子码流，避免双拉主码流。
    """
    return _resolve_rtsp_url(device)


def _default_builtin_model_name(model_id: int) -> Optional[str]:
    """Align with VIDEO realtime defaults: -1 yolo11n, -2 yolov8n, -3 yolo26n."""
    return {
        -1: 'yolo11n',
        -2: 'yolov8n',
        -3: 'yolo26n',
    }.get(int(model_id))


def _ensure_onnx_script() -> Path:
    return _repo_root() / 'RUNTIME' / 'scripts' / 'ensure_onnx_model.py'


def _python_for_export() -> str:
    """Prefer a Python that has ultralytics (VIDEO/base conda), not bare system python."""
    for key in ('RUNTIME_PYTHON', 'EASYAIOT_PYTHON', 'VIDEO_PYTHON'):
        cand = (os.getenv(key) or '').strip()
        if cand and Path(cand).is_file():
            return cand
    for cand in (
        '/home/ubuntu/miniconda3/bin/python',
        str(Path.home() / 'miniconda3' / 'bin' / 'python'),
        str(Path.home() / 'anaconda3' / 'bin' / 'python'),
        '/opt/conda/bin/python',
        sys.executable or '',
        'python3',
    ):
        if not cand:
            continue
        p = Path(cand) if cand.startswith('/') else None
        if p is not None and not p.is_file():
            continue
        return cand
    return 'python3'


def _export_pt_to_onnx(pt_path: Path, onnx_path: Path, *, force: bool = False) -> Optional[Path]:
    """Export Ultralytics .pt → .onnx via RUNTIME/scripts/ensure_onnx_model.py."""
    script = _ensure_onnx_script()
    if not script.is_file():
        logger.warning('ensure_onnx_model.py missing: %s', script)
        return onnx_path if onnx_path.is_file() else None
    if onnx_path.is_file() and not force:
        try:
            if (not pt_path.is_file()) or onnx_path.stat().st_mtime >= pt_path.stat().st_mtime:
                return onnx_path
        except OSError:
            pass
    py = _python_for_export()
    cmd = [
        py,
        str(script),
        '--input', str(pt_path if pt_path.is_file() else pt_path.name),
        '--output', str(onnx_path),
    ]
    if force:
        cmd.append('--force')
    logger.info('RUNTIME model export: %s', ' '.join(cmd))
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=int(os.getenv('RUNTIME_ONNX_EXPORT_TIMEOUT', '600') or '600'),
            check=False,
        )
        if completed.stdout:
            logger.info('ensure_onnx stdout: %s', completed.stdout.strip()[-2000:])
        if completed.returncode != 0:
            logger.error(
                'ensure_onnx failed rc=%s stderr=%s',
                completed.returncode,
                (completed.stderr or '')[-2000:],
            )
            return onnx_path if onnx_path.is_file() else None
    except Exception as e:
        logger.error('ensure_onnx exception: %s', e)
        return onnx_path if onnx_path.is_file() else None
    return onnx_path if onnx_path.is_file() else None


def _pick_names(onnx_path: Path, fallback: Path) -> str:
    sibling = onnx_path.with_suffix('.names')
    if sibling.is_file():
        return str(sibling)
    if fallback.is_file():
        return str(fallback)
    remote = Path('/opt/easyaiot/RUNTIME/models/coco.names')
    if remote.is_file():
        return str(remote)
    return str(fallback)


def _resolve_builtin_onnx(stem: str) -> Tuple[str, str]:
    """Resolve built-in yolo11n / yolov8n / yolo26n to onnx (+ names)."""
    root = _repo_root()
    video_root = Path(__file__).resolve().parents[2]
    default_names = root / 'RUNTIME' / 'models' / 'coco.names'
    search_dirs = [
        root / 'RUNTIME' / 'models',
        Path('/opt/easyaiot/RUNTIME/models'),
        video_root,
        video_root / 'data' / 'models' / 'builtin',
    ]
    # Prefer existing onnx
    for d in search_dirs:
        cand = d / f'{stem}.onnx'
        if cand.is_file():
            return str(cand), _pick_names(cand, default_names)
    # Export from .pt if present (or let ultralytics download by name)
    onnx_out = root / 'RUNTIME' / 'models' / f'{stem}.onnx'
    onnx_out.parent.mkdir(parents=True, exist_ok=True)
    pt_candidates = []
    for d in search_dirs:
        pt_candidates.append(d / f'{stem}.pt')
    pt_candidates.append(Path(f'{stem}.pt'))  # bare name → ultralytics download
    pt_src = next((p for p in pt_candidates if p.is_file()), Path(f'{stem}.pt'))
    exported = _export_pt_to_onnx(pt_src, onnx_out)
    if exported and exported.is_file():
        return str(exported), _pick_names(exported, default_names)
    # Last resort: historical default
    legacy = root / 'RUNTIME' / 'models' / 'yolov11n.onnx'
    if legacy.is_file():
        logger.warning('builtin %s onnx missing, fallback %s', stem, legacy)
        return str(legacy), _pick_names(legacy, default_names)
    raise ValueError(f'无法解析内置模型 {stem} 的 ONNX（请安装 ultralytics 并允许导出）')


def _resolve_custom_model_dir(model_id: int, prefer_cluster: bool) -> Optional[Path]:
    root = _repo_root()
    video_root = Path(__file__).resolve().parents[2]
    candidates: List[Path] = []
    if prefer_cluster:
        try:
            lib = str((root / '.scripts' / 'lib').resolve())
            if lib not in sys.path:
                sys.path.insert(0, lib)
            from model_resolver import get_model_cluster_dir  # type: ignore
            candidates.append(Path(get_model_cluster_dir(model_id)))
        except Exception as e:
            logger.debug('cluster model dir unavailable: %s', e)
    candidates.append(video_root / 'data' / 'models' / str(model_id))
    candidates.append(Path('/opt/easyaiot/VIDEO/data/models') / str(model_id))
    for d in candidates:
        if d.is_dir():
            return d
    return candidates[0] if candidates else None


def _resolve_dir_to_onnx(model_dir: Path, default_names: Path) -> Optional[Tuple[str, str]]:
    if not model_dir.is_dir():
        # Still allow canonical remote path for Agent nodes
        canonical = model_dir / 'model.onnx'
        return str(canonical), _pick_names(canonical, default_names)

    onnx_matches = sorted(model_dir.glob('*.onnx')) + sorted(model_dir.glob('*.ONNX'))
    # Prefer model.onnx
    preferred = [p for p in onnx_matches if p.name.lower() == 'model.onnx']
    if preferred:
        return str(preferred[0]), _pick_names(preferred[0], default_names)
    if onnx_matches:
        return str(onnx_matches[0]), _pick_names(onnx_matches[0], default_names)

    pt_matches = sorted(model_dir.glob('*.pt')) + sorted(model_dir.glob('*.PT'))
    preferred_pt = [p for p in pt_matches if p.name.lower() in ('model.pt', 'best.pt', 'weights.pt')]
    pt = preferred_pt[0] if preferred_pt else (pt_matches[0] if pt_matches else None)
    if pt is None:
        return None
    onnx_out = model_dir / 'model.onnx'
    exported = _export_pt_to_onnx(pt, onnx_out)
    if exported and exported.is_file():
        return str(exported), _pick_names(exported, default_names)
    return None


def _resolve_single_model_path(
    mid_int: int, *, prefer_cluster: bool, default_names: Path
) -> Optional[Tuple[str, str]]:
    """Resolve one model id → (onnx_path, names_path); None if unresolvable."""
    root = _repo_root()
    builtin = _default_builtin_model_name(mid_int)
    if builtin:
        if prefer_cluster:
            remote_models = Path('/opt/easyaiot/RUNTIME/models')
            return str(remote_models / f'{builtin}.onnx'), str(remote_models / 'coco.names')
        try:
            return _resolve_builtin_onnx(builtin)
        except Exception as e:
            logger.warning('builtin model %s resolve failed: %s', builtin, e)
            return None

    if mid_int <= 0:
        return None

    # cluster resolver may return a file path directly
    if prefer_cluster:
        try:
            lib = str((root / '.scripts' / 'lib').resolve())
            if lib not in sys.path:
                sys.path.insert(0, lib)
            from model_resolver import try_resolve_cluster_model_path  # type: ignore
            found = try_resolve_cluster_model_path(mid_int)
            if found:
                found_p = Path(found)
                if found_p.suffix.lower() == '.onnx' and found_p.is_file():
                    return str(found_p), _pick_names(found_p, default_names)
                if found_p.suffix.lower() == '.pt' and found_p.is_file():
                    onnx_out = found_p.with_suffix('.onnx')
                    exported = _export_pt_to_onnx(found_p, onnx_out)
                    if exported and exported.is_file():
                        return str(exported), _pick_names(exported, default_names)
        except Exception as e:
            logger.debug('cluster file resolve skip: %s', e)

    model_dir = _resolve_custom_model_dir(mid_int, prefer_cluster=prefer_cluster)
    if model_dir is not None:
        resolved = _resolve_dir_to_onnx(model_dir, default_names)
        if resolved:
            return resolved
    return None


def _resolve_model_paths(task: AlgorithmTask, prefer_cluster: bool = False) -> List[Tuple[str, str]]:
    """Resolve task.model_ids → [(onnx_path, names_path), ...] in model order for RUNTIME.

    Supports:
      - builtin ids: -1 yolo11n, -2 yolov8n, -3 yolo26n (.pt auto-exported to onnx)
      - custom positive ids: cluster/local dir, prefer .onnx else export .pt
    Returns at least one model; unresolvable ids are skipped (首个模型即 [ai] 主模型，
    其余按 model_path_<i> / classes_path_<i> 写入，RUNTIME 内多模型聚合推理）。
    """
    root = _repo_root()
    default_names = root / 'RUNTIME' / 'models' / 'coco.names'
    remote_default_names = Path('/opt/easyaiot/RUNTIME/models/coco.names')
    env_model = (os.getenv('RUNTIME_MODEL_PATH') or '').strip()
    env_names = (os.getenv('RUNTIME_CLASSES_PATH') or '').strip()

    model_ids: list = []
    raw = task.model_ids
    if raw:
        try:
            model_ids = json.loads(raw) if isinstance(raw, str) else list(raw)
        except Exception:
            model_ids = []

    resolved: List[Tuple[str, str]] = []
    for mid in model_ids:
        try:
            mid_int = int(mid)
        except Exception:
            continue
        pair = _resolve_single_model_path(mid_int, prefer_cluster=prefer_cluster, default_names=default_names)
        if pair:
            resolved.append(pair)

    if resolved:
        return resolved

    if prefer_cluster:
        remote_default_onnx = Path('/opt/easyaiot/RUNTIME/models/yolo11n.onnx')
        if not remote_default_onnx.is_file():
            remote_default_onnx = Path('/opt/easyaiot/RUNTIME/models/yolov11n.onnx')
        if remote_default_onnx.is_file():
            names = str(remote_default_names if remote_default_names.is_file() else (env_names or remote_default_names))
            return [(str(remote_default_onnx), names)]

    if env_model:
        p = Path(env_model)
        if p.suffix.lower() == '.pt':
            exported = _export_pt_to_onnx(p, p.with_suffix('.onnx'))
            if exported and exported.is_file():
                return [(str(exported), (env_names or _pick_names(exported, default_names)))]
        return [(env_model, (env_names or str(default_names)))]

    # Final fallback: ensure yolo11n onnx exists
    try:
        return [_resolve_builtin_onnx('yolo11n')]
    except Exception:
        pass
    default_onnx = root / 'RUNTIME' / 'models' / 'yolo11n.onnx'
    if not default_onnx.is_file():
        legacy = root / 'RUNTIME' / 'models' / 'yolov11n.onnx'
        if legacy.is_file():
            default_onnx = legacy
    return [(str(default_onnx), env_names or str(default_names))]


def _control_port(task: AlgorithmTask) -> int:
    custom = getattr(task, 'runtime_control_port', None)
    if custom and 8000 <= int(custom) <= 9000:
        return int(custom)
    return 8000 + (int(task.id) % 1000)


def _realtime_device_control_port(task_id: int, device_index: int) -> int:
    """realtime 多路：每设备独立控制端口（8000–9000）。"""
    # 与 stream_forward 错开：8200 段起，每任务最多 10 路（device_index % 10）
    port = 8200 + (int(task_id) % 70) * 10 + (int(device_index) % 10)
    return max(8000, min(9000, port))


def runtime_config_dir() -> Path:
    env_dir = (os.getenv('RUNTIME_CONFIG_DIR') or '').strip()
    if env_dir:
        path = Path(env_dir)
    else:
        path = _repo_root() / 'RUNTIME' / 'config'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _regions_ini_block(devices: List[Device], task_id: int) -> str:
    lines: List[str] = []
    for device in devices:
        try:
            regions = DeviceDetectionRegion.query.filter_by(
                device_id=device.id, task_id=task_id, is_enabled=True
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


def _devices_json(
    devices: List[Device],
    resolved_urls: Optional[Dict[str, str]] = None,
) -> str:
    items = []
    for d in devices:
        url = (resolved_urls or {}).get(str(d.id)) or resolve_algo_rtsp_url(d)
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
        return rewrite_task_stream_url(raw, task.id, device.id) or ''

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
        return rewrite_task_stream_url(ai_rtmp, task.id, device.id) or ''
    except Exception as e:
        logger.warning('生成 ai_rtmp 失败 device_id=%s: %s', getattr(device, 'id', None), e)
        return ''


def _build_runtime_ini_text(
    task: AlgorithmTask,
    *,
    task_type: str,
    device: Device,
    devices_for_json: List[Device],
    rtsp_url: str,
    rtmp_out: str,
    enable_rtmp: bool,
    models: List[Tuple[str, str]],
    log_path: str,
    alert_image_dir: str,
    control_port: int,
    frame_skip: int,
    conf: float,
    cooldown: int,
    algo_name: str,
    prefer_gpu: bool,
    force_cpu: bool,
    gpu_device_id: int,
    cron: str,
    patrol_mode: str,
    patrol_interval: int,
    patrol_pool: int,
    hook_tt: str,
    mqtt_broker_urls: str,
    mqtt_username: str,
    mqtt_password: str,
    mqtt_client_id: str,
    mqtt_tenant: str,
    algo_bus_transport: str,
    alert_hook_url: str,
    compute_node_id: str,
    resolved_urls: Dict[str, str],
    heartbeat_url: str,
) -> str:
    devices_json_one_line = _devices_json(devices_for_json, resolved_urls).replace('\n', '')
    regions_block = _regions_ini_block(devices_for_json, task.id)
    device_name = (device.name or device.id or '').replace('\n', ' ')
    from app.utils.alert_class_filter import parse_alert_class_names
    alert_class_names = parse_alert_class_names(getattr(task, 'alert_class_names', None))
    alert_class_names_ini = json.dumps(alert_class_names, ensure_ascii=False, separators=(',', ':'))
    # RUNTIME 人脸链路桥：仅 realtime 且启用人脸匹配且配置了人脸库时开启，
    # C++ 在 MQTT/InferEvent 告警路径下会额外向 alert_hook_url 投递 face_feed_only 告警
    face_matching_ini = 'true' if (
        task_type == 'realtime'
        and bool(getattr(task, 'face_matching_enabled', False))
        and AlgorithmTask._parse_library_ids(getattr(task, 'face_library_ids', None))
    ) else 'false'
    # RUNTIME 车牌链路桥：仅 realtime 且启用车牌匹配且配置了车牌库时开启，
    # C++ 在 MQTT/InferEvent 告警路径下会额外向 alert_hook_url 投递 plate_feed_only 告警
    plate_matching_ini = 'true' if (
        task_type == 'realtime'
        and bool(getattr(task, 'plate_matching_enabled', False))
        and AlgorithmTask._parse_library_ids(getattr(task, 'plate_library_ids', None))
    ) else 'false'
    # 多模型：首模型写 model_path/classes_path，其余写 model_path_<i>/classes_path_<i>
    ai_model_lines: List[str] = []
    for i, (onnx_path, names_path) in enumerate(models):
        prefix = 'model_path' if i == 0 else f'model_path_{i}'
        class_prefix = 'classes_path' if i == 0 else f'classes_path_{i}'
        ai_model_lines.append(f'{prefix}={onnx_path}')
        ai_model_lines.append(f'{class_prefix}={names_path}')
    ai_model_block = '\n'.join(ai_model_lines)
    return f"""# Auto-generated by VIDEO for executor=cpp — do not edit by hand while task is running
[video]
rtsp_url={rtsp_url}
rtmp_url={rtmp_out}
width=1920
height=1080
fps=25

[ai]
enable=true
{ai_model_block}
threads=2
frame_skip={frame_skip}
prefer_gpu={'true' if prefer_gpu else 'false'}
force_cpu={'true' if force_cpu else 'false'}
gpu_device_id={gpu_device_id}
prefer_hwaccel={'true' if (prefer_gpu and not force_cpu) else 'false'}
force_soft_av={'true' if (force_cpu or not prefer_gpu) else 'false'}
hwaccel_device_id={gpu_device_id}
nvenc_preset={(os.getenv('RUNTIME_NVENC_PRESET') or os.getenv('REALTIME_NVENC_PRESET') or 'p3').strip() or 'p3'}

[alarm]
enable={'true' if task.alert_event_enabled else 'false'}
confidence_threshold={conf}
cooldown_time={cooldown}
image_dir={alert_image_dir}
alert_hook_url={alert_hook_url}
alert_class_names={alert_class_names_ini}

[task]
id={task.id}
control_port={control_port}

[video_task]
device_id={device.id}
device_name={device_name}
task_type={hook_tt}
algorithm_name={algo_name}
heartbeat_url={heartbeat_url}
heartbeat_interval_sec={'15' if task_type == 'patrol' else '10'}
log_path={log_path}
alert_image_dir={alert_image_dir}
face_matching_enabled={face_matching_ini}
plate_matching_enabled={plate_matching_ini}
algo_bus_transport={algo_bus_transport}
alert_hook_url={alert_hook_url}
mqtt_broker_urls={mqtt_broker_urls}
mqtt_username={mqtt_username}
mqtt_password={mqtt_password}
mqtt_client_id={mqtt_client_id}
mqtt_tenant={mqtt_tenant}
compute_node_id={compute_node_id}
headless=true
frame_skip={frame_skip}
cron_expression={cron}
patrol_mode={patrol_mode}
patrol_interval_sec={patrol_interval}
patrol_pool_size={patrol_pool}
devices_json={devices_json_one_line}

[mqtt]
broker_urls={mqtt_broker_urls}
username={mqtt_username}
password={mqtt_password}
client_id={mqtt_client_id}
tenant={mqtt_tenant}
transport={algo_bus_transport}

[features]
enable_rtmp={'true' if enable_rtmp else 'false'}
enable_draw=true
enable_alarm={'true' if task.alert_event_enabled else 'false'}

[regions]
{regions_block}
"""


def generate_runtime_inis(
    task: AlgorithmTask,
    log_path: str,
    *,
    prefer_cluster_model: bool = False,
    write_local: bool = True,
    only_device_ids: Optional[List[str]] = None,
    force_per_device: bool = False,
    remote_ini_dir: Optional[str] = None,
    heartbeat_url: Optional[str] = None,
    compute_node_id: Optional[str] = None,
    mqtt_broker_urls: Optional[str] = None,
) -> List[str]:
    """生成 RUNTIME ini 路径列表。

    - realtime：每路摄像头一份 ini / 一个进程（推各自 ai/{{device_id}}）
    - snap / patrol：仍为一份 ini（进程内多路调度）
    - only_device_ids：仅生成指定设备（集群分片）
    - force_per_device：分片场景下即使单路也使用 task_{id}_{deviceId}.ini
    - remote_ini_dir：远程节点上的 ini 目录（write_local=False 时用于路径）
    - compute_node_id：远程部署时传入目标节点 id（默认取本机环境变量）
    - mqtt_broker_urls：远程部署时传入控制面可达的告警总线地址（默认取本机环境变量）
    """
    task_type = (getattr(task, 'task_type', None) or 'realtime').strip().lower()
    if task_type == 'snapshot':
        task_type = 'snap'
    if task_type not in ('realtime', 'snap', 'patrol'):
        raise ValueError(f'executor=cpp 不支持任务类型: {task_type}')

    all_devices = _task_devices(task)
    if not all_devices:
        raise ValueError(f'任务 {task.id} 未绑定设备，无法生成 RUNTIME 配置')

    device_index_map = {str(d.id): i for i, d in enumerate(all_devices)}
    if only_device_ids:
        by_id = {str(d.id): d for d in all_devices}
        devices: List[Device] = []
        for raw_id in only_device_ids:
            did = str(raw_id)
            if did not in by_id:
                raise ValueError(f'任务 {task.id} 未绑定设备 {did}，无法生成分片配置')
            devices.append(by_id[did])
    else:
        devices = list(all_devices)

    devices, resolved_urls = _resolve_available_device_urls(devices)
    if not devices:
        raise ValueError(f'任务 {task.id} 的设备均无可用 RTSP/source 地址')

    models = _resolve_model_paths(task, prefer_cluster=prefer_cluster_model)
    for onnx_path, _names_path in models:
        if write_local and not os.path.isfile(onnx_path):
            raise ValueError(f'模型文件不存在: {onnx_path}（cpp 需要 .onnx；.pt 应已自动导出）')
        if write_local and not str(onnx_path).lower().endswith('.onnx'):
            raise ValueError(f'RUNTIME 最终需要 .onnx，当前为: {onnx_path}')
        if prefer_cluster_model and not str(onnx_path).lower().endswith('.onnx'):
            raise ValueError(
                f'远程 cpp 需要 ONNX 模型，当前解析到: {onnx_path}。'
                f'请确保模型已同步至集群，或允许控制面执行 .pt→onnx 导出'
            )

    conf = float(task.detect_conf if task.detect_conf is not None else 0.5)
    cooldown = int(task.alert_event_suppress_time or 30)
    algo_name = (task.model_names or 'detection').split(',')[0].strip() or 'detection'

    frame_skip = int(getattr(task, 'extract_interval', None) or getattr(task, 'frame_skip', None) or 8)
    if frame_skip <= 0:
        frame_skip = 8

    cron = (getattr(task, 'cron_expression', None) or '').strip()
    patrol_mode = (getattr(task, 'patrol_mode', None) or 'pool').strip() or 'pool'
    patrol_interval = max(3, int(getattr(task, 'patrol_interval_sec', None) or 10))
    patrol_pool = max(1, min(int(getattr(task, 'patrol_pool_size', None) or 4), 16))

    log_dir = log_path if log_path else str(runtime_config_dir())
    alert_image_dir = (os.getenv('ALERT_IMAGES_DIR') or '').strip() or os.path.join(log_dir, 'alerts')
    if write_local:
        os.makedirs(alert_image_dir, exist_ok=True)

    # 远程部署时控制面显式传入可达地址（如 192.168.1.10:1883）；
    # 未传时回退控制面环境变量，最后兜底回环（仅适用于本机 RUNTIME）
    mqtt_broker_urls = (
        (mqtt_broker_urls or '').strip()
        or (os.getenv('MQTT_BROKER_URLS') or '').strip()
        or '127.0.0.1:1883'
    )
    mqtt_username = (os.getenv('MQTT_ALGO_USERNAME') or '').strip()
    mqtt_password = (os.getenv('MQTT_ALGO_PASSWORD') or '').strip()
    mqtt_tenant = (os.getenv('MQTT_ALGO_TENANT') or 'default').strip()
    algo_bus_transport = (os.getenv('ALGO_BUS_TRANSPORT') or 'mqtt').strip() or 'mqtt'
    alert_hook_url = ''
    # RUNTIME 人脸/车牌链路桥：realtime + 启用人脸/车牌匹配 + 配置对应库 → C++ 需向 VIDEO hook
    # 补投 face_feed_only / plate_feed_only 告警（MQTT/InferEvent 路径下 hook 不参与主告警流），
    # 始终填 hook 地址
    face_matching_enabled = bool(
        task_type == 'realtime'
        and getattr(task, 'face_matching_enabled', False)
        and AlgorithmTask._parse_library_ids(getattr(task, 'face_library_ids', None))
    )
    plate_matching_enabled = bool(
        task_type == 'realtime'
        and getattr(task, 'plate_matching_enabled', False)
        and AlgorithmTask._parse_library_ids(getattr(task, 'plate_library_ids', None))
    )
    matching_enabled = face_matching_enabled or plate_matching_enabled
    # edge：无 EMQX/iot-sink，强制 HTTP → VIDEO /video/alert/hook 直连落库
    try:
        from app.utils.service_urls import is_edge_deploy_profile, resolve_alert_hook_url
        if is_edge_deploy_profile() and algo_bus_transport.lower() in (
            'off', '0', 'false', 'no', 'mqtt', '',
        ):
            algo_bus_transport = 'http'
        if algo_bus_transport.lower() in ('http', 'off'):
            alert_hook_url = resolve_alert_hook_url()
        elif matching_enabled:
            alert_hook_url = resolve_alert_hook_url()
    except Exception:
        if algo_bus_transport.lower() in ('http', 'off'):
            alert_hook_url = f'{resolve_video_service_base_url().rstrip("/")}/video/alert/hook'
        elif matching_enabled:
            alert_hook_url = f'{resolve_video_service_base_url().rstrip("/")}/video/alert/hook'
    compute_node_id = (
        (compute_node_id or '').strip()
        or (os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or '').strip()
    )

    hook_tt = _hook_task_type(task_type)
    resolved_heartbeat_url = (heartbeat_url or '').strip() or _heartbeat_url(
        task_type,
        resolve_video_service_base_url().rstrip('/'),
    )

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

    # realtime：一路一进程；snap/patrol：单进程多设备（分片时仅包含 only_device_ids）
    targets: List[Tuple[Device, int, List[Device]]]
    if task_type == 'realtime':
        targets = [
            (d, device_index_map.get(str(d.id), i), [d])
            for i, d in enumerate(devices)
        ]
    else:
        primary_index = device_index_map.get(str(devices[0].id), 0)
        targets = [(devices[0], primary_index, devices)]

    per_device = force_per_device or (task_type == 'realtime' and (
        len(all_devices) > 1 or bool(only_device_ids)
    ))
    # snap/patrol 分片：单 ini，但需独立端口/文件名，避免同节点多 workload 冲突
    shard_mode = bool(only_device_ids) and task_type in ('snap', 'patrol')
    ini_base = Path(remote_ini_dir) if remote_ini_dir else runtime_config_dir()

    paths: List[str] = []
    contents: List[str] = []
    for device, device_index, devices_for_json in targets:
        rtsp_url = resolved_urls[str(device.id)]
        rtmp_out = _resolve_ai_rtmp_url(device, task)
        enable_rtmp = False
        if task_type == 'realtime':
            if rtmp_out:
                enable_rtmp = True
            else:
                raise ValueError(
                    f'realtime 任务 {task.id} 无法解析 AI 推流地址（ai_rtmp）。'
                    f'请为设备 {device.id} 配置 ai_rtmp_stream，或确保 SRS/媒体节点可用以便自动生成 rtmp://…/ai/{device.id}'
                )
        elif rtmp_out:
            enable_rtmp = True

        if task_type == 'realtime' and per_device:
            control_port = _realtime_device_control_port(int(task.id), device_index)
            ini_path = ini_base / f'task_{task.id}_{device.id}.ini'
            device_log = os.path.join(log_dir, f'runtime_{device.id}')
            if write_local:
                os.makedirs(device_log, exist_ok=True)
            mqtt_client_id = (
                os.getenv('MQTT_ALGO_CLIENT_ID') or f'algo-runtime-{task.id}-{device.id}'
            ).strip()
        elif shard_mode:
            shard_key = '_'.join(str(d.id) for d in devices_for_json[:3])
            if len(devices_for_json) > 3:
                shard_key = f'{shard_key}_n{len(devices_for_json)}'
            control_port = _realtime_device_control_port(int(task.id), device_index)
            ini_path = ini_base / f'task_{task.id}_shard_{shard_key}.ini'
            device_log = os.path.join(log_dir, f'runtime_shard_{shard_key}')
            if write_local:
                os.makedirs(device_log, exist_ok=True)
            mqtt_client_id = (
                os.getenv('MQTT_ALGO_CLIENT_ID') or f'algo-runtime-{task.id}-shard-{shard_key}'
            ).strip()
        else:
            control_port = _control_port(task)
            ini_path = ini_base / f'task_{task.id}.ini'
            device_log = log_path
            mqtt_client_id = (os.getenv('MQTT_ALGO_CLIENT_ID') or f'algo-runtime-{task.id}').strip()

        if task_type == 'realtime':
            logger.info(
                'RUNTIME realtime 推检测流 task_id=%s device_id=%s rtmp_url=%s enable_rtmp=%s port=%s',
                task.id,
                device.id,
                rtmp_out,
                enable_rtmp,
                control_port,
            )

        content = _build_runtime_ini_text(
            task,
            task_type=task_type,
            device=device,
            devices_for_json=devices_for_json,
            rtsp_url=rtsp_url,
            rtmp_out=rtmp_out or '',
            enable_rtmp=enable_rtmp,
            models=models,
            log_path=device_log,
            alert_image_dir=alert_image_dir,
            control_port=control_port,
            frame_skip=frame_skip,
            conf=conf,
            cooldown=cooldown,
            algo_name=algo_name,
            prefer_gpu=prefer_gpu,
            force_cpu=force_cpu,
            gpu_device_id=gpu_device_id,
            cron=cron,
            patrol_mode=patrol_mode,
            patrol_interval=patrol_interval,
            patrol_pool=patrol_pool,
            hook_tt=hook_tt,
            mqtt_broker_urls=mqtt_broker_urls,
            mqtt_username=mqtt_username,
            mqtt_password=mqtt_password,
            mqtt_client_id=mqtt_client_id,
            mqtt_tenant=mqtt_tenant,
            algo_bus_transport=algo_bus_transport,
            alert_hook_url=alert_hook_url,
            compute_node_id=compute_node_id,
            resolved_urls=resolved_urls,
            heartbeat_url=resolved_heartbeat_url,
        )
        contents.append(content)
        if write_local:
            ini_path.parent.mkdir(parents=True, exist_ok=True)
            ini_path.write_text(content, encoding='utf-8')
            logger.info(
                '已生成 RUNTIME 配置: %s (task_id=%s, type=%s, device=%s)',
                ini_path, task.id, task_type, device.id,
            )
        paths.append(str(ini_path))

    generate_runtime_inis.last_contents = contents  # type: ignore[attr-defined]
    generate_runtime_ini.last_ini_paths = paths  # type: ignore[attr-defined]
    if contents:
        generate_runtime_ini.last_content = contents[0]  # type: ignore[attr-defined]
    return paths


def generate_runtime_ini(
    task: AlgorithmTask,
    log_path: str,
    *,
    prefer_cluster_model: bool = False,
    write_local: bool = True,
    remote_ini_path: Optional[str] = None,
    heartbeat_url: Optional[str] = None,
    compute_node_id: Optional[str] = None,
    mqtt_broker_urls: Optional[str] = None,
) -> str:
    """Generate RUNTIME ini；realtime 多路时写多份并返回第一路路径（完整列表见 generate_runtime_inis）。"""
    if remote_ini_path and write_local is False:
        # 远程单文件兼容：仍按旧逻辑生成「主设备」一份内容
        paths = generate_runtime_inis(
            task,
            log_path,
            prefer_cluster_model=prefer_cluster_model,
            write_local=False,
            heartbeat_url=heartbeat_url,
            compute_node_id=compute_node_id,
            mqtt_broker_urls=mqtt_broker_urls,
        )
        # 覆盖远程路径名（调用方指定）
        generate_runtime_ini.last_content = (  # type: ignore[attr-defined]
            getattr(generate_runtime_inis, 'last_contents', ['']) or ['']
        )[0]
        return remote_ini_path
    paths = generate_runtime_inis(
        task,
        log_path,
        prefer_cluster_model=prefer_cluster_model,
        write_local=write_local,
        heartbeat_url=heartbeat_url,
        compute_node_id=compute_node_id,
        mqtt_broker_urls=mqtt_broker_urls,
    )
    return paths[0]


def generate_runtime_ini_content(
    task: AlgorithmTask,
    log_path: str,
    *,
    prefer_cluster_model: bool = True,
    remote_ini_path: Optional[str] = None,
    only_device_ids: Optional[List[str]] = None,
    force_per_device: bool = False,
    heartbeat_url: Optional[str] = None,
    compute_node_id: Optional[str] = None,
    mqtt_broker_urls: Optional[str] = None,
) -> Tuple[str, str]:
    """Return (remote_ini_path, ini_content) without requiring local model file.

    远程多路时返回第一路内容；完整列表见 generate_runtime_inis.last_contents。
    """
    remote_dir = None
    if remote_ini_path:
        remote_dir = os.path.dirname(remote_ini_path) or None
    paths = generate_runtime_inis(
        task,
        log_path,
        prefer_cluster_model=prefer_cluster_model,
        write_local=False,
        only_device_ids=only_device_ids,
        force_per_device=force_per_device,
        remote_ini_dir=remote_dir,
        heartbeat_url=heartbeat_url,
        compute_node_id=compute_node_id,
        mqtt_broker_urls=mqtt_broker_urls,
    )
    contents = getattr(generate_runtime_inis, 'last_contents', None) or []
    if not contents:
        raise ValueError('生成 RUNTIME ini 内容失败')
    path = remote_ini_path or paths[0]
    generate_runtime_ini.last_content = contents[0]  # type: ignore[attr-defined]
    return path, contents[0]


def generate_runtime_inis_content(
    task: AlgorithmTask,
    log_path: str,
    *,
    prefer_cluster_model: bool = True,
    only_device_ids: Optional[List[str]] = None,
    force_per_device: bool = False,
    remote_ini_dir: Optional[str] = None,
    heartbeat_url: Optional[str] = None,
    compute_node_id: Optional[str] = None,
    mqtt_broker_urls: Optional[str] = None,
) -> List[Tuple[str, str]]:
    """返回 [(ini_path, content), ...]，供远程分片多路部署。"""
    paths = generate_runtime_inis(
        task,
        log_path,
        prefer_cluster_model=prefer_cluster_model,
        write_local=False,
        only_device_ids=only_device_ids,
        force_per_device=force_per_device,
        remote_ini_dir=remote_ini_dir,
        heartbeat_url=heartbeat_url,
        compute_node_id=compute_node_id,
        mqtt_broker_urls=mqtt_broker_urls,
    )
    contents = getattr(generate_runtime_inis, 'last_contents', None) or []
    if len(contents) != len(paths):
        raise ValueError('生成 RUNTIME ini 内容数量与路径不一致')
    return list(zip(paths, contents))


def _stream_forward_control_port(task_id: int, device_index: int) -> int:
    port = 8000 + (int(task_id) % 100) * 10 + (int(device_index) % 10)
    return max(8000, min(9000, port))


def _stream_forward_runtime_ini_content(
    task,
    device: Device,
    rtsp_url: str,
    rtmp_url: str,
    log_path: str,
    *,
    device_index: int = 0,
) -> str:
    heartbeat_env = (os.getenv('VIDEO_HEARTBEAT_URL') or '').strip()
    if heartbeat_env:
        heartbeat = heartbeat_env
    else:
        video_base = resolve_video_service_base_url().rstrip('/')
        heartbeat = f'{video_base}/video/stream-forward/heartbeat'
    control_port = _stream_forward_control_port(int(task.id), device_index)
    log_dir = os.path.dirname(log_path) if log_path else str(runtime_config_dir())
    device_log = os.path.join(log_dir, f'forward_{device.id}')
    device_name = (device.name or device.id or '').replace('\n', ' ')
    return f"""# Auto-generated by VIDEO stream-forward executor=cpp
[video]
rtsp_url={rtsp_url}
rtmp_url={rtmp_url}

[task]
id={task.id}_{device.id}
control_port={control_port}

[video_task]
device_id={device.id}
device_name={device_name}
task_type=forward
heartbeat_url={heartbeat}
heartbeat_interval_sec=10
log_path={device_log}
headless=true

[features]
enable_rtmp=true
enable_draw=false
enable_alarm=false

[ai]
enable=false
"""


def generate_stream_forward_runtime_ini(
    task,
    device: Device,
    rtsp_url: str,
    rtmp_url: str,
    log_path: str,
    *,
    device_index: int = 0,
    write_local: bool = True,
    remote_ini_path: Optional[str] = None,
) -> str:
    """Generate RUNTIME forward-only ini for stream forward task (executor=cpp)."""
    if not (rtsp_url or '').strip():
        rtsp_url = resolve_forward_rtsp_url(device)
    content = _stream_forward_runtime_ini_content(
        task, device, rtsp_url, rtmp_url, log_path, device_index=device_index,
    )
    if remote_ini_path:
        ini_path = Path(remote_ini_path)
    else:
        ini_path = runtime_config_dir() / f'forward_task_{task.id}_{device.id}.ini'
    if write_local:
        ini_path.parent.mkdir(parents=True, exist_ok=True)
        ini_path.write_text(content, encoding='utf-8')
        os.makedirs(os.path.dirname(log_path) if log_path else str(runtime_config_dir()), exist_ok=True)
    return str(ini_path)


def generate_stream_forward_runtime_ini_content(
    task,
    device: Device,
    rtsp_url: str,
    rtmp_url: str,
    log_path: str,
    *,
    device_index: int = 0,
    remote_ini_path: Optional[str] = None,
) -> Tuple[str, str]:
    """Return (ini_path, content) for remote node upload."""
    content = _stream_forward_runtime_ini_content(
        task, device, rtsp_url, rtmp_url, log_path, device_index=device_index,
    )
    if remote_ini_path:
        path = str(remote_ini_path)
    else:
        path = str(runtime_config_dir() / f'forward_task_{task.id}_{device.id}.ini')
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


def _deploy_env_library_paths() -> List[str]:
    """从 RUNTIME/deploy.env 读取库目录（不依赖进程 env，避免被 nvidia 路径抢先占位）。"""
    deploy_env = _repo_root() / 'RUNTIME' / 'deploy.env'
    if not deploy_env.is_file():
        return []
    kv: Dict[str, str] = {}
    try:
        for line in deploy_env.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                kv[key] = value
    except Exception as e:
        logger.warning('解析 RUNTIME/deploy.env 库路径失败: %s', e)
        return []

    paths: List[str] = []
    for key in (
        'RUNTIME_CONDA_LIB_HOST',
        'RUNTIME_ORT_LIB_HOST',
        'RUNTIME_CUDA_LIB_HOST',
    ):
        raw = (kv.get(key) or '').strip()
        if not raw:
            continue
        for segment in raw.split(':'):
            segment = segment.strip()
            if segment and os.path.isdir(segment):
                paths.append(segment)

    ld = (kv.get('LD_LIBRARY_PATH') or '').strip()
    if ld:
        for segment in ld.split(':'):
            segment = segment.strip()
            if segment and os.path.isdir(segment):
                paths.append(segment)
    return paths


def runtime_library_path_env() -> str:
    """Build LD_LIBRARY_PATH hint for conda + ORT SDK + CUDA (host or Docker mounts)."""
    apply_runtime_deploy_env()
    parts: List[str] = []
    # deploy.env 中的 OpenCV/ORT 路径优先（须在 nvidia pip 库之前）
    parts.extend(_deploy_env_library_paths())
    for mounted in (
        '/opt/easyaiot/runtime-conda-lib',
        '/opt/easyaiot/ort-lib',
        '/opt/easyaiot/cuda-lib',
        '/opt/easyaiot/RUNTIME/lib',
    ):
        if os.path.isdir(mounted):
            parts.append(mounted)
    conda = (os.getenv('CONDA_PREFIX') or '').strip()
    if conda:
        parts.append(os.path.join(conda, 'lib'))
    # common local ORT layout (gpu preferred)
    root = _repo_root()
    runtime_bundle_lib = root / 'RUNTIME' / 'lib'
    if runtime_bundle_lib.is_dir():
        parts.append(str(runtime_bundle_lib))
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
    existing = (os.getenv('LD_LIBRARY_PATH') or '').strip()
    if existing:
        for segment in existing.split(':'):
            segment = segment.strip()
            if segment:
                parts.append(segment)
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
