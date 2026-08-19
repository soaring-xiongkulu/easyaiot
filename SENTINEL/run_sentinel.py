#!/usr/bin/env python3
"""
EasyAIoT Sentinel Agent - 集群节点观察者
- 组件探测 + 可调度性上报
- 工作负载执行（接收 NODE 控制面调度指令）
- HTTP 服务：端口 9100
"""
import logging
import os
import platform
import socket
import sys
import threading
import time
from typing import Any, Dict, List, Optional

_repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
_lib_root = os.path.join(_repo_root, '.scripts', 'lib')
for _p in (_repo_root, _lib_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import psutil
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger('easyaiot-sentinel')

NODE_ID = int(os.environ.get('NODE_ID', '0'))
AGENT_TOKEN = os.environ.get('AGENT_TOKEN', '')
CONTROL_PLANE_URL = os.environ.get(
    'CONTROL_PLANE_URL', 'http://localhost:48080/admin-api/node/agent'
).rstrip('/')
HEARTBEAT_INTERVAL = int(os.environ.get('HEARTBEAT_INTERVAL', '10'))
AGENT_VERSION = '2.0.0-sentinel'
AGENT_ENV_FILE = os.environ.get('AGENT_ENV_FILE', '')
BOOTSTRAP_WAIT_SECONDS = int(os.environ.get('BOOTSTRAP_WAIT_SECONDS', '180'))
BOOTSTRAP_RETRY_INTERVAL = int(os.environ.get('BOOTSTRAP_RETRY_INTERVAL', '3'))


def _detect_platform_agent() -> bool:
  """仅当 agent.env 显式设置 PLATFORM_AGENT=1 时才视为控制面宿主机 Agent。"""
  explicit = os.environ.get('PLATFORM_AGENT', '').strip().lower()
  return explicit in ('1', 'true', 'yes')


PLATFORM_AGENT = _detect_platform_agent()


def bootstrap_url() -> str:
    base = CONTROL_PLANE_URL.rstrip('/')
    if base.endswith('/agent'):
        base = base[:-len('/agent')]
    return f'{base}/platform-agent-bootstrap'


def persist_credentials() -> None:
    env_path = AGENT_ENV_FILE
    if not env_path:
        for candidate in (
            '/opt/easyaiot/sentinel-agent/agent.env',
            '/opt/easyaiot/node-agent/agent.env',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent.env'),
        ):
            if os.path.isfile(candidate):
                env_path = candidate
                break
    if not env_path or not os.path.isfile(env_path):
        return
    try:
        with open(env_path, encoding='utf-8') as f:
            lines = f.readlines()
        with open(env_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('NODE_ID='):
                    f.write(f'NODE_ID={NODE_ID}\n')
                elif line.startswith('AGENT_TOKEN='):
                    f.write(f'AGENT_TOKEN={AGENT_TOKEN}\n')
                else:
                    f.write(line)
        logger.info('已同步凭据至 %s', env_path)
    except OSError as e:
        logger.debug('无法持久化 agent.env: %s', e)


def try_refresh_credentials(*, allow_node_id_change: bool = False) -> bool:
    global NODE_ID, AGENT_TOKEN
    url = bootstrap_url()
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.debug('bootstrap 请求失败 HTTP %s: %s', resp.status_code, url)
            return False
        data = resp.json()
        if data.get('code') != 0:
            logger.debug('bootstrap 返回错误: %s', data.get('msg', data))
            return False
        payload = data.get('data') or data
        new_id = payload.get('nodeId')
        new_token = payload.get('agentToken')
        if not new_id or not new_token:
            return False
        new_id = int(new_id)
        can_change_id = allow_node_id_change or PLATFORM_AGENT
        if NODE_ID and NODE_ID != new_id and not can_change_id:
            logger.debug('bootstrap nodeId=%s 与当前 NODE_ID=%s 不一致，跳过刷新', new_id, NODE_ID)
            return False
        if new_token == AGENT_TOKEN and new_id == NODE_ID:
            return True
        if NODE_ID and NODE_ID != new_id:
            logger.info('bootstrap 同步 nodeId %s -> %s', NODE_ID, new_id)
        NODE_ID = new_id
        AGENT_TOKEN = new_token
        logger.info('已从 bootstrap 刷新凭据 nodeId=%s', NODE_ID)
        persist_credentials()
        return True
    except Exception as e:
        logger.debug('bootstrap 刷新失败: %s', e)
    return False


def is_credential_error(msg: str) -> bool:
    if not msg:
        return False
    text = str(msg)
    if '节点不存在' in text:
        return True
    if '令牌' in text:
        return True
    lowered = text.lower()
    return 'token' in lowered and 'invalid' in lowered


def wait_for_platform_credentials() -> None:
    """控制面 Agent 启动时等待 iot-node bootstrap 就绪并同步凭据。"""
    if not PLATFORM_AGENT:
        return
    deadline = time.time() + BOOTSTRAP_WAIT_SECONDS
    logger.info('控制面 Agent 等待 bootstrap 就绪（最长 %ss）...', BOOTSTRAP_WAIT_SECONDS)
    while time.time() < deadline:
        if try_refresh_credentials(allow_node_id_change=True):
            return
        time.sleep(BOOTSTRAP_RETRY_INTERVAL)
    logger.warning('bootstrap 等待超时，将使用本地 agent.env 继续尝试注册')


def _parse_smi_number(raw: str) -> float:
    """nvidia-smi 在 vGPU/GRID 上常返回 [N/A]，按 0 处理。"""
    text = (raw or '').strip()
    if not text or text.upper() in ('[N/A]', 'N/A', 'NA', 'NONE'):
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def get_gpu_info() -> List[Dict[str, Any]]:
    """采集 GPU 列表。GRID/vGPU（如 RTX6000-4Q）部分字段可能为 [N/A]，仍应上报卡数与可用显存。"""
    gpus: List[Dict[str, Any]] = []
    try:
        import subprocess
        queries = [
            ['nvidia-smi', '--query-gpu=index,name,utilization.gpu,memory.used,memory.total',
             '--format=csv,noheader,nounits'],
            # 部分 vGPU 不支持 utilization，退化为仅索引/名称/显存
            ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total',
             '--format=csv,noheader,nounits'],
        ]
        for cmd in queries:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if result.returncode != 0:
                continue
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    gpus.append({
                        'id': int(_parse_smi_number(parts[0])),
                        'name': parts[1],
                        'util': _parse_smi_number(parts[2]),
                        'mem_used_mb': _parse_smi_number(parts[3]),
                        'mem_total_mb': _parse_smi_number(parts[4]),
                    })
                elif len(parts) >= 4:
                    gpus.append({
                        'id': int(_parse_smi_number(parts[0])),
                        'name': parts[1],
                        'util': 0.0,
                        'mem_used_mb': _parse_smi_number(parts[2]),
                        'mem_total_mb': _parse_smi_number(parts[3]),
                    })
            if gpus:
                break
        if not gpus:
            # 最后兜底：至少上报卡名（显存可能为 0，概览仍显示卡数量）
            listed = subprocess.run(
                ['nvidia-smi', '-L'], capture_output=True, text=True, timeout=8,
            )
            if listed.returncode == 0:
                for idx, line in enumerate(listed.stdout.strip().split('\n')):
                    line = line.strip()
                    if not line:
                        continue
                    # GPU 0: GRID RTX6000-4Q (UUID: ...)
                    name = line
                    if ':' in line:
                        name = line.split(':', 1)[1].strip()
                    if '(' in name:
                        name = name.split('(', 1)[0].strip()
                    gpus.append({
                        'id': idx,
                        'name': name or f'GPU {idx}',
                        'util': 0.0,
                        'mem_used_mb': 0.0,
                        'mem_total_mb': 0.0,
                    })
        if not gpus:
            logger.debug('nvidia-smi 可用但未解析到 GPU 行')
    except FileNotFoundError:
        logger.debug('未安装 nvidia-smi，跳过 GPU 采集')
    except Exception as e:
        logger.debug('GPU 采集跳过: %s', e)
    return gpus


def collect_metrics(level: Optional[str] = None) -> Dict[str, Any]:
    from workload_manager import WorkloadManager
    # 使用模块级 manager（agent_server 中创建）
    try:
        from agent_server import manager as workload_mgr
        active_tasks = workload_mgr.active_count()
        workloads = workload_mgr.list_workloads()
    except Exception:
        active_tasks = 0
        workloads = []

    # 整机平均利用率 0–100%，与系统监视器一致（勿对各核求和，否则会随逻辑核数虚高）
    cpu = round(psutil.cpu_percent(interval=0.5), 2)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cluster_mode = False
    nfs_mount_root = ''
    nfs_mount_ready = False
    metrics = {
        'cpuPercent': cpu,
        'memPercent': round(mem.percent, 2),
        'memUsedBytes': mem.used,
        'memTotalBytes': mem.total,
        'diskPercent': round(disk.percent, 2),
        'diskUsedBytes': disk.used,
        'diskTotalBytes': disk.total,
        'activeTasks': active_tasks,
        'bandwidthMbps': 0,
        'gpuInfo': get_gpu_info(),
        'workloads': workloads,
    }
    try:
        from cluster_storage import get_mount_root, is_cluster_mode, verify_nfs_mount
        cluster_mode = is_cluster_mode()
        nfs_mount_root = get_mount_root()
        nfs_mount_ready = verify_nfs_mount()
        metrics['clusterMode'] = cluster_mode
        metrics['nfsMountRoot'] = nfs_mount_root
        metrics['nfsMountReady'] = nfs_mount_ready
        # 兼容旧控制面字段名
        metrics['cephMountRoot'] = nfs_mount_root
        metrics['cephMountReady'] = nfs_mount_ready
    except ImportError:
        pass
    try:
        from sentinel.orchestrator import run_sentinel_probe
        from sentinel.base import ProbeLevel
        probe_level = ProbeLevel.L0
        raw = (level or os.environ.get('SENTINEL_PROBE_LEVEL') or 'L0').upper()
        if raw == 'L1':
            probe_level = ProbeLevel.L1
        elif raw == 'L2':
            probe_level = ProbeLevel.L2
        metrics['sentinel'] = run_sentinel_probe(
            node_id=NODE_ID,
            gpu_info=metrics.get('gpuInfo') or [],
            cluster_mode=cluster_mode,
            nfs_mount_ready=nfs_mount_ready,
            level=probe_level,
        )
    except Exception as e:
        logger.debug('Sentinel 探测跳过: %s', e)
    return metrics


def post_json(path: str, payload: Dict[str, Any], *, allow_refresh: bool = True) -> tuple:
    """返回 (成功?, 错误文案)。错误文案用于识别主机名/容量冲突，避免无效重注册。"""
    url = f'{CONTROL_PLANE_URL}{path}'
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                return True, ''
            msg = str(data.get('msg', data))
            if allow_refresh and is_credential_error(msg):
                node_missing = '节点不存在' in msg
                if try_refresh_credentials(
                    allow_node_id_change=node_missing or PLATFORM_AGENT,
                ):
                    payload = {**payload, 'nodeId': NODE_ID, 'agentToken': AGENT_TOKEN}
                    return post_json(path, payload, allow_refresh=False)
            logger.warning('请求失败 %s: %s', url, msg)
            return False, msg
        logger.warning('HTTP %s: %s', resp.status_code, url)
        return False, f'HTTP {resp.status_code}'
    except Exception as e:
        logger.warning('请求异常 %s: %s', url, e)
        return False, str(e)


def is_identity_conflict(msg: str) -> bool:
    if not msg:
        return False
    return (
        '主机名与节点已绑定主机不一致' in msg
        or '内存/磁盘容量与已绑定指纹不一致' in msg
        or 'NODE_ID' in msg and '多个 Agent' in msg
    )


def register() -> bool:
    payload = {
        'nodeId': NODE_ID,
        'agentToken': AGENT_TOKEN,
        'hostname': socket.gethostname(),
        'osInfo': f'{platform.system()} {platform.release()}',
        'agentVersion': AGENT_VERSION,
    }
    logger.info('注册节点 nodeId=%s -> %s', NODE_ID, CONTROL_PLANE_URL)
    ok, _ = post_json('/register', payload)
    return ok


def heartbeat(level: Optional[str] = None) -> tuple:
    metrics = collect_metrics(level)
    sentinel = metrics.get('sentinel') or {}
    try:
        from sentinel.remediator import observe_scan, snapshot as rem_snapshot
        observe_scan(sentinel)
        sentinel['remediation'] = rem_snapshot()
        metrics['sentinel'] = sentinel
    except Exception as e:
        logger.debug('Sentinel 打标跳过: %s', e)
    payload = {
        'nodeId': NODE_ID,
        'agentToken': AGENT_TOKEN,
        # 与 register 一致上报主机名，控制面可拦截多 Agent 共用同一 NODE_ID 的冲突心跳
        'hostname': socket.gethostname(),
        **metrics,
    }
    ok, msg = post_json('/heartbeat', payload)
    return ok, msg, metrics


def heartbeat_loop():
    # 注册失败也不阻塞：hostname 换绑靠心跳（带容量指纹）更可靠，避免卡死写不进 metric
    if register():
        logger.info('注册成功，开始心跳 (interval=%ss) 经网关上报 NODE', HEARTBEAT_INTERVAL)
    else:
        logger.warning('注册未成功，仍将尝试心跳 (interval=%ss)', HEARTBEAT_INTERVAL)
    last_l1 = 0.0
    l1_interval = int(os.environ.get('SENTINEL_L1_INTERVAL', '300'))
    auto_remediate = os.environ.get('SENTINEL_AUTO_REMEDIATE', 'true').strip().lower() in ('1', 'true', 'yes')
    first = True
    while True:
        now = time.time()
        use_l1 = first or (now - last_l1 >= l1_interval)
        level = 'L1' if use_l1 else 'L0'
        ok, msg, metrics = heartbeat(level)
        first = False
        if use_l1 and ok:
            last_l1 = now
            logger.info('Sentinel %s 扫描已经网关上报 NODE', level)
        if auto_remediate:
            try:
                from sentinel.remediator import maybe_start_heal
                sentinel = (metrics or {}).get('sentinel') or {}
                missing = sentinel.get('missingExpectedComponents') or []
                unhealthy = [
                    item.get('componentId')
                    for item in (sentinel.get('components') or [])
                    if isinstance(item, dict)
                    and item.get('expected')
                    and item.get('state') in ('unavailable', 'unknown', 'degraded')
                ]
                maybe_start_heal(list(dict.fromkeys([*(missing or []), *unhealthy])))
            except Exception as e:
                logger.debug('自愈合跳过: %s', e)
        if not ok:
            if is_identity_conflict(msg):
                logger.warning('心跳因身份/容量冲突被拒，跳过重新注册（请检查是否多个 Agent 共用 NODE_ID）: %s', msg)
            else:
                logger.warning('心跳失败，尝试重新注册...')
                register()
        time.sleep(HEARTBEAT_INTERVAL)


def _wait_for_control_plane() -> None:
    """iot-node 重启后再次尝试 bootstrap，避免使用过期凭据上报。"""
    if not PLATFORM_AGENT:
        return
    deadline = time.time() + min(BOOTSTRAP_WAIT_SECONDS, 60)
    url = bootstrap_url()
    while time.time() < deadline:
        if try_refresh_credentials(allow_node_id_change=True):
            return
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200 and (resp.json() or {}).get('code') == 0:
                try_refresh_credentials(allow_node_id_change=True)
                return
        except Exception:
            pass
        time.sleep(BOOTSTRAP_RETRY_INTERVAL)


def main():
    wait_for_platform_credentials()
    _wait_for_control_plane()
    if not NODE_ID or not AGENT_TOKEN:
        logger.error('请设置环境变量 NODE_ID 和 AGENT_TOKEN')
        sys.exit(1)

    from agent_server import run_server  # noqa: F401 - 先加载 HTTP 服务与 workload manager

    threading.Thread(target=heartbeat_loop, daemon=True).start()
    run_server()


if __name__ == '__main__':
    main()
