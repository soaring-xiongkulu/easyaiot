"""
iot-node 控制面客户端：节点调度与工作负载远程部署。
"""
import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 90


def _is_mini_deploy_profile() -> bool:
    profile = os.getenv('EASYAIOT_DEPLOY_PROFILE', '').strip().lower()
    return profile in ('mini', '1', 'minimal', '4g')


def resolve_java_backend_url() -> str:
    explicit = (os.getenv('JAVA_BACKEND_URL') or '').strip()
    if explicit:
        return explicit.rstrip('/')
    gateway = (os.getenv('GATEWAY_URL') or '').strip()
    if gateway:
        return gateway.rstrip('/')
    if _is_mini_deploy_profile():
        return 'http://localhost:48099'
    return 'http://localhost:48080'


JAVA_BACKEND_URL = resolve_java_backend_url()
NODE_API_BASE = f'{JAVA_BACKEND_URL}/admin-api/node'


def _headers() -> Dict[str, str]:
    headers = {'Content-Type': 'application/json'}
    token = os.getenv('JWT_TOKEN') or ''
    if not token:
        try:
            from flask import has_request_context, request as flask_request
            if has_request_context():
                token = flask_request.headers.get('X-Authorization', '').replace('Bearer ', '')
        except Exception:
            pass
    if token:
        headers['X-Authorization'] = f'Bearer {token}'
    return headers


