"""车牌匹配 Kafka 投递服务"""
import json
import logging
import threading
from datetime import datetime
from typing import Dict, Optional

from flask import current_app

from app.services.alert_hook_service import get_kafka_producer

logger = logging.getLogger(__name__)


def _plate_matching_topic() -> str:
    try:
        return current_app.config.get('KAFKA_PLATE_MATCHING_TOPIC', 'iot-plate-matching')
    except RuntimeError:
        import os
        return os.getenv('KAFKA_PLATE_MATCHING_TOPIC', 'iot-plate-matching')


def build_plate_matching_message(
        *,
        task_id: int,
        task_name: str,
        task_type: str,
        device_id: str,
        device_name: Optional[str],
        library_id: Optional[int] = None,
        library_name: Optional[str] = None,
        plate_no: str,
        plate_color: Optional[str] = None,
        plate_image_path: Optional[str] = None,
        detect_conf: Optional[float] = None,
        alert_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
        rect: Optional[list] = None,
        landmarks: Optional[list] = None,
) -> Dict:
    message = {
        'taskId': task_id,
        'taskName': task_name,
        'taskType': task_type or 'realtime',
        'deviceId': device_id,
        'deviceName': device_name,
        'libraryId': library_id,
        'libraryName': library_name,
        'plateNo': plate_no,
        'plateColor': plate_color,
        'plateImagePath': plate_image_path,
        'detectConf': detect_conf,
        'alertId': alert_id,
        'rect': rect,
        'landmarks': landmarks,
        'timestamp': datetime.now().isoformat(),
    }
    if correlation_id:
        message['correlationId'] = correlation_id
    return message


def send_plate_matching_to_kafka(message: Dict) -> bool:
    producer = get_kafka_producer()
    if producer is None:
        logger.warning(
            "Kafka生产者不可用，车牌匹配消息未发送: deviceId=%s, libraryId=%s, plateNo=%s",
            message.get('deviceId'),
            message.get('libraryId'),
            message.get('plateNo'),
        )
        return False
    topic = _plate_matching_topic()
    key = message.get('deviceId') or str(message.get('taskId') or 'plate')
    try:
        future = producer.send(topic, key=key, value=message)
        future.get(timeout=10)
        logger.info(
            "车牌匹配消息已投递 Kafka: topic=%s, deviceId=%s, libraryId=%s, plateNo=%s",
            topic,
            message.get('deviceId'),
            message.get('libraryId'),
            message.get('plateNo'),
        )
        return True
    except Exception as exc:
        logger.error("车牌匹配消息投递 Kafka 失败: %s", exc, exc_info=True)
        return False


def send_plate_matching_async(message: Dict) -> None:
    thread = threading.Thread(target=lambda: send_plate_matching_to_kafka(message), daemon=True)
    thread.start()
