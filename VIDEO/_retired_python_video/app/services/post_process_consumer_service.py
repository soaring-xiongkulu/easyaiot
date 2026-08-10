"""
算法任务 AI 后处理结果入库逻辑（仅供查询 API 复用；Kafka 消费与落库已迁移至 iot-sink）。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from models import db, AlgorithmPostProcessResult

logger = logging.getLogger(__name__)


def _parse_event_time(message: Dict[str, Any]) -> Optional[datetime]:
    raw = message.get('timestamp') or message.get('eventTime')
    if not raw:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    try:
        text = str(raw).replace('Z', '+00:00')
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _json_dump(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def process_post_process_message(message: Dict[str, Any]) -> None:
    """保留给测试/手工回放；生产链路由 iot-sink PostProcessResultConsumer 写入。"""
    task_id = message.get('taskId') or message.get('task_id')
    device_id = message.get('deviceId') or message.get('device_id')
    if task_id is None or not device_id:
        logger.warning('后处理消息缺少 taskId/deviceId: %s', message)
        return

    correlation_id = message.get('correlationId') or message.get('correlation_id')
    if correlation_id:
        exists = AlgorithmPostProcessResult.query.filter_by(correlation_id=correlation_id).first()
        if exists:
            logger.debug('后处理结果已存在，跳过: correlationId=%s', correlation_id)
            return

    payload = message.get('payload')
    if payload is None:
        payload = {
            k: message.get(k)
            for k in ('counts', 'events', 'alerts', 'detections', 'suppress_default_alert')
            if message.get(k) is not None
        }

    record = AlgorithmPostProcessResult(
        task_id=int(task_id),
        task_name=message.get('taskName') or message.get('task_name'),
        task_code=message.get('taskCode') or message.get('task_code'),
        task_type=message.get('taskType') or message.get('task_type'),
        device_id=str(device_id),
        device_name=message.get('deviceName') or message.get('device_name'),
        frame_number=message.get('frameNumber') or message.get('frame_number'),
        event_time=_parse_event_time(message),
        counts=_json_dump(message.get('counts')),
        events=_json_dump(message.get('events')),
        alerts=_json_dump(message.get('alerts')),
        payload=_json_dump(payload),
        correlation_id=correlation_id,
    )
    db.session.add(record)
    db.session.commit()
