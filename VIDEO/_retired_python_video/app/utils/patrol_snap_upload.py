"""巡检帧上传抓拍空间（MinIO / Kafka 暂存）。"""
from __future__ import annotations

import io
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def upload_patrol_frame_to_snap_space(
    device_id: str,
    frame: np.ndarray,
    *,
    task_id: Optional[int] = None,
    session_id: Optional[int] = None,
) -> bool:
    """将巡检帧写入设备抓拍空间，不产生告警。"""
    try:
        from app.utils.snap_media_client import stage_snap_frame
        from app.services.media_kafka_service import is_snap_kafka_mode

        staging = os.getenv('MEDIA_SNAP_STAGING_ENABLED', '').lower() in ('1', 'true', 'yes')
        ref_id = task_id or session_id
        if staging or is_snap_kafka_mode():
            return stage_snap_frame(
                device_id,
                frame,
                source='patrol',
                task_id=ref_id,
            )
    except Exception as exc:
        logger.debug('巡检抓拍暂存不可用，回退 MinIO: %s', exc)

    endpoint = os.getenv('MINIO_ENDPOINT')
    access_key = os.getenv('MINIO_ACCESS_KEY')
    secret_key = os.getenv('MINIO_SECRET_KEY')
    if not endpoint or not access_key or not secret_key:
        return False

    try:
        from minio import Minio
    except ImportError:
        return False

    secure = os.getenv('MINIO_SECURE', 'false').lower() in ('1', 'true', 'yes')
    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    bucket_name = 'snap-space'

    try:
        from flask import Flask
        from models import db, SnapSpace

        database_url = os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://', 1)
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        with app.app_context():
            snap_space = SnapSpace.query.filter_by(device_id=device_id).first()
            if snap_space and snap_space.bucket_name:
                bucket_name = snap_space.bucket_name
    except Exception as exc:
        logger.debug('查询抓拍空间失败，使用默认 bucket: %s', exc)

    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
    except Exception as exc:
        logger.warning('创建 bucket 失败: %s', exc)
        return False

    ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        return False

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    object_name = f'{device_id}/{uuid.uuid4().hex[:8]}_{ts}.jpg'
    data = encoded.tobytes()
    try:
        client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type='image/jpeg',
        )
        try:
            from app.services.space_file_metadata_service import upsert_snap_image
            from flask import Flask
            from models import db, SnapSpace

            database_url = os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://', 1)
            app = Flask(__name__)
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            db.init_app(app)
            with app.app_context():
                snap_space = SnapSpace.query.filter_by(device_id=device_id).first()
                if snap_space:
                    upsert_snap_image(
                        space_id=snap_space.id,
                        device_id=device_id,
                        object_name=object_name,
                        bucket_name=bucket_name,
                        file_size=len(data),
                        source='patrol',
                    )
        except Exception as meta_err:
            logger.debug('写入抓拍元数据失败: %s', meta_err)
        return True
    except Exception as exc:
        logger.warning('巡检上传抓拍空间失败 device=%s: %s', device_id, exc)
        return False
