#!/usr/bin/env python3
"""Snap Upload Worker：消费 media.snap.completed。"""
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
logger = logging.getLogger('snap-upload-worker')

TOPIC = os.getenv('MEDIA_KAFKA_SNAP_TOPIC', 'media.snap.completed')
GROUP = os.getenv('MEDIA_KAFKA_SNAP_CONSUMER_GROUP', 'upload-worker-snap')
BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
if 'Kafka' in BOOTSTRAP or 'kafka-server' in BOOTSTRAP:
    BOOTSTRAP = 'localhost:9092'


def run():
    from kafka import KafkaConsumer
    from app.services.snap_upload_service import process_snap_event
    from app.services.media_kafka_service import publish_snap_dlq
    from run import create_app

    app = create_app(start_background_tasks=False)
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP.split(','),
        group_id=GROUP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        key_deserializer=lambda k: k.decode('utf-8') if k else None,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        max_poll_records=10,
        session_timeout_ms=60000,
        heartbeat_interval_ms=10000,
    )
    logger.info('Snap Worker 启动 topic=%s group=%s', TOPIC, GROUP)

    with app.app_context():
        while True:
            try:
                records = consumer.poll(timeout_ms=1000, max_records=10)
                if not records:
                    continue
                for _, messages in records.items():
                    for msg in messages:
                        event = msg.value or {}
                        try:
                            if process_snap_event(event):
                                consumer.commit()
                            else:
                                retries = int(event.get('_retry', 0)) + 1
                                if retries >= 8:
                                    publish_snap_dlq(event, 'max retries exceeded')
                                    consumer.commit()
                                else:
                                    time.sleep(min(retries * 2, 20))
                        except Exception as e:
                            logger.error('抓拍处理异常: %s', e, exc_info=True)
                            publish_snap_dlq(event, str(e))
                            consumer.commit()
            except Exception as e:
                logger.error('Consumer 轮询异常: %s', e, exc_info=True)
                time.sleep(5)


if __name__ == '__main__':
    run()
