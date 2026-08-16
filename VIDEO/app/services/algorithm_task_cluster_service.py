"""
算法任务集群按设备分片部署（对齐推流转发）。

realtime / snap / patrol + auto/node + 多路时：每分片独立 workload，打散到集群节点。
- realtime：默认一路一 RUNTIME（ALGORITHM_DEVICES_PER_SHARD=1）
- snap/patrol：分片内多设备共用一个进程（可用 ALGORITHM_SNAP_DEVICES_PER_SHARD，默认 4）

环境变量：
- ALGORITHM_DEVICE_LEVEL_SCHEDULE（默认 true）
- ALGORITHM_DEVICES_PER_SHARD（realtime 默认 1）
- ALGORITHM_SNAP_DEVICES_PER_SHARD（snap/patrol 默认 4，未设则回退 ALGORITHM_DEVICES_PER_SHARD）
- ALGORITHM_SPREAD_SHARDS（默认 true）
- ALGORITHM_AUTO_INCLUDE_LOCAL / ALGORITHM_LOCAL_MAX_SHARDS
- ALGORITHM_REMOTE_FALLBACK_LOCAL（默认 true）
"""
from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from models import db, AlgorithmTask

logger = logging.getLogger(__name__)

WORKLOAD_TYPE_ALGORITHM = 'algorithm_task'

_local_shard_processes: Dict[str, subprocess.Popen] = {}
_local_shard_lock = threading.Lock()


