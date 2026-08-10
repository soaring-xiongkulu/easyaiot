"""
DVR 段上传流水线：MinIO 上传、Playback 写入、本地文件清理。
供 Hook 同步模式与 Kafka Upload Worker 共用。
"""
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import quote

import cv2
from minio.error import S3Error

from app.services.dvr_device_resolver import resolve_device_from_hook
from app.services.media_dvr_utils import (
    extract_thumbnail_from_video,
    ffprobe_video_duration_seconds,
    parse_srs_dvr_path_date,
    resolve_playback_absolute_path,
    srs_dvr_min_file_bytes,
    wait_dvr_file_stable,
)
from app.services.media_kafka_service import publish_dvr_dlq
from app.utils.minio_bucket_policy import ensure_bucket_public_read_write_policy
from app.utils.service_urls import ensure_shanghai_aware, epoch_to_shanghai_datetime, minio_storage_enabled
from models import Device, Playback, db

logger = logging.getLogger(__name__)


def process_dvr_event(event: Dict[str, Any]) -> bool:
    """处理单条 DVR Kafka 事件或 Hook 同步任务。成功返回 True。"""
    stream = event.get('stream', '') or ''
    file_path = event.get('file_path', '') or ''
    cwd = event.get('cwd', '') or ''
    device_id = event.get('device_id') or stream

    device = Device.query.get(device_id) if device_id else None
    if not device:
        resolved_id, device = resolve_device_from_hook(stream, file_path)
        if device:
            device_id = resolved_id

    if not device:
        absolute_file_path = resolve_playback_absolute_path(file_path, cwd) if file_path else ''
        if absolute_file_path:
            from app.services.playback_disk_guard_service import remove_playback_file
            remove_playback_file(absolute_file_path, reason='设备已删除')
        logger.info('DVR 上传：设备不存在，已丢弃本地回放 stream=%s file=%s', stream, file_path)
        return True

    from app.services.record_space_service import (
        create_record_space_for_device,
        get_minio_client,
        get_record_space_by_device_id,
    )

    record_space = get_record_space_by_device_id(device_id)
    if not record_space:
        try:
            record_space = create_record_space_for_device(device_id, device.name)
        except Exception as e:
            logger.error('创建设备录像空间失败 device_id=%s error=%s', device_id, e, exc_info=True)
            return False

    absolute_file_path = resolve_playback_absolute_path(file_path, cwd)
    file_size = wait_dvr_file_stable(absolute_file_path)
    if file_size <= 0:
        min_bytes = srs_dvr_min_file_bytes()
        try:
            if os.path.exists(absolute_file_path):
                sz = os.path.getsize(absolute_file_path)
                if 0 < sz < min_bytes:
                    logger.info(
                        'DVR 片段过小已丢弃 file=%s size=%s min=%s',
                        absolute_file_path, sz, min_bytes,
                    )
                    _cleanup_local_file(absolute_file_path, device_id)
                    return True
        except OSError:
            pass
        logger.warning('DVR 文件未就绪或过小 file=%s', absolute_file_path)
        return False

    try:
        from app.services.playback_disk_guard_service import ensure_playback_path_deletable
        ensure_playback_path_deletable(absolute_file_path)
    except Exception as perm_err:
        logger.warning('修复回放文件权限失败 file=%s error=%s', absolute_file_path, perm_err)

    parsed_date_dir, parsed_record_time = parse_srs_dvr_path_date(absolute_file_path)
    if parsed_date_dir and parsed_record_time:
        date_dir = parsed_date_dir
        record_time = parsed_record_time
    else:
        try:
            record_time = epoch_to_shanghai_datetime(os.path.getmtime(absolute_file_path))
            date_dir = record_time.strftime('%Y/%m/%d')
        except OSError:
            record_time = datetime.now(timezone(timedelta(hours=8)))
            date_dir = record_time.strftime('%Y/%m/%d')

    filename = os.path.basename(absolute_file_path)
    file_ext = os.path.splitext(filename)[1].lower()
    object_name = f'{device_id}/{date_dir}/{filename}'

    from models import RecordFile
    existing_rf = RecordFile.query.filter_by(device_id=device_id, object_name=object_name).first()
    if existing_rf:
        if minio_storage_enabled():
            _cleanup_local_file(absolute_file_path, device_id)
        duration = int(existing_rf.duration or 0) or int(ffprobe_video_duration_seconds(absolute_file_path))
        file_path_url = (existing_rf.url or '').strip() or absolute_file_path
        _patch_alert_record(device_id, record_time, duration, file_path_url)
        logger.debug('DVR 已存在元数据，仍回写告警 record_path object=%s', object_name)
        return True

    if not minio_storage_enabled():
        content_type_map = {
            '.mp4': 'video/mp4', '.flv': 'video/x-flv', '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime', '.mkv': 'video/x-matroska', '.ts': 'video/mp2t',
        }
        local_content_type = content_type_map.get(file_ext, 'video/mp4')
        local_bucket_name = record_space.bucket_name
        file_path_url = absolute_file_path
        duration = int(ffprobe_video_duration_seconds(absolute_file_path))
        _upsert_playback(device, device_id, file_path_url, object_name, record_time, file_size, duration, None)
        _upsert_record_metadata(record_space, device_id, object_name, local_bucket_name, filename,
                                file_size, local_content_type, file_path_url, None, duration, record_time)
        _patch_alert_record(device_id, record_time, duration, file_path_url)
        logger.info('mini 形态 DVR 保留本地路径 device_id=%s path=%s size=%s', device_id, absolute_file_path, file_size)
        return True

    content_type_map = {
        '.mp4': 'video/mp4', '.flv': 'video/x-flv', '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime', '.mkv': 'video/x-matroska', '.ts': 'video/mp2t',
    }
    content_type = content_type_map.get(file_ext, 'video/mp4')
    bucket_name = record_space.bucket_name
    minio_client = get_minio_client()

    if not minio_client.bucket_exists(bucket_name):
        try:
            minio_client.make_bucket(bucket_name)
        except Exception as e:
            logger.error('创建 MinIO bucket 失败 bucket=%s error=%s', bucket_name, e, exc_info=True)
            return False
    ensure_bucket_public_read_write_policy(minio_client, bucket_name)

    try:
        minio_client.fput_object(bucket_name, object_name, absolute_file_path, content_type=content_type)
    except S3Error as e:
        logger.error('MinIO 上传失败 device_id=%s object=%s error=%s', device_id, object_name, e, exc_info=True)
        publish_dvr_dlq(event, str(e))
        return False

    file_path_url = f'/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(object_name, safe="")}'
    thumbnail_path = _upload_thumbnail(minio_client, bucket_name, device_id, date_dir, filename, absolute_file_path)
    duration = int(ffprobe_video_duration_seconds(absolute_file_path))
    _upsert_playback(device, device_id, file_path_url, object_name, record_time, file_size, duration, thumbnail_path)
    _upsert_record_metadata(record_space, device_id, object_name, bucket_name, filename,
                            file_size, content_type, file_path_url, thumbnail_path, duration, record_time)
    _patch_alert_record(device_id, record_time, duration, file_path_url)
    _cleanup_local_file(absolute_file_path, device_id)
    logger.info('DVR 上传完成 device_id=%s object=%s size=%s', device_id, object_name, file_size)
    return True


