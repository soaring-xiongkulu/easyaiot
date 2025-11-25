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

logger = logging.getLogger(__name__)


def get_minio_client():
    """创建并返回Minio客户端"""
    minio_endpoint = current_app.config.get('MINIO_ENDPOINT', 'localhost:9000')
    access_key = current_app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = current_app.config.get('MINIO_SECRET_KEY', 'minioadmin')
    secure = current_app.config.get('MINIO_SECURE', 'false').lower() == 'true'
    return Minio(minio_endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def create_snap_space(space_name, save_mode=0, save_time=0, description=None):
    """创建抓拍空间"""
    try:
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


def delete_snap_space(space_id):
    """删除抓拍空间"""
    try:
        snap_space = SnapSpace.query.get_or_404(space_id)
        
        # 检查是否有任务关联
        task_count = SnapTask.query.filter_by(space_id=space_id).count()
        if task_count > 0:
            raise ValueError(f"该空间下还有 {task_count} 个任务，请先删除任务")
        
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
        
        folder_path = f"{device_id}/"
        logger.info(f"为设备 {device_id} 在空间 {snap_space.space_name} 中创建文件夹: {folder_path}")
        
        return folder_path
    except Exception as e:
        logger.error(f"创建摄像头文件夹失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建摄像头文件夹失败: {str(e)}")

