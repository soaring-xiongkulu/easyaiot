"""Nacos 服务发现（与 AI/app/utils/nacos_service_discovery 对齐，供 POST 探活/模板推送）。"""
from __future__ import annotations

import logging
import os
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_nacos_client = None


def get_nacos_client():
    global _nacos_client
    if _nacos_client is not None:
        return _nacos_client
    if not (os.getenv('NACOS_SERVER') or '').strip():
        return None
    try:
        from nacos import NacosClient
        _nacos_client = NacosClient(
            server_addresses=os.getenv('NACOS_SERVER', 'localhost:8848'),
            namespace=os.getenv('NACOS_NAMESPACE', ''),
            username=os.getenv('NACOS_USERNAME', 'nacos'),
            password=os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754'),
        )
        return _nacos_client
    except Exception as e:
        logger.warning('Nacos 客户端不可用: %s', e)
        return None


def get_service_instances(service_name: str, healthy_only: bool = True) -> List[Dict]:
    client = get_nacos_client()
    if not client:
        return []
    try:
        instances = client.list_naming_instance(
            service_name=service_name,
            healthy_only=healthy_only,
        )
    except Exception as e:
        logger.warning('list_naming_instance failed: %s', e)
        return []
    if isinstance(instances, dict):
        instances = instances.get('hosts') or instances.get('instances') or instances.get('data') or []
    if not isinstance(instances, list):
        return []
    out = []
    for inst in instances:
        if not isinstance(inst, dict):
            continue
        ip = inst.get('ip') or inst.get('IP') or ''
        port = inst.get('port') or inst.get('PORT') or 0
        if not ip:
            continue
        try:
            port = int(port)
        except Exception:
            port = 8089
        out.append({'ip': ip, 'port': port})
    return out


def get_random_service_url(service_name: str) -> Optional[str]:
    instances = get_service_instances(service_name, healthy_only=True)
    if not instances:
        return None
    inst = random.choice(instances)
    return f"http://{inst['ip']}:{inst['port']}"


def post_nacos_service() -> str:
    return (os.getenv('POST_NACOS_SERVICE') or 'easyaiot-post').strip()


def list_post_instances() -> List[Dict]:
    return get_service_instances(post_nacos_service(), healthy_only=True)


def pick_post_base_urls() -> List[str]:
    """返回可用 POST base URL 列表：Nacos healthy 优先，静态 POST_BASE_URL 兜底。"""
    urls = []
    for inst in list_post_instances():
        urls.append(f"http://{inst['ip']}:{inst['port']}")
    static = (os.getenv('POST_BASE_URL') or '').strip().rstrip('/')
    if static and static not in urls:
        urls.append(static)
    return urls