def _post(path: str, payload: Dict[str, Any], *, timeout: int = REQUEST_TIMEOUT) -> Any:
    url = f'{NODE_API_BASE}{path}'
    resp = requests.post(url, json=payload, headers=_headers(), timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        msg = data.get('msg') or data.get('message') or f'节点 API 失败: {url}'
        if msg == '系统异常':
            logger.error(
                '节点 API 返回系统异常（详见 iot-node 日志）url=%s payload_keys=%s resp=%s',
                url, list(payload.keys()), data,
            )
        raise RuntimeError(msg)
    result = data.get('data')
    return result if result is not None else {}


def _get(path: str, params: Dict[str, Any]) -> Any:
    url = f'{NODE_API_BASE}{path}'
    resp = requests.get(url, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(data.get('msg') or f'节点 API 失败: {url}')
    result = data.get('data')
    return result if result is not None else {}


def is_remote_deploy_enabled() -> bool:
    raw = (os.getenv('NODE_REMOTE_DEPLOY') or '').strip().lower()
    if raw:
        return raw in ('1', 'true', 'yes')
    # mini 形态不部署 iot-node，默认本机运行工作负载
    if _is_mini_deploy_profile():
        return False
    return True


def _is_cluster_mode() -> bool:
    try:
        from cluster_storage import is_cluster_mode
        return is_cluster_mode()
    except ImportError:
        return os.getenv('CLUSTER_MODE', '').strip().lower() in ('1', 'true', 'yes', 'on')


def _node_nfs_mount_ready(node: Dict[str, Any]) -> bool:
    if node.get('isPlatform') or node.get('is_platform'):
        return True
    tags = node.get('tags') or {}
    ready = str(tags.get('nfs_mount_ready') or tags.get('ceph_mount_ready') or '').strip().lower()
    return ready in ('true', '1', 'yes', 'on')


def _node_ceph_mount_ready(node: Dict[str, Any]) -> bool:
    """兼容旧调用名。"""
    return _node_nfs_mount_ready(node)


def allocate_node(
    workload_type: str,
    workload_id: str,
    capabilities: Optional[List[str]] = None,
    gpu_count: int = 0,
    prefer_gpu: Optional[bool] = None,
    region: Optional[str] = None,
    sticky: bool = True,
    target_node_id: Optional[int] = None,
    exclude_node_ids: Optional[List[int]] = None,
    require_nfs_mount: Optional[bool] = None,
    require_ceph_mount: Optional[bool] = None,
    require_schedulable: Optional[bool] = None,
) -> Dict[str, Any]:
    if require_nfs_mount is None:
        require_nfs_mount = require_ceph_mount
    if require_nfs_mount is None:
        require_nfs_mount = _is_cluster_mode()
    if require_schedulable is None:
        require_schedulable = _is_cluster_mode()

    if target_node_id:
        node = get_node(target_node_id)
        if require_nfs_mount and not _node_nfs_mount_ready(node):
            raise RuntimeError(
                f'指定节点 #{target_node_id} NFS 未挂载就绪，请先在节点管理部署存储客户端'
            )
        return {
            'nodeId': target_node_id,
            'host': node.get('host'),
            'agentPort': node.get('agentPort', 9100),
            'gpuIds': _format_gpu_ids(node.get('maxGpuCount', 0)),
            'bindingId': None,
        }

    requirements: Dict[str, Any] = {
        'capabilities': capabilities or ['algorithm_realtime'],
        'gpuCount': gpu_count,
        'region': region,
    }
    if prefer_gpu is not None:
        requirements['preferGpu'] = prefer_gpu
    if exclude_node_ids:
        requirements['excludeNodeIds'] = exclude_node_ids
    if require_nfs_mount:
        requirements['requireNfsMount'] = True
        requirements['requireCephMount'] = True
    if require_schedulable:
        requirements['requireSchedulable'] = True

    payload = {
        'workloadType': workload_type,
        'workloadId': workload_id,
        'sticky': sticky,
        'requirements': requirements,
    }
    return _post('/scheduler/allocate', payload)


def release_workload(workload_type: str, workload_id: str) -> None:
    url = f'{NODE_API_BASE}/scheduler/release'
    params = {
        'workloadType': workload_type,
        'workloadId': workload_id,
    }
    resp = requests.post(url, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(data.get('msg') or '释放节点绑定失败')


def get_node(node_id: int) -> Dict[str, Any]:
    return _get('/get', {'id': node_id})


def camera_access(node_id: int, operation: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    """通过 iot-node 调用目标节点的摄像头接入代理。"""
    allowed = {'discover', 'scan-segment', 'probe-onvif', 'probe-stream', 'nvr-channels'}
    op = (operation or '').strip().lower()
    if op not in allowed:
        raise ValueError(f'不支持的摄像头接入操作: {operation}')
    return _post(f'/camera-access/{op}', {
        'nodeId': int(node_id),
        'payload': payload or {},
    }, timeout=360 if op == 'scan-segment' else 120)


def get_platform_node_id() -> Optional[int]:
    """获取控制面节点 ID，用于调度时排除或降权本机。"""
    try:
        data = _get('/platform-agent-bootstrap', {})
        node_id = data.get('nodeId')
        return int(node_id) if node_id is not None else None
    except Exception as e:
        logger.debug('获取控制面节点 ID 失败: %s', e)
        return None


def resolve_platform_host() -> str:
    """从 iot-node 自动探测控制面宿主机 IP（远程 worker 心跳 / DB 回连等）。"""
    try:
        data = _get('/platform-host', {})
        host = (data.get('host') or '').strip()
        if host and host not in ('127.0.0.1', 'localhost'):
            return host
    except Exception as e:
        logger.debug('platform-host 探测失败: %s', e)
    node_id = get_platform_node_id()
    if node_id:
        try:
            node = get_node(node_id)
            host = (node.get('host') or '').strip()
            if host and host not in ('127.0.0.1', 'localhost'):
                return host
        except Exception as e:
            logger.debug('读取平台节点 host 失败: %s', e)
    return ''


def deploy_media_stack(node_id: int, stack_type: str = 'srs_live') -> Dict[str, Any]:
    """通过 Agent 在目标节点部署 SRS/ZLM 媒体栈。"""
    payload = {
        'nodeId': node_id,
        'stackType': stack_type,
    }
    return _post('/media/deploy-stack', payload)


def deploy_workload(
    node_id: int,
    workload_type: str,
    workload_id: str,
    command: List[str],
    work_dir: str,
    log_dir: str,
    env: Dict[str, str],
    gpu_ids: Optional[str] = None,
    files: Optional[List[Dict[str, str]]] = None,
    runtime: Optional[str] = None,
    image: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {
        'nodeId': node_id,
        'workloadType': workload_type,
        'workloadId': workload_id,
        'command': command or [],
        'workDir': work_dir,
        'logDir': log_dir,
        'gpuIds': gpu_ids,
        'env': env,
    }
    if files:
        payload['files'] = files
    if runtime:
        payload['runtime'] = runtime
    if image:
        payload['image'] = image
    return _post('/workload/deploy', payload)


def stop_workload(node_id: int, workload_type: str, workload_id: str) -> None:
    url = f'{NODE_API_BASE}/workload/stop'
    params = {
        'nodeId': node_id,
        'workloadType': workload_type,
        'workloadId': workload_id,
    }
    resp = requests.post(url, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(data.get('msg') or '停止远程工作负载失败')


def check_runtime_cpp_ready(node_id: int) -> Dict[str, Any]:
    """SSH 检测目标节点是否已安装 RUNTIME(C++) 二进制。"""
    url = f'{NODE_API_BASE}/workload-bundle/runtime-cpp/check-ssh'
    resp = requests.post(url, params={'nodeId': node_id}, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(data.get('msg') or f'检测节点 RUNTIME 失败: node_id={node_id}')
    return data.get('data') or {}


def _format_gpu_ids(max_gpu_count: int) -> Optional[str]:
    if not max_gpu_count or max_gpu_count <= 0:
        return None
    return ','.join(str(i) for i in range(max_gpu_count))
