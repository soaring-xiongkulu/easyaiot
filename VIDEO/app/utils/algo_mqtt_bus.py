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
import time
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


def post_enabled() -> bool:
    """Infer 是否切到 POST 定制后处理（发 InferEvent 而非直发最终告警）。"""
    val = (os.getenv('POST_ENABLED') or 'true').strip().lower()
    return val in {'1', 'true', 'yes', 'on'}


def post_failover_open() -> bool:
    """POST 不可用时是否 fail-open 直发 sink（v1.7 §12.3，默认 true）。"""
    val = (os.getenv('POST_FAILOVER_OPEN') or 'true').strip().lower()
    return val in {'1', 'true', 'yes', 'on'}


def post_base_url() -> str:
    """静态兜底；有 Nacos 时优先用发现结果（见 pick）。"""
    return (os.getenv('POST_BASE_URL') or '').strip().rstrip('/')


def infer_heartbeat_sec() -> int:
    try:
        n = int(os.getenv('INFER_HEARTBEAT_SEC') or '60')
    except ValueError:
        n = 60
    return max(15, n)


# --- POST 集群探活（v1.9：Nacos healthy / 静态兜底）---
_post_health_lock = None
_post_ready = True
_post_fail_streak = 0
_post_ok_streak = 0
_post_health_started = False


def _health_lock():
    global _post_health_lock
    if _post_health_lock is None:
        import threading
        _post_health_lock = threading.Lock()
    return _post_health_lock


def _probe_post_cluster_available() -> bool:
    """v1.9：Nacos healthy 实例数 > 0，或静态 POST_BASE_URL /readyz 成功。"""
    try:
        from app.utils.nacos_service_discovery import list_post_instances, pick_post_base_urls
    except ImportError:
        try:
            from nacos_service_discovery import list_post_instances, pick_post_base_urls  # type: ignore
        except ImportError:
            list_post_instances = lambda: []  # type: ignore
            pick_post_base_urls = lambda: ([post_base_url()] if post_base_url() else [])

    instances = list_post_instances()
    if instances:
        return True
    # 无 Nacos 或列表空 → 静态兜底抽检 readyz
    for base in pick_post_base_urls():
        if not base:
            continue
        try:
            import urllib.request
            req = urllib.request.Request(f'{base}/readyz', method='GET')
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status != 200:
                    continue
                body = resp.read().decode('utf-8', errors='ignore')
                try:
                    data = json.loads(body)
                    if isinstance(data, dict) and 'ready' in data:
                        if bool(data.get('ready')):
                            return True
                        continue
                except Exception:
                    pass
                return True
        except Exception as exc:
            logger.debug('POST readyz probe failed %s: %s', base, exc)
    return False


def _probe_post_readyz() -> bool:
    return _probe_post_cluster_available()


def _health_threshold() -> int:
    try:
        return max(1, int(os.getenv('POST_HEALTH_FAIL_THRESHOLD') or '3'))
    except ValueError:
        return 3


def _health_interval() -> int:
    try:
        return max(1, int(os.getenv('POST_HEALTH_INTERVAL_SEC') or '5'))
    except ValueError:
        return 5


def post_is_ready() -> bool:
    """当前是否认为 POST ready（由后台探活维护）。"""
    ensure_post_health_probe()
    with _health_lock():
        return bool(_post_ready)


def post_in_bypass() -> bool:
    """POST_ENABLED 且 fail-open 且 POST 不 ready → 应直发 sink。"""
    if not post_enabled():
        return False
    if not post_failover_open():
        return False
    return not post_is_ready()


def should_publish_infer_event() -> bool:
    """应走 InferEvent → POST 定制链路（防双发）。"""
    if not post_enabled():
        return False
    if post_failover_open() and not post_is_ready():
        return False
    return True


def ensure_post_health_probe() -> None:
    """启动后台 /readyz 探活（幂等）。"""
    global _post_health_started, _post_ready, _post_fail_streak, _post_ok_streak
    if not post_enabled():
        return
    with _health_lock():
        if _post_health_started:
            return
        _post_health_started = True

    import threading

    def _loop():
        global _post_ready, _post_fail_streak, _post_ok_streak
        thr = _health_threshold()
        while True:
            ok = _probe_post_readyz()
            with _health_lock():
                if ok:
                    _post_fail_streak = 0
                    _post_ok_streak += 1
                    if not _post_ready and _post_ok_streak >= thr:
                        _post_ready = True
                        logger.info('POST health recovered → exit bypass')
                    elif _post_ready:
                        _post_ok_streak = thr  # saturate
                else:
                    _post_ok_streak = 0
                    _post_fail_streak += 1
                    if _post_ready and _post_fail_streak >= thr:
                        _post_ready = False
                        logger.warning(
                            'POST health failed %sx → bypass (FAILOVER_OPEN=%s)',
                            thr, post_failover_open(),
                        )
            time.sleep(_health_interval())

    threading.Thread(target=_loop, name='post-health', daemon=True).start()
    # 启动时立即探一次，避免长时间误判
    ok = _probe_post_readyz()
    with _health_lock():
        if not ok:
            _post_fail_streak = _health_threshold()
            _post_ready = False
            logger.warning('POST initial readyz failed → start in bypass if FAILOVER_OPEN')
        else:
            _post_ready = True


