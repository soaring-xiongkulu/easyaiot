"""
人脸匹配 Kafka 投递服务
"""
import json
import logging
import threading
from datetime import datetime
from typing import Dict, Optional

from flask import current_app

from app.services.alert_hook_service import get_kafka_producer

logger = logging.getLogger(__name__)


def _face_matching_topic() -> str:
    try:
        return current_app.config.get('KAFKA_FACE_MATCHING_TOPIC', 'iot-face-matching')
    except RuntimeError:
        import os
        return os.getenv('KAFKA_FACE_MATCHING_TOPIC', 'iot-face-matching')


def build_face_matching_message(
        *,
        task_id: int,
        task_name: str,
        task_type: str,
        device_id: str,
        device_name: Optional[str],
        library_id: Optional[int] = None,
        library_name: Optional[str] = None,
        face_image_path: str,
        threshold: Optional[float],
        alert_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
        source_event: Optional[str] = None,
        bbox: Optional[list] = None,
        confidence: Optional[float] = None,
) -> Dict:
    message = {
        'taskId': task_id,
        'taskName': task_name,
        'taskType': task_type or 'realtime',
        'deviceId': device_id,
        'deviceName': device_name,
        'libraryId': library_id,
        'libraryName': library_name,
        'faceImagePath': face_image_path,
        'threshold': threshold,
        'faceMatchingThreshold': threshold,
        'alertId': alert_id,
        'bbox': bbox,
        'confidence': confidence,
        'timestamp': datetime.now().isoformat(),
    }
    if correlation_id:
        message['correlationId'] = correlation_id
    if source_event:
        message['sourceEvent'] = source_event
    return message


def send_face_matching_to_kafka(message: Dict) -> bool:
    producer = get_kafka_producer()
    if producer is None:
        logger.warning(
            "Kafka生产者不可用，人脸匹配消息未发送: deviceId=%s, libraryId=%s",
            message.get('deviceId'),
            message.get('libraryId'),
        )
        return False
    topic = _face_matching_topic()
    key = message.get('deviceId') or str(message.get('taskId') or 'face')
    try:
        future = producer.send(topic, key=key, value=message)
        future.get(timeout=10)
        logger.info(
            "人脸匹配消息已投递 Kafka: topic=%s, deviceId=%s, libraryId=%s, path=%s",
            topic,
            message.get('deviceId'),
            message.get('libraryId'),
            message.get('faceImagePath'),
        )
        return True
    except Exception as exc:
        logger.error("人脸匹配消息投递 Kafka 失败: %s", exc, exc_info=True)
        return False


def send_face_matching_async(message: Dict) -> None:
    thread = threading.Thread(target=lambda: send_face_matching_to_kafka(message), daemon=True)
    thread.start()
