"""
Nacos 服务发现（VIDEO 模块）。
"""
from __future__ import annotations

import logging
import os
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_nacos_client = None


def get_nacos_client():
    global _nacos_client
    if _nacos_client is not None:
        return _nacos_client
    try:
        from nacos import NacosClient

        _nacos_client = NacosClient(
            server_addresses=os.getenv('NACOS_SERVER', 'localhost:8848'),
            namespace=os.getenv('NACOS_NAMESPACE', ''),
            username=os.getenv('NACOS_USERNAME', 'nacos'),
            password=os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754'),
        )
        return _nacos_client
    except Exception as exc:
        logger.warning('Nacos 客户端初始化失败: %s', exc)
        return None


def _normalize_instances(raw: Any) -> List[Dict[str, Any]]:
    if not raw:
        return []
    if isinstance(raw, dict):
        for key in ('hosts', 'instances', 'data', 'list'):
            if key in raw and isinstance(raw[key], list):
                raw = raw[key]
                break
        else:
            if any(k in raw for k in ('ip', 'IP', 'port', 'PORT')):
                raw = [raw]
            else:
                return []
    if not isinstance(raw, list):
        return []

    out: List[Dict[str, Any]] = []
    for inst in raw:
        if not isinstance(inst, dict):
            continue
        ip = str(inst.get('ip') or inst.get('IP') or '').strip()
        port = inst.get('port') or inst.get('PORT') or 8089
        if not ip:
            continue
        try:
            port = int(port)
        except (TypeError, ValueError):
            port = 8089
        healthy = inst.get('healthy')
        if healthy is False:
            continue
        out.append({'ip': ip, 'port': port})
    return out


def get_service_instances(service_name: str, *, healthy_only: bool = True) -> List[Dict[str, Any]]:
    client = get_nacos_client()
    if not client:
        return []
    try:
        raw = client.list_naming_instance(service_name=service_name, healthy_only=healthy_only)
        return _normalize_instances(raw)
    except Exception as exc:
        logger.warning('Nacos 查询 %s 失败: %s', service_name, exc)
        return []


def post_service_name() -> str:
    return (os.getenv('POST_NACOS_SERVICE') or 'easyaiot-post').strip()


def list_post_instances() -> List[Dict[str, Any]]:
    return get_service_instances(post_service_name(), healthy_only=True)


def pick_post_base_urls() -> List[str]:
    explicit = (os.getenv('POST_BASE_URL') or '').strip().rstrip('/')
    if explicit:
        return [explicit]
    urls = []
    for inst in list_post_instances():
        urls.append(f"http://{inst['ip']}:{inst['port']}")
    return urls


def pick_post_base_url() -> Optional[str]:
    urls = pick_post_base_urls()
    if not urls:
        return None
    return random.choice(urls)
