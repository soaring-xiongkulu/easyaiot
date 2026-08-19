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


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f'{NODE_API_BASE}{path}'
    resp = requests.post(url, json=payload, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        msg = data.get('msg') or data.get('message') or f'节点 API 失败: {url}'
        raise RuntimeError(msg)
    return data.get('data') or {}


def _get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f'{NODE_API_BASE}{path}'
    resp = requests.get(url, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(data.get('msg') or f'节点 API 失败: {url}')
    return data.get('data') or {}


def is_remote_deploy_enabled() -> bool:
    raw = (os.getenv('NODE_REMOTE_DEPLOY') or '').strip().lower()
    if raw:
        return raw in ('1', 'true', 'yes')
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
    """调度分配节点。指定 target_node_id 时直接返回该节点（不经过评分）。"""
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
        'capabilities': capabilities or ['ai_inference'],
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


def get_node(node_id: int) -> Dict[str, Any]:
    return _get('/get', {'id': node_id})


def deploy_workload(
    node_id: int,
    workload_type: str,
    workload_id: str,
    command: list,
    work_dir: str,
    log_dir: str,
    env: Dict[str, str],
    gpu_ids: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {
        'nodeId': node_id,
        'workloadType': workload_type,
        'workloadId': workload_id,
        'command': command,
        'workDir': work_dir,
        'logDir': log_dir,
        'gpuIds': gpu_ids,
        'env': env,
    }
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


def release_binding(workload_type: str, workload_id: str) -> None:
    try:
        url = f'{NODE_API_BASE}/scheduler/release'
        resp = requests.post(
            url,
            params={'workloadType': workload_type, 'workloadId': workload_id},
            headers=_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get('code') == 0:
            return
    except Exception as e:
        logger.warning('释放节点绑定失败: %s', e)


def _format_gpu_ids(max_gpu_count: int) -> Optional[str]:
    if not max_gpu_count or max_gpu_count <= 0:
        return None
    return ','.join(str(i) for i in range(max_gpu_count))
