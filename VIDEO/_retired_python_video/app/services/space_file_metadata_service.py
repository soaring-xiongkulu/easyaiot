"""
录像/抓拍空间文件元数据服务
上传 MinIO 后写入 DB，列表查询走数据库分页，避免 MinIO 全量列举超时。
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote, urlparse, parse_qs

from models import db, RecordFile, SnapImage, Playback, RecordSpace, SnapSpace
from app.services.record_space_service import get_minio_client
from app.utils.service_urls import now_shanghai_naive, normalize_to_shanghai_naive

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.flv')


def build_download_url(bucket_name: str, object_name: str) -> str:
    return f"/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(object_name, safe='')}"


def extract_prefix_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    if not url.startswith('/api/v1/buckets/'):
        return url
    try:
        parsed = urlparse(url)
        return parse_qs(parsed.query).get('prefix', [None])[0]
    except Exception:
        return None


def upsert_record_file(
    *,
    space_id: int,
    device_id: str,
    object_name: str,
    bucket_name: str,
    filename: Optional[str] = None,
    file_size: Optional[int] = None,
    content_type: str = 'video/mp4',
    etag: Optional[str] = None,
    url: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    duration: Optional[int] = None,
    event_time: Optional[datetime] = None,
    source: str = 'dvr',
) -> RecordFile:
    """上传 MinIO 后写入或更新录像元数据"""
    filename = filename or object_name.split('/')[-1]
    url = url or build_download_url(bucket_name, object_name)
    event_time = event_time or datetime.utcnow()

    record = RecordFile.query.filter_by(bucket_name=bucket_name, object_name=object_name).first()
    if record:
        record.space_id = space_id
        record.device_id = device_id
        record.filename = filename
        if file_size is not None:
            record.file_size = file_size
        record.content_type = content_type
        if etag:
            record.etag = etag
        record.url = url
        if thumbnail_url is not None:
            record.thumbnail_url = thumbnail_url
        if duration is not None:
            record.duration = duration
        record.event_time = event_time
        record.source = source
        record.updated_at = datetime.utcnow()
    else:
        record = RecordFile(
            space_id=space_id,
            device_id=device_id,
            object_name=object_name,
            bucket_name=bucket_name,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            etag=etag,
            url=url,
            thumbnail_url=thumbnail_url,
            duration=duration,
            event_time=event_time,
            source=source,
        )
        db.session.add(record)
    db.session.commit()
    return record


def upsert_snap_image(
    *,
    space_id: int,
    device_id: str,
    object_name: str,
    bucket_name: str,
    filename: Optional[str] = None,
    file_size: Optional[int] = None,
    content_type: str = 'image/jpeg',
    etag: Optional[str] = None,
    url: Optional[str] = None,
    captured_at: Optional[datetime] = None,
    task_id: Optional[int] = None,
    source: str = 'snap',
) -> SnapImage:
    """上传 MinIO 后写入或更新抓拍元数据"""
    filename = filename or object_name.split('/')[-1]
    url = url or build_download_url(bucket_name, object_name)
    captured_at = captured_at or now_shanghai_naive()

    image = SnapImage.query.filter_by(bucket_name=bucket_name, object_name=object_name).first()
    if image:
        image.space_id = space_id
        image.device_id = device_id
        image.filename = filename
        if file_size is not None:
            image.file_size = file_size
        image.content_type = content_type
        if etag:
            image.etag = etag
        image.url = url
        image.captured_at = captured_at
        if task_id is not None:
            image.task_id = task_id
        image.source = source
    else:
        image = SnapImage(
            space_id=space_id,
            device_id=device_id,
            object_name=object_name,
            bucket_name=bucket_name,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            etag=etag,
            url=url,
            captured_at=captured_at,
            task_id=task_id,
            source=source,
        )
        db.session.add(image)
    db.session.commit()
    return image


def delete_record_files_metadata(bucket_name: str, object_names: List[str]) -> int:
    """删除录像 DB 元数据（含 Playback 关联记录）"""
    if not object_names:
        return 0

    deleted = RecordFile.query.filter(
        RecordFile.bucket_name == bucket_name,
        RecordFile.object_name.in_(object_names),
    ).delete(synchronize_session=False)

    url_candidates = [build_download_url(bucket_name, name) for name in object_names]
    all_paths = list(set(object_names + url_candidates))
    Playback.query.filter(Playback.file_path.in_(all_paths)).delete(synchronize_session=False)

    db.session.commit()
    return deleted


def delete_snap_images_metadata(bucket_name: str, object_names: List[str]) -> int:
    """删除抓拍 DB 元数据"""
    if not object_names:
        return 0
    deleted = SnapImage.query.filter(
        SnapImage.bucket_name == bucket_name,
        SnapImage.object_name.in_(object_names),
    ).delete(synchronize_session=False)
    db.session.commit()
    return deleted


def count_record_files(space_id: int) -> int:
    return RecordFile.query.filter_by(space_id=space_id).count()


def count_snap_images(space_id: int) -> int:
    return SnapImage.query.filter_by(space_id=space_id).count()


def _is_video_file(filename: str) -> bool:
    return filename.lower().endswith(VIDEO_EXTENSIONS)


def sync_record_files_from_minio(space_id: int) -> Dict:
    """从 MinIO 回填录像元数据到数据库（一次性迁移/同步操作）"""
    record_space = RecordSpace.query.get_or_404(space_id)
    bucket_name = record_space.bucket_name
    device_id = record_space.device_id

    minio_client = get_minio_client()
    if not minio_client.bucket_exists(bucket_name):
        return {'synced_count': 0, 'skipped_count': 0, 'error_count': 0}

    prefix = f"{device_id}/" if device_id else ""
    synced = skipped = errors = 0
    batch = 0

    for obj in minio_client.list_objects(bucket_name, prefix=prefix, recursive=True):
        if obj.object_name.endswith('/'):
            continue
        filename = obj.object_name.split('/')[-1]
        if not _is_video_file(filename):
            continue

        existing = RecordFile.query.filter_by(bucket_name=bucket_name, object_name=obj.object_name).first()
        if existing:
            skipped += 1
            continue

        try:
            stat = minio_client.stat_object(bucket_name, obj.object_name)
            obj_device_id = obj.object_name.split('/')[0] if '/' in obj.object_name else (device_id or 'unknown')

            playback = Playback.query.filter(
                Playback.device_id == obj_device_id,
                Playback.file_path.in_([
                    obj.object_name,
                    build_download_url(bucket_name, obj.object_name),
                ]),
            ).first()

            thumbnail_url = None
            duration = None
            event_time = stat.last_modified.replace(tzinfo=None) if stat.last_modified else datetime.utcnow()

            if playback:
                duration = playback.duration
                thumbnail_url = playback.thumbnail_path
                if playback.event_time:
                    event_time = playback.event_time.replace(tzinfo=None) if playback.event_time.tzinfo else playback.event_time
            else:
                thumb_name = obj.object_name.rsplit('.', 1)[0] + '.jpg'
                try:
                    minio_client.stat_object(bucket_name, thumb_name)
                    thumbnail_url = build_download_url(bucket_name, thumb_name)
                except Exception:
                    pass

            upsert_record_file(
                space_id=space_id,
                device_id=obj_device_id,
                object_name=obj.object_name,
                bucket_name=bucket_name,
                filename=filename,
                file_size=stat.size,
                content_type=stat.content_type or 'video/mp4',
                etag=stat.etag,
                thumbnail_url=thumbnail_url,
                duration=duration,
                event_time=event_time,
                source='dvr',
            )
            synced += 1
            batch += 1
            if batch >= 100:
                batch = 0
        except Exception as e:
            errors += 1
            logger.warning(f"同步录像元数据失败: {obj.object_name}, error={e}")

    return {'synced_count': synced, 'skipped_count': skipped, 'error_count': errors}


def sync_snap_images_from_minio(space_id: int) -> Dict:
    """从 MinIO 回填抓拍元数据到数据库"""
    snap_space = SnapSpace.query.get_or_404(space_id)
    bucket_name = snap_space.bucket_name
    device_id = snap_space.device_id

    if not device_id:
        return {'synced_count': 0, 'skipped_count': 0, 'error_count': 0}

    minio_client = get_minio_client()
    if not minio_client.bucket_exists(bucket_name):
        return {'synced_count': 0, 'skipped_count': 0, 'error_count': 0}

    prefix = f"{device_id}/"
    synced = skipped = errors = 0

    for obj in minio_client.list_objects(bucket_name, prefix=prefix, recursive=True):
        if obj.object_name.endswith('/'):
            continue

        existing = SnapImage.query.filter_by(bucket_name=bucket_name, object_name=obj.object_name).first()
        if existing:
            skipped += 1
            continue

        try:
            stat = minio_client.stat_object(bucket_name, obj.object_name)
            upsert_snap_image(
                space_id=space_id,
                device_id=device_id,
                object_name=obj.object_name,
                bucket_name=bucket_name,
                file_size=stat.size,
                content_type=stat.content_type or 'image/jpeg',
                etag=stat.etag,
                captured_at=(
                    normalize_to_shanghai_naive(stat.last_modified)
                    if stat.last_modified
                    else now_shanghai_naive()
                ),
                source='snap',
            )
            synced += 1
        except Exception as e:
            errors += 1
            logger.warning(f"同步抓拍元数据失败: {obj.object_name}, error={e}")

    return {'synced_count': synced, 'skipped_count': skipped, 'error_count': errors}
