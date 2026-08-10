"""
流媒体 DVR Kafka 生产者：Hook 快速入队。
"""
import json
import logging
import os  # noqa: F401 — used by build_event_from_srs_hook
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

TOPIC_DVR_COMPLETED = os.getenv('MEDIA_KAFKA_DVR_TOPIC', 'media.dvr.completed')
TOPIC_DVR_DLQ = os.getenv('MEDIA_KAFKA_DVR_DLQ_TOPIC', 'media.dvr.dlq')
TOPIC_SNAP_COMPLETED = os.getenv('MEDIA_KAFKA_SNAP_TOPIC', 'media.snap.completed')
TOPIC_SNAP_DLQ = os.getenv('MEDIA_KAFKA_SNAP_DLQ_TOPIC', 'media.snap.dlq')

_producer = None


def is_kafka_upload_mode() -> bool:
    mode = os.getenv('MEDIA_UPLOAD_MODE', 'sync').lower()
    return mode in ('kafka', 'hybrid')


def is_hybrid_upload_mode() -> bool:
    return os.getenv('MEDIA_UPLOAD_MODE', 'sync').lower() == 'hybrid'


def is_snap_kafka_mode() -> bool:
    mode = os.getenv('MEDIA_SNAP_UPLOAD_MODE', '').strip().lower()
    if mode == 'kafka':
        return True
    if mode == 'sync':
        return False
    return is_kafka_upload_mode()


def _bootstrap_servers() -> str:
    servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    if 'Kafka' in servers or 'kafka-server' in servers:
        return 'localhost:9092'
    return servers


def _get_producer():
    global _producer
    if _producer is not None:
        return _producer
    try:
        from kafka import KafkaProducer
        _producer = KafkaProducer(
            bootstrap_servers=_bootstrap_servers().split(','),
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            linger_ms=5,
        )
    except Exception as e:
        logger.error('Kafka Producer 初始化失败: %s', e)
        raise
    return _producer


def build_event_from_srs_hook(data: Dict[str, Any], device_id: Optional[str] = None) -> Dict[str, Any]:
    stream = data.get('stream', '') or ''
    file_path = data.get('file', '') or data.get('file_path', '') or ''
    segment_start_ms = None
    filename = os.path.basename(file_path.replace('\\', '/'))
    stem, _ = os.path.splitext(filename)
    if stem.isdigit():
        segment_start_ms = int(stem)
    return {
        'event_id': str(uuid.uuid4()),
        'device_id': device_id or stream,
        'app': data.get('app', 'live'),
        'stream': stream,
        'file_path': file_path,
        'cwd': data.get('cwd', ''),
        'source': 'srs',
        'media_node_id': data.get('media_node_id') or data.get('server_id'),
        'segment_start_ms': segment_start_ms,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }


def build_event_from_zlm_hook(data: Dict[str, Any], device_id: Optional[str] = None) -> Dict[str, Any]:
    stream = data.get('stream', '') or ''
    file_path = data.get('file_path', '') or data.get('file_name', '') or ''
    return {
        'event_id': str(uuid.uuid4()),
        'device_id': device_id or stream,
        'app': data.get('app', 'record'),
        'stream': stream,
        'file_path': file_path,
        'cwd': '',
        'source': 'zlm',
        'media_node_id': data.get('mediaServerId'),
        'segment_start_ms': data.get('start_time'),
        'created_at': datetime.now(timezone.utc).isoformat(),
    }


def publish_dvr_event(event: Dict[str, Any]) -> bool:
    device_id = event.get('device_id') or event.get('stream') or 'unknown'
    try:
        producer = _get_producer()
        producer.send(TOPIC_DVR_COMPLETED, key=device_id, value=event)
        producer.flush(timeout=10)
        logger.debug('DVR 事件已入队 topic=%s device_id=%s file=%s',
                     TOPIC_DVR_COMPLETED, device_id, event.get('file_path'))
        return True
    except Exception as e:
        logger.error('DVR 事件入队失败 device_id=%s error=%s', device_id, e)
        return False


def publish_dvr_dlq(event: Dict[str, Any], error: str) -> None:
    payload = {**event, 'error': error, 'dlq_at': datetime.now(timezone.utc).isoformat()}
    try:
        producer = _get_producer()
        producer.send(TOPIC_DVR_DLQ, key=event.get('device_id', 'unknown'), value=payload)
        producer.flush(timeout=10)
    except Exception as e:
        logger.error('写入 DLQ 失败: %s', e)


def enqueue_srs_dvr_hook(data: Dict[str, Any], device_id: Optional[str] = None) -> bool:
    event = build_event_from_srs_hook(data, device_id=device_id)
    return publish_dvr_event(event)


def enqueue_zlm_record_hook(data: Dict[str, Any], device_id: Optional[str] = None) -> bool:
    event = build_event_from_zlm_hook(data, device_id=device_id)
    return publish_dvr_event(event)


def publish_snap_event(event: Dict[str, Any]) -> bool:
    device_id = event.get('device_id') or 'unknown'
    try:
        producer = _get_producer()
        producer.send(TOPIC_SNAP_COMPLETED, key=device_id, value=event)
        producer.flush(timeout=10)
        logger.debug('抓拍事件已入队 topic=%s device_id=%s file=%s',
                     TOPIC_SNAP_COMPLETED, device_id, event.get('file_path'))
        return True
    except Exception as e:
        logger.error('抓拍事件入队失败 device_id=%s error=%s', device_id, e)
        return False


def publish_snap_dlq(event: Dict[str, Any], error: str) -> None:
    payload = {**event, 'error': error, 'dlq_at': datetime.now(timezone.utc).isoformat()}
    try:
        producer = _get_producer()
        producer.send(TOPIC_SNAP_DLQ, key=event.get('device_id', 'unknown'), value=payload)
        producer.flush(timeout=10)
    except Exception as e:
        logger.error('抓拍 DLQ 写入失败: %s', e)
