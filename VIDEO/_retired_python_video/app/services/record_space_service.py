"""
监控录像空间服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import io
import logging
import uuid
from flask import current_app
from minio import Minio
from minio.error import S3Error
from sqlalchemy.exc import IntegrityError

from models import db, RecordSpace
from app.utils.minio_bucket_policy import ensure_bucket_public_read_write_policy
from app.utils.service_urls import minio_storage_enabled

logger = logging.getLogger(__name__)

RECORD_SPACE_BUCKET = "record-space"


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


def _find_record_space_by_device_id(device_id):
    """按 device_id 查询录像空间（刷新会话，避免脏缓存）。"""
    if not device_id:
        return None
    db.session.expire_all()
    return RecordSpace.query.filter_by(device_id=device_id).first()


def create_record_space(space_name, save_mode=0, save_time=1, description=None, device_id=None, save_time_custom=False):
    """创建监控录像空间
    
    Args:
        space_name: 空间名称
        save_mode: 存储模式 0:标准存储, 1:归档存储
        save_time: 保存时长 0:永久保存, >=1:小时
        description: 描述
        device_id: 设备ID（可选，如果提供则检查该设备文件夹是否已存在）
    """
    try:
        # 刷新数据库会话，确保获取最新数据（避免缓存问题）
        db.session.expire_all()
        
        # 如果提供了设备ID，检查该设备是否已有监控录像空间（幂等：已存在则直接返回）
        if device_id:
            existing_space = _find_record_space_by_device_id(device_id)
            if existing_space:
                logger.info(f"设备 '{device_id}' 已有关联的监控录像空间，返回现有空间")
                return existing_space
        
        # 注意：允许同名空间，因为通过space_code来保证唯一性
        
        # 生成唯一编号
        space_code = f"RECORD_{uuid.uuid4().hex[:8].upper()}"
        bucket_name = RECORD_SPACE_BUCKET

        if not minio_storage_enabled():
            record_space = RecordSpace(
                space_name=space_name,
                space_code=space_code,
                bucket_name=bucket_name,
                save_mode=save_mode,
                save_time=save_time,
                save_time_custom=save_time_custom,
                description=description,
                device_id=device_id
            )
            db.session.add(record_space)
            db.session.commit()
            logger.info(
                "mini 形态监控录像空间创建成功（仅数据库）: %s (%s)，设备ID: %s",
                space_name, space_code, device_id,
            )
            return record_space
        
        # 确保 record-space bucket 存在且具备公开策略（否则 /api/v1/buckets/.../download 返回 500）
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"创建MinIO bucket: {bucket_name}")
        ensure_bucket_public_read_write_policy(minio_client, bucket_name)
        
        # 现在不再使用 space_code 作为文件夹层级，直接使用 device_id
        # 如果提供了设备ID，检查该设备是否已有文件夹
        if device_id:
            device_folder = f"{device_id}/"
            objects = list(minio_client.list_objects(bucket_name, prefix=device_folder, recursive=False))
            # 检查是否有实际文件（不是空文件夹）
            has_files = False
            for obj in objects:
                if not obj.object_name.endswith('/'):  # 不是文件夹标记
                    has_files = True
                    break
            if has_files:
                logger.warning(
                    f"设备 '{device_id}' 在 MinIO 中已有录像文件，将继续确保数据库录像空间记录存在"
                )
        
        # 创建数据库记录
        record_space = RecordSpace(
            space_name=space_name,
            space_code=space_code,
            bucket_name=bucket_name,
            save_mode=save_mode,
            save_time=save_time,
            save_time_custom=save_time_custom,
            description=description,
            device_id=device_id
        )
        db.session.add(record_space)
        db.session.commit()
        
        # 现在不再使用 space_code 作为文件夹层级，不需要创建目录标记
        # 如果提供了设备ID，可以创建设备目录标记（可选）
        if device_id:
            try:
                device_folder = f"{device_id}/"
                minio_client.put_object(
                    bucket_name,
                    device_folder,
                    io.BytesIO(b''),
                    0
                )
                logger.info(f"创建MinIO设备目录: {bucket_name}/{device_folder}")
            except S3Error as e:
                # 如果创建目录标记失败，记录警告但不影响整体流程（因为MinIO使用前缀即可）
                logger.warning(f"创建MinIO设备目录标记失败: {bucket_name}/{device_folder}, 错误: {str(e)}")
        
        logger.info(f"监控录像空间创建成功: {space_name} ({space_code})，bucket: {bucket_name}，设备ID: {device_id}")
        return record_space
    except IntegrityError as e:
        db.session.rollback()
        if device_id and 'device_id' in str(getattr(e, 'orig', e)):
            existing_space = _find_record_space_by_device_id(device_id)
            if existing_space:
                logger.info(
                    f"设备 '{device_id}' 监控录像空间已存在（并发创建），返回现有空间"
                )
                return existing_space
        logger.error(f"创建监控录像空间失败（唯一约束冲突）: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建监控录像空间失败: {str(e)}")
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
        existing_space = _find_record_space_by_device_id(device_id)
        if existing_space:
            logger.info(f"设备 '{device_id}' 已有关联的监控录像空间，返回现有空间")
            return existing_space
        
        # 生成空间名称：直接使用设备名称（允许同名，因为通过space_code唯一）
        space_name = device_name or device.name or device_id
        
        from app.services.space_save_time_service import resolve_save_time_for_device, SPACE_KIND_RECORD
        directory_save_time = resolve_save_time_for_device(device_id, SPACE_KIND_RECORD)
        return create_record_space(
            space_name=space_name,
            save_mode=0,
            save_time=directory_save_time,
            save_time_custom=False,
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


def update_record_space(space_id, space_name=None, save_mode=None, save_time=None, description=None, save_time_custom=None):
    """更新监控录像空间"""
    try:
        from app.services.space_save_time_service import apply_space_save_time_update, SPACE_KIND_RECORD
        record_space = RecordSpace.query.get_or_404(space_id)
        
        # 允许同名空间，因为通过space_code来保证唯一性
        if space_name is not None:
            record_space.space_name = space_name
        if save_mode is not None:
            record_space.save_mode = save_mode
        if save_time is not None or save_time_custom is not None:
            apply_space_save_time_update(
                record_space, SPACE_KIND_RECORD,
                save_time=save_time, save_time_custom=save_time_custom,
            )
        if description is not None:
            record_space.description = description
        
        db.session.commit()
        logger.info(f"监控录像空间更新成功: ID={space_id}")
        return record_space
    except ValueError:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新监控录像空间失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新监控录像空间失败: {str(e)}")


def check_space_has_videos(space_id):
    """检查监控录像空间是否有录像（查数据库）"""
    try:
        from app.services.space_file_metadata_service import count_record_files
        file_count = count_record_files(space_id)
        return file_count > 0, file_count
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
        # 注意：现在路径是 device_id/filename，不再使用 space_code 前缀
        # 如果空间关联了设备，只删除该设备的文件；否则删除所有文件
        if minio_storage_enabled():
            try:
                minio_client = get_minio_client()
                if minio_client.bucket_exists(bucket_name):
                    if record_space.device_id:
                        # 只删除该设备的文件
                        device_prefix = f"{record_space.device_id}/"
                        objects = minio_client.list_objects(bucket_name, prefix=device_prefix, recursive=True)
                        for obj in objects:
                            minio_client.remove_object(bucket_name, obj.object_name)
                        logger.info(f"删除MinIO设备文件夹: {bucket_name}/{device_prefix}")
                    else:
                        # 空间没有关联设备，删除所有文件（这种情况应该很少见）
                        objects = minio_client.list_objects(bucket_name, prefix="", recursive=True)
                        for obj in objects:
                            minio_client.remove_object(bucket_name, obj.object_name)
                        logger.info(f"删除MinIO空间所有文件: {bucket_name}/")
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


def list_record_spaces(page_no=1, page_size=10, search=None, parent_key=None, scope=None):
    """查询监控录像空间列表（支持 NVR / GB28181 文件夹层级）。"""
    try:
        from app.services.space_folder_tree_service import list_space_folder_nodes, SPACE_KIND_RECORD
        return list_space_folder_nodes(
            SPACE_KIND_RECORD,
            page_no=page_no,
            page_size=page_size,
            search=search,
            parent_key=parent_key,
            scope=scope,
        )
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"查询监控录像空间列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询监控录像空间列表失败: {str(e)}")


def create_camera_folder(space_id, device_id):
    """为摄像头创建独立的文件夹（在MinIO bucket中）"""
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        folder_path = f"{device_id}/"
        if not minio_storage_enabled():
            logger.info(f"mini 形态跳过 MinIO 目录创建，返回逻辑路径: {folder_path}")
            return folder_path

        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        
        # 在bucket中创建以device_id命名的文件夹（实际上MinIO不需要显式创建文件夹，使用前缀即可）
        # 这里我们只是验证bucket存在
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            raise ValueError(f"监控录像空间的MinIO bucket不存在: {bucket_name}")
        
        # 检查该设备是否已有文件夹（有文件存在）
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
                raise ValueError(f"设备 '{device_id}' 已存在文件夹，不能重复创建")
        
        logger.info(f"为设备 {device_id} 创建文件夹: {folder_path}")
        
        return folder_path
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"创建摄像头文件夹失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建摄像头文件夹失败: {str(e)}")


def sync_spaces_to_minio():
    """同步所有监控录像空间到Minio，创建不存在的目录"""
    try:
        spaces = RecordSpace.query.all()
        total_spaces = len(spaces)
        if not minio_storage_enabled():
            logger.info('MinIO 未启用，跳过监控录像空间同步')
            return {
                'total_spaces': total_spaces,
                'created_count': 0,
                'skipped_count': total_spaces,
                'error_count': 0,
            }

        minio_client = get_minio_client()
        bucket_name = RECORD_SPACE_BUCKET
        
        # 确保 bucket 存在且具备公开策略
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"创建MinIO bucket: {bucket_name}")
        ensure_bucket_public_read_write_policy(minio_client, bucket_name)
        
        # 获取所有监控录像空间
        total_spaces = len(spaces)
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        # 现在不再使用 space_code 作为文件夹层级，直接使用 device_id
        # 如果空间关联了设备，检查设备目录是否存在
        for space in spaces:
            try:
                if space.device_id:
                    device_prefix = f"{space.device_id}/"
                    # 检查目录是否已存在（通过列出对象来判断）
                    # 使用迭代器只检查是否有至少一个对象，提高效率
                    objects_iter = minio_client.list_objects(bucket_name, prefix=device_prefix, recursive=False)
                    has_objects = next(objects_iter, None) is not None
                    
                    # 如果目录不存在（没有对象），创建一个空对象作为目录标记
                    # MinIO中目录实际上是通过以"/"结尾的对象名来表示的
                    if not has_objects:
                        # 创建一个目录标记对象（空对象，以"/"结尾）
                        try:
                            minio_client.put_object(
                                bucket_name,
                                device_prefix,
                                io.BytesIO(b''),
                                0
                            )
                            created_count += 1
                            logger.info(f"创建设备目录: {bucket_name}/{device_prefix} (空间: {space.space_name}, 设备: {space.device_id})")
                        except S3Error as e:
                            # 如果创建失败，记录错误但继续处理其他空间
                            logger.warning(f"创建设备目录失败: {bucket_name}/{device_prefix}, 错误: {str(e)}")
                            error_count += 1
                    else:
                        skipped_count += 1
                        logger.debug(f"设备目录已存在，跳过: {bucket_name}/{device_prefix} (空间: {space.space_name})")
                else:
                    skipped_count += 1
                    logger.debug(f"空间未关联设备，跳过: {space.space_name}")
            except Exception as e:
                logger.error(f"同步监控录像空间 {space.space_name} ({space.space_code}) 失败: {str(e)}", exc_info=True)
                error_count += 1
        
        result = {
            'total_spaces': total_spaces,
            'created_count': created_count,
            'skipped_count': skipped_count,
            'error_count': error_count
        }
        logger.info(f"监控录像空间同步Minio完成: {result}")
        return result
    except Exception as e:
        logger.error(f"同步监控录像空间到Minio失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"同步监控录像空间到Minio失败: {str(e)}")


def auto_cleanup_all_record_spaces(app=None):
    """自动清理所有录像空间的过期文件（按各空间 effective save_time）。"""
    if app is None:
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            logger.error("自动清理所有录像空间失败: 没有应用上下文，请传入app参数")
            raise RuntimeError("自动清理所有录像空间失败: 没有应用上下文，请传入app参数")

    with app.app_context():
        try:
            from app.services.record_video_service import cleanup_old_videos_by_save_time
            from app.services.space_save_time_service import enrich_record_space_dict

            spaces = RecordSpace.query.all()
            total_processed = 0
            total_deleted = 0
            total_archived = 0
            total_errors = 0

            total_orphan_deleted = 0
            total_orphan_scanned = 0
            total_orphan_errors = 0

            for space in spaces:
                info = enrich_record_space_dict({'save_time': space.save_time}, space)
                save_time_hours = info.get('effective_save_time') or 0
                if save_time_hours <= 0:
                    continue
                try:
                    result = cleanup_old_videos_by_save_time(space.id, save_time_hours)
                    total_processed += result['processed_count']
                    total_deleted += result['deleted_count']
                    total_archived += result['archived_count']
                    total_errors += result['error_count']
                    total_orphan_deleted += result.get('orphan_deleted_count', 0)
                    total_orphan_scanned += result.get('orphan_scanned_count', 0)
                    total_orphan_errors += result.get('orphan_error_count', 0)
                    logger.info(f"录像空间 {space.space_name} 清理完成: {result}")
                except Exception as e:
                    logger.error(f"清理录像空间 {space.space_name} 失败: {str(e)}", exc_info=True)
                    total_errors += 1

            logger.info(
                '所有录像空间自动清理完成: 处理=%s, 删除=%s, 归档=%s, 错误=%s, '
                '孤儿扫描=%s, 孤儿删除=%s, 孤儿错误=%s',
                total_processed, total_deleted, total_archived, total_errors,
                total_orphan_scanned, total_orphan_deleted, total_orphan_errors,
            )
            return {
                'processed_count': total_processed,
                'deleted_count': total_deleted,
                'archived_count': total_archived,
                'error_count': total_errors,
                'orphan_deleted_count': total_orphan_deleted,
                'orphan_scanned_count': total_orphan_scanned,
                'orphan_error_count': total_orphan_errors,
            }
        except Exception as e:
            logger.error(f"自动清理所有录像空间失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"自动清理所有录像空间失败: {str(e)}")

