#!/usr/bin/env python3
"""
DVR Upload Worker：消费 media.dvr.completed，上传 MinIO 并清理 CephFS 本地段。
"""
import json
import logging
import os
import sys
import time

VIDEO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if VIDEO_ROOT not in sys.path:
    sys.path.insert(0, VIDEO_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger('media-upload-worker')

TOPIC = os.getenv('MEDIA_KAFKA_DVR_TOPIC', 'media.dvr.completed')
GROUP = os.getenv('MEDIA_KAFKA_DVR_CONSUMER_GROUP', 'upload-worker-dvr')
BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
if 'Kafka' in BOOTSTRAP or 'kafka-server' in BOOTSTRAP:
    BOOTSTRAP = 'localhost:9092'


def _create_app():
    from run import create_app
    return create_app(start_background_tasks=False)


def run():
    from kafka import KafkaConsumer
    from app.services.dvr_upload_service import process_dvr_event
    from app.services.media_kafka_service import publish_dvr_dlq

    app = _create_app()
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP.split(','),
        group_id=GROUP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        key_deserializer=lambda k: k.decode('utf-8') if k else None,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        max_poll_records=5,
        session_timeout_ms=60000,
        heartbeat_interval_ms=10000,
    )
    logger.info('Worker 启动 topic=%s group=%s bootstrap=%s', TOPIC, GROUP, BOOTSTRAP)

    with app.app_context():
        while True:
            try:
                records = consumer.poll(timeout_ms=1000, max_records=5)
                if not records:
                    continue
                for tp, messages in records.items():
                    for msg in messages:
                        event = msg.value or {}
                        try:
                            ok = process_dvr_event(event)
                            if ok:
                                consumer.commit()
                            else:
                                retries = int(event.get('_retry', 0)) + 1
                                if retries >= 12:
                                    publish_dvr_dlq(event, 'max retries exceeded')
                                    consumer.commit()
                                else:
                                    event['_retry'] = retries
                                    logger.warning('DVR 处理失败，稍后重试 device=%s retry=%s',
                                                   event.get('device_id'), retries)
                                    time.sleep(min(retries * 2, 30))
                        except Exception as e:
                            logger.error('DVR 处理异常: %s', e, exc_info=True)
                            publish_dvr_dlq(event, str(e))
                            consumer.commit()
            except Exception as e:
                logger.error('Consumer 轮询异常: %s', e, exc_info=True)
                time.sleep(5)


if __name__ == '__main__':
    run()
