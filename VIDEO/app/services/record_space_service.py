"""
监控录像空间服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from flask import current_app
from minio import Minio
from minio.error import S3Error

from models import db, RecordSpace

logger = logging.getLogger(__name__)


def get_minio_client():
    """创建并返回Minio客户端"""
    minio_endpoint = current_app.config.get('MINIO_ENDPOINT', 'localhost:9000')
    access_key = current_app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = current_app.config.get('MINIO_SECRET_KEY', 'minioadmin')
    secure_value = current_app.config.get('MINIO_SECURE', False)
    # 处理 secure 可能是布尔值或字符串的情况
    if isinstance(secure_value, bool):
        secure = secure_value
    else:
        secure = str(secure_value).lower() == 'true'
    return Minio(minio_endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def create_record_space(space_name, save_mode=0, save_time=0, description=None, device_id=None):
    """创建监控录像空间
    
    Args:
        space_name: 空间名称
        save_mode: 存储模式 0:标准存储, 1:归档存储
        save_time: 保存时间 0:永久保存, >=7:保存天数
        description: 描述
        device_id: 设备ID（可选，如果提供则检查该设备文件夹是否已存在）
    """
    try:
        # 刷新数据库会话，确保获取最新数据（避免缓存问题）
        db.session.expire_all()
        
        # 如果提供了设备ID，检查该设备是否已有监控录像空间
        if device_id:
            existing_space = RecordSpace.query.filter_by(device_id=device_id).first()
            if existing_space:
                raise ValueError(f"设备 '{device_id}' 已有关联的监控录像空间，不能重复创建")
        
        # 注意：允许同名空间，因为通过space_code来保证唯一性
        
        # 生成唯一编号
        space_code = f"RECORD_{uuid.uuid4().hex[:8].upper()}"
        # 统一使用 record-space bucket
        bucket_name = "record-space"
        
        # 确保 record-space bucket 存在
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"创建MinIO bucket: {bucket_name}")
        
        # 在 record-space bucket 下创建空间文件夹（实际上MinIO不需要显式创建文件夹，使用前缀即可）
        # 这里我们只是验证空间文件夹是否已存在
        space_folder = f"{space_code}/"
        objects = list(minio_client.list_objects(bucket_name, prefix=space_folder, recursive=False))
        if objects:
            # 检查是否有实际文件（不是空文件夹）
            has_files = False
            for obj in objects:
                if not obj.object_name.endswith('/'):  # 不是文件夹标记
                    has_files = True
                    break
            if has_files:
                raise ValueError(f"空间编号 '{space_code}' 已存在文件，不能重复创建")
        
        # 如果提供了设备ID，检查该设备在record-space仓库下是否已有文件夹
        if device_id:
            # 检查所有空间下是否存在该设备的文件夹（有实际文件）
            device_folder = f"{space_code}/{device_id}/"
            objects = list(minio_client.list_objects(bucket_name, prefix=device_folder, recursive=True))
            # 检查是否有实际文件（不是空文件夹）
            has_files = False
            for obj in objects:
                if not obj.object_name.endswith('/'):  # 不是文件夹标记
                    has_files = True
                    break
            if has_files:
                raise ValueError(f"设备 '{device_id}' 在空间 '{space_code}' 下已存在文件夹，不能重复创建")
        
        # 创建数据库记录
        record_space = RecordSpace(
            space_name=space_name,
            space_code=space_code,
            bucket_name=bucket_name,
            save_mode=save_mode,
            save_time=save_time,
            description=description,
            device_id=device_id
        )
        db.session.add(record_space)
        db.session.commit()
        
        logger.info(f"监控录像空间创建成功: {space_name} ({space_code})，路径: {bucket_name}/{space_folder}，设备ID: {device_id}")
        return record_space
    except ValueError:
        db.session.rollback()
        raise
    except S3Error as e:
        db.session.rollback()
        logger.error(f"MinIO操作失败: {str(e)}")
        raise RuntimeError(f"创建MinIO存储桶失败: {str(e)}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建监控录像空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建监控录像空间失败: {str(e)}")


def create_record_space_for_device(device_id, device_name=None):
    """为设备自动创建监控录像空间
    
    Args:
        device_id: 设备ID
        device_name: 设备名称（可选，用于生成空间名称）
    
    Returns:
        RecordSpace: 创建的监控录像空间对象
    """
    try:
        from models import Device
        
        # 检查设备是否存在
        device = Device.query.get(device_id)
        if not device:
            raise ValueError(f"设备 '{device_id}' 不存在")
        
        # 检查该设备是否已有监控录像空间
        existing_space = RecordSpace.query.filter_by(device_id=device_id).first()
        if existing_space:
            logger.info(f"设备 '{device_id}' 已有关联的监控录像空间，返回现有空间")
            return existing_space
        
        # 生成空间名称：直接使用设备名称（允许同名，因为通过space_code唯一）
        space_name = device_name or device.name or device_id
        
        # 使用默认配置创建监控录像空间
        return create_record_space(
            space_name=space_name,
            save_mode=0,  # 默认标准存储
            save_time=0,  # 默认永久保存
            description=f"设备 {device_id} 的自动创建监控录像空间",
            device_id=device_id
        )
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"为设备创建监控录像空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"为设备创建监控录像空间失败: {str(e)}")


def get_record_space_by_device_id(device_id):
    """根据设备ID获取监控录像空间
    
    Args:
        device_id: 设备ID
    
    Returns:
        RecordSpace: 监控录像空间对象，如果不存在则返回None
    """
    try:
        return RecordSpace.query.filter_by(device_id=device_id).first()
    except Exception as e:
        logger.error(f"根据设备ID获取监控录像空间失败: {str(e)}", exc_info=True)
        return None


def update_record_space(space_id, space_name=None, save_mode=None, save_time=None, description=None):
    """更新监控录像空间"""
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        
        # 允许同名空间，因为通过space_code来保证唯一性
        if space_name is not None:
            record_space.space_name = space_name
        if save_mode is not None:
            record_space.save_mode = save_mode
        if save_time is not None:
            record_space.save_time = save_time
        if description is not None:
            record_space.description = description
        
        db.session.commit()
        logger.info(f"监控录像空间更新成功: ID={space_id}")
        return record_space
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新监控录像空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新监控录像空间失败: {str(e)}")


def check_space_has_videos(space_id):
    """检查监控录像空间是否有录像"""
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            return False, 0
        
        # 统计该空间文件夹下的所有文件（排除文件夹标记）
        space_prefix = f"{space_code}/"
        file_count = 0
        objects = minio_client.list_objects(bucket_name, prefix=space_prefix, recursive=True)
        for obj in objects:
            if not obj.object_name.endswith('/'):  # 不是文件夹标记
                file_count += 1
                if file_count > 0:  # 只要有一个文件就返回True
                    return True, file_count
        
        return False, 0
    except Exception as e:
        logger.error(f"检查监控录像空间录像失败: {str(e)}", exc_info=True)
        return False, 0


def check_device_space_has_videos(device_id):
    """检查设备关联的监控录像空间是否有录像
    
    Args:
        device_id: 设备ID
    
    Returns:
        tuple: (是否有录像, 录像数量)
    """
    try:
        record_space = RecordSpace.query.filter_by(device_id=device_id).first()
        if not record_space:
            return False, 0
        
        return check_space_has_videos(record_space.id)
    except Exception as e:
        logger.error(f"检查设备监控录像空间录像失败: {str(e)}", exc_info=True)
        return False, 0


def delete_record_space(space_id):
    """删除监控录像空间"""
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        
        # 检查是否有录像
        has_videos, video_count = check_space_has_videos(space_id)
        if has_videos:
            raise ValueError(f"该空间下还有 {video_count} 个监控录像，请先删除所有录像后再删除空间")
        
        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        
        # 删除MinIO bucket中该空间文件夹下的所有对象
        try:
            minio_client = get_minio_client()
            if minio_client.bucket_exists(bucket_name):
                # 列出该空间文件夹下的所有对象并删除
                space_prefix = f"{space_code}/"
                objects = minio_client.list_objects(bucket_name, prefix=space_prefix, recursive=True)
                for obj in objects:
                    minio_client.remove_object(bucket_name, obj.object_name)
                logger.info(f"删除MinIO空间文件夹: {bucket_name}/{space_prefix}")
        except S3Error as e:
            logger.warning(f"删除MinIO空间文件夹失败（可能不存在）: {str(e)}")
        
        # 删除数据库记录
        db.session.delete(record_space)
        db.session.commit()
        
        logger.info(f"监控录像空间删除成功: ID={space_id}")
        return True
    except ValueError:
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除监控录像空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除监控录像空间失败: {str(e)}")


def get_record_space(space_id):
    """获取监控录像空间详情"""
    try:
        return RecordSpace.query.get_or_404(space_id)
    except Exception as e:
        logger.error(f"获取监控录像空间失败: {str(e)}")
        raise ValueError(f"监控录像空间不存在: ID={space_id}")


def list_record_spaces(page_no=1, page_size=10, search=None):
    """查询监控录像空间列表"""
    try:
        query = RecordSpace.query
        
        if search:
            query = query.filter(RecordSpace.space_name.ilike(f'%{search}%'))
        
        query = query.order_by(RecordSpace.created_at.desc())
        
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
        logger.error(f"查询监控录像空间列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询监控录像空间列表失败: {str(e)}")


def create_camera_folder(space_id, device_id):
    """为摄像头创建独立的文件夹（在MinIO bucket中）"""
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        
        # 在bucket中创建以space_code/device_id命名的文件夹（实际上MinIO不需要显式创建文件夹，使用前缀即可）
        # 这里我们只是验证bucket存在
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            raise ValueError(f"监控录像空间的MinIO bucket不存在: {bucket_name}")
        
        # 检查该设备在该空间下是否已有文件夹（有文件存在）
        folder_path = f"{space_code}/{device_id}/"
        objects = list(minio_client.list_objects(bucket_name, prefix=folder_path, recursive=False))
        if objects:
            # 检查是否有实际文件（不是空文件夹）
            has_files = False
            for obj in objects:
                if not obj.object_name.endswith('/'):  # 不是文件夹标记
                    has_files = True
                    break
            if has_files:
                raise ValueError(f"设备 '{device_id}' 在空间 '{record_space.space_name}' 下已存在文件夹，不能重复创建")
        
        logger.info(f"为设备 {device_id} 在空间 {record_space.space_name} 中创建文件夹: {folder_path}")
        
        return folder_path
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"创建摄像头文件夹失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建摄像头文件夹失败: {str(e)}")

