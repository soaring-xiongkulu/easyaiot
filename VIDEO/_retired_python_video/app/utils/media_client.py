"""
iot-node 媒体节点池客户端：设备 SRS/ZLM 流绑定与 URL 生成。
"""
import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

from app.utils.node_client import JAVA_BACKEND_URL

MEDIA_API_BASE = f'{JAVA_BACKEND_URL}/admin-api/node/media'
REQUEST_TIMEOUT = 30


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


def is_media_pool_enabled() -> bool:
    return os.getenv('MEDIA_NODE_POOL_ENABLED', 'false').lower() in ('1', 'true', 'yes')


def allocate_device_media(
    device_id: str,
    *,
    need_srs_live: bool = True,
    need_srs_ai: bool = True,
    need_zlm: bool = False,
    region: Optional[str] = None,
    http_play_host: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {
        'deviceId': device_id,
        'needSrsLive': need_srs_live,
        'needSrsAi': need_srs_ai,
        'needZlm': need_zlm,
        'region': region or os.getenv('MEDIA_NODE_REGION'),
        'httpPlayHost': http_play_host or os.getenv('MEDIA_HTTP_PLAY_HOST'),
    }
    url = f'{MEDIA_API_BASE}/allocate'
    resp = requests.post(url, json=payload, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(data.get('msg') or f'媒体绑定失败: {url}')
    return data.get('data') or {}


def get_device_media_binding(device_id: str) -> Dict[str, Any]:
    url = f'{MEDIA_API_BASE}/binding'
    resp = requests.get(url, params={'deviceId': device_id}, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(data.get('msg') or f'查询媒体绑定失败: {url}')
    return data.get('data') or {}


def stream_urls_from_binding(binding: Dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        binding.get('rtmpStream') or '',
        binding.get('httpStream') or '',
        binding.get('aiRtmpStream') or '',
        binding.get('aiHttpStream') or '',
    )
