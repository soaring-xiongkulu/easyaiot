"""
抓拍图上传流水线：本地 CephFS → MinIO snap-space → 元数据 → 删本地。
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import quote

from app.services.media_dvr_utils import resolve_playback_absolute_path
from app.services.media_kafka_service import publish_snap_dlq
from app.services.playback_disk_guard_service import get_snap_staging_dir, remove_playback_file
from app.utils.minio_bucket_policy import ensure_bucket_public_read_write_policy
from app.utils.service_urls import minio_storage_enabled, now_shanghai_naive
from models import SnapSpace, db

logger = logging.getLogger(__name__)


def _wait_snap_file_stable(file_path: str, max_retries: int = 6, interval: float = 0.5) -> int:
    last = -1
    stable = 0
    for _ in range(max_retries):
        if not os.path.isfile(file_path):
            stable = 0
        else:
            try:
                size = os.path.getsize(file_path)
                if size == last and size > 0:
                    stable += 1
                    if stable >= 2:
                        return size
                else:
                    stable = 1 if size > 0 else 0
                last = size
            except OSError:
                stable = 0
        import time
        time.sleep(interval)
    return last if last > 0 else 0


def build_snap_event(
    device_id: str,
    file_path: str,
    *,
    source: str = 'algorithm',
    task_id: Optional[int] = None,
    space_id: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        'event_id': str(uuid.uuid4()),
        'device_id': device_id,
        'file_path': file_path,
        'source': source,
        'task_id': task_id,
        'space_id': space_id,
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }


def process_snap_event(event: Dict[str, Any]) -> bool:
    device_id = (event.get('device_id') or '').strip()
    file_path = event.get('file_path') or ''
    if not device_id or not file_path:
        return False

    absolute_path = resolve_playback_absolute_path(file_path)
    file_size = _wait_snap_file_stable(absolute_path)
    if file_size <= 0:
        logger.warning('抓拍文件未就绪 file=%s', absolute_path)
        return False

    snap_space = SnapSpace.query.filter_by(device_id=device_id).first()
    if not snap_space:
        logger.warning('设备无抓拍空间 device_id=%s', device_id)
        return False

    filename = os.path.basename(absolute_path)
    object_name = f'{device_id}/{filename}'
    bucket_name = snap_space.bucket_name or 'snap-space'

    from models import SnapImage
    if SnapImage.query.filter_by(bucket_name=bucket_name, object_name=object_name).first():
        if minio_storage_enabled():
            remove_playback_file(absolute_path, reason='抓拍已上传')
        return True

    if not minio_storage_enabled():
        file_url = absolute_path
        try:
            from app.services.space_file_metadata_service import upsert_snap_image
            upsert_snap_image(
                space_id=snap_space.id,
                device_id=device_id,
                object_name=object_name,
                bucket_name=bucket_name,
                file_size=file_size,
                url=file_url,
                captured_at=now_shanghai_naive(),
                task_id=event.get('task_id'),
                source=event.get('source') or 'algorithm',
            )
        except Exception as e:
            logger.error('mini 形态抓拍元数据写入失败 device=%s error=%s', device_id, e, exc_info=True)
            db.session.rollback()
            return False
        logger.info('mini 形态抓拍保留本地路径 device=%s path=%s size=%s', device_id, absolute_path, file_size)
        return True

    from app.services.record_space_service import get_minio_client
    minio_client = get_minio_client()
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    ensure_bucket_public_read_write_policy(minio_client, bucket_name)

    try:
        minio_client.fput_object(
            bucket_name, object_name, absolute_path, content_type='image/jpeg',
        )
    except Exception as e:
        logger.error('抓拍上传 MinIO 失败 device=%s object=%s error=%s', device_id, object_name, e)
        publish_snap_dlq(event, str(e))
        return False

    file_url = f'/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(object_name, safe="")}'
    try:
        from app.services.space_file_metadata_service import upsert_snap_image
        upsert_snap_image(
            space_id=snap_space.id,
            device_id=device_id,
            object_name=object_name,
            bucket_name=bucket_name,
            file_size=file_size,
            url=file_url,
            captured_at=now_shanghai_naive(),
            task_id=event.get('task_id'),
            source=event.get('source') or 'algorithm',
        )
    except Exception as e:
        logger.error('抓拍元数据写入失败 device=%s error=%s', device_id, e, exc_info=True)
        db.session.rollback()
        return False

    remove_playback_file(absolute_path, reason='抓拍已上传MinIO')
    logger.info('抓拍上传完成 device=%s object=%s size=%s', device_id, object_name, file_size)
    return True
