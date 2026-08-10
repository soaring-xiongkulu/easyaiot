"""
抓拍图片管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import io
import logging
import os
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import current_app
from minio.error import S3Error

from models import db, SnapSpace, SnapImage
from app.services.snap_space_service import get_minio_client
from app.services.playback_disk_guard_service import get_snap_staging_dir
from app.utils.service_urls import minio_storage_enabled
from app.services.space_file_metadata_service import (
    delete_snap_images_metadata,
    sync_snap_images_from_minio,
)

logger = logging.getLogger(__name__)


def list_snap_images(
    space_id: int,
    device_id: Optional[str] = None,
    page_no: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    source: Optional[str] = None,
) -> Dict:
    """获取抓拍图片列表（数据库分页）"""
    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        query = SnapImage.query.filter_by(space_id=space_id)

        effective_device_id = device_id or snap_space.device_id
        if effective_device_id:
            query = query.filter(SnapImage.device_id == effective_device_id)
        elif not device_id:
            logger.warning(f"抓拍空间 {space_id} 没有关联设备，返回空列表")
            return {'items': [], 'total': 0, 'page_no': page_no, 'page_size': page_size}

        if search:
            query = query.filter(SnapImage.filename.ilike(f'%{search}%'))
        if start_time:
            query = query.filter(SnapImage.captured_at >= start_time)
        if end_time:
            query = query.filter(SnapImage.captured_at <= end_time)
        if source:
            query = query.filter(SnapImage.source == source)

        query = query.order_by(SnapImage.captured_at.desc())
        pagination = query.paginate(page=page_no, per_page=page_size, error_out=False)

        return {
            'items': [item.to_list_item() for item in pagination.items],
            'total': pagination.total,
            'page_no': page_no,
            'page_size': page_size,
        }
    except Exception as e:
        logger.error(f"获取抓拍图片列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取抓拍图片列表失败: {str(e)}")


def delete_snap_images(space_id: int, object_names: List[str]) -> Dict:
    """批量删除抓拍图片（MinIO/本地 + 数据库）"""
    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        bucket_name = snap_space.bucket_name

        deleted_count = 0
        failed_count = 0
        failed_objects = []

        if not minio_storage_enabled():
            snap_root = get_snap_staging_dir()
            for object_name in object_names:
                local_path = os.path.join(snap_root, object_name.replace('/', os.sep))
                try:
                    if os.path.isfile(local_path):
                        os.remove(local_path)
                    deleted_count += 1
                    logger.info('mini 形态删除抓拍图片: %s', local_path)
                except OSError as e:
                    failed_count += 1
                    failed_objects.append(object_name)
                    logger.warning('mini 形态删除抓拍图片失败: %s error=%s', local_path, e)
        else:
            minio_client = get_minio_client()
            if not minio_client.bucket_exists(bucket_name):
                raise ValueError(f"抓拍空间的MinIO bucket不存在: {bucket_name}")

            for object_name in object_names:
                try:
                    minio_client.remove_object(bucket_name, object_name)
                    deleted_count += 1
                    logger.info(f"删除抓拍图片成功: {bucket_name}/{object_name}")
                except Exception as e:
                    failed_count += 1
                    failed_objects.append(object_name)
                    logger.warning(f"删除抓拍图片失败: {bucket_name}/{object_name}, error={str(e)}")

        success_objects = [n for n in object_names if n not in failed_objects]
        delete_snap_images_metadata(bucket_name, success_objects)

        return {
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'failed_objects': failed_objects,
        }
    except Exception as e:
        logger.error(f"批量删除抓拍图片失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"批量删除抓拍图片失败: {str(e)}")


def get_snap_image(space_id: int, object_name: str):
    """获取抓拍图片内容"""
    import mimetypes
    import os

    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        bucket_name = snap_space.bucket_name

        if not minio_storage_enabled():
            record = SnapImage.query.filter_by(
                space_id=space_id,
                object_name=object_name,
            ).first()
            local_path = (record.url if record and record.url else '').strip()
            if local_path.startswith('/video/'):
                local_path = ''
            if not local_path or not os.path.isfile(local_path):
                local_path = os.path.join(get_snap_staging_dir(), object_name.replace('/', os.sep))
            if not os.path.isfile(local_path):
                raise ValueError(f"图片不存在: {object_name}")
            with open(local_path, 'rb') as handle:
                content = handle.read()
            filename = object_name.split('/')[-1]
            guessed, _ = mimetypes.guess_type(filename)
            return content, guessed or 'image/jpeg', filename

        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            raise ValueError(f"抓拍空间的MinIO bucket不存在: {bucket_name}")

        try:
            stat = minio_client.stat_object(bucket_name, object_name)
            data = minio_client.get_object(bucket_name, object_name)
            content = data.read()
            data.close()
            data.release_conn()
            return content, stat.content_type, object_name.split('/')[-1]
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise ValueError(f"图片不存在: {object_name}")
            raise
    except Exception as e:
        logger.error(f"获取抓拍图片失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取抓拍图片失败: {str(e)}")


def cleanup_old_images_by_save_time(space_id: int, save_time_hours: int) -> Dict:
    """根据保存时长（小时）清理旧的抓拍图片"""
    try:
        from app.services.space_save_time_service import save_time_cutoff_naive

        snap_space = SnapSpace.query.get_or_404(space_id)
        bucket_name = snap_space.bucket_name
        save_mode = snap_space.save_mode

        if not snap_space.device_id:
            return {'processed_count': 0, 'deleted_count': 0, 'archived_count': 0, 'error_count': 0}

        cutoff_time = save_time_cutoff_naive(save_time_hours)
        if cutoff_time is None:
            return {'processed_count': 0, 'deleted_count': 0, 'archived_count': 0, 'error_count': 0}
        records = SnapImage.query.filter(
            SnapImage.space_id == space_id,
            SnapImage.device_id == snap_space.device_id,
            SnapImage.captured_at < cutoff_time,
        ).all()

        if not records:
            return {'processed_count': 0, 'deleted_count': 0, 'archived_count': 0, 'error_count': 0}

        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            return {'processed_count': 0, 'deleted_count': 0, 'archived_count': 0, 'error_count': 0}

        archive_bucket_name = current_app.config.get('MINIO_ARCHIVE_BUCKET', 'snap-archive')
        if save_mode == 1 and not minio_client.bucket_exists(archive_bucket_name):
            minio_client.make_bucket(archive_bucket_name)

        processed_count = deleted_count = archived_count = error_count = 0

        if save_mode == 0:
            object_names = []
            for record in records:
                try:
                    minio_client.remove_object(bucket_name, record.object_name)
                    object_names.append(record.object_name)
                    deleted_count += 1
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"删除图片失败: {record.object_name}, error={e}")
            delete_snap_images_metadata(bucket_name, object_names)
        else:
            try:
                zip_buffer = io.BytesIO()
                removed_names = []
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for record in records:
                        try:
                            data = minio_client.get_object(bucket_name, record.object_name)
                            file_content = data.read()
                            data.close()
                            data.release_conn()
                            zip_file.writestr(record.filename, file_content)
                            minio_client.remove_object(bucket_name, record.object_name)
                            removed_names.append(record.object_name)
                            deleted_count += 1
                        except Exception as e:
                            error_count += 1
                            logger.error(f"处理图片失败: {record.object_name}, error={e}")

                if zip_buffer.tell() > 0:
                    zip_buffer.seek(0)
                    archive_object_name = f"{snap_space.device_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
                    minio_client.put_object(
                        archive_bucket_name,
                        archive_object_name,
                        zip_buffer,
                        length=zip_buffer.tell(),
                        content_type='application/zip',
                    )
                    archived_count += 1
                    processed_count += len(removed_names)
                    delete_snap_images_metadata(bucket_name, removed_names)
            except Exception as e:
                error_count += len(records)
                logger.error(f"归档抓拍图片失败: error={e}", exc_info=True)

        return {
            'processed_count': processed_count,
            'deleted_count': deleted_count,
            'archived_count': archived_count,
            'error_count': error_count,
        }
    except Exception as e:
        logger.error(f"清理过期图片失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"清理过期图片失败: {str(e)}")


def sync_snap_images_metadata(space_id: int) -> Dict:
    """从 MinIO 同步抓拍元数据到数据库"""
    return sync_snap_images_from_minio(space_id)
