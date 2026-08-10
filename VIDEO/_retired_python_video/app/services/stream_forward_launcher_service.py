"""
推流转发任务服务启动器
用于自动启动推流转发任务相关的服务（本机守护进程或 iot-node 远程部署）

多摄像头 + auto/node 调度时默认按设备分片（每分片独立 workload），分散到集群节点拉流推流。

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import os
import socket
import subprocess
import logging
import threading
import signal
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from models import db, StreamForwardTask
from app.utils.node_remote_python import resolve_video_bundle_python
from .stream_forward_daemon import StreamForwardDaemon

logger = logging.getLogger(__name__)

WORKLOAD_TYPE_STREAM_FORWARD = 'stream_forward'

_running_daemons: Dict[int, StreamForwardDaemon] = {}
_daemons_lock = threading.Lock()
_starting_tasks: Dict[int, threading.Lock] = {}
_starting_lock = threading.Lock()
_local_shard_processes: Dict[str, subprocess.Popen] = {}
_local_shard_lock = threading.Lock()


def _get_video_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _auto_include_local() -> bool:
    """auto 调度时是否将少量分片留在本机（控制面节点仅作兜底）。"""
    return os.getenv('STREAM_FORWARD_AUTO_INCLUDE_LOCAL', 'true').strip().lower() in (
        '1', 'true', 'yes', 'on',
    )


def _local_shard_max() -> int:
    """auto 调度时本机（控制面）最多承载的分片数，0 表示完全不下本机。"""
    try:
        return max(0, int(os.getenv('STREAM_FORWARD_LOCAL_MAX_SHARDS', '1')))
    except (TypeError, ValueError):
        return 1


def _should_deploy_shard_locally(task: StreamForwardTask, shard_index: int, total_shards: int) -> bool:
    policy = getattr(task, 'schedule_policy', None) or 'local'
    if policy == 'local':
        return True
    if policy != 'auto' or not _auto_include_local():
        return False
    max_local = _local_shard_max()
    if max_local <= 0:
        return False
    if total_shards <= max_local:
        return shard_index < total_shards
    # 仅前 max_local 个分片留在本机，其余全部分配到远程计算节点
    return shard_index < max_local


def _stop_local_shard(workload_id: str) -> None:
    with _local_shard_lock:
        proc = _local_shard_processes.pop(workload_id, None)
    if not proc:
        return
    try:
        if proc.poll() is None:
            if os.name != 'nt':
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.kill()
    except (ProcessLookupError, OSError) as e:
        logger.warning('停止本机推流转发分片失败 workload_id=%s: %s', workload_id, e)


def _stop_all_local_shards(task: StreamForwardTask) -> None:
    deployments = _parse_device_deployments(task)
    for dep in deployments:
        if dep.get('local'):
            workload_id = dep.get('workload_id')
            if workload_id:
                _stop_local_shard(str(workload_id))


def _deploy_shard_locally(
    task_id: int,
    task: StreamForwardTask,
    shard_index: int,
    device_ids: List[str],
) -> Dict[str, Any]:
    from app.services.camera_service import _get_host_ip_for_stream_urls
    from app.services.stream_url_sync_service import sync_devices_for_deployment
    import sys

    workload_id = _workload_id(task_id, shard_index, device_ids)
    host = _get_host_ip_for_stream_urls()
    video_root = _get_video_root()
    log_dir = os.path.join(
        video_root,
        'logs',
        f'stream_forward_task_{task_id}',
        _shard_log_suffix(shard_index, device_ids),
    )
    os.makedirs(log_dir, exist_ok=True)

    _stop_local_shard(workload_id)
    env = os.environ.copy()
    env.update(_build_stream_forward_deploy_env(task_id, log_dir, host, device_ids, workload_id))
    env['VIDEO_ROOT'] = video_root
    deploy_script = os.path.join(video_root, 'services', 'stream_forward_service', 'run_deploy.py')

    proc = subprocess.Popen(
        [sys.executable, deploy_script],
        cwd=video_root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid if os.name != 'nt' else None,
    )

    with _local_shard_lock:
        _local_shard_processes[workload_id] = proc

    deployment = {
        'device_ids': device_ids,
        'node_id': None,
        'host': host,
        'workload_id': workload_id,
        'pid': proc.pid,
        'log_dir': log_dir,
        'local': True,
    }
    try:
        sync_devices_for_deployment(deployment, commit=False)
    except Exception as e:
        logger.warning('本机分片流地址同步失败 task_id=%s: %s', task_id, e)

    logger.info(
        '推流转发分片本机部署成功 task_id=%s workload_id=%s host=%s devices=%s pid=%s',
        task_id, workload_id, host, device_ids, proc.pid,
    )
    return deployment


def _spread_shards_enabled() -> bool:
    """auto 调度批量部署时，尽量将分片分散到不同节点（轮询式反亲和）。"""
    return os.getenv('STREAM_FORWARD_SPREAD_SHARDS', 'true').strip().lower() in (
        '1', 'true', 'yes', 'on',
    )


def _should_spread_shards(task: StreamForwardTask) -> bool:
    policy = getattr(task, 'schedule_policy', None) or 'local'
    return policy == 'auto' and _spread_shards_enabled()


def _remote_fallback_local_enabled() -> bool:
    """远程分片部署失败时是否回退到本机（单节点/SSH 未配置时避免整任务部分失败）。"""
    return os.getenv('STREAM_FORWARD_REMOTE_FALLBACK_LOCAL', 'true').strip().lower() in (
        '1', 'true', 'yes', 'on',
    )


def _deploy_shard_for_schedule(
    task_id: int,
    task: StreamForwardTask,
    shard_index: int,
    device_ids: List[str],
    total_shards: int,
    spread_assigned_node_ids: Optional[List[int]] = None,
    fresh_allocate: bool = False,
) -> Dict[str, Any]:
    if _should_deploy_shard_locally(task, shard_index, total_shards):
        return _deploy_shard_locally(task_id, task, shard_index, device_ids)
    try:
        deployment = _deploy_shard_on_remote_node(
            task_id, task, shard_index, device_ids,
            spread_assigned_node_ids=spread_assigned_node_ids,
            fresh_allocate=fresh_allocate,
        )
    except Exception as e:
        if not _remote_fallback_local_enabled():
            raise
        logger.warning(
            '推流转发远程分片部署失败，回退本机 task_id=%s shard=%s devices=%s: %s',
            task_id, shard_index, device_ids, e,
        )
        deployment = _deploy_shard_locally(task_id, task, shard_index, device_ids)
        deployment['remote_fallback'] = True
        deployment['remote_error'] = str(e)[:200]
        return deployment
    if spread_assigned_node_ids is not None:
        node_id = deployment.get('node_id')
        if node_id is not None:
            nid = int(node_id)
            if nid not in spread_assigned_node_ids:
                spread_assigned_node_ids.append(nid)
    return deployment


def _use_remote_deploy(task: StreamForwardTask) -> bool:
    from app.utils.node_client import is_remote_deploy_enabled
    if not is_remote_deploy_enabled():
        return False
    policy = getattr(task, 'schedule_policy', None) or 'local'
    return policy in ('auto', 'node')


def _devices_per_shard() -> int:
    try:
        return max(1, int(os.getenv('STREAM_FORWARD_DEVICES_PER_SHARD', '4')))
    except (TypeError, ValueError):
        return 4


def _merge_exclude_node_ids(*groups: Optional[List[int]]) -> Optional[List[int]]:
    excludes: List[int] = []
    seen = set()
    for group in groups:
        for node_id in group or []:
            if node_id is None:
                continue
            nid = int(node_id)
            if nid not in seen:
                seen.add(nid)
                excludes.append(nid)
    return excludes or None


def _resolve_exclude_node_ids(extra: Optional[List[int]] = None) -> Optional[List[int]]:
    """合并调用方显式排除的节点 ID（控制面降权由 iot-node 调度器 score 负责）。"""
    excludes: List[int] = []
    seen = set()
    for node_id in extra or []:
        if node_id is None:
            continue
        nid = int(node_id)
        if nid not in seen:
            seen.add(nid)
            excludes.append(nid)
    hard_exclude_platform = os.getenv('STREAM_FORWARD_EXCLUDE_PLATFORM', 'false').strip().lower() in (
        '1', 'true', 'yes', 'on',
    )
    if hard_exclude_platform:
        try:
            from app.utils import node_client
            platform_id = node_client.get_platform_node_id()
            if platform_id is not None and platform_id not in seen:
                seen.add(platform_id)
                excludes.append(platform_id)
        except Exception as e:
            logger.debug('获取控制面节点 ID 失败: %s', e)
    return excludes or None


def _tag_int(tags: Optional[dict], key: str, default: int) -> int:
    if not tags:
        return default
    raw = tags.get(key)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _srs_ports_from_tags(tags: Optional[dict]) -> Dict[str, int]:
    tag_map = tags or {}
    return {
        'rtmp': _tag_int(tag_map, 'srs_rtmp_port', 1935),
        'http': _tag_int(tag_map, 'srs_http_port', 8080),
        'api': _tag_int(tag_map, 'srs_api_port', 1985),
    }


def _check_rtmp_port(host: str, port: int, timeout: float = 2.0) -> bool:
    host = (host or '').strip()
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _check_srs_api_ready(host: str, api_port: int, timeout: float = 3.0) -> bool:
    """通过 SRS HTTP API 判断媒体栈是否真正就绪（避免仅 TCP 端口占用误判）。"""
    host = (host or '').strip()
    if not host:
        return False
    try:
        import requests
        resp = requests.get(
            f'http://{host}:{api_port}/api/v1/versions',
            timeout=timeout,
        )
        if resp.status_code != 200:
            return False
        data = resp.json()
        return data.get('code') == 0 and bool(data.get('data'))
    except Exception:
        return False


def _ensure_node_srs_ready(node_id: int, host: str, tags: Optional[dict] = None) -> None:
    """远程推流前确认目标节点 SRS 可用，不可用则尝试 Agent 拉起媒体栈。"""
    if os.getenv('STREAM_FORWARD_ENSURE_SRS', 'true').strip().lower() not in ('1', 'true', 'yes', 'on'):
        return
    tag_map = tags or {}
    try:
        from app.utils import node_client
        if not tag_map:
            node = node_client.get_node(node_id)
            tag_map = node.get('tags') or {}
            host = host or str(node.get('host') or '').strip()
    except Exception as e:
        logger.warning('查询节点 SRS 配置失败 node_id=%s: %s', node_id, e)
        return

    srs_ports = _srs_ports_from_tags(tag_map)
    rtmp_port = srs_ports['rtmp']
    api_port = srs_ports['api']

    if _check_srs_api_ready(host, api_port):
        return

    if _check_rtmp_port(host, rtmp_port) and not _check_srs_api_ready(host, api_port):
        logger.warning(
            '目标节点 RTMP 端口 %s:%s 可连接但 SRS API %s 不可用，可能端口被非 SRS 进程占用',
            host, rtmp_port, api_port,
        )

    logger.warning(
        '目标节点 SRS 未就绪，尝试拉起媒体栈 node_id=%s host=%s api=%s rtmp=%s',
        node_id, host, api_port, rtmp_port,
    )
    try:
        from app.utils import node_client
        node_client.deploy_media_stack(node_id, stack_type='srs_live')
        for _ in range(15):
            time.sleep(2)
            if _check_srs_api_ready(host, api_port):
                logger.info(
                    '目标节点 SRS 已就绪 node_id=%s host=%s api=%s rtmp=%s',
                    node_id, host, api_port, rtmp_port,
                )
                return
        logger.error(
            '目标节点 SRS 启动超时 node_id=%s host=%s api=%s rtmp=%s，推流可能失败',
            node_id, host, api_port, rtmp_port,
        )
        raise RuntimeError(
            f'目标节点 SRS 未就绪: {host} (API {api_port}, RTMP {rtmp_port})，'
            f'请先在节点管理部署媒体栈或检查端口/防火墙'
        )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error('目标节点媒体栈部署失败 node_id=%s: %s', node_id, e, exc_info=True)
        raise RuntimeError(
            f'目标节点媒体栈部署失败: {host} (node_id={node_id}): {e}'
        ) from e


def _use_device_level_schedule(task: StreamForwardTask) -> bool:
    """多路摄像头远程部署时按设备/分片拆分 workload。"""
    if not _use_remote_deploy(task):
        return False
    device_count = len(task.devices or [])
    if device_count <= 1:
        return False
    flag = os.getenv('STREAM_FORWARD_DEVICE_LEVEL_SCHEDULE', 'true').strip().lower()
    return flag in ('1', 'true', 'yes', 'on')


def _parse_device_deployments(task: Optional[StreamForwardTask]) -> List[Dict[str, Any]]:
    if not task:
        return []
    if hasattr(task, '_parse_device_deployments'):
        return task._parse_device_deployments()
    raw = getattr(task, 'device_deployments', None)
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _serialize_device_deployments(deployments: List[Dict[str, Any]]) -> str:
    return json.dumps(deployments, ensure_ascii=False)


def _make_device_shards(device_ids: List[str]) -> List[List[str]]:
    shard_size = _devices_per_shard()
    return [device_ids[i:i + shard_size] for i in range(0, len(device_ids), shard_size)]


def _workload_id(task_id: int, shard_index: int, device_ids: List[str]) -> str:
    if len(device_ids) == 1:
        safe_id = str(device_ids[0]).replace(':', '_')
        return f'{task_id}:{safe_id}'
    return f'{task_id}:s{shard_index}'


def _shard_log_suffix(shard_index: int, device_ids: List[str]) -> str:
    if len(device_ids) == 1:
        safe_id = str(device_ids[0]).replace('/', '_').replace(':', '_')
        return f'device_{safe_id}'
    return f'shard_{shard_index}'


def _task_has_active_remote_deployments(task: StreamForwardTask) -> bool:
    deployments = _parse_device_deployments(task)
    if deployments:
        return True
    return bool(getattr(task, 'node_id', None))


def _heartbeat_stale(last_heartbeat, timeout_sec: int) -> bool:
    if not last_heartbeat:
        return True
    return (datetime.utcnow() - last_heartbeat).total_seconds() > timeout_sec


def _local_shard_process_alive(workload_id: str) -> bool:
    with _local_shard_lock:
        proc = _local_shard_processes.get(workload_id)
    if proc is None:
        return False
    return proc.poll() is None


def _stream_forward_deployments_healthy(task: StreamForwardTask) -> bool:
    """判断 DB 中的分片部署是否仍在运行（本机子进程存活 + 心跳未超时）。"""
    deployments = _parse_device_deployments(task)
    if not deployments:
        return False

    timeout = max(30, int(os.getenv('STREAM_FORWARD_HEARTBEAT_FAILOVER_SECONDS', '90')))

    for dep in deployments:
        if dep.get('local'):
            workload_id = str(dep.get('workload_id') or '')
            if not workload_id or not _local_shard_process_alive(workload_id):
                return False
            continue
        node_id = dep.get('node_id')
        if node_id and not _is_compute_node_online(int(node_id)):
            return False

    return not _heartbeat_stale(task.service_last_heartbeat, timeout)


def _resolve_video_control_url() -> str:
    from app.utils.node_client import resolve_java_backend_url
    return f'{resolve_java_backend_url()}/admin-api/video'


def _build_stream_forward_deploy_env(
    task_id: int,
    log_path: str,
    server_host: str,
    device_ids: Optional[List[str]] = None,
    workload_id: Optional[str] = None,
    node_tags: Optional[dict] = None,
) -> dict:
    env = {}
    for key in (
        'DATABASE_URL', 'GATEWAY_URL', 'JWT_TOKEN', 'JAVA_BACKEND_URL', 'POD_IP', 'HOST_IP', 'VIDEO_ENV',
        'USE_GPU', 'GPU_IDS', 'GPU_POLICY', 'FFMPEG_GPU_POLICY', 'FFMPEG_HWACCEL', 'FFMPEG_THREADS',
        'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES',
        'VIEW_OUTPUT_FPS', 'VIEW_SOURCE_FPS', 'VIEW_EXTRACT_INTERVAL',
        'VIEW_TARGET_WIDTH', 'VIEW_TARGET_HEIGHT', 'VIEW_FFMPEG_PRESET',
        'VIEW_FFMPEG_VIDEO_BITRATE', 'VIEW_FFMPEG_GOP_SIZE', 'VIEW_VIDEO_QUALITY_PROFILE',
        'VIEW_PUSH_FLUSH_EVERY', 'VIEW_AUTO_QUALITY_ENABLED',
        'SOURCE_FPS', 'TARGET_WIDTH', 'TARGET_HEIGHT',
        'FFMPEG_PRESET', 'FFMPEG_VIDEO_BITRATE', 'FFMPEG_GOP_SIZE', 'VIDEO_QUALITY_PROFILE',
        'AUTO_QUALITY_ENABLED', 'AUTO_QUALITY_LOCK_PROFILE',
        'AI_RTSP_ASYNC_READ', 'AI_RTSP_ASYNC_QUEUE_MAX', 'AI_RTSP_TRANSPORT',
        'OPENCV_FFMPEG_RTSP_TRANSPORT', 'RTSP_OPEN_TIMEOUT_MSEC', 'RTSP_READ_TIMEOUT_MSEC',
        'PUSH_FLUSH_EVERY',
        'STREAM_FORWARD_FFMPEG_NATIVE', 'STREAM_FORWARD_FFMPEG_MUX',
        'STREAM_FORWARD_RELAY_RESTART_DELAY_SEC', 'STREAM_FORWARD_RELAY_RESTART_COOLDOWN_SEC',
        'STREAM_FORWARD_RELAY_MAX_BACKOFF_SEC', 'STREAM_FORWARD_REMOTE_FALLBACK_LOCAL',
        'STREAM_FORWARD_ENSURE_SRS', 'STREAM_FORWARD_NVENC_PRESET', 'STREAM_FORWARD_NVENC_SKIP_TEST',
        'STREAM_FORWARD_VIDEO_COPY', 'STREAM_FORWARD_X264_THREADS',
        'STREAM_FORWARD_ANALYZEDURATION', 'STREAM_FORWARD_PROBESIZE',
        'STREAM_FORWARD_RW_TIMEOUT_US', 'STREAM_FORWARD_RECONNECT_DELAY_MAX',
        'STREAM_FORWARD_THREAD_QUEUE_SIZE', 'STREAM_FORWARD_MAX_MUXING_QUEUE_SIZE',
        'STREAM_FORWARD_TARGET_STREAMS',
        'STREAM_FORWARD_DEVICES_PER_SHARD', 'STREAM_FORWARD_LOCAL_MAX_SHARDS',
        'SRS_RTMP_PORT', 'SRS_HTTP_PORT', 'SRS_API_PORT',
    ):
        val = os.getenv(key)
        if val is not None and val != '':
            env[key] = val

    # 推流转发子进程不继承 AI 检测抽帧配置，避免误压观看帧率
    env.pop('EXTRACT_INTERVAL', None)
    env.setdefault('VIEW_EXTRACT_INTERVAL', '1')
    env.setdefault('VIEW_OUTPUT_FPS', os.getenv('VIEW_OUTPUT_FPS') or os.getenv('VIEW_SOURCE_FPS') or '25')

    srs_ports = _srs_ports_from_tags(node_tags)
    env.setdefault('SRS_RTMP_PORT', str(srs_ports['rtmp']))
    env.setdefault('SRS_HTTP_PORT', str(srs_ports['http']))
    env.setdefault('SRS_API_PORT', str(srs_ports['api']))

    video_control_url = _resolve_video_control_url()
    video_service_port = os.getenv('FLASK_RUN_PORT', '6000')
    env['PYTHONUNBUFFERED'] = '1'
    env['TASK_ID'] = str(task_id)
    env['VIDEO_SERVICE_PORT'] = video_service_port
    env['VIDEO_CONTROL_URL'] = video_control_url
    env['VIDEO_HEARTBEAT_URL'] = f'{video_control_url}/stream-forward/heartbeat'
    env['LOG_PATH'] = log_path
    env['POD_IP'] = server_host
    env['HOST_IP'] = server_host
    if device_ids:
        env['DEVICE_IDS'] = ','.join(device_ids)
    if workload_id:
        env['WORKLOAD_ID'] = workload_id
    from app.utils.node_remote_tools import apply_remote_toolchain_env
    apply_remote_toolchain_env(env)
    return env


def _apply_task_service_fields_from_deployments(task: StreamForwardTask, deployments: List[Dict[str, Any]]) -> None:
    if not deployments:
        task.node_id = None
        task.service_server_ip = None
        task.service_process_id = None
        task.service_log_path = None
        task.device_deployments = None
        return

    task.device_deployments = _serialize_device_deployments(deployments)
    hosts = sorted({dep.get('host') for dep in deployments if dep.get('host')})
    node_ids = sorted({dep.get('node_id') for dep in deployments if dep.get('node_id') is not None})
    task.service_server_ip = ','.join(hosts) if hosts else None
    task.service_process_id = deployments[0].get('pid')
    task.service_log_path = deployments[0].get('log_dir')
    task.node_id = node_ids[0] if len(node_ids) == 1 else None


def _release_remote_workload_binding(workload_id: str) -> None:
    """释放调度器中的 workload 绑定，避免重启后 running 计数与 sticky 沿用旧状态。"""
    from app.utils import node_client
    try:
        node_client.release_workload(WORKLOAD_TYPE_STREAM_FORWARD, str(workload_id))
    except Exception as e:
        logger.warning('释放推流转发节点绑定失败 workload_id=%s: %s', workload_id, e)


def _release_all_task_workload_bindings(task: StreamForwardTask) -> None:
    """释放任务下全部分片的调度绑定（全量重启前调用）。"""
    workload_ids = set()
    for dep in _parse_device_deployments(task):
        workload_id = dep.get('workload_id')
        if workload_id:
            workload_ids.add(str(workload_id))
    if not workload_ids and task.id:
        workload_ids.add(str(task.id))
    for workload_id in sorted(workload_ids):
        _release_remote_workload_binding(workload_id)


def _allocate_stream_forward_node(
    task: StreamForwardTask,
    workload_id: str,
    *,
    exclude_node_ids: Optional[List[int]] = None,
    spread_assigned_node_ids: Optional[List[int]] = None,
    fresh_allocate: bool = False,
) -> Dict[str, Any]:
    from app.utils import node_client

    policy = getattr(task, 'schedule_policy', None) or 'local'
    target_node_id = getattr(task, 'target_node_id', None)
    if policy == 'node' and not target_node_id:
        raise RuntimeError('已选择指定节点但未配置目标节点')

    base_excludes = _resolve_exclude_node_ids(exclude_node_ids)
    spread_excludes = (
        list(spread_assigned_node_ids)
        if _should_spread_shards(task) and spread_assigned_node_ids
        else None
    )
    full_excludes = _merge_exclude_node_ids(base_excludes, spread_excludes)

    sticky = not fresh_allocate
    prefer_gpu = getattr(task, 'prefer_gpu', True)
    try:
        return node_client.allocate_node(
            WORKLOAD_TYPE_STREAM_FORWARD,
            workload_id,
            capabilities=['stream_forward', 'srs_live'],
            gpu_count=1,
            prefer_gpu=prefer_gpu,
            target_node_id=target_node_id if policy == 'node' else None,
            sticky=sticky,
            exclude_node_ids=full_excludes,
        )
    except RuntimeError:
        if spread_excludes:
            logger.warning(
                '推流转发分片分散调度候选不足，回退为负载优先 workload_id=%s excludes=%s',
                workload_id, spread_excludes,
            )
            return node_client.allocate_node(
                WORKLOAD_TYPE_STREAM_FORWARD,
                workload_id,
                capabilities=['stream_forward', 'srs_live'],
                gpu_count=1,
                prefer_gpu=prefer_gpu,
                target_node_id=target_node_id if policy == 'node' else None,
                sticky=sticky,
                exclude_node_ids=base_excludes,
            )
        raise


def _deploy_shard_with_workload_id(
    task_id: int,
    task: StreamForwardTask,
    device_ids: List[str],
    workload_id: str,
    *,
    shard_index: Optional[int] = None,
    exclude_node_ids: Optional[List[int]] = None,
    spread_assigned_node_ids: Optional[List[int]] = None,
    fresh_allocate: bool = False,
) -> Dict[str, Any]:
    from app.utils import node_client

    policy = getattr(task, 'schedule_policy', None) or 'local'
    target_node_id = getattr(task, 'target_node_id', None)
    if policy == 'node' and not target_node_id:
        raise RuntimeError('已选择指定节点但未配置目标节点')

    if shard_index is None:
        if ':s' in workload_id:
            try:
                shard_index = int(workload_id.rsplit(':s', 1)[1])
            except (TypeError, ValueError):
                shard_index = 0
        else:
            shard_index = 0

    allocation = _allocate_stream_forward_node(
        task,
        workload_id,
        exclude_node_ids=exclude_node_ids,
        spread_assigned_node_ids=spread_assigned_node_ids,
        fresh_allocate=fresh_allocate,
    )

    node_id = allocation['nodeId']
    host = allocation['host']
    gpu_ids = allocation.get('gpuIds')

    node_tags = None
    try:
        node_info = node_client.get_node(node_id)
        node_tags = node_info.get('tags')
    except Exception as e:
        logger.debug('查询分配节点详情失败 node_id=%s: %s', node_id, e)
    _ensure_node_srs_ready(node_id, host, node_tags)

    video_root_remote = os.getenv('NODE_REMOTE_VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    work_dir = os.path.join(video_root_remote, 'services', 'stream_forward_service')
    log_dir = os.path.join(
        video_root_remote,
        'logs',
        f'stream_forward_task_{task_id}',
        _shard_log_suffix(shard_index, device_ids),
    )
    python_exec = resolve_video_bundle_python('stream_forward', video_root_remote)
    deploy_script = os.path.join(work_dir, 'run_deploy.py')
    command = [python_exec, deploy_script]

    env = _build_stream_forward_deploy_env(task_id, log_dir, host, device_ids, workload_id, node_tags)
    env['VIDEO_ROOT'] = video_root_remote

    result = node_client.deploy_workload(
        node_id=node_id,
        workload_type=WORKLOAD_TYPE_STREAM_FORWARD,
        workload_id=workload_id,
        command=command,
        work_dir=work_dir,
        log_dir=log_dir,
        env=env,
        gpu_ids=gpu_ids,
    )

    logger.info(
        '推流转发分片远程部署成功 task_id=%s workload_id=%s node_id=%s host=%s devices=%s pid=%s',
        task_id, workload_id, node_id, host, device_ids, result.get('pid'),
    )
    deployment = {
        'device_ids': device_ids,
        'node_id': node_id,
        'host': host,
        'workload_id': workload_id,
        'pid': result.get('pid'),
        'log_dir': log_dir,
    }
    try:
        from app.services.stream_url_sync_service import sync_devices_for_deployment
        sync_devices_for_deployment(deployment, commit=False)
    except Exception as e:
        logger.warning('远程分片流地址同步失败 task_id=%s: %s', task_id, e)
    return deployment


def _deploy_shard_on_remote_node(
    task_id: int,
    task: StreamForwardTask,
    shard_index: int,
    device_ids: List[str],
    *,
    spread_assigned_node_ids: Optional[List[int]] = None,
    fresh_allocate: bool = False,
) -> Dict[str, Any]:
    workload_id = _workload_id(task_id, shard_index, device_ids)
    return _deploy_shard_with_workload_id(
        task_id, task, device_ids, workload_id, shard_index=shard_index,
        spread_assigned_node_ids=spread_assigned_node_ids,
        fresh_allocate=fresh_allocate,
    )


def _shard_index_from_workload_id(workload_id: str) -> int:
    if ':s' in workload_id:
        try:
            return int(workload_id.rsplit(':s', 1)[1])
        except (TypeError, ValueError):
            pass
    return 0


def redeploy_existing_shard(
    task_id: int,
    task: StreamForwardTask,
    deployment: Dict[str, Any],
    exclude_node_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """在节点故障或进程异常时，将已有分片重新部署到其他节点。"""
    device_ids = list(deployment.get('device_ids') or [])
    workload_id = str(deployment.get('workload_id') or '')
    if not device_ids or not workload_id:
        raise ValueError('分片部署信息不完整')

    if deployment.get('local'):
        return _deploy_shard_locally(
            task_id,
            task,
            _shard_index_from_workload_id(workload_id),
            device_ids,
        )

    old_node_id = deployment.get('node_id')
    if old_node_id:
        _stop_remote_workload(int(old_node_id), workload_id)
    else:
        _release_remote_workload_binding(workload_id)

    excludes = list(exclude_node_ids or [])
    if old_node_id and int(old_node_id) not in excludes:
        excludes.append(int(old_node_id))
    try:
        from app.utils import node_client
        platform_id = node_client.get_platform_node_id()
        if platform_id is not None and platform_id not in excludes:
            excludes.append(platform_id)
    except Exception as e:
        logger.debug('获取控制面节点 ID 失败: %s', e)

    return _deploy_shard_with_workload_id(
        task_id,
        task,
        device_ids,
        workload_id,
        exclude_node_ids=excludes or None,
        fresh_allocate=True,
    )


def _is_compute_node_online(node_id: int) -> bool:
    from app.utils import node_client
    try:
        node = node_client.get_node(node_id)
        return str(node.get('status') or '').lower() == 'online'
    except Exception as e:
        logger.warning('查询节点状态失败 node_id=%s: %s', node_id, e)
        return False


def migrate_unhealthy_stream_forward_task(task_id: int) -> int:
    """检查并迁移离线节点分片或心跳超时任务，返回成功迁移的分片数。"""
    task = StreamForwardTask.query.get(task_id)
    if not task or not task.is_enabled or not _use_remote_deploy(task):
        return 0

    deployments = _parse_device_deployments(task)
    if not deployments:
        node_id = getattr(task, 'node_id', None)
        if not node_id:
            return 0
        device_ids = [d.id for d in (task.devices or []) if d.id]
        deployments = [{
            'device_ids': device_ids,
            'node_id': node_id,
            'workload_id': str(task_id),
            'host': task.service_server_ip,
        }]

    policy = getattr(task, 'schedule_policy', None) or 'local'
    heartbeat_timeout = max(30, int(os.getenv('STREAM_FORWARD_HEARTBEAT_FAILOVER_SECONDS', '90')))
    heartbeat_stale = False
    if task.service_last_heartbeat:
        heartbeat_stale = (
            datetime.utcnow() - task.service_last_heartbeat
        ).total_seconds() > heartbeat_timeout

    updated = list(deployments)
    migrated = 0
    offline_indices: List[int] = []

    for index, dep in enumerate(deployments):
        node_id = dep.get('node_id')
        if node_id and not _is_compute_node_online(int(node_id)):
            offline_indices.append(index)

    if offline_indices:
        for index in offline_indices:
            dep = deployments[index]
            node_id = dep.get('node_id')
            if policy == 'node':
                logger.error(
                    '推流转发指定节点离线，无法自动迁移 task_id=%s node_id=%s',
                    task_id, node_id,
                )
                continue
            try:
                updated[index] = redeploy_existing_shard(
                    task_id, task, dep, exclude_node_ids=[int(node_id)],
                )
                migrated += 1
            except Exception as e:
                logger.error(
                    '推流转发分片迁移失败 task_id=%s workload=%s: %s',
                    task_id, dep.get('workload_id'), e, exc_info=True,
                )
    elif heartbeat_stale and policy != 'node':
        for index, dep in enumerate(deployments):
            try:
                updated[index] = redeploy_existing_shard(task_id, task, dep)
                migrated += 1
            except Exception as e:
                logger.error(
                    '推流转发心跳超时重部署失败 task_id=%s workload=%s: %s',
                    task_id, dep.get('workload_id'), e, exc_info=True,
                )

    if migrated:
        _apply_task_service_fields_from_deployments(task, updated)
        db.session.commit()
        logger.info('推流转发任务分片迁移完成 task_id=%s migrated=%s', task_id, migrated)

    return migrated


def _deploy_task_on_remote_node(
    task_id: int,
    task: StreamForwardTask,
    *,
    fresh_allocate: bool = False,
) -> Tuple[bool, str, bool]:
    device_ids = [d.id for d in (task.devices or []) if d.id]
    if not device_ids:
        return (False, '任务未关联可用摄像头', False)

    if _use_device_level_schedule(task):
        shards = _make_device_shards(device_ids)
        deployments: List[Dict[str, Any]] = []
        failed: List[str] = []
        spread_assigned: Optional[List[int]] = [] if _should_spread_shards(task) else None

        for shard_index, shard_device_ids in enumerate(shards):
            try:
                deployments.append(
                    _deploy_shard_for_schedule(
                        task_id, task, shard_index, shard_device_ids, len(shards),
                        spread_assigned_node_ids=spread_assigned,
                        fresh_allocate=fresh_allocate,
                    )
                )
            except Exception as e:
                logger.error(
                    '推流转发分片部署失败 task_id=%s devices=%s: %s',
                    task_id, shard_device_ids, e, exc_info=True,
                )
                failed.append(','.join(shard_device_ids))

        if not deployments:
            return (False, f'所有分片部署失败: {"; ".join(failed)}', False)

        _apply_task_service_fields_from_deployments(task, deployments)
        db.session.commit()

        if failed:
            return (
                True,
                f'部分分片已下发（{len(deployments)}/{len(shards)}），失败: {"; ".join(failed)}',
                False,
            )
        hosts = sorted({dep.get('host') for dep in deployments if dep.get('host')})
        return (True, f'已按 {len(deployments)} 个分片下发到节点: {", ".join(hosts)}', False)

    from app.utils import node_client

    policy = getattr(task, 'schedule_policy', None) or 'local'
    target_node_id = getattr(task, 'target_node_id', None)
    if policy == 'node' and not target_node_id:
        return (False, '已选择指定节点但未配置目标节点', False)

    allocation = _allocate_stream_forward_node(
        task,
        str(task_id),
        exclude_node_ids=_resolve_exclude_node_ids(),
        fresh_allocate=fresh_allocate,
    )

    node_id = allocation['nodeId']
    host = allocation['host']
    gpu_ids = allocation.get('gpuIds')

    node_tags = None
    try:
        node_info = node_client.get_node(node_id)
        node_tags = node_info.get('tags')
    except Exception as e:
        logger.debug('查询分配节点详情失败 node_id=%s: %s', node_id, e)
    _ensure_node_srs_ready(node_id, host, node_tags)

    video_root_remote = os.getenv('NODE_REMOTE_VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    work_dir = os.path.join(video_root_remote, 'services', 'stream_forward_service')
    log_dir = os.path.join(video_root_remote, 'logs', f'stream_forward_task_{task_id}')
    python_exec = resolve_video_bundle_python('stream_forward', video_root_remote)
    deploy_script = os.path.join(work_dir, 'run_deploy.py')
    command = [python_exec, deploy_script]

    env = _build_stream_forward_deploy_env(task_id, log_dir, host, node_tags=node_tags)
    env['VIDEO_ROOT'] = video_root_remote

    result = node_client.deploy_workload(
        node_id=node_id,
        workload_type=WORKLOAD_TYPE_STREAM_FORWARD,
        workload_id=str(task_id),
        command=command,
        work_dir=work_dir,
        log_dir=log_dir,
        env=env,
        gpu_ids=gpu_ids,
    )

    deployment = [{
        'device_ids': device_ids,
        'node_id': node_id,
        'host': host,
        'workload_id': str(task_id),
        'pid': result.get('pid'),
        'log_dir': log_dir,
    }]
    try:
        from app.services.stream_url_sync_service import sync_devices_for_deployment
        for dep in deployment:
            sync_devices_for_deployment(dep, commit=False)
    except Exception as e:
        logger.warning('推流转发任务流地址同步失败 task_id=%s: %s', task_id, e)
    _apply_task_service_fields_from_deployments(task, deployment)
    task.node_id = node_id
    db.session.commit()

    logger.info(
        '推流转发任务远程部署成功 task_id=%s node_id=%s host=%s pid=%s',
        task_id, node_id, host, result.get('pid'),
    )
    return (True, f'已下发到节点 {host}', False)


def _stop_remote_workload(node_id: int, workload_id: str) -> None:
    from app.utils import node_client
    try:
        node_client.stop_workload(node_id, WORKLOAD_TYPE_STREAM_FORWARD, workload_id)
    except Exception as e:
        logger.warning('远程停止推流转发 workload 失败 node_id=%s workload_id=%s: %s', node_id, workload_id, e)
    _release_remote_workload_binding(workload_id)


def _stop_all_remote_deployments(task: StreamForwardTask) -> None:
    deployments = _parse_device_deployments(task)
    if deployments:
        for dep in deployments:
            node_id = dep.get('node_id')
            workload_id = dep.get('workload_id')
            if node_id and workload_id:
                _stop_remote_workload(int(node_id), str(workload_id))
        return

    task_id = task.id
    node_id = getattr(task, 'node_id', None)
    if node_id:
        _stop_remote_workload(int(node_id), str(task_id))


def get_service_script_path() -> str:
    video_root = _get_video_root()
    return os.path.join(video_root, 'services', 'stream_forward_service', 'run_deploy.py')


def _get_log_path(task_id: int) -> str:
    log_base_dir = os.path.join(_get_video_root(), 'logs')
    log_dir = os.path.join(log_base_dir, f'stream_forward_task_{task_id}')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


_STREAM_FORWARD_DEPLOY_MARKER = 'stream_forward_service/run_deploy.py'


def _is_stream_forward_deploy_cmdline(cmdline) -> bool:
    return any(_STREAM_FORWARD_DEPLOY_MARKER in str(arg) for arg in (cmdline or []))


def _collect_protected_stream_forward_pids(task_id: Optional[int] = None) -> set:
    """收集仍在管理的推流 worker PID（守护进程、本机分片及其子进程）。"""
    protected_pids = set()
    try:
        import psutil
    except ImportError:
        psutil = None

    with _daemons_lock:
        daemon_items = list(_running_daemons.items())
    for tid, daemon in daemon_items:
        if task_id is not None and tid != task_id:
            continue
        if not (daemon._running and daemon._process and daemon._process.poll() is None):
            continue
        protected_pids.add(daemon._process.pid)
        if psutil:
            try:
                for child in psutil.Process(daemon._process.pid).children(recursive=True):
                    protected_pids.add(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    with _local_shard_lock:
        shard_procs = list(_local_shard_processes.values())
    for proc in shard_procs:
        if not proc or proc.poll() is not None:
            continue
        protected_pids.add(proc.pid)
        if psutil:
            try:
                for child in psutil.Process(proc.pid).children(recursive=True):
                    protected_pids.add(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    return protected_pids


def _terminate_pid_tree(pid: int, graceful_timeout: float = 5.0) -> bool:
    """终止进程及其进程组（含 ffmpeg 子进程）。"""
    if pid <= 0:
        return False
    try:
        if os.name != 'nt':
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, OSError):
        try:
            import psutil
            psutil.Process(pid).terminate()
        except Exception:
            return False

    deadline = time.time() + graceful_timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
            time.sleep(0.2)
        except OSError:
            return True

    try:
        if os.name != 'nt':
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass
    return True


def _process_task_id(proc_info: dict, parent=None) -> Optional[str]:
    environ = proc_info.get('environ') or {}
    task_id = environ.get('TASK_ID')
    if task_id:
        return str(task_id)
    if parent is not None:
        try:
            parent_env = parent.environ()
            if parent_env and parent_env.get('TASK_ID'):
                return str(parent_env['TASK_ID'])
        except Exception:
            pass
    return None


def _kill_stream_forward_worker_processes(
    task_id: Optional[int] = None,
    protected_pids: Optional[set] = None,
) -> int:
    """清理推流转发 run_deploy / ffmpeg 遗留进程（仅限 stream_forward_service）。"""
    protected = set(protected_pids or ())
    killed_roots = set()
    killed_count = 0

    try:
        import psutil
    except ImportError:
        psutil = None

    if psutil:
        deploy_pids = []
        for proc in psutil.process_iter(['pid', 'cmdline', 'environ']):
            try:
                cmdline = proc.info.get('cmdline') or []
                if not _is_stream_forward_deploy_cmdline(cmdline):
                    continue
                pid = proc.info['pid']
                if pid in protected:
                    continue
                proc_task_id = _process_task_id(proc.info)
                if task_id is not None and proc_task_id != str(task_id):
                    continue
                deploy_pids.append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for pid in deploy_pids:
            if pid in killed_roots:
                continue
            if _terminate_pid_tree(pid):
                killed_roots.add(pid)
                killed_count += 1

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pid = proc.info['pid']
                if pid in protected or pid in killed_roots:
                    continue
                cmdline_str = ' '.join(proc.info.get('cmdline') or [])
                if 'ffmpeg' not in cmdline_str.lower():
                    continue
                parent = proc.parent()
                if not parent or not _is_stream_forward_deploy_cmdline(parent.cmdline()):
                    continue
                parent_task_id = None
                try:
                    parent_task_id = parent.environ().get('TASK_ID')
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if task_id is not None and parent_task_id != str(task_id):
                    continue
                if _terminate_pid_tree(pid):
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return killed_count

    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return 0
        for line in result.stdout.split('\n'):
            if _STREAM_FORWARD_DEPLOY_MARKER not in line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1])
            except ValueError:
                continue
            if pid in protected or pid in killed_roots:
                continue
            if _terminate_pid_tree(pid):
                killed_roots.add(pid)
                killed_count += 1
    except Exception as e:
        logger.warning('清理推流转发遗留进程失败: %s', e)
    return killed_count


def cleanup_orphaned_processes(task_id: int):
    """清理本机遗留的 run_deploy.py / FFmpeg 进程（远程任务跳过）"""
    try:
        protected_pids = _collect_protected_stream_forward_pids(task_id)
        killed_count = _kill_stream_forward_worker_processes(task_id, protected_pids)
        if killed_count > 0:
            logger.info('🧹 清理了 %d 个推流转发遗留进程 (task_id=%s)', killed_count, task_id)
    except Exception as e:
        logger.warning('清理遗留进程时出错: %s', e)


def cleanup_all_orphaned_stream_forward_processes() -> int:
    """清理本机所有推流转发 worker（VIDEO 服务关闭时的兜底 sweep）。"""
    try:
        protected_pids = _collect_protected_stream_forward_pids()
        killed_count = _kill_stream_forward_worker_processes(None, protected_pids)
        if killed_count > 0:
            logger.info('🧹 兜底清理了 %d 个推流转发遗留进程', killed_count)
        return killed_count
    except Exception as e:
        logger.warning('兜底清理推流转发遗留进程失败: %s', e)
        return 0


def stop_all_daemons():
    """停止所有推流转发守护进程与本机分片（VIDEO 服务关闭时调用）。"""
    with _local_shard_lock:
        workload_ids = list(_local_shard_processes.keys())
    for workload_id in workload_ids:
        _stop_local_shard(workload_id)

    with _daemons_lock:
        task_ids = list(_running_daemons.keys())

    if task_ids:
        logger.info('正在停止 %d 个推流转发守护进程...', len(task_ids))
    for task_id in task_ids:
        try:
            with _daemons_lock:
                daemon = _running_daemons.get(task_id)
            if not daemon:
                continue
            daemon.stop()
            logger.info('✅ 停止推流转发守护进程成功: task_id=%s', task_id)
        except Exception as e:
            logger.error('❌ 停止推流转发守护进程失败: task_id=%s, error=%s', task_id, e)
        finally:
            with _daemons_lock:
                _running_daemons.pop(task_id, None)

    cleanup_all_orphaned_stream_forward_processes()
    logger.info('✅ 推流转发 worker 已全部停止')


def stop_stream_forward_task(task_id: int):
    """停止推流转发任务（本机或远程，含设备级多分片）"""
    with _starting_lock:
        if task_id in _starting_tasks:
            task_start_lock = _starting_tasks[task_id]
            if task_start_lock.acquire(blocking=True, timeout=5):
                task_start_lock.release()

    task = StreamForwardTask.query.get(task_id)
    was_remote = bool(task and _task_has_active_remote_deployments(task))
    if was_remote and task:
        _stop_all_remote_deployments(task)
        _stop_all_local_shards(task)
        _apply_task_service_fields_from_deployments(task, [])
        db.session.commit()

    with _daemons_lock:
        if task_id in _running_daemons:
            daemon = _running_daemons[task_id]
            try:
                daemon.stop()
                logger.info(f"✅ 停止推流转发服务成功: task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 停止推流转发服务失败: task_id={task_id}, error={str(e)}")
            finally:
                del _running_daemons[task_id]

    if not was_remote:
        cleanup_orphaned_processes(task_id)


def _collect_deployed_device_ids(deployments: List[Dict[str, Any]]) -> set:
    deployed = set()
    for dep in deployments:
        for device_id in dep.get('device_ids') or []:
            deployed.add(device_id)
    return deployed


def _next_shard_index(deployments: List[Dict[str, Any]]) -> int:
    max_index = -1
    for dep in deployments:
        workload_id = str(dep.get('workload_id') or '')
        if ':s' in workload_id:
            try:
                max_index = max(max_index, int(workload_id.rsplit(':s', 1)[1]))
            except (TypeError, ValueError):
                pass
    return max(max_index + 1, len(deployments))


def rebalance_stream_forward_task(task_id: int) -> bool:
    """设备列表变更后增量重平衡：仅停止移除分片、部署新增分片。"""
    task = StreamForwardTask.query.get(task_id)
    if not task:
        return False
    if not task.is_enabled:
        return True

    if not _use_remote_deploy(task):
        with _daemons_lock:
            daemon = _running_daemons.get(task_id)
            if daemon:
                try:
                    daemon.restart()
                    logger.info('推流转发本机任务已重启以同步设备列表: task_id=%s', task_id)
                    return True
                except Exception as e:
                    logger.error('推流转发本机任务重启失败 task_id=%s: %s', task_id, e)
                    return False
        start_stream_forward_task(task_id)
        return True

    if not _use_device_level_schedule(task):
        return restart_stream_forward_task_services(task_id)

    current_ids = {d.id for d in (task.devices or []) if d.id}
    deployments = _parse_device_deployments(task)
    deployed_ids = _collect_deployed_device_ids(deployments)
    removed_ids = deployed_ids - current_ids
    added_ids = sorted(current_ids - deployed_ids)

    if not removed_ids and not added_ids:
        logger.info('推流转发任务无需重平衡: task_id=%s', task_id)
        return True

    logger.info(
        '推流转发任务开始重平衡: task_id=%s, 新增=%s, 移除=%s',
        task_id, added_ids, sorted(removed_ids),
    )

    kept_deployments: List[Dict[str, Any]] = []
    for dep in deployments:
        dep_devices = set(dep.get('device_ids') or [])
        if dep_devices & removed_ids:
            node_id = dep.get('node_id')
            workload_id = dep.get('workload_id')
            if dep.get('local') and workload_id:
                _stop_local_shard(str(workload_id))
            elif node_id and workload_id:
                _stop_remote_workload(int(node_id), str(workload_id))
            continue
        kept_deployments.append(dep)

    failed_added: List[str] = []
    if added_ids:
        shards = _make_device_shards(added_ids)
        shard_index = _next_shard_index(kept_deployments)
        spread_assigned: Optional[List[int]] = None
        if _should_spread_shards(task):
            spread_assigned = []
            for dep in kept_deployments:
                node_id = dep.get('node_id')
                if node_id is not None and int(node_id) not in spread_assigned:
                    spread_assigned.append(int(node_id))
        for shard_device_ids in shards:
            try:
                kept_deployments.append(
                    _deploy_shard_for_schedule(
                        task_id, task, shard_index, shard_device_ids, len(shards) + len(kept_deployments),
                        spread_assigned_node_ids=spread_assigned,
                    )
                )
                shard_index += 1
            except Exception as e:
                logger.error(
                    '推流转发新增分片部署失败 task_id=%s devices=%s: %s',
                    task_id, shard_device_ids, e, exc_info=True,
                )
                failed_added.extend(shard_device_ids)

    if not kept_deployments and current_ids:
        logger.warning('推流转发重平衡后无存活分片，回退全量部署: task_id=%s', task_id)
        return restart_stream_forward_task_services(task_id)

    _apply_task_service_fields_from_deployments(task, kept_deployments)
    db.session.commit()

    if failed_added:
        logger.warning('推流转发重平衡部分失败 task_id=%s failed=%s', task_id, failed_added)
        return False
    return True


def restart_stream_forward_task_services(task_id: int) -> bool:
    """重启推流转发任务服务"""
    task = StreamForwardTask.query.get(task_id)
    if task and _use_remote_deploy(task):
        _stop_all_remote_deployments(task)
        _release_all_task_workload_bindings(task)
        _stop_all_local_shards(task)
        _apply_task_service_fields_from_deployments(task, [])
        db.session.commit()
        success, _, _ = _deploy_task_on_remote_node(task_id, task, fresh_allocate=True)
        return success

    with _daemons_lock:
        if task_id in _running_daemons:
            daemon = _running_daemons[task_id]
            try:
                daemon.restart()
                logger.info(f"✅ 重启推流转发任务 {task_id} 的服务成功")
                return True
            except Exception as e:
                logger.error(f"❌ 重启推流转发任务 {task_id} 的服务失败: {str(e)}")
                return False

    # VIDEO 进程重启后内存中无守护进程记录，回退为重新拉起
    if task and not _use_remote_deploy(task):
        try:
            logger.info('推流转发任务 %s 本机守护进程不在内存中，回退为重新启动', task_id)
            start_stream_forward_task(task_id)
            return True
        except Exception as e:
            logger.error('推流转发任务 %s 回退启动失败: %s', task_id, e, exc_info=True)
            return False

    logger.warning(f"推流转发任务 {task_id} 的服务未运行，无法重启")
    return False


def start_stream_forward_task(task_id: int):
    """启动推流转发任务（本机守护进程或远程节点/设备级分片）"""
    task = StreamForwardTask.query.get(task_id)
    if not task:
        raise ValueError(f"推流转发任务不存在: task_id={task_id}")

    with _starting_lock:
        if task_id not in _starting_tasks:
            _starting_tasks[task_id] = threading.Lock()
        task_start_lock = _starting_tasks[task_id]

    with task_start_lock:
        if _use_remote_deploy(task):
            if _task_has_active_remote_deployments(task):
                if _stream_forward_deployments_healthy(task):
                    logger.info('推流转发任务 %s 分片仍在运行，跳过重复部署', task_id)
                    return
                logger.info(
                    '推流转发任务 %s 部署记录存在但分片未运行或心跳超时，重新部署',
                    task_id,
                )
                _stop_all_local_shards(task)
            success, message, _ = _deploy_task_on_remote_node(task_id, task)
            if not success:
                raise RuntimeError(message)
            return

        with _daemons_lock:
            if task_id in _running_daemons:
                daemon = _running_daemons[task_id]
                if daemon._running and daemon._process and daemon._process.poll() is None:
                    logger.warning(f"推流转发任务已在运行: task_id={task_id}")
                    return

        cleanup_orphaned_processes(task_id)
        log_path = _get_log_path(task_id)

        with _daemons_lock:
            daemon = StreamForwardDaemon(task_id, log_path)
            _running_daemons[task_id] = daemon

        logger.info(f"✅ 启动推流转发服务成功: task_id={task_id}, log_path={log_path}")

        with _starting_lock:
            if task_id in _starting_tasks:
                del _starting_tasks[task_id]


def auto_start_all_tasks(app=None):
    """自动启动所有启用的推流转发任务的服务"""
    try:
        if app:
            with app.app_context():
                _auto_start_all_tasks_internal()
        else:
            _auto_start_all_tasks_internal()
    except Exception as e:
        logger.error(f"❌ 自动启动推流转发任务服务失败: {str(e)}", exc_info=True)


def _auto_start_all_tasks_internal():
    try:
        all_tasks = StreamForwardTask.query.all()
        if all_tasks:
            logger.info(f"📊 数据库中共有 {len(all_tasks)} 个推流转发任务")
            for task in all_tasks:
                device_count = len(task.devices) if task.devices else 0
                policy = getattr(task, 'schedule_policy', None) or 'local'
                dep_count = len(_parse_device_deployments(task))
                status = "运行中" if task.is_enabled else "已停止"
                logger.info(
                    f"  任务 {task.id} ({task.task_name}): is_enabled={task.is_enabled} ({status}), "
                    f"设备数={device_count}, schedule={policy}, 远程分片={dep_count}"
                )

        tasks = StreamForwardTask.query.filter(StreamForwardTask.is_enabled == True).all()
        if not tasks:
            logger.info("没有需要启动的推流转发任务（is_enabled=True）")
            return

        logger.info(f"发现 {len(tasks)} 个需要启动的推流转发任务，开始启动服务...")
        success_count = 0
        for task in tasks:
            try:
                if not task.devices:
                    logger.warning(f"任务 {task.id} ({task.task_name}) 没有关联的摄像头，跳过")
                    continue
                if _use_remote_deploy(task) and _task_has_active_remote_deployments(task):
                    if _stream_forward_deployments_healthy(task):
                        logger.info('任务 %s 分片仍在运行，跳过自动启动', task.id)
                        success_count += 1
                        continue
                    logger.info(
                        '任务 %s 部署记录存在但分片未运行，服务启动时重新部署',
                        task.id,
                    )
                start_stream_forward_task(task.id)
                success_count += 1
                logger.info(f"✅ 任务 {task.id} ({task.task_name}) 的服务启动成功")
            except Exception as e:
                logger.error(f"❌ 启动任务 {task.id} 的服务时出错: {str(e)}", exc_info=True)

        logger.info(f"✅ 自动启动完成: {success_count}/{len(tasks)} 个任务的服务启动成功")
    except Exception as e:
        logger.error(f"❌ 自动启动推流转发任务服务失败: {str(e)}", exc_info=True)
