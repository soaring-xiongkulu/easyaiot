"""
监控录像管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import zipfile
import io
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
from flask import current_app
from minio import Minio
from minio.error import S3Error

from models import db, RecordSpace, Playback
from app.services.record_space_service import get_minio_client

logger = logging.getLogger(__name__)


def list_record_videos(space_id: int, device_id: Optional[str] = None, 
                       page_no: int = 1, page_size: int = 20) -> Dict:
    """获取监控录像列表
    
    Args:
        space_id: 监控录像空间ID
        device_id: 设备ID（可选）
        page_no: 页码
        page_size: 每页数量
    
    Returns:
        dict: 包含录像列表和总数
    """
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            return {'items': [], 'total': 0, 'page_no': page_no, 'page_size': page_size}
        
        # 构建前缀：device_id/ 或 空（列出所有设备）
        if device_id:
            prefix = f"{device_id}/"
        else:
            prefix = ""  # 列出所有设备目录
        
        # 获取所有对象
        videos = []
        objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
        
        # 支持的视频格式
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v']
        
        # 先收集所有视频文件的object_name和对象，用于批量查询Playback记录
        video_object_names = []
        video_objects = []  # 存储视频对象，避免重复遍历
        
        for obj in objects:
            # 排除文件夹标记
            if obj.object_name.endswith('/'):
                continue
            
            # 只处理视频文件
            filename = obj.object_name.split('/')[-1]
            if any(filename.lower().endswith(ext) for ext in video_extensions):
                video_object_names.append(obj.object_name)
                video_objects.append(obj)
        
        # 批量查询Playback记录
        playback_map = {}
        if video_object_names:
            playbacks = Playback.query.filter(Playback.file_path.in_(video_object_names)).all()
            for playback in playbacks:
                playback_map[playback.file_path] = playback
        
        # 遍历视频对象，构建视频列表
        for obj in video_objects:
            
            try:
                stat = minio_client.stat_object(bucket_name, obj.object_name)
                
                # 查找对应的Playback记录
                playback = playback_map.get(obj.object_name)
                thumbnail_url = None
                duration = None
                
                if playback and playback.thumbnail_path:
                    # 如果Playback记录中有封面路径，构建下载URL
                    thumbnail_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(playback.thumbnail_path, safe='')}"
                else:
                    # 如果没有Playback记录，尝试根据视频文件名构建封面路径
                    # 将视频文件扩展名替换为 .jpg
                    thumbnail_object_name = obj.object_name.rsplit('.', 1)[0] + '.jpg'
                    # 检查封面文件是否存在
                    try:
                        minio_client.stat_object(bucket_name, thumbnail_object_name)
                        thumbnail_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(thumbnail_object_name, safe='')}"
                    except S3Error:
                        # 封面文件不存在，保持为None
                        pass
                
                # 从Playback记录获取时长
                if playback:
                    duration = playback.duration
                
                videos.append({
                    'object_name': obj.object_name,
                    'filename': filename,
                    'size': stat.size,
                    'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                    'etag': stat.etag,
                    'content_type': stat.content_type or 'video/mp4',
                    'url': f"/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(obj.object_name, safe='')}",
                    'duration': duration,
                    'thumbnail_url': thumbnail_url
                })
            except Exception as e:
                logger.warning(f"获取对象信息失败: {bucket_name}/{obj.object_name}, error={str(e)}")
        
        # 按时间倒序排序
        videos.sort(key=lambda x: x['last_modified'] or '', reverse=True)
        
        # 分页
        total = len(videos)
        start = (page_no - 1) * page_size
        end = start + page_size
        paginated_videos = videos[start:end]
        
        return {
            'items': paginated_videos,
            'total': total,
            'page_no': page_no,
            'page_size': page_size
        }
    except Exception as e:
        logger.error(f"获取监控录像列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取监控录像列表失败: {str(e)}")


def delete_record_videos(space_id: int, object_names: List[str]) -> Dict:
    """批量删除监控录像
    
    Args:
        space_id: 监控录像空间ID
        object_names: 对象名称列表
    
    Returns:
        dict: 删除结果
    """
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            raise ValueError(f"监控录像空间的MinIO bucket不存在: {bucket_name}")
        
        deleted_count = 0
        failed_count = 0
        failed_objects = []
        
        for object_name in object_names:
            try:
                # object_name 应该是 device_id/filename 格式，不需要 space_code 前缀
                # 如果传入的是完整路径，直接使用；如果是文件名，需要加上 device_id
                if '/' not in object_name:
                    # 如果只是文件名，需要从 object_names 中提取 device_id（这里假设 object_names 是完整路径）
                    # 实际上，前端应该传递完整路径 device_id/filename
                    pass
                minio_client.remove_object(bucket_name, object_name)
                deleted_count += 1
                logger.info(f"删除监控录像成功: {bucket_name}/{object_name}")
            except Exception as e:
                failed_count += 1
                failed_objects.append(object_name)
                logger.warning(f"删除监控录像失败: {bucket_name}/{object_name}, error={str(e)}")
        
        return {
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'failed_objects': failed_objects
        }
    except Exception as e:
        logger.error(f"批量删除监控录像失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"批量删除监控录像失败: {str(e)}")


def get_record_video(space_id: int, object_name: str):
    """获取监控录像内容
    
    Args:
        space_id: 监控录像空间ID
        object_name: 对象名称
    
    Returns:
        tuple: (文件内容, 内容类型, 文件名)
    """
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            raise ValueError(f"监控录像空间的MinIO bucket不存在: {bucket_name}")
        
        # object_name 应该是 device_id/filename 格式，不需要 space_code 前缀
        # 如果传入的是完整路径，直接使用
        
        try:
            stat = minio_client.stat_object(bucket_name, object_name)
            data = minio_client.get_object(bucket_name, object_name)
            content = data.read()
            data.close()
            data.release_conn()
            
            return content, stat.content_type or 'video/mp4', object_name.split('/')[-1]
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise ValueError(f"录像不存在: {object_name}")
            raise
    except Exception as e:
        logger.error(f"获取监控录像失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取监控录像失败: {str(e)}")


def cleanup_old_videos_by_days(space_id: int, days: int) -> Dict:
    """根据天数清理旧的监控录像（标准存储：直接删除；归档存储：压缩后归档）
    
    Args:
        space_id: 监控录像空间ID
        days: 保留天数（超过此天数的录像将被处理）
    
    Returns:
        dict: 清理结果
    """
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name
        space_code = record_space.space_code
        save_mode = record_space.save_mode  # 0:标准存储, 1:归档存储
        
        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            return {
                'processed_count': 0,
                'deleted_count': 0,
                'archived_count': 0,
                'error_count': 0
            }
        
        # 计算截止时间
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 获取归档bucket配置
        archive_bucket_name = current_app.config.get('MINIO_ARCHIVE_BUCKET', 'record-archive')
        if save_mode == 1:  # 归档存储
            # 确保归档bucket存在
            if not minio_client.bucket_exists(archive_bucket_name):
                minio_client.make_bucket(archive_bucket_name)
                logger.info(f"创建归档bucket: {archive_bucket_name}")
        
        processed_count = 0
        deleted_count = 0
        archived_count = 0
        error_count = 0
        
        # 获取该空间文件夹下所有需要处理的录像（现在路径是 device_id/filename）
        objects_to_process = []
        # 不再使用 space_code 前缀，直接列出所有对象
        objects = minio_client.list_objects(bucket_name, prefix="", recursive=True)
        
        # 支持的视频格式
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v']
        
        for obj in objects:
            if obj.object_name.endswith('/'):  # 跳过文件夹标记
                continue
            
            # 只处理视频文件
            filename = obj.object_name.split('/')[-1]
            if not any(filename.lower().endswith(ext) for ext in video_extensions):
                continue
            
            try:
                stat = minio_client.stat_object(bucket_name, obj.object_name)
                if stat.last_modified and stat.last_modified.replace(tzinfo=None) < cutoff_time:
                    objects_to_process.append({
                        'object_name': obj.object_name,
                        'size': stat.size,
                        'last_modified': stat.last_modified
                    })
            except Exception as e:
                logger.warning(f"获取对象信息失败: {bucket_name}/{obj.object_name}, error={str(e)}")
        
        # 处理录像
        if save_mode == 0:  # 标准存储：直接删除
            for obj_info in objects_to_process:
                try:
                    minio_client.remove_object(bucket_name, obj_info['object_name'])
                    deleted_count += 1
                    processed_count += 1
                    logger.info(f"删除过期录像: {bucket_name}/{obj_info['object_name']}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"删除录像失败: {bucket_name}/{obj_info['object_name']}, error={str(e)}")
        
        else:  # 归档存储：压缩后归档
            # 按设备分组（路径格式：device_id/filename）
            device_groups = {}
            for obj_info in objects_to_process:
                # 路径格式：device_id/filename，需要提取 device_id
                parts = obj_info['object_name'].split('/')
                if len(parts) >= 1:
                    device_id = parts[0]  # device_id 是 parts[0]
                else:
                    device_id = 'unknown'
                if device_id not in device_groups:
                    device_groups[device_id] = []
                device_groups[device_id].append(obj_info)
            
            # 为每个设备创建压缩包
            for device_id, obj_list in device_groups.items():
                try:
                    # 创建ZIP压缩包
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for obj_info in obj_list:
                            try:
                                # 下载文件
                                data = minio_client.get_object(bucket_name, obj_info['object_name'])
                                file_content = data.read()
                                data.close()
                                data.release_conn()
                                
                                # 添加到ZIP
                                filename = obj_info['object_name'].split('/')[-1]
                                zip_file.writestr(filename, file_content)
                                
                                # 删除原文件
                                minio_client.remove_object(bucket_name, obj_info['object_name'])
                                deleted_count += 1
                                
                            except Exception as e:
                                logger.error(f"处理录像失败: {bucket_name}/{obj_info['object_name']}, error={str(e)}")
                                error_count += 1
                    
                    # 上传压缩包到归档bucket
                    if zip_buffer.tell() > 0:
                        zip_buffer.seek(0)
                        archive_object_name = f"{device_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
                        minio_client.put_object(
                            archive_bucket_name,
                            archive_object_name,
                            zip_buffer,
                            length=zip_buffer.tell(),
                            content_type='application/zip'
                        )
                        archived_count += 1
                        processed_count += len(obj_list)
                        logger.info(f"归档录像完成: {archive_bucket_name}/{archive_object_name}, 包含 {len(obj_list)} 个录像")
                    
                except Exception as e:
                    logger.error(f"归档设备录像失败: device_id={device_id}, error={str(e)}", exc_info=True)
                    error_count += len(obj_list)
        
        return {
            'processed_count': processed_count,
            'deleted_count': deleted_count,
            'archived_count': archived_count,
            'error_count': error_count
        }
        
    except Exception as e:
        logger.error(f"清理过期录像失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"清理过期录像失败: {str(e)}")

