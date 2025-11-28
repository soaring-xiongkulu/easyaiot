"""
抓拍空间服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from flask import current_app
from minio import Minio
from minio.error import S3Error

from models import db, SnapSpace, SnapTask
from app.services.snap_image_service import cleanup_old_images_by_days

logger = logging.getLogger(__name__)


def get_minio_client():
    """创建并返回Minio客户端"""
    minio_endpoint = current_app.config.get('MINIO_ENDPOINT', 'localhost:9000')
    access_key = current_app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = current_app.config.get('MINIO_SECRET_KEY', 'minioadmin')
    secure = current_app.config.get('MINIO_SECURE', 'false').lower() == 'true'
    return Minio(minio_endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def create_snap_space(space_name, save_mode=0, save_time=0, description=None, device_id=None):
    """创建抓拍空间
    
    Args:
        space_name: 空间名称
        save_mode: 存储模式 0:标准存储, 1:归档存储
        save_time: 保存时间 0:永久保存, >=7:保存天数
        description: 描述
        device_id: 设备ID（可选，如果提供则检查该设备文件夹是否已存在）
    """
    try:
        # 检查是否已有同名空间
        existing_space = SnapSpace.query.filter_by(space_name=space_name).first()
        if existing_space:
            raise ValueError(f"空间名称 '{space_name}' 已存在，请使用其他名称")
        
        # 生成唯一编号
        space_code = f"SPACE_{uuid.uuid4().hex[:8].upper()}"
        bucket_name = f"snap-space-{space_code.lower()}"
        
        # 创建MinIO bucket
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"创建MinIO bucket: {bucket_name}")
        else:
            logger.warning(f"MinIO bucket已存在: {bucket_name}")
        
        # 如果提供了设备ID，检查该设备在snap-space仓库下是否已有文件夹
        if device_id:
            # 检查所有snap-space开头的bucket
            buckets = minio_client.list_buckets()
            for bucket in buckets:
                if bucket.name.startswith('snap-space-'):
                    # 检查该bucket下是否存在该设备的文件夹（有实际文件）
                    device_folder = f"{device_id}/"
                    objects = list(minio_client.list_objects(bucket.name, prefix=device_folder, recursive=True))
                    # 检查是否有实际文件（不是空文件夹）
                    has_files = False
                    for obj in objects:
                        if not obj.object_name.endswith('/'):  # 不是文件夹标记
                            has_files = True
                            break
                    if has_files:
                        raise ValueError(f"设备 '{device_id}' 在空间 '{bucket.name}' 下已存在文件夹，不能重复创建")
        
        # 创建数据库记录
        snap_space = SnapSpace(
            space_name=space_name,
            space_code=space_code,
            bucket_name=bucket_name,
            save_mode=save_mode,
            save_time=save_time,
            description=description
        )
        db.session.add(snap_space)
        db.session.commit()
        
        logger.info(f"抓拍空间创建成功: {space_name} ({space_code})")
        return snap_space
    except ValueError:
        db.session.rollback()
        raise
    except S3Error as e:
        db.session.rollback()
        logger.error(f"MinIO操作失败: {str(e)}")
        raise RuntimeError(f"创建MinIO存储桶失败: {str(e)}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建抓拍空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建抓拍空间失败: {str(e)}")


def update_snap_space(space_id, space_name=None, save_mode=None, save_time=None, description=None):
    """更新抓拍空间"""
    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        
        if space_name is not None:
            snap_space.space_name = space_name
        if save_mode is not None:
            snap_space.save_mode = save_mode
        if save_time is not None:
            snap_space.save_time = save_time
        if description is not None:
            snap_space.description = description
        
        db.session.commit()
        logger.info(f"抓拍空间更新成功: ID={space_id}")
        return snap_space
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新抓拍空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新抓拍空间失败: {str(e)}")


def check_space_has_images(space_id):
    """检查抓拍空间是否有抓拍图片"""
    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        bucket_name = snap_space.bucket_name
        
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            return False, 0
        
        # 统计所有文件（排除文件夹标记）
        file_count = 0
        objects = minio_client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            if not obj.object_name.endswith('/'):  # 不是文件夹标记
                file_count += 1
                if file_count > 0:  # 只要有一个文件就返回True
                    return True, file_count
        
        return False, 0
    except Exception as e:
        logger.error(f"检查抓拍空间图片失败: {str(e)}", exc_info=True)
        return False, 0


def delete_snap_space(space_id):
    """删除抓拍空间"""
    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        
        # 检查是否有任务关联
        task_count = SnapTask.query.filter_by(space_id=space_id).count()
        if task_count > 0:
            raise ValueError(f"该空间下还有 {task_count} 个任务，请先删除任务")
        
        # 检查是否有抓拍图片
        has_images, image_count = check_space_has_images(space_id)
        if has_images:
            raise ValueError(f"该空间下还有 {image_count} 张抓拍图片，请先删除所有图片后再删除空间")
        
        bucket_name = snap_space.bucket_name
        
        # 删除MinIO bucket中的所有对象
        try:
            minio_client = get_minio_client()
            if minio_client.bucket_exists(bucket_name):
                # 列出所有对象并删除
                objects = minio_client.list_objects(bucket_name, recursive=True)
                for obj in objects:
                    minio_client.remove_object(bucket_name, obj.object_name)
                # 删除bucket
                minio_client.remove_bucket(bucket_name)
                logger.info(f"删除MinIO bucket: {bucket_name}")
        except S3Error as e:
            logger.warning(f"删除MinIO bucket失败（可能不存在）: {str(e)}")
        
        # 删除数据库记录
        db.session.delete(snap_space)
        db.session.commit()
        
        logger.info(f"抓拍空间删除成功: ID={space_id}")
        return True
    except ValueError:
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除抓拍空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除抓拍空间失败: {str(e)}")


def get_snap_space(space_id):
    """获取抓拍空间详情"""
    try:
        return SnapSpace.query.get_or_404(space_id)
    except Exception as e:
        logger.error(f"获取抓拍空间失败: {str(e)}")
        raise ValueError(f"抓拍空间不存在: ID={space_id}")


def list_snap_spaces(page_no=1, page_size=10, search=None):
    """查询抓拍空间列表"""
    try:
        query = SnapSpace.query
        
        if search:
            query = query.filter(SnapSpace.space_name.ilike(f'%{search}%'))
        
        query = query.order_by(SnapSpace.created_at.desc())
        
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )
        
        return {
            'items': [space.to_dict() for space in pagination.items],
            'total': pagination.total,
            'page_no': page_no,
            'page_size': page_size
        }
    except Exception as e:
        logger.error(f"查询抓拍空间列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询抓拍空间列表失败: {str(e)}")


def create_camera_folder(space_id, device_id):
    """为摄像头创建独立的文件夹（在MinIO bucket中）"""
    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        bucket_name = snap_space.bucket_name
        
        # 在bucket中创建以device_id命名的文件夹（实际上MinIO不需要显式创建文件夹，使用前缀即可）
        # 这里我们只是验证bucket存在
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            raise ValueError(f"抓拍空间的MinIO bucket不存在: {bucket_name}")
        
        # 检查该设备在该空间下是否已有文件夹（有文件存在）
        folder_path = f"{device_id}/"
        objects = list(minio_client.list_objects(bucket_name, prefix=folder_path, recursive=False))
        if objects:
            # 检查是否有实际文件（不是空文件夹）
            has_files = False
            for obj in objects:
                if not obj.object_name.endswith('/'):  # 不是文件夹标记
                    has_files = True
                    break
            if has_files:
                raise ValueError(f"设备 '{device_id}' 在空间 '{snap_space.space_name}' 下已存在文件夹，不能重复创建")
        
        logger.info(f"为设备 {device_id} 在空间 {snap_space.space_name} 中创建文件夹: {folder_path}")
        
        return folder_path
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"创建摄像头文件夹失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建摄像头文件夹失败: {str(e)}")


def auto_cleanup_all_spaces():
    """自动清理所有抓拍空间的过期图片"""
    try:
        spaces = SnapSpace.query.filter(SnapSpace.save_time > 0).all()
        total_processed = 0
        total_deleted = 0
        total_archived = 0
        total_errors = 0
        
        for space in spaces:
            try:
                result = cleanup_old_images_by_days(space.id, space.save_time)
                total_processed += result['processed_count']
                total_deleted += result['deleted_count']
                total_archived += result['archived_count']
                total_errors += result['error_count']
                logger.info(f"空间 {space.space_name} 清理完成: {result}")
            except Exception as e:
                logger.error(f"清理空间 {space.space_name} 失败: {str(e)}", exc_info=True)
                total_errors += 1
        
        logger.info(f"所有抓拍空间自动清理完成: 处理={total_processed}, 删除={total_deleted}, 归档={total_archived}, 错误={total_errors}")
        return {
            'processed_count': total_processed,
            'deleted_count': total_deleted,
            'archived_count': total_archived,
            'error_count': total_errors
        }
    except Exception as e:
        logger.error(f"自动清理所有抓拍空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"自动清理所有抓拍空间失败: {str(e)}")

