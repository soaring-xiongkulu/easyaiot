"""
算法后处理入队客户端：经 HTTP 投递至 iot-sink，由 Java 侧对接 Kafka（VIDEO 不直连 Kafka）。
"""
from __future__ import annotations

import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


def _sink_enqueue_url() -> str:
    explicit = (os.getenv('IOT_SINK_API_URL') or '').strip().rstrip('/')
    if explicit:
        return f'{explicit}/post-process/enqueue'
    # 算法进程与 iot-sink 同机部署，默认直连 sink-server（48092），避免网关路由配置影响内网入队
    use_gateway = (os.getenv('IOT_SINK_USE_GATEWAY') or '').strip().lower() in ('1', 'true', 'yes')
    if not use_gateway:
        host = (os.getenv('IOT_SINK_HOST') or '127.0.0.1').strip()
        port = (os.getenv('IOT_SINK_PORT') or '48092').strip()
        return f'http://{host}:{port}/post-process/enqueue'
    gateway = os.getenv('JAVA_BACKEND_URL', os.getenv('GATEWAY_URL', 'http://localhost:48080')).rstrip('/')
    return f'{gateway}/admin-api/sink/post-process/enqueue'


def build_post_process_request_message(
    ctx: Dict[str, Any],
    *,
    correlation_id: Optional[str] = None,
    alert_image_path: Optional[str] = None,
) -> Dict[str, Any]:
    ts = ctx.get('timestamp')
    timestamp_epoch = ts if isinstance(ts, (int, float)) else None
    if timestamp_epoch is not None:
        event_time = datetime.fromtimestamp(timestamp_epoch, tz=timezone.utc).isoformat()
    else:
        event_time = datetime.now(timezone.utc).isoformat()

    return {
        'taskId': ctx.get('task_id'),
        'taskName': ctx.get('task_name'),
        'taskCode': ctx.get('task_code'),
        'taskType': ctx.get('task_type'),
        'deviceId': ctx.get('device_id'),
        'deviceName': ctx.get('device_name'),
        'frameNumber': ctx.get('frame_number'),
        'timestamp': event_time,
        'timestampEpoch': timestamp_epoch,
        'detections': ctx.get('detections') or [],
        'trackedDetections': ctx.get('tracked_detections') or [],
        'trackingEnabled': bool(ctx.get('tracking_enabled')),
        'regions': ctx.get('regions') or [],
        'modelIds': ctx.get('model_ids') or [],
        'alertClassNames': ctx.get('alert_class_names') or [],
        'poseAnalysisEnabled': bool(ctx.get('pose_analysis_enabled')),
        'poseIntentEnabled': bool(ctx.get('pose_intent_enabled')),
        'alertImagePath': alert_image_path or ctx.get('alert_image_path'),
        'correlationId': correlation_id or ctx.get('correlation_id') or str(uuid.uuid4()),
    }


def publish_post_process_request(
    ctx: Dict[str, Any],
    *,
    alert_image_path: Optional[str] = None,
) -> bool:
    message = build_post_process_request_message(ctx, alert_image_path=alert_image_path)
    url = _sink_enqueue_url()
    try:
        response = requests.post(url, json=message, timeout=5, headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            logger.warning(
                '后处理入队失败 status=%s url=%s body=%s',
                response.status_code,
                url,
                response.text[:200],
            )
            return False
        data = response.json()
        if isinstance(data, dict) and data.get('code') not in (0, None):
            logger.warning('后处理入队业务失败 url=%s resp=%s', url, data)
            return False
        return True
    except Exception as exc:
        logger.warning('后处理入队 HTTP 异常 url=%s: %s', url, exc)
        return False


def publish_post_process_request_async(
    ctx: Dict[str, Any],
    *,
    alert_image_path: Optional[str] = None,
) -> None:
    thread = threading.Thread(
        target=lambda: publish_post_process_request(ctx, alert_image_path=alert_image_path),
        daemon=True,
    )
    thread.start()
