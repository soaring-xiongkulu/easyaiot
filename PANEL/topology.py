"""EasyAIoT 平台拓扑：静态调用关系 + 实时容器状态/流量。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from docker_ops import container_stats, list_containers

# group: middleware | platform | business | edge | ui
# containerHints: 匹配 docker container name 的子串（小写）
SERVICE_NODES: List[Dict[str, Any]] = [
    # —— 中间件 ——
    {'id': 'nacos', 'label': 'Nacos', 'group': 'middleware', 'hints': ['nacos-server', 'nacos']},
    {'id': 'postgres', 'label': 'PostgreSQL', 'group': 'middleware', 'hints': ['postgres-server', 'postgres']},
    {'id': 'redis', 'label': 'Redis', 'group': 'middleware', 'hints': ['redis-server', 'redis']},
    {'id': 'kafka', 'label': 'Kafka', 'group': 'middleware', 'hints': ['kafka-server', 'kafka']},
    {'id': 'minio', 'label': 'MinIO', 'group': 'middleware', 'hints': ['minio-server', 'minio']},
    {'id': 'milvus', 'label': 'Milvus', 'group': 'middleware', 'hints': ['milvus-server', 'milvus']},
    {'id': 'emqx', 'label': 'EMQX', 'group': 'middleware', 'hints': ['emqx-server', 'emqx']},
    {'id': 'tdengine', 'label': 'TDengine', 'group': 'middleware', 'hints': ['tdengine-server', 'tdengine']},
    {'id': 'srs', 'label': 'SRS', 'group': 'middleware', 'hints': ['srs-server', 'srs']},
    {'id': 'zlmediakit', 'label': 'ZLMediaKit', 'group': 'middleware', 'hints': ['zlmediakit-server', 'zlmediakit']},
    {'id': 'nodered', 'label': 'Node-RED', 'group': 'middleware', 'hints': ['nodered-server', 'nodered']},
    {'id': 'fuxa', 'label': 'FUXA', 'group': 'middleware', 'hints': ['fuxa-server', 'fuxa']},
    # —— 平台服务 ——
    {'id': 'gateway', 'label': 'iot-gateway', 'group': 'platform', 'hints': ['iot-gateway', 'gateway']},
    {'id': 'system', 'label': 'iot-system', 'group': 'platform', 'hints': ['iot-system']},
    {'id': 'infra', 'label': 'iot-infra', 'group': 'platform', 'hints': ['iot-infra']},
    {'id': 'device', 'label': 'iot-device', 'group': 'platform', 'hints': ['iot-device']},
    {'id': 'file', 'label': 'iot-file', 'group': 'platform', 'hints': ['iot-file']},
    {'id': 'message', 'label': 'iot-message', 'group': 'platform', 'hints': ['iot-message']},
    {'id': 'sink', 'label': 'iot-sink', 'group': 'platform', 'hints': ['iot-sink']},
    {'id': 'node', 'label': 'iot-node', 'group': 'platform', 'hints': ['iot-node']},
    {'id': 'dataset', 'label': 'iot-dataset', 'group': 'platform', 'hints': ['iot-dataset']},
    {'id': 'tdengine-svc', 'label': 'iot-tdengine', 'group': 'platform', 'hints': ['iot-tdengine']},
    {'id': 'visualize-svc', 'label': 'iot-visualize', 'group': 'platform', 'hints': ['iot-visualize']},
    {'id': 'gb28181', 'label': 'iot-gb28181', 'group': 'platform', 'hints': ['iot-gb28181', 'wvp']},
    # —— 业务能力 ——
    {'id': 'video', 'label': 'VIDEO', 'group': 'business', 'hints': ['easyaiot-video', 'video-server', 'iot-video']},
    {'id': 'ai', 'label': 'AI', 'group': 'business', 'hints': ['easyaiot-ai', 'ai-server', 'iot-ai']},
    {'id': 'transform', 'label': 'TRANSFORM', 'group': 'business', 'hints': ['transform-runtime', 'iot-transform']},
    {'id': 'app', 'label': 'APP', 'group': 'ui', 'hints': ['easyaiot-app', 'iot-app']},
    {'id': 'visualize', 'label': 'VISUALIZE', 'group': 'ui', 'hints': ['easyaiot-visualize', 'visualize']},
    {'id': 'web', 'label': 'WEB', 'group': 'ui', 'hints': ['web-service', 'easyaiot-web', 'iot-web', 'web-nginx', 'aiot-web']},
    {'id': 'panel', 'label': 'PANEL', 'group': 'edge', 'hints': ['easyaiot-panel', 'panel-agent']},
]

# 调用 / 依赖关系（源 -> 目标）
SERVICE_EDGES: List[Tuple[str, str, str]] = [
    ('web', 'gateway', 'HTTP'),
    ('web', 'system', 'HTTP(mini)'),
    ('app', 'gateway', 'HTTP'),
    ('gateway', 'system', 'RPC'),
    ('gateway', 'infra', 'RPC'),
    ('gateway', 'device', 'RPC'),
    ('gateway', 'file', 'RPC'),
    ('gateway', 'message', 'RPC'),
    ('gateway', 'node', 'RPC'),
    ('gateway', 'dataset', 'RPC'),
    ('gateway', 'visualize-svc', 'RPC'),
    ('gateway', 'tdengine-svc', 'RPC'),
    ('gateway', 'gb28181', 'RPC'),
    ('gateway', 'video', 'HTTP'),
    ('gateway', 'ai', 'HTTP'),
    ('system', 'postgres', 'SQL'),
    ('system', 'redis', 'KV'),
    ('system', 'nacos', '注册'),
    ('infra', 'postgres', 'SQL'),
    ('infra', 'redis', 'KV'),
    ('infra', 'nacos', '注册'),
    ('device', 'postgres', 'SQL'),
    ('device', 'kafka', 'MQ'),
    ('device', 'emqx', 'MQTT'),
    ('device', 'nacos', '注册'),
    ('sink', 'kafka', '消费'),
    ('sink', 'emqx', 'MQTT'),
    ('sink', 'tdengine', '写入'),
    ('transform', 'kafka', '消费'),
    ('node', 'postgres', 'SQL'),
    ('node', 'emqx', 'MQTT'),
    ('node', 'redis', 'KV'),
    ('video', 'minio', '对象'),
    ('video', 'zlmediakit', '流媒体'),
    ('video', 'srs', '流媒体'),
    ('ai', 'minio', '对象'),
    ('ai', 'milvus', '向量'),
    ('dataset', 'minio', '对象'),
    ('file', 'minio', '对象'),
    ('message', 'redis', 'KV'),
    ('gb28181', 'zlmediakit', '流媒体'),
    ('visualize-svc', 'postgres', 'SQL'),
    ('nodered', 'emqx', 'MQTT'),
    ('fuxa', 'emqx', 'MQTT'),
    ('tdengine-svc', 'tdengine', '查询'),
]


def _match_container(hints: List[str], containers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    lower_hints = [h.lower() for h in hints]
    for c in containers:
        name = (c.get('name') or '').lower()
        image = (c.get('image') or '').lower()
        for h in lower_hints:
            if h and (h in name or h in image):
                return c
    return None


def _parse_net_io(net_io: str) -> Dict[str, str]:
    # e.g. "1.2kB / 3.4kB"
    parts = [p.strip() for p in (net_io or '').split('/')]
    return {
        'rx': parts[0] if parts else '',
        'tx': parts[1] if len(parts) > 1 else '',
        'raw': net_io or '',
    }


def build_topology() -> Dict[str, Any]:
    containers = list_containers(True)
    stats = container_stats()

    nodes: List[Dict[str, Any]] = []
    matched_ids = set()

    for svc in SERVICE_NODES:
        c = _match_container(svc['hints'], containers)
        state = 'missing'
        stats_item = None
        container_name = None
        container_id = None
        if c:
            matched_ids.add(c.get('id') or '')
            container_name = c.get('name')
            container_id = c.get('id')
            st = (c.get('state') or '').lower()
            if st == 'running':
                state = 'running'
            elif st in ('exited', 'dead', 'created'):
                state = st or 'stopped'
            else:
                state = st or 'unknown'
            stats_item = (
                stats.get(c.get('id') or '')
                or stats.get((c.get('id') or '')[:12])
                or stats.get(c.get('name') or '')
            )

        net = _parse_net_io((stats_item or {}).get('netIO', ''))
        nodes.append({
            'id': svc['id'],
            'label': svc['label'],
            'group': svc['group'],
            'state': state,
            'containerName': container_name,
            'containerId': container_id,
            'cpuPercent': (stats_item or {}).get('cpuPercent', 0),
            'memPercent': (stats_item or {}).get('memPercent', 0),
            'memUsage': (stats_item or {}).get('memUsage', ''),
            'netIO': net,
            'category': svc['group'],
        })

    # 未建模但在跑的容器：挂到「其他」
    for c in containers:
        cid = c.get('id') or ''
        if cid in matched_ids:
            continue
        name = c.get('name') or cid[:12]
        # 跳过明显无关（panel 自己已建模）
        sid = f'other-{name}'
        st = (c.get('state') or '').lower()
        stats_item = stats.get(cid) or stats.get(cid[:12]) or stats.get(name) or {}
        nodes.append({
            'id': sid,
            'label': name,
            'group': 'other',
            'state': 'running' if st == 'running' else (st or 'unknown'),
            'containerName': name,
            'containerId': cid,
            'cpuPercent': stats_item.get('cpuPercent', 0),
            'memPercent': stats_item.get('memPercent', 0),
            'memUsage': stats_item.get('memUsage', ''),
            'netIO': _parse_net_io(stats_item.get('netIO', '')),
            'category': 'other',
        })

    present = {n['id'] for n in nodes}
    edges: List[Dict[str, Any]] = []
    for src, dst, kind in SERVICE_EDGES:
        if src in present and dst in present:
            src_node = next(n for n in nodes if n['id'] == src)
            dst_node = next(n for n in nodes if n['id'] == dst)
            active = src_node['state'] == 'running' and dst_node['state'] == 'running'
            edges.append({
                'source': src,
                'target': dst,
                'label': kind,
                'active': active,
            })

    summary = {
        'total': len(nodes),
        'running': sum(1 for n in nodes if n['state'] == 'running'),
        'stopped': sum(1 for n in nodes if n['state'] not in ('running', 'missing')),
        'missing': sum(1 for n in nodes if n['state'] == 'missing'),
        'containers': len(containers),
    }
    return {'nodes': nodes, 'edges': edges, 'summary': summary}