def _upload_thumbnail(minio_client, bucket_name, device_id, date_dir, filename, absolute_file_path) -> Optional[str]:
    try:
        frame = extract_thumbnail_from_video(absolute_file_path, output_path=None, frame_position=0.1)
        if frame is None:
            return None
        thumbnail_filename = os.path.splitext(filename)[0] + '.jpg'
        thumbnail_object_name = f'{device_id}/{date_dir}/{thumbnail_filename}'
        success, encoded_image = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            return None
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_thumbnail_path = tmp_file.name
            tmp_file.write(encoded_image.tobytes())
        try:
            minio_client.fput_object(
                bucket_name, thumbnail_object_name, tmp_thumbnail_path, content_type='image/jpeg',
            )
            return f'/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(thumbnail_object_name, safe="")}'
        finally:
            try:
                os.remove(tmp_thumbnail_path)
            except OSError:
                pass
    except Exception as e:
        logger.error('封面上传失败 device_id=%s error=%s', device_id, e, exc_info=True)
    return None


def _upsert_playback(device, device_id, file_path_url, object_name, record_time, file_size, duration, thumbnail_path):
    try:
        shanghai_tz = timezone(timedelta(hours=8))
        record_time = ensure_shanghai_aware(record_time)
        existing = Playback.query.filter_by(file_path=file_path_url, device_id=device_id).first()
        if not existing:
            existing = Playback.query.filter_by(file_path=object_name, device_id=device_id).first()
        if existing:
            existing.file_path = file_path_url
            existing.thumbnail_path = thumbnail_path
            existing.file_size = file_size
            existing.event_time = record_time
            if duration > 0:
                existing.duration = duration
            existing.updated_at = datetime.now(shanghai_tz)
        else:
            current_time = datetime.now(shanghai_tz)
            playback = Playback(
                file_path=file_path_url,
                event_time=record_time,
                device_id=device_id,
                device_name=device.name if device else '',
                duration=duration if duration > 0 else 1,
                thumbnail_path=thumbnail_path,
                file_size=file_size,
                created_at=current_time,
                updated_at=current_time,
            )
            db.session.add(playback)
        db.session.commit()
    except Exception as e:
        logger.error('Playback 写入失败 device_id=%s error=%s', device_id, e, exc_info=True)
        db.session.rollback()


def _upsert_record_metadata(record_space, device_id, object_name, bucket_name, filename,
                            file_size, content_type, file_path_url, thumbnail_path, duration, record_time):
    try:
        from app.services.space_file_metadata_service import upsert_record_file
        event_time_naive = record_time.replace(tzinfo=None) if hasattr(record_time, 'tzinfo') and record_time.tzinfo else record_time
        upsert_record_file(
            space_id=record_space.id,
            device_id=device_id,
            object_name=object_name,
            bucket_name=bucket_name,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            url=file_path_url,
            thumbnail_url=thumbnail_path,
            duration=duration if duration > 0 else 1,
            event_time=event_time_naive,
            source='dvr',
        )
    except Exception as e:
        logger.error('录像元数据写入失败 device_id=%s error=%s', device_id, e, exc_info=True)
        db.session.rollback()


def _patch_alert_record(device_id, record_time, duration, file_path_url):
    try:
        from app.services.alert_service import patch_alerts_record

        record_time = ensure_shanghai_aware(record_time)
        event_time_str = record_time.strftime('%Y-%m-%d %H:%M:%S')
        patch_alerts_record({
            'event_time': event_time_str,
            'duration': duration if duration > 0 else 1,
            'device_id': device_id,
            'file_path': file_path_url,
        })
    except Exception as e:
        logger.error('关联告警 record_path 失败 device_id=%s error=%s', device_id, e, exc_info=True)


def _cleanup_local_file(absolute_file_path, device_id):
    try:
        from app.services.playback_disk_guard_service import (
            cleanup_device_recordings,
            remove_local_after_minio_upload,
        )
        remove_local_after_minio_upload(absolute_file_path)
        cleanup_device_recordings(device_id)
    except Exception as e:
        logger.error('本地回放清理失败 device_id=%s error=%s', device_id, e, exc_info=True)