def _get_video_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _env_bool(name: str, default: str = 'true') -> bool:
    return os.getenv(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


def _normalize_task_type(task: AlgorithmTask) -> str:
    task_type = (getattr(task, 'task_type', None) or '').strip().lower()
    if task_type == 'snapshot':
        return 'snap'
    return task_type


def use_remote_deploy(task: AlgorithmTask) -> bool:
    from app.utils.node_client import is_remote_deploy_enabled
    if not is_remote_deploy_enabled():
        return False
    policy = getattr(task, 'schedule_policy', None) or 'local'
    return policy in ('auto', 'node')


def use_device_level_schedule(task: AlgorithmTask) -> bool:
    """realtime/snap/patrol 多路 + auto/node 时按设备分片。"""
    if not use_remote_deploy(task):
        return False
    task_type = _normalize_task_type(task)
    if task_type not in ('realtime', 'snap', 'patrol'):
        return False
    if len(task.devices or []) <= 1:
        return False
    return _env_bool('ALGORITHM_DEVICE_LEVEL_SCHEDULE', 'true')


def _devices_per_shard(task: Optional[AlgorithmTask] = None) -> int:
    task_type = _normalize_task_type(task) if task is not None else 'realtime'
    if task_type in ('snap', 'patrol'):
        raw = os.getenv('ALGORITHM_SNAP_DEVICES_PER_SHARD')
        if raw is None or str(raw).strip() == '':
            raw = os.getenv('ALGORITHM_DEVICES_PER_SHARD', '4')
        default = 4
    else:
        raw = os.getenv('ALGORITHM_DEVICES_PER_SHARD', '1')
        default = 1
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return default


def _make_device_shards(device_ids: List[str], task: Optional[AlgorithmTask] = None) -> List[List[str]]:
    size = _devices_per_shard(task)
    return [device_ids[i:i + size] for i in range(0, len(device_ids), size)]


def _workload_id(task_id: int, shard_index: int, device_ids: List[str]) -> str:
    if len(device_ids) == 1:
        return f'{task_id}:{str(device_ids[0]).replace(":", "_")}'
    return f'{task_id}:s{shard_index}'


def _shard_log_suffix(shard_index: int, device_ids: List[str]) -> str:
    if len(device_ids) == 1:
        safe = str(device_ids[0]).replace('/', '_').replace(':', '_')
        return f'device_{safe}'
    return f'shard_{shard_index}'


def parse_device_deployments(task: Optional[AlgorithmTask]) -> List[Dict[str, Any]]:
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


def serialize_device_deployments(deployments: List[Dict[str, Any]]) -> str:
    return json.dumps(deployments, ensure_ascii=False)


def apply_task_service_fields_from_deployments(
    task: AlgorithmTask,
    deployments: List[Dict[str, Any]],
) -> None:
    if not deployments:
        task.node_id = None
        task.service_server_ip = None
        task.service_process_id = None
        task.service_log_path = None
        task.device_deployments = None
        return
    task.device_deployments = serialize_device_deployments(deployments)
    hosts = sorted({dep.get('host') for dep in deployments if dep.get('host')})
    node_ids = sorted({dep.get('node_id') for dep in deployments if dep.get('node_id') is not None})
    task.service_server_ip = ','.join(hosts) if hosts else None
    task.service_process_id = deployments[0].get('pid')
    task.service_log_path = deployments[0].get('log_dir')
    task.node_id = node_ids[0] if len(node_ids) == 1 else None
    task.run_status = 'running'


def _auto_include_local() -> bool:
    return _env_bool('ALGORITHM_AUTO_INCLUDE_LOCAL', 'true')


def _local_shard_max() -> int:
    try:
        return max(0, int(os.getenv('ALGORITHM_LOCAL_MAX_SHARDS', '1')))
    except (TypeError, ValueError):
        return 1


def _should_deploy_shard_locally(task: AlgorithmTask, shard_index: int, total_shards: int) -> bool:
    policy = getattr(task, 'schedule_policy', None) or 'local'
    if policy == 'local':
        return True
    if policy != 'auto' or not _auto_include_local():
        return False
    max_local = _local_shard_max()
    if max_local <= 0:
        return False
    return shard_index < max_local


def _should_spread_shards(task: AlgorithmTask) -> bool:
    policy = getattr(task, 'schedule_policy', None) or 'local'
    return policy == 'auto' and _env_bool('ALGORITHM_SPREAD_SHARDS', 'true')


def _remote_fallback_local_enabled() -> bool:
    return _env_bool('ALGORITHM_REMOTE_FALLBACK_LOCAL', 'true')


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
    excludes: List[int] = []
    seen = set()
    for node_id in extra or []:
        if node_id is None:
            continue
        nid = int(node_id)
        if nid not in seen:
            seen.add(nid)
            excludes.append(nid)
    if _env_bool('ALGORITHM_EXCLUDE_PLATFORM', 'false'):
        try:
            from app.utils import node_client
            platform_id = node_client.get_platform_node_id()
            if platform_id is not None and platform_id not in seen:
                excludes.append(int(platform_id))
        except Exception as e:
            logger.debug('获取控制面节点 ID 失败: %s', e)
    return excludes or None


def _normalize_executor(task: AlgorithmTask) -> str:
    from app.services.runtime_config_service import normalize_executor
    return normalize_executor(getattr(task, 'executor', None) or 'cpp')


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
        logger.warning('停止本机算法分片失败 workload_id=%s: %s', workload_id, e)


def stop_all_local_shards(task: AlgorithmTask) -> None:
    for dep in parse_device_deployments(task):
        if dep.get('local') and dep.get('workload_id'):
            _stop_local_shard(str(dep['workload_id']))


def _local_shard_process_alive(workload_id: str) -> bool:
    with _local_shard_lock:
        proc = _local_shard_processes.get(workload_id)
    return proc is not None and proc.poll() is None


def _is_compute_node_online(node_id: int) -> bool:
    from app.utils import node_client
    try:
        node = node_client.get_node(node_id)
        return str(node.get('status') or '').lower() == 'online'
    except Exception as e:
        logger.warning('查询节点状态失败 node_id=%s: %s', node_id, e)
        return False


def _heartbeat_stale(last_heartbeat, timeout_sec: int) -> bool:
    if not last_heartbeat:
        return True
    return (datetime.utcnow() - last_heartbeat).total_seconds() > timeout_sec


def deployments_healthy(task: AlgorithmTask) -> bool:
    deployments = parse_device_deployments(task)
    if not deployments:
        return False
    timeout = max(30, int(os.getenv('ALGORITHM_HEARTBEAT_FAILOVER_SECONDS', '90')))
    for dep in deployments:
        if dep.get('local'):
            wid = str(dep.get('workload_id') or '')
            if not wid or not _local_shard_process_alive(wid):
                return False
            continue
        node_id = dep.get('node_id')
        if node_id and not _is_compute_node_online(int(node_id)):
            return False
    return not _heartbeat_stale(task.service_last_heartbeat, timeout)


def release_remote_workload_binding(workload_id: str) -> None:
    from app.utils import node_client
    try:
        node_client.release_workload(WORKLOAD_TYPE_ALGORITHM, str(workload_id))
    except Exception as e:
        logger.warning('释放算法任务节点绑定失败 workload_id=%s: %s', workload_id, e)


def release_all_task_workload_bindings(task: AlgorithmTask) -> None:
    workload_ids = set()
    for dep in parse_device_deployments(task):
        wid = dep.get('workload_id')
        if wid:
            workload_ids.add(str(wid))
    if not workload_ids and task.id:
        workload_ids.add(str(task.id))
    for wid in sorted(workload_ids):
        release_remote_workload_binding(wid)


def stop_remote_workload(node_id: int, workload_id: str) -> None:
    from app.utils import node_client
    try:
        node_client.stop_workload(node_id, WORKLOAD_TYPE_ALGORITHM, workload_id)
    except Exception as e:
        logger.warning(
            '远程停止算法 workload 失败 node_id=%s workload_id=%s: %s',
            node_id, workload_id, e,
        )
    release_remote_workload_binding(workload_id)


def stop_all_remote_deployments(task: AlgorithmTask) -> None:
    deployments = parse_device_deployments(task)
    if deployments:
        for dep in deployments:
            node_id = dep.get('node_id')
            workload_id = dep.get('workload_id')
            if node_id and workload_id and not dep.get('local'):
                stop_remote_workload(int(node_id), str(workload_id))
        return
    node_id = getattr(task, 'node_id', None)
    if node_id:
        stop_remote_workload(int(node_id), str(task.id))


def stop_all_shards(task: AlgorithmTask) -> None:
    stop_all_local_shards(task)
    stop_all_remote_deployments(task)
    release_all_task_workload_bindings(task)


def _allocate_algorithm_node(
    task: AlgorithmTask,
    workload_id: str,
    *,
    exclude_node_ids: Optional[List[int]] = None,
    spread_assigned_node_ids: Optional[List[int]] = None,
    fresh_allocate: bool = False,
) -> Dict[str, Any]:
    from app.utils import node_client
    from app.services.algorithm_task_launcher_service import _task_capabilities

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
    caps = _task_capabilities(task.task_type)
    try:
        return node_client.allocate_node(
            WORKLOAD_TYPE_ALGORITHM,
            workload_id,
            capabilities=caps,
            prefer_gpu=prefer_gpu,
            target_node_id=target_node_id if policy == 'node' else None,
            sticky=sticky,
            exclude_node_ids=full_excludes,
        )
    except RuntimeError:
        if spread_excludes:
            logger.warning(
                '算法分片分散调度候选不足，回退负载优先 workload_id=%s excludes=%s',
                workload_id, spread_excludes,
            )
            return node_client.allocate_node(
                WORKLOAD_TYPE_ALGORITHM,
                workload_id,
                capabilities=caps,
                prefer_gpu=prefer_gpu,
                target_node_id=target_node_id if policy == 'node' else None,
                sticky=sticky,
                exclude_node_ids=base_excludes,
            )
        raise


def _ensure_runtime_ready_on_node(node_id: int, host: str) -> None:
    from app.utils import node_client
    try:
        rt_check = node_client.check_runtime_cpp_ready(int(node_id))
    except Exception as e:
        raise RuntimeError(f'无法检测节点 {host} 的 RUNTIME 状态: {e}') from e
    ready = bool(rt_check.get('runtimeReady') or rt_check.get('success'))
    if not ready:
        detail = (rt_check.get('message') or '').strip() or 'RUNTIME 未安装或不可用'
        raise RuntimeError(
            f'节点 {host} 未就绪高性能执行器：{detail}。'
            f'请先在 WEB「节点管理 → 业务运行时分发」对该节点「分发 RUNTIME」'
        )


def _deploy_cpp_shard_command_and_files(
    task: AlgorithmTask,
    task_id: int,
    device_ids: List[str],
    log_dir: str,
) -> Tuple[List[str], List[Dict[str, str]], str]:
    """返回 (command, files, work_dir)。"""
    from app.services.runtime_config_service import (
        REMOTE_RUNTIME_BIN,
        generate_runtime_inis_content,
    )

    task_type = _normalize_task_type(task)
    # realtime：一路一 ini；snap/patrol：分片内多设备一个 ini
    force_per_device = task_type == 'realtime'
    pairs = generate_runtime_inis_content(
        task,
        log_dir,
        prefer_cluster_model=True,
        only_device_ids=device_ids,
        force_per_device=force_per_device,
        remote_ini_dir=log_dir,
    )
    files = [{'path': p, 'content': c, 'mode': '0644'} for p, c in pairs]
    work_dir = '/opt/easyaiot/RUNTIME'
    if len(pairs) == 1:
        return [REMOTE_RUNTIME_BIN, pairs[0][0]], files, work_dir

    # realtime 分片内多路（DEVICES_PER_SHARD>1）：bash 并行拉起
    ini_args = ' '.join(f'"{p}"' for p, _ in pairs)
    script = (
        'set -e; pids=(); '
        f'for f in {ini_args}; do "{REMOTE_RUNTIME_BIN}" "$f" & pids+=($!); done; '
        'trap \'kill "${pids[@]}" 2>/dev/null || true\' EXIT TERM INT; '
        'wait'
    )
    return ['/bin/bash', '-lc', script], files, work_dir


def _deploy_python_shard_command(
    task: AlgorithmTask,
    task_id: int,
) -> Tuple[List[str], str]:
    from app.utils.node_remote_python import resolve_video_bundle_python

    video_root_remote = os.getenv('NODE_REMOTE_VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    service_dir = {
        'realtime': 'realtime_algorithm_service',
        'snap': 'snapshot_algorithm_service',
        'patrol': 'patrol_algorithm_service',
    }.get(task.task_type, 'realtime_algorithm_service')
    work_dir = os.path.join(video_root_remote, 'services', service_dir)
    bundle = {
        'snap': 'algorithm_snap',
        'patrol': 'algorithm_patrol',
    }.get(task.task_type, 'algorithm_realtime')
    python_exec = resolve_video_bundle_python(bundle, video_root_remote)
    deploy_script = os.path.join(work_dir, 'run_deploy.py')
    return [python_exec, deploy_script], work_dir


def _build_shard_env(
    task: AlgorithmTask,
    task_id: int,
    log_dir: str,
    host: str,
    device_ids: List[str],
    workload_id: str,
) -> dict:
    from app.services.algorithm_task_launcher_service import _build_task_deploy_env
    from app.services.runtime_config_service import REMOTE_RUNTIME_BIN, REMOTE_RUNTIME_LD_LIBRARY_PATH

    env = _build_task_deploy_env(task_id, task.task_type, log_dir, host, task=task)
    video_root_remote = os.getenv('NODE_REMOTE_VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    env['VIDEO_ROOT'] = video_root_remote
    env['WORKLOAD_ID'] = workload_id
    env['DEVICE_IDS'] = ','.join(str(x) for x in device_ids)
    env['ALGORITHM_SHARD_DEVICE_IDS'] = env['DEVICE_IDS']
    if _normalize_executor(task) == 'cpp':
        env['RUNTIME_BIN'] = REMOTE_RUNTIME_BIN
        env['LD_LIBRARY_PATH'] = REMOTE_RUNTIME_LD_LIBRARY_PATH
        env['USE_GPU'] = 'true' if getattr(task, 'prefer_gpu', True) else 'false'
        env['RUNTIME_PREFER_GPU'] = env['USE_GPU']
    return env


def _deploy_shard_locally(
    task_id: int,
    task: AlgorithmTask,
    shard_index: int,
    device_ids: List[str],
) -> Dict[str, Any]:
    from app.services.camera_service import _get_host_ip_for_stream_urls
    from app.services.runtime_config_service import (
        ensure_runtime_bin_ready,
        generate_runtime_inis,
        runtime_library_path_env,
    )

    workload_id = _workload_id(task_id, shard_index, device_ids)
    host = _get_host_ip_for_stream_urls()
    video_root = _get_video_root()
    log_dir = os.path.join(
        video_root, 'logs', f'task_{task_id}', _shard_log_suffix(shard_index, device_ids),
    )
    os.makedirs(log_dir, exist_ok=True)
    _stop_local_shard(workload_id)

    executor = _normalize_executor(task)
    if executor != 'cpp':
        raise RuntimeError('算法本机分片兜底目前仅支持 executor=cpp')

    runtime_bin = ensure_runtime_bin_ready(task)
    force_per_device = _normalize_task_type(task) == 'realtime'
    ini_paths = generate_runtime_inis(
        task,
        log_dir,
        prefer_cluster_model=False,
        write_local=True,
        only_device_ids=device_ids,
        force_per_device=force_per_device,
    )
    env = os.environ.copy()
    env.update(_build_shard_env(task, task_id, log_dir, host, device_ids, workload_id))
    lib_path = runtime_library_path_env()
    if lib_path:
        existing = (env.get('LD_LIBRARY_PATH') or '').strip()
        env['LD_LIBRARY_PATH'] = f'{lib_path}:{existing}' if existing else lib_path

    if len(ini_paths) == 1:
        cmd = [runtime_bin, ini_paths[0]]
    else:
        ini_args = ' '.join(f'"{p}"' for p in ini_paths)
        script = (
            'set -e; pids=(); '
            f'for f in {ini_args}; do "{runtime_bin}" "$f" & pids+=($!); done; '
            'trap \'kill "${pids[@]}" 2>/dev/null || true\' EXIT TERM INT; '
            'wait'
        )
        cmd = ['/bin/bash', '-lc', script]

    proc = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(runtime_bin) or video_root,
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
    logger.info(
        '算法分片本机部署成功 task_id=%s workload_id=%s host=%s devices=%s pid=%s',
        task_id, workload_id, host, device_ids, proc.pid,
    )
    return deployment


def deploy_shard_with_workload_id(
    task_id: int,
    task: AlgorithmTask,
    device_ids: List[str],
    workload_id: str,
    *,
    shard_index: Optional[int] = None,
    exclude_node_ids: Optional[List[int]] = None,
    spread_assigned_node_ids: Optional[List[int]] = None,
    fresh_allocate: bool = False,
) -> Dict[str, Any]:
    from app.utils import node_client

    if shard_index is None:
        if ':s' in workload_id:
            try:
                shard_index = int(workload_id.rsplit(':s', 1)[1])
            except (TypeError, ValueError):
                shard_index = 0
        else:
            shard_index = 0

    allocation = _allocate_algorithm_node(
        task,
        workload_id,
        exclude_node_ids=exclude_node_ids,
        spread_assigned_node_ids=spread_assigned_node_ids,
        fresh_allocate=fresh_allocate,
    )
    node_id = allocation['nodeId']
    host = allocation['host']
    gpu_ids = allocation.get('gpuIds')

    video_root_remote = os.getenv('NODE_REMOTE_VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    log_dir = os.path.join(
        video_root_remote,
        'logs',
        f'task_{task_id}',
        _shard_log_suffix(shard_index, device_ids),
    )

    executor = _normalize_executor(task)
    files = None
    if executor == 'cpp':
        _ensure_runtime_ready_on_node(int(node_id), host)
        command, files, work_dir = _deploy_cpp_shard_command_and_files(
            task, task_id, device_ids, log_dir,
        )
    else:
        command, work_dir = _deploy_python_shard_command(task, task_id)

    env = _build_shard_env(task, task_id, log_dir, host, device_ids, workload_id)
    result = node_client.deploy_workload(
        node_id=node_id,
        workload_type=WORKLOAD_TYPE_ALGORITHM,
        workload_id=workload_id,
        command=command,
        work_dir=work_dir,
        log_dir=log_dir,
        env=env,
        gpu_ids=gpu_ids,
        files=files,
    )

    logger.info(
        '算法分片远程部署成功 task_id=%s workload_id=%s node_id=%s host=%s devices=%s pid=%s',
        task_id, workload_id, node_id, host, device_ids, result.get('pid'),
    )
    return {
        'device_ids': device_ids,
        'node_id': node_id,
        'host': host,
        'workload_id': workload_id,
        'pid': result.get('pid'),
        'log_dir': log_dir,
        'local': False,
    }


def _deploy_shard_for_schedule(
    task_id: int,
    task: AlgorithmTask,
    shard_index: int,
    device_ids: List[str],
    total_shards: int,
    spread_assigned_node_ids: Optional[List[int]] = None,
    fresh_allocate: bool = False,
) -> Dict[str, Any]:
    if _should_deploy_shard_locally(task, shard_index, total_shards):
        return _deploy_shard_locally(task_id, task, shard_index, device_ids)
    try:
        deployment = deploy_shard_with_workload_id(
            task_id,
            task,
            device_ids,
            _workload_id(task_id, shard_index, device_ids),
            shard_index=shard_index,
            spread_assigned_node_ids=spread_assigned_node_ids,
            fresh_allocate=fresh_allocate,
        )
    except Exception as e:
        if not _remote_fallback_local_enabled():
            raise
        logger.warning(
            '算法远程分片部署失败，回退本机 task_id=%s shard=%s devices=%s: %s',
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


def deploy_sharded_algorithm_task(
    task_id: int,
    task: AlgorithmTask,
    *,
    fresh_allocate: bool = False,
) -> Tuple[bool, str, bool]:
    from app.services.algorithm_task_launcher_service import _ensure_task_models_on_cluster

    ok, sync_msg = _ensure_task_models_on_cluster(task)
    if not ok:
        return False, f'集群模型预同步失败: {sync_msg}', False

    device_ids = [d.id for d in (task.devices or []) if d.id]
    if not device_ids:
        return False, '任务未关联可用摄像头', False

    shards = _make_device_shards(device_ids, task)
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
                '算法分片部署失败 task_id=%s devices=%s: %s',
                task_id, shard_device_ids, e, exc_info=True,
            )
            failed.append(','.join(str(x) for x in shard_device_ids))

    if not deployments:
        return False, f'所有分片部署失败: {"; ".join(failed)}', False

    apply_task_service_fields_from_deployments(task, deployments)
    if getattr(task, 'runtime_control_port', None):
        task.service_port = int(task.runtime_control_port)
    else:
        task.service_port = 8000 + (int(task_id) % 1000)
    db.session.commit()

    if failed:
        return (
            True,
            f'部分分片已下发（{len(deployments)}/{len(shards)}），失败: {"; ".join(failed)}',
            False,
        )
    hosts = sorted({dep.get('host') for dep in deployments if dep.get('host')})
    return True, f'已按 {len(deployments)} 个分片下发到节点: {", ".join(hosts)}', False


def _shard_index_from_workload_id(workload_id: str) -> int:
    if ':s' in workload_id:
        try:
            return int(workload_id.rsplit(':s', 1)[1])
        except (TypeError, ValueError):
            pass
    return 0


def redeploy_existing_shard(
    task_id: int,
    task: AlgorithmTask,
    deployment: Dict[str, Any],
    *,
    exclude_node_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    device_ids = [str(x) for x in (deployment.get('device_ids') or [])]
    workload_id = str(deployment.get('workload_id') or '')
    if not device_ids or not workload_id:
        raise RuntimeError('分片部署缺少 device_ids/workload_id')

    if deployment.get('local'):
        return _deploy_shard_locally(
            task_id, task, _shard_index_from_workload_id(workload_id), device_ids,
        )

    old_node_id = deployment.get('node_id')
    if old_node_id:
        stop_remote_workload(int(old_node_id), workload_id)
    else:
        release_remote_workload_binding(workload_id)

    excludes = list(exclude_node_ids or [])
    if old_node_id is not None:
        excludes.append(int(old_node_id))
    return deploy_shard_with_workload_id(
        task_id,
        task,
        device_ids,
        workload_id,
        shard_index=_shard_index_from_workload_id(workload_id),
        exclude_node_ids=excludes or None,
        fresh_allocate=True,
    )


def migrate_unhealthy_algorithm_task(task_id: int) -> int:
    task = AlgorithmTask.query.get(task_id)
    if not task or not use_device_level_schedule(task):
        return 0

    deployments = parse_device_deployments(task)
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
    heartbeat_timeout = max(30, int(os.getenv('ALGORITHM_HEARTBEAT_FAILOVER_SECONDS', '90')))
    heartbeat_stale = _heartbeat_stale(task.service_last_heartbeat, heartbeat_timeout)

    updated = list(deployments)
    migrated = 0
    offline_indices: List[int] = []

    for index, dep in enumerate(deployments):
        if dep.get('local'):
            wid = str(dep.get('workload_id') or '')
            if wid and not _local_shard_process_alive(wid):
                offline_indices.append(index)
            continue
        node_id = dep.get('node_id')
        if node_id and not _is_compute_node_online(int(node_id)):
            offline_indices.append(index)

    if offline_indices:
        for index in offline_indices:
            dep = deployments[index]
            node_id = dep.get('node_id')
            if policy == 'node' and not dep.get('local'):
                logger.error(
                    '算法任务指定节点离线，无法自动迁移 task_id=%s node_id=%s',
                    task_id, node_id,
                )
                continue
            try:
                updated[index] = redeploy_existing_shard(
                    task_id, task, dep,
                    exclude_node_ids=[int(node_id)] if node_id else None,
                )
                migrated += 1
            except Exception as e:
                logger.error(
                    '算法分片迁移失败 task_id=%s workload=%s: %s',
                    task_id, dep.get('workload_id'), e, exc_info=True,
                )
    elif heartbeat_stale and policy != 'node':
        for index, dep in enumerate(deployments):
            try:
                updated[index] = redeploy_existing_shard(task_id, task, dep)
                migrated += 1
            except Exception as e:
                logger.error(
                    '算法心跳超时重部署失败 task_id=%s workload=%s: %s',
                    task_id, dep.get('workload_id'), e, exc_info=True,
                )

    if migrated:
        apply_task_service_fields_from_deployments(task, updated)
        db.session.commit()
        logger.info('算法任务分片迁移完成 task_id=%s migrated=%s', task_id, migrated)
    return migrated


def task_has_active_sharded_deployments(task: AlgorithmTask) -> bool:
    return bool(parse_device_deployments(task))
