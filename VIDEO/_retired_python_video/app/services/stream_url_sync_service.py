"""
设备流地址同步：集群推流/媒体节点池场景下，保证 rtmp_stream / http_stream 与真实推流/播放节点一致。
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from models import Device, StreamForwardTask, db

logger = logging.getLogger(__name__)


def _tag_int(tags: Optional[Dict[str, Any]], key: str, default: int) -> int:
    if not tags:
        return default
    raw = tags.get(key)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def build_stream_urls_for_host(
    host: str,
    device_id: str,
    *,
    tags: Optional[Dict[str, Any]] = None,
    http_play_host: Optional[str] = None,
) -> Tuple[str, str, str, str]:
    """根据 SRS 节点 host/tags 生成 live/ai 流地址。"""
    rtmp_port = _tag_int(tags, 'srs_rtmp_port', 1935)
    http_port = _tag_int(tags, 'srs_http_port', 8080)
    play_host = (http_play_host or os.getenv('MEDIA_HTTP_PLAY_HOST') or '').strip() or host
    rtmp_stream = f'rtmp://{host}:{rtmp_port}/live/{device_id}'
    http_stream = f'http://{play_host}:{http_port}/live/{device_id}.flv'
    ai_rtmp_stream = f'rtmp://{host}:{rtmp_port}/ai/{device_id}'
    ai_http_stream = f'http://{play_host}:{http_port}/ai/{device_id}.flv'
    return rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream


def _find_stream_forward_deployment(device_id: str) -> Optional[Dict[str, Any]]:
    tasks = (
        StreamForwardTask.query.filter(StreamForwardTask.is_enabled.is_(True))
        .all()
    )
    for task in tasks:
        deployments = task._parse_device_deployments() if hasattr(task, '_parse_device_deployments') else []
        for dep in deployments or []:
            device_ids = dep.get('device_ids') or []
            if device_id in device_ids and dep.get('host'):
                return dep
        if not deployments and task.service_server_ip:
            task_device_ids = {d.id for d in (task.devices or []) if d.id}
            if device_id in task_device_ids:
                hosts = [h.strip() for h in str(task.service_server_ip).split(',') if h.strip()]
                if hosts:
                    return {
                        'device_ids': list(task_device_ids),
                        'host': hosts[0],
                        'node_id': task.node_id,
                    }
    return None


def resolve_device_stream_urls(device: Device) -> Tuple[str, str, str, str]:
    """解析设备当前应使用的流地址（只读，不写库）。"""
    device_id = device.id
    try:
        from app.utils.media_client import (
            get_device_media_binding,
            is_media_pool_enabled,
            stream_urls_from_binding,
        )
        if is_media_pool_enabled():
            binding = get_device_media_binding(device_id)
            if binding:
                return stream_urls_from_binding(binding)
    except Exception as e:
        logger.debug('媒体绑定查询失败 device_id=%s: %s', device_id, e)

    deployment = _find_stream_forward_deployment(device_id)
    if deployment:
        host = str(deployment.get('host') or '').strip()
        node_id = deployment.get('node_id')
        tags = None
        if node_id:
            try:
                from app.utils import node_client
                node = node_client.get_node(int(node_id))
                tags = node.get('tags')
                if not host:
                    host = str(node.get('host') or '').strip()
            except Exception as e:
                logger.debug('查询部署节点失败 node_id=%s: %s', node_id, e)
        if host:
            return build_stream_urls_for_host(host, device_id, tags=tags)

    return (
        device.rtmp_stream or '',
        device.http_stream or '',
        device.ai_rtmp_stream or '',
        device.ai_http_stream or '',
    )


def sync_device_stream_urls(
    device_ids: Iterable[str],
    *,
    deploy_host: str,
    node_id: Optional[int] = None,
    commit: bool = True,
) -> int:
    """将设备流地址同步到指定推流/媒体节点（写库）。"""
    host = (deploy_host or '').strip()
    if not host:
        return 0

    tags = None
    if node_id:
        try:
            from app.utils import node_client
            node = node_client.get_node(int(node_id))
            tags = node.get('tags')
        except Exception as e:
            logger.warning('同步流地址时查询节点失败 node_id=%s: %s', node_id, e)

    updated = 0
    for device_id in device_ids:
        device = Device.query.get(device_id)
        if not device:
            continue
        try:
            from app.utils.media_client import (
                allocate_device_media,
                is_media_pool_enabled,
                stream_urls_from_binding,
            )
            if is_media_pool_enabled():
                binding = allocate_device_media(device_id)
                rtmp, http, ai_rtmp, ai_http = stream_urls_from_binding(binding)
            else:
                rtmp, http, ai_rtmp, ai_http = build_stream_urls_for_host(
                    host, device_id, tags=tags,
                )
        except Exception as e:
            logger.warning(
                '设备流地址同步失败 device_id=%s host=%s，回退节点默认地址: %s',
                device_id, host, e,
            )
            rtmp, http, ai_rtmp, ai_http = build_stream_urls_for_host(host, device_id, tags=tags)

        changed = False
        if rtmp and device.rtmp_stream != rtmp:
            device.rtmp_stream = rtmp
            changed = True
        if http and device.http_stream != http:
            device.http_stream = http
            changed = True
        if ai_rtmp and (device.ai_rtmp_stream or '') != ai_rtmp:
            device.ai_rtmp_stream = ai_rtmp
            changed = True
        if ai_http and (device.ai_http_stream or '') != ai_http:
            device.ai_http_stream = ai_http
            changed = True
        if changed:
            updated += 1
            logger.info(
                '已同步设备流地址 device_id=%s host=%s http=%s',
                device_id, host, http,
            )

    if updated and commit:
        db.session.commit()
    return updated


def sync_devices_for_deployment(deployment: Dict[str, Any], *, commit: bool = True) -> int:
    device_ids = list(deployment.get('device_ids') or [])
    if not device_ids:
        return 0
    return sync_device_stream_urls(
        device_ids,
        deploy_host=str(deployment.get('host') or ''),
        node_id=deployment.get('node_id'),
        commit=commit,
    )
