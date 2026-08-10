"""
设备存储空间管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
from datetime import datetime
from typing import Optional, Tuple

from models import db, DeviceStorageConfig, Device
from app.services.snap_space_service import get_minio_client

logger = logging.getLogger(__name__)


def get_or_create_device_storage_config(device_id: str) -> DeviceStorageConfig:
    """获取或创建设备存储配置"""
    try:
        config = DeviceStorageConfig.query.filter_by(device_id=device_id).first()
        if not config:
            # 检查设备是否存在
            device = Device.query.get_or_404(device_id)
            config = DeviceStorageConfig(device_id=device_id)
            db.session.add(config)
            db.session.commit()
            logger.info(f"创建设备存储配置: device_id={device_id}")
        return config
    except Exception as e:
        db.session.rollback()
        logger.error(f"获取或创建设备存储配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取或创建设备存储配置失败: {str(e)}")


def update_device_storage_config(device_id: str, **kwargs) -> DeviceStorageConfig:
    """更新设备存储配置"""
    try:
        config = get_or_create_device_storage_config(device_id)
        
        updatable_fields = [
            'snap_storage_bucket', 'snap_storage_max_size', 'snap_storage_cleanup_enabled',
            'snap_storage_cleanup_threshold', 'snap_storage_cleanup_ratio',
            'video_storage_bucket', 'video_storage_max_size', 'video_storage_cleanup_enabled',
            'video_storage_cleanup_threshold', 'video_storage_cleanup_ratio'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(config, field, kwargs[field])
        
        db.session.commit()
        logger.info(f"更新设备存储配置成功: device_id={device_id}")
        return config
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新设备存储配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新设备存储配置失败: {str(e)}")


def get_bucket_size(bucket_name: str, prefix: Optional[str] = None) -> Tuple[int, int]:
    """计算bucket或指定前缀下的存储空间大小和文件数量
    
    Returns:
        Tuple[int, int]: (总大小（字节）, 文件数量)
    """
    try:
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            return 0, 0
        
        total_size = 0
        file_count = 0
        
        objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
        for obj in objects:
            try:
                stat = minio_client.stat_object(bucket_name, obj.object_name)
                total_size += stat.size
                file_count += 1
            except Exception as e:
                logger.warning(f"获取对象信息失败: {bucket_name}/{obj.object_name}, error={str(e)}")
        
        return total_size, file_count
    except Exception as e:
        logger.error(f"计算bucket大小失败: bucket={bucket_name}, prefix={prefix}, error={str(e)}", exc_info=True)
        return 0, 0


def cleanup_old_files(bucket_name: str, prefix: Optional[str] = None, 
                      cleanup_ratio: float = 0.3) -> Tuple[int, int]:
    """清理最老的文件
    
    Args:
        bucket_name: bucket名称
        prefix: 文件前缀（如设备ID）
        cleanup_ratio: 清理比例（0-1之间）
    
    Returns:
        Tuple[int, int]: (删除的文件数量, 释放的空间（字节）)
    """
    try:
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            return 0, 0
        
        # 获取所有文件及其元数据
        files = []
        objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
        for obj in objects:
            try:
                stat = minio_client.stat_object(bucket_name, obj.object_name)
                files.append({
                    'object_name': obj.object_name,
                    'size': stat.size,
                    'last_modified': stat.last_modified
                })
            except Exception as e:
                logger.warning(f"获取对象信息失败: {bucket_name}/{obj.object_name}, error={str(e)}")
        
        if not files:
            return 0, 0
        
        # 按时间排序（最老的在前）
        files.sort(key=lambda x: x['last_modified'])
        
        # 计算需要删除的文件数量
        delete_count = max(1, int(len(files) * cleanup_ratio))
        files_to_delete = files[:delete_count]
        
        # 删除文件
        deleted_count = 0
        freed_size = 0
        for file_info in files_to_delete:
            try:
                minio_client.remove_object(bucket_name, file_info['object_name'])
                deleted_count += 1
                freed_size += file_info['size']
            except Exception as e:
                logger.warning(f"删除文件失败: {bucket_name}/{file_info['object_name']}, error={str(e)}")
        
        logger.info(f"清理完成: bucket={bucket_name}, prefix={prefix}, "
                   f"删除文件数={deleted_count}, 释放空间={freed_size}字节")
        return deleted_count, freed_size
        
    except Exception as e:
        logger.error(f"清理文件失败: bucket={bucket_name}, prefix={prefix}, error={str(e)}", exc_info=True)
        return 0, 0


def check_and_cleanup_storage(device_id: str) -> dict:
    """检查并清理设备存储空间
    
    Returns:
        dict: 清理结果
    """
    try:
        config = DeviceStorageConfig.query.filter_by(device_id=device_id).first()
        if not config:
            return {'cleaned': False, 'message': '设备存储配置不存在'}
        
        result = {
            'snap_cleaned': False,
            'video_cleaned': False,
            'snap_deleted_count': 0,
            'snap_freed_size': 0,
            'video_deleted_count': 0,
            'video_freed_size': 0
        }
        
        # 检查抓拍图片存储
        if config.snap_storage_bucket and config.snap_storage_max_size and config.snap_storage_cleanup_enabled:
            current_size, _ = get_bucket_size(config.snap_storage_bucket, prefix=f"{device_id}/")
            usage_ratio = current_size / config.snap_storage_max_size if config.snap_storage_max_size > 0 else 0
            
            if usage_ratio >= config.snap_storage_cleanup_threshold:
                deleted_count, freed_size = cleanup_old_files(
                    config.snap_storage_bucket,
                    prefix=f"{device_id}/",
                    cleanup_ratio=config.snap_storage_cleanup_ratio
                )
                result['snap_cleaned'] = True
                result['snap_deleted_count'] = deleted_count
                result['snap_freed_size'] = freed_size
                config.last_snap_cleanup_time = datetime.utcnow()
        
        # 检查录像存储
        if config.video_storage_bucket and config.video_storage_max_size and config.video_storage_cleanup_enabled:
            current_size, _ = get_bucket_size(config.video_storage_bucket, prefix=f"{device_id}/")
            usage_ratio = current_size / config.video_storage_max_size if config.video_storage_max_size > 0 else 0
            
            if usage_ratio >= config.video_storage_cleanup_threshold:
                deleted_count, freed_size = cleanup_old_files(
                    config.video_storage_bucket,
                    prefix=f"{device_id}/",
                    cleanup_ratio=config.video_storage_cleanup_ratio
                )
                result['video_cleaned'] = True
                result['video_deleted_count'] = deleted_count
                result['video_freed_size'] = freed_size
                config.last_video_cleanup_time = datetime.utcnow()
        
        if result['snap_cleaned'] or result['video_cleaned']:
            db.session.commit()
        
        return result
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"检查并清理存储空间失败: device_id={device_id}, error={str(e)}", exc_info=True)
        raise RuntimeError(f"检查并清理存储空间失败: {str(e)}")


def get_device_storage_info(device_id: str) -> dict:
    """获取设备存储信息"""
    try:
        config = DeviceStorageConfig.query.filter_by(device_id=device_id).first()
        if not config:
            return {
                'snap_size': 0,
                'snap_count': 0,
                'snap_usage_ratio': 0,
                'video_size': 0,
                'video_count': 0,
                'video_usage_ratio': 0
            }
        
        snap_size = 0
        snap_count = 0
        if config.snap_storage_bucket:
            snap_size, snap_count = get_bucket_size(config.snap_storage_bucket, prefix=f"{device_id}/")
        
        video_size = 0
        video_count = 0
        if config.video_storage_bucket:
            video_size, video_count = get_bucket_size(config.video_storage_bucket, prefix=f"{device_id}/")
        
        snap_usage_ratio = 0
        if config.snap_storage_max_size and config.snap_storage_max_size > 0:
            snap_usage_ratio = snap_size / config.snap_storage_max_size
        
        video_usage_ratio = 0
        if config.video_storage_max_size and config.video_storage_max_size > 0:
            video_usage_ratio = video_size / config.video_storage_max_size
        
        return {
            'snap_size': snap_size,
            'snap_count': snap_count,
            'snap_max_size': config.snap_storage_max_size,
            'snap_usage_ratio': snap_usage_ratio,
            'video_size': video_size,
            'video_count': video_count,
            'video_max_size': config.video_storage_max_size,
            'video_usage_ratio': video_usage_ratio,
            'last_snap_cleanup_time': config.last_snap_cleanup_time.isoformat() if config.last_snap_cleanup_time else None,
            'last_video_cleanup_time': config.last_video_cleanup_time.isoformat() if config.last_video_cleanup_time else None
        }
    except Exception as e:
        logger.error(f"获取设备存储信息失败: device_id={device_id}, error={str(e)}", exc_info=True)
        raise RuntimeError(f"获取设备存储信息失败: {str(e)}")