def _publish_raw(topic: str, payload: Dict[str, Any], *, qos: int = 1) -> bool:
    """发布裸 JSON（无 algo bus envelope），供 POST InferEvent 契约使用。"""
    if not bus_enabled():
        return False
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning('paho-mqtt 未安装，无法 MQTT 发布 topic=%s', topic)
        return False

    brokers = _brokers()
    if not brokers:
        return False

    body = json.dumps(payload, ensure_ascii=False)
    username = os.getenv('MQTT_ALGO_USERNAME') or ''
    password = os.getenv('MQTT_ALGO_PASSWORD') or ''
    client_id = (os.getenv('MQTT_ALGO_CLIENT_ID') or 'algo-video-bus') + '-infer-' + uuid.uuid4().hex[:8]
    last_err: Optional[Exception] = None
    for host, port in brokers:
        try:
            client = mqtt.Client(client_id=client_id, clean_session=True)
            if username:
                client.username_pw_set(username, password)
            client.connect(host, port, keepalive=30)
            info = client.publish(topic, body, qos=qos)
            info.wait_for_publish(timeout=5)
            client.disconnect()
            return True
        except Exception as exc:
            last_err = exc
            logger.warning('MQTT raw 发布失败 topic=%s %s:%s — %s', topic, host, port, exc)
    if last_err:
        logger.error('MQTT raw 全部 broker 失败 topic=%s: %s', topic, last_err)
    return False


def build_infer_event(
    *,
    task_id: int,
    task_type: str,
    device_id: str,
    detections: Optional[list] = None,
    event_kind: str = 'infer',
    task_name: str = '',
    device_name: str = '',
    frame_number: int = 0,
    frame_width: int = 0,
    frame_height: int = 0,
    image_path: str = '',
    model_ids: Optional[list] = None,
    correlation_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    hints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """构造 infer_event.v1 载荷。"""
    dets_out = []
    for d in detections or []:
        bbox = d.get('bbox') or [0, 0, 0, 0]
        if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
            bbox4 = [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
        else:
            bbox4 = [0.0, 0.0, 0.0, 0.0]
        dets_out.append({
            'model_id': d.get('model_id'),
            'bbox': bbox4,
            'class_id': int(d.get('class_id') or 0),
            'class_name': d.get('class_name') or 'unknown',
            'confidence': float(d.get('confidence') or 0),
            'track_id': int(d.get('track_id') or 0),
        })
    ts = timestamp or datetime.now(timezone.utc).astimezone().isoformat()
    return {
        'schema': 'infer_event.v1',
        'event_kind': event_kind or 'infer',
        'correlation_id': correlation_id or str(uuid.uuid4()),
        'task_id': int(task_id),
        'task_name': task_name or '',
        'task_type': task_type or 'realtime',
        'device_id': str(device_id),
        'device_name': device_name or '',
        'timestamp': ts,
        'frame_number': int(frame_number or 0),
        'frame_width': int(frame_width or 0),
        'frame_height': int(frame_height or 0),
        'image_path': image_path or '',
        'detections': dets_out,
        'model_ids': list(model_ids or []),
        'hints': hints or {},
    }


def publish_infer_event(event: Dict[str, Any]) -> bool:
    """发布 InferEvent 到 mqtt/iot-infer-event（裸 JSON，供 POST 消费）。"""
    topic = (os.getenv('TOPIC_INFER_EVENT') or 'mqtt/iot-infer-event').strip()
    ok = _publish_raw(topic, event, qos=1)
    if ok:
        logger.info(
            'MQTT InferEvent 已发布 kind=%s task=%s device=%s dets=%s',
            event.get('event_kind'),
            event.get('task_id'),
            event.get('device_id'),
            len(event.get('detections') or []),
        )
    return ok


def start_infer_heartbeat(
    *,
    stop_event,
    get_context,
    interval_sec: Optional[int] = None,
):
    """启动 Infer 心跳线程。get_context() -> dict 含 task_id/device_id/...；返回 daemon Thread。

    get_context 可返回 None 跳过本轮；也可返回 list[dict] 多设备。
    bypass 期间停发（§12.3.3）。
    """
    import threading

    ensure_post_health_probe()
    sec = interval_sec if interval_sec is not None else infer_heartbeat_sec()

    def _loop():
        while not stop_event.is_set():
            for _ in range(sec):
                if stop_event.is_set():
                    return
                time.sleep(1)
            if not should_publish_infer_event():
                continue
            try:
                ctx = get_context()
            except Exception as exc:
                logger.warning('infer heartbeat context error: %s', exc)
                continue
            if ctx is None:
                continue
            items = ctx if isinstance(ctx, list) else [ctx]
            for item in items:
                if not item:
                    continue
                try:
                    ev = build_infer_event(
                        task_id=int(item['task_id']),
                        task_type=str(item.get('task_type') or 'realtime'),
                        device_id=str(item['device_id']),
                        detections=[],
                        event_kind='heartbeat',
                        task_name=str(item.get('task_name') or ''),
                        device_name=str(item.get('device_name') or ''),
                        frame_width=int(item.get('frame_width') or 0),
                        frame_height=int(item.get('frame_height') or 0),
                        model_ids=item.get('model_ids') or [],
                    )
                    publish_infer_event(ev)
                except Exception as exc:
                    logger.warning('infer heartbeat publish failed: %s', exc)

    t = threading.Thread(target=_loop, name='infer-heartbeat', daemon=True)
    t.start()
    return t


def inject_post_bypass_info(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """为 fail-open 直发告警写入 information.post_bypass 标记。"""
    data = dict(alert_data or {})
    info = data.get('information')
    if isinstance(info, str):
        try:
            info_obj = json.loads(info) if info else {}
        except Exception:
            info_obj = {'raw': info}
    elif isinstance(info, dict):
        info_obj = dict(info)
    else:
        info_obj = {}
    info_obj['post_bypass'] = True
    info_obj['post_bypass_reason'] = 'post_unready'
    data['information'] = json.dumps(info_obj, ensure_ascii=False)
    return data
