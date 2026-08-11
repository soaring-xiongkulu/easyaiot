"""VIDEO / 算法进程：默认经 MQTT 将告警与后处理发到算法总线（iot-sink）。

环境变量：
- ALGO_BUS_TRANSPORT：默认空视为 mqtt；显式 http/off/0/false 时关闭总线
- MQTT_BROKER_URLS：broker 列表（host:port，逗号分隔）
- MQTT_ALGO_TENANT / MQTT_ALGO_USERNAME / MQTT_ALGO_PASSWORD / MQTT_ALGO_CLIENT_ID
- COMPUTE_NODE_ID / NODE_ID：可选，写入 payload.node_id
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger('algo_mqtt_bus')

_DISABLE_VALUES = frozenset({'http', 'off', '0', 'false', 'no'})


def _brokers() -> list[Tuple[str, int]]:
    raw = (os.getenv('MQTT_BROKER_URLS') or '').strip() or '127.0.0.1:1883'
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    out: list[Tuple[str, int]] = []
    for p in parts:
        p = p.replace('tcp://', '').replace('mqtt://', '')
        if ':' in p:
            h, _, s = p.rpartition(':')
            try:
                out.append((h, int(s)))
            except ValueError:
                out.append((p, 1883))
        else:
            out.append((p, 1883))
    return out


def bus_enabled() -> bool:
    """默认开启 MQTT；仅当显式设为 http/off/0/false 时关闭。"""
    val = (os.getenv('ALGO_BUS_TRANSPORT') or '').strip().lower()
    return val not in _DISABLE_VALUES


def _node_id_from_env() -> Optional[int]:
    raw = os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or ''
    raw = str(raw).strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _normalize_alert_payload(alert_data: Dict[str, Any], *, snapshot: bool = False) -> Dict[str, Any]:
    """将扁平 hook 字段规范为 sink 期望的嵌套 alert 结构。"""
    raw = dict(alert_data or {})
    default_task_type = 'snap' if snapshot else 'realtime'

    if isinstance(raw.get('alert'), dict):
        payload = dict(raw)
        alert = dict(payload['alert'])
        alert.setdefault('task_type', payload.get('task_type') or default_task_type)
        if alert.get('image_path') is None and alert.get('imagePath') is not None:
            alert['image_path'] = alert.get('imagePath')
        payload['alert'] = alert
        payload.setdefault('task_type', alert.get('task_type') or default_task_type)
    else:
        alert_time = raw.get('time')
        alert = {
            'object': raw.get('object'),
            'event': raw.get('event'),
            'region': raw.get('region'),
            'information': raw.get('information'),
            'image_path': raw.get('image_path', raw.get('imagePath')),
            'record_path': raw.get('record_path', raw.get('recordPath')),
            'time': alert_time,
            'task_type': raw.get('task_type') or default_task_type,
        }
        payload = {
            'device_id': raw.get('device_id', raw.get('deviceId')),
            'device_name': raw.get('device_name', raw.get('deviceName')),
            'task_id': raw.get('task_id', raw.get('taskId')),
            'task_name': raw.get('task_name', raw.get('taskName')),
            'correlation_id': raw.get('correlation_id', raw.get('correlationId')),
            'timestamp': raw.get('timestamp', alert_time),
            'time': alert_time,
            'task_type': alert['task_type'],
            'alert': alert,
        }
        # 透传检测开关等顶层字段，避免 MQTT 路径丢字段
        for key in (
            'face_detection_enabled',
            'faceDetectionEnabled',
            'plate_detection_enabled',
            'plateDetectionEnabled',
            'should_notify',
            'shouldNotify',
            'notify_users',
            'notifyUsers',
            'notify_methods',
            'notifyMethods',
            'channels',
            'alert_id',
            'alertId',
        ):
            if key in raw and key not in payload:
                payload[key] = raw[key]

    node_id = _node_id_from_env()
    if node_id is not None:
        payload.setdefault('node_id', node_id)
        payload.setdefault('nodeId', node_id)
    return payload


def _publish(topic: str, msg_type: str, payload: Dict[str, Any]) -> bool:
    if not bus_enabled():
        return False
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning('paho-mqtt 未安装，无法 MQTT 发布 topic=%s', topic)
        return False

    brokers = _brokers()
    if not brokers:
        logger.warning('MQTT_BROKER_URLS 为空，跳过 MQTT 发布 topic=%s', topic)
        return False

    tenant = os.getenv('MQTT_ALGO_TENANT') or 'default'
    envelope = {
        'version': '1.0',
        'msgId': str(uuid.uuid4()),
        'msgType': msg_type,
        'tenant': tenant,
        'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        'payload': payload,
    }
    body = json.dumps(envelope, ensure_ascii=False)
    username = os.getenv('MQTT_ALGO_USERNAME') or ''
    password = os.getenv('MQTT_ALGO_PASSWORD') or ''
    client_id = (os.getenv('MQTT_ALGO_CLIENT_ID') or 'algo-video-bus') + '-pub-' + uuid.uuid4().hex[:8]

    last_err: Optional[Exception] = None
    for host, port in brokers:
        try:
            client = mqtt.Client(client_id=client_id, clean_session=True)
            if username:
                client.username_pw_set(username, password)
            client.connect(host, port, keepalive=30)
            info = client.publish(topic, body, qos=1)
            info.wait_for_publish(timeout=5)
            client.disconnect()
            logger.info(
                'MQTT 已发布 topic=%s type=%s broker=%s:%s',
                topic,
                msg_type,
                host,
                port,
            )
            return True
        except Exception as exc:
            last_err = exc
            logger.warning('MQTT 发布失败 topic=%s %s:%s — %s', topic, host, port, exc)
    if last_err:
        logger.error('MQTT 全部 broker 失败 topic=%s: %s', topic, last_err)
    return False


def publish_alert(alert_data: Dict[str, Any], *, snapshot: bool = False) -> bool:
    """发布告警到 mqtt/iot-alert-notification 或 mqtt/iot-snapshot-alert。"""
    if not bus_enabled():
        return False
    payload = _normalize_alert_payload(alert_data, snapshot=snapshot)
    topic = 'mqtt/iot-snapshot-alert' if snapshot else 'mqtt/iot-alert-notification'
    msg_type = 'alert.snapshot' if snapshot else 'alert.notification'
    ok = _publish(topic, msg_type, payload)
    if ok:
        logger.info(
            'MQTT 告警已发布 topic=%s device=%s',
            topic,
            payload.get('device_id'),
        )
    return ok


def publish_post_process(message_dict: Dict[str, Any]) -> bool:
    """发布后处理入队请求到 mqtt/iot-post-process-request。"""
    if not bus_enabled():
        return False
    payload = dict(message_dict or {})
    node_id = _node_id_from_env()
    if node_id is not None:
        payload.setdefault('node_id', node_id)
        payload.setdefault('nodeId', node_id)
    return _publish('mqtt/iot-post-process-request', 'post_process.request', payload)
