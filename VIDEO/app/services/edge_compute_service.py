"""通用边缘计算控制面：纳管、查询、监控与 MQTT 命令。"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from models import EdgeComputeCommand, EdgeComputeMetric, EdgeComputeNode, db
from sqlalchemy import or_


SPEC_VERSION = 'easyaiot.edge.telemetry/v1'
OFFLINE_AFTER_SECONDS = max(30, int(os.getenv('EDGE_NODE_OFFLINE_AFTER_SECONDS', '90')))


def _clean(value, default=None):
    if value is None:
        return default
    result = str(value).strip()
    return result if result else default


def _integer(value, default=0, minimum=0, maximum=65535):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(number, maximum))


def _broker_urls():
    raw = _clean(os.getenv('MQTT_BROKER_URLS'), '127.0.0.1:1883')
    return [item.strip() for item in raw.replace(';', ',').split(',') if item.strip()]


def _topics(node_id):
    prefix = f'mqtt/iot-edge-node/{node_id}'
    return {
        'heartbeat': f'{prefix}/heartbeat',
        'status': f'{prefix}/status',
        'command': f'{prefix}/command',
        'commandAck': f'{prefix}/command-ack',
    }


def _runtime_config(node, include_token=True):
    data = {
        'specVersion': SPEC_VERSION,
        'nodeId': node.id,
        'mqttBrokerUrls': _broker_urls(),
        'mqttUsername': node.mqtt_username,
        'mqttClientId': node.mqtt_client_id,
        'topics': _topics(node.id),
        'heartbeatIntervalSeconds': max(5, int(os.getenv('EDGE_NODE_HEARTBEAT_SECONDS', '10'))),
        'offlineAfterSeconds': OFFLINE_AFTER_SECONDS,
    }
    if include_token:
        data['agentToken'] = node.agent_token
        data['mqttPassword'] = node.agent_token
    return data


def enroll_node(payload, remote_addr=None):
    fingerprint = _clean(payload.get('fingerprint'))
    if not fingerprint or len(fingerprint) > 128:
        raise ValueError('fingerprint 不能为空且最长 128 位')

    node = EdgeComputeNode.query.filter_by(fingerprint=fingerprint).first()
    created = node is None
    if created:
        suffix = uuid.uuid4().hex
        node = EdgeComputeNode(
            fingerprint=fingerprint,
            name=_clean(payload.get('name'), f'edge-{fingerprint[:8]}'),
            host=_clean(payload.get('host'), remote_addr),
            mqtt_username=f'pending-{suffix}',
            mqtt_client_id=f'pending-{suffix}',
            agent_token=secrets.token_urlsafe(32),
            status='offline',
        )
        db.session.add(node)
        db.session.flush()
        node.mqtt_username = f'edge-node-{node.id}'
        node.mqtt_client_id = f'easyaiot-edge-{node.id}'
    else:
        supplied_token = _clean(payload.get('agentToken') or payload.get('agent_token'), '')
        if node.enabled and not hmac.compare_digest(node.agent_token, supplied_token):
            raise FileExistsError('该硬件指纹已纳管，不能重复领取节点凭据')
        if not node.enabled:
            # 管理端停用节点后允许重新纳管，同时轮换旧凭据，便于盒子重装后安全恢复。
            node.agent_token = secrets.token_urlsafe(32)
        node.name = _clean(payload.get('name'), node.name)
        node.host = _clean(payload.get('host'), node.host or remote_addr)

    node.enabled = True
    node.node_kind = _clean(payload.get('nodeKind') or payload.get('node_kind'), node.node_kind or 'edge_box')
    node.hardware_provider = _clean(payload.get('hardwareProvider') or payload.get('hardware_provider'), node.hardware_provider)
    node.soc_model = _clean(payload.get('socModel') or payload.get('soc_model'), node.soc_model)
    node.accelerator_type = _clean(payload.get('acceleratorType') or payload.get('accelerator_type'), node.accelerator_type)
    node.accelerator_count = _integer(
        payload.get('acceleratorCount', payload.get('accelerator_count')),
        node.accelerator_count or 0,
        maximum=64,
    )
    node.runtime_target = _clean(payload.get('runtimeTarget') or payload.get('runtime_target'), node.runtime_target)
    node.runtime_version = _clean(payload.get('runtimeVersion') or payload.get('runtime_version'), node.runtime_version)
    node.agent_version = _clean(payload.get('agentVersion') or payload.get('agent_version'), node.agent_version)
    node.agent_port = _integer(
        payload.get('agentPort', payload.get('agent_port')),
        node.agent_port or 9100,
        minimum=1,
    )
    node.max_task_count = _integer(
        payload.get('maxTaskCount', payload.get('max_task_count')),
        node.max_task_count or 0,
        maximum=10000,
    )
    db.session.commit()
    return {'created': created, **_runtime_config(node, include_token=True)}


def runtime_config(node_id, agent_token):
    node = db.session.get(EdgeComputeNode, int(node_id))
    if node is None or not node.enabled or not hmac.compare_digest(node.agent_token, str(agent_token or '')):
        raise ValueError('边缘节点身份无效')
    return _runtime_config(node, include_token=True)


def _is_stale(node, now=None):
    if not node.last_heartbeat_at:
        return True
    now = now or datetime.now(timezone.utc)
    heartbeat = node.last_heartbeat_at
    if heartbeat.tzinfo is None:
        heartbeat = heartbeat.replace(tzinfo=timezone.utc)
    return now - heartbeat > timedelta(seconds=OFFLINE_AFTER_SECONDS)


def node_dict(node):
    result = node.to_dict()
    if _is_stale(node):
        result['status'] = 'offline'
    result['telemetryTransport'] = 'mqtt'
    result['topics'] = _topics(node.id)
    return result


def list_nodes(page_no=1, page_size=20, keyword=None, status=None, soc_model=None, enabled=None):
    query = EdgeComputeNode.query
    if keyword:
        pattern = f'%{keyword.strip()}%'
        query = query.filter(
            or_(EdgeComputeNode.name.ilike(pattern), EdgeComputeNode.host.ilike(pattern),
                EdgeComputeNode.fingerprint.ilike(pattern))
        )
    if soc_model:
        query = query.filter(EdgeComputeNode.soc_model.ilike(f'%{soc_model.strip()}%'))
    if enabled is not None:
        query = query.filter(EdgeComputeNode.enabled.is_(bool(enabled)))
    heartbeat_cutoff = datetime.now(timezone.utc) - timedelta(seconds=OFFLINE_AFTER_SECONDS)
    if status == 'online':
        query = query.filter(
            EdgeComputeNode.status == 'online',
            EdgeComputeNode.last_heartbeat_at.isnot(None),
            EdgeComputeNode.last_heartbeat_at >= heartbeat_cutoff,
        )
    elif status == 'offline':
        query = query.filter(or_(
            EdgeComputeNode.status != 'online',
            EdgeComputeNode.last_heartbeat_at.is_(None),
            EdgeComputeNode.last_heartbeat_at < heartbeat_cutoff,
        ))
    page_no = max(1, int(page_no))
    page_size = max(1, min(int(page_size), 200))
    page = query.order_by(EdgeComputeNode.updated_at.desc(), EdgeComputeNode.id.desc()).paginate(
        page=page_no, per_page=page_size, error_out=False,
    )
    items = [node_dict(node) for node in page.items]
    return {'list': items, 'total': page.total, 'pageNo': page_no, 'pageSize': page_size}


def get_node(node_id):
    node = db.session.get(EdgeComputeNode, int(node_id))
    if node is None:
        raise ValueError('边缘节点不存在')
    return node_dict(node)


def update_node(node_id, payload):
    node = db.session.get(EdgeComputeNode, int(node_id))
    if node is None:
        raise ValueError('边缘节点不存在')
    if 'name' in payload:
        node.name = _clean(payload.get('name'), node.name)
    if 'remark' in payload:
        node.remark = _clean(payload.get('remark'))
    if 'enabled' in payload:
        node.enabled = bool(payload.get('enabled'))
        if not node.enabled:
            node.status = 'offline'
    db.session.commit()
    return node_dict(node)


def delete_node(node_id):
    node = db.session.get(EdgeComputeNode, int(node_id))
    if node is None:
        raise ValueError('边缘节点不存在')
    node.enabled = False
    node.status = 'offline'
    db.session.commit()


def list_metrics(node_id, minutes=60, limit=360):
    node = db.session.get(EdgeComputeNode, int(node_id))
    if node is None:
        raise ValueError('边缘节点不存在')
    since = datetime.now(timezone.utc) - timedelta(minutes=max(1, min(int(minutes), 10080)))
    rows = EdgeComputeMetric.query.filter(
        EdgeComputeMetric.node_id == node.id,
        EdgeComputeMetric.collected_at >= since,
    ).order_by(EdgeComputeMetric.collected_at.desc()).limit(max(1, min(int(limit), 2000))).all()
    return [row.to_dict() for row in reversed(rows)]


def _parse_broker(raw):
    value = raw if '://' in raw else f'mqtt://{raw}'
    parsed = urlparse(value)
    if not parsed.hostname:
        raise ValueError(f'MQTT Broker 地址无效: {raw}')
    secure = parsed.scheme in ('mqtts', 'ssl', 'tls')
    return parsed.hostname, parsed.port or (8883 if secure else 1883), secure


def _publish_command(node, envelope):
    import paho.mqtt.client as mqtt

    host, port, secure = _parse_broker(_broker_urls()[0])
    client_id = f'easyaiot-edge-control-{uuid.uuid4().hex[:10]}'
    try:
        client = mqtt.Client(client_id=client_id, clean_session=True)
    except TypeError:
        client = mqtt.Client(client_id=client_id)
    username = _clean(os.getenv('MQTT_EDGE_CONTROL_USERNAME') or os.getenv('MQTT_ALGO_USERNAME'))
    password = _clean(os.getenv('MQTT_EDGE_CONTROL_PASSWORD') or os.getenv('MQTT_ALGO_PASSWORD'))
    if username:
        client.username_pw_set(username, password or '')
    if secure:
        client.tls_set()
    client.connect(host, port, keepalive=20)
    client.loop_start()
    try:
        info = client.publish(_topics(node.id)['command'], json.dumps(envelope, ensure_ascii=False), qos=1)
        info.wait_for_publish(timeout=5)
        if getattr(info, 'rc', 0) != 0:
            raise RuntimeError(f'MQTT 发布失败 rc={info.rc}')
    finally:
        client.loop_stop()
        client.disconnect()


def send_command(node_id, command, params=None):
    node = db.session.get(EdgeComputeNode, int(node_id))
    if node is None or not node.enabled:
        raise ValueError('边缘节点不存在或已停用')
    command = _clean(command)
    if command not in {'ping', 'status', 'runtime.restart', 'runtime.reload', 'frp.restart'}:
        raise ValueError('不支持的边缘节点命令')
    command_id = uuid.uuid4().hex
    payload_obj = {'commandId': command_id, 'command': command, 'params': params or {}}
    payload = json.dumps(payload_obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    sent_at = int(time.time() * 1000)
    message_id = uuid.uuid4().hex
    canonical = '\n'.join((SPEC_VERSION, 'command', str(node.id), message_id, str(sent_at), payload))
    signature = hmac.new(node.agent_token.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    envelope = {
        'specVersion': SPEC_VERSION,
        'messageType': 'command',
        'nodeId': node.id,
        'messageId': message_id,
        'sentAt': sent_at,
        'payload': payload,
        'signature': signature,
    }
    record = EdgeComputeCommand(
        command_id=command_id,
        node_id=node.id,
        command=command,
        request_payload=payload_obj,
        status='sending',
    )
    db.session.add(record)
    db.session.commit()
    try:
        _publish_command(node, envelope)
        record.status = 'sent'
        db.session.commit()
    except Exception:
        record.status = 'failed'
        db.session.commit()
        raise
    return {'commandId': command_id, 'status': record.status}
