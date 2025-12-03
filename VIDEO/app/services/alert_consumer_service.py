"""
告警Kafka消费者服务：订阅告警事件，上传图片到MinIO并更新数据库
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
import os
import threading
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote

from flask import current_app
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from minio import Minio
from minio.error import S3Error

from models import db, Alert
from app.services.minio_service import ModelService

logger = logging.getLogger(__name__)

_consumer = None
_consumer_thread = None
_consumer_running = False
_consumer_init_failed = False
_last_init_attempt_time = 0
_init_retry_interval = 60  # 初始化失败后，60秒内不再重试

# MinIO清空后的等待时间控制
_last_minio_cleanup_time = 0  # 上次清空MinIO的时间戳
_minio_cleanup_wait_seconds = 5  # 清空后等待5秒才能再次上传
_minio_cleanup_lock = threading.Lock()  # 保护清空时间变量的锁


def get_kafka_consumer():
    """获取Kafka消费者实例（单例，带错误处理和重试限制）"""
    global _consumer, _consumer_init_failed, _last_init_attempt_time
    
    # 从Flask配置中获取Kafka配置
    try:
        bootstrap_servers = current_app.config.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        kafka_topic = current_app.config.get('KAFKA_ALERT_TOPIC', 'iot-alert-notification')
        consumer_group = current_app.config.get('KAFKA_ALERT_CONSUMER_GROUP', 'video-alert-consumer')
        init_retry_interval = current_app.config.get('KAFKA_INIT_RETRY_INTERVAL', 60)
    except RuntimeError:
        # 不在Flask应用上下文中，使用环境变量作为后备
        import os
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        kafka_topic = os.getenv('KAFKA_ALERT_TOPIC', 'iot-alert-notification')
        consumer_group = os.getenv('KAFKA_ALERT_CONSUMER_GROUP', 'video-alert-consumer')
        init_retry_interval = int(os.getenv('KAFKA_INIT_RETRY_INTERVAL', '60'))
    
    # 如果已经初始化成功，直接返回
    if _consumer is not None:
        return _consumer
    
    # 如果之前初始化失败，且距离上次尝试时间不足，不再重试
    current_time = time.time()
    if _consumer_init_failed and (current_time - _last_init_attempt_time) < init_retry_interval:
        return None
    
    # 尝试初始化
    try:
        _consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=bootstrap_servers.split(','),
            group_id=consumer_group,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest',  # 从最新消息开始消费
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            consumer_timeout_ms=1000,  # 1秒超时，避免阻塞
            api_version=(2, 5, 0),
        )
        logger.info(f"Kafka消费者初始化成功: topic={kafka_topic}, group={consumer_group}, servers={bootstrap_servers}")
        _consumer_init_failed = False
    except Exception as e:
        _consumer = None
        _consumer_init_failed = True
        _last_init_attempt_time = current_time
        logger.warning(f"Kafka消费者初始化失败: {str(e)}，将在 {init_retry_interval} 秒后重试")
        return None
    
    return _consumer


def delete_all_alert_images_from_minio():
    """
    删除MinIO的alert-images存储桶下的所有图片
    清空后会记录时间，后续5秒内的上传请求将被跳过
    
    Returns:
        int: 删除的图片数量，如果失败返回0
    """
    global _last_minio_cleanup_time
    
    try:
        # 获取MinIO客户端
        minio_client = ModelService.get_minio_client()
        
        # 存储桶名称
        bucket_name = 'alert-images'
        
        # 检查存储桶是否存在
        if not minio_client.bucket_exists(bucket_name):
            logger.info(f"MinIO存储桶不存在，无需删除: {bucket_name}")
            return 0
        
        # 列出所有对象并删除
        deleted_count = 0
        objects = minio_client.list_objects(bucket_name, prefix="", recursive=True)
        
        for obj in objects:
            try:
                # 跳过文件夹标记（以/结尾的对象）
                if obj.object_name.endswith('/'):
                    continue
                
                minio_client.remove_object(bucket_name, obj.object_name)
                deleted_count += 1
                logger.debug(f"删除告警图片: {bucket_name}/{obj.object_name}")
            except Exception as e:
                logger.warning(f"删除告警图片失败: {bucket_name}/{obj.object_name}, error={str(e)}")
        
        # 记录清空时间（使用锁保护）
        with _minio_cleanup_lock:
            _last_minio_cleanup_time = time.time()
        
        logger.info(f"已删除MinIO告警图片存储桶下的所有图片，共 {deleted_count} 张，将在 {_minio_cleanup_wait_seconds} 秒内跳过所有上传请求")
        return deleted_count
        
    except S3Error as e:
        logger.error(f"删除MinIO告警图片失败（S3Error）: {str(e)}")
        return 0
    except Exception as e:
        logger.error(f"删除MinIO告警图片失败: {str(e)}", exc_info=True)
        return 0


def wait_for_file_stable(image_path: str, max_wait_seconds: int = 5, check_interval: float = 0.1) -> Optional[int]:
    """
    等待文件写入完成（文件大小稳定）
    
    Args:
        image_path: 文件路径
        max_wait_seconds: 最大等待时间（秒）
        check_interval: 检查间隔（秒）
    
    Returns:
        int: 稳定的文件大小（字节），如果超时或文件不存在返回None
    """
    if not os.path.exists(image_path):
        return None
    
    start_time = time.time()
    last_size = None
    stable_count = 0
    required_stable_checks = 3  # 需要连续3次大小相同才认为稳定
    
    while (time.time() - start_time) < max_wait_seconds:
        try:
            current_size = os.path.getsize(image_path)
            
            if current_size == 0:
                # 文件大小为0，可能还在写入，继续等待
                time.sleep(check_interval)
                continue
            
            if last_size is None:
                last_size = current_size
                stable_count = 1
            elif current_size == last_size:
                stable_count += 1
                if stable_count >= required_stable_checks:
                    # 文件大小已稳定
                    return current_size
            else:
                # 文件大小变化了，重置计数
                last_size = current_size
                stable_count = 1
            
            time.sleep(check_interval)
        except OSError:
            # 文件可能被删除或无法访问
            return None
    
    # 超时，返回最后一次检测到的大小（如果存在）
    return last_size if last_size and last_size > 0 else None


def upload_image_to_minio(image_path: str, alert_id: int, device_id: str) -> Optional[str]:
    """
    上传告警图片到MinIO的alert-images存储桶
    如果最近5秒内清空过MinIO，将跳过上传
    
    Args:
        image_path: 本地图片路径
        alert_id: 告警ID
        device_id: 设备ID
    
    Returns:
        str: MinIO中的对象路径，如果失败返回None
    """
    # 检查是否在清空后的等待期内
    with _minio_cleanup_lock:
        if _last_minio_cleanup_time > 0:
            current_time = time.time()
            elapsed = current_time - _last_minio_cleanup_time
            if elapsed < _minio_cleanup_wait_seconds:
                wait_remaining = _minio_cleanup_wait_seconds - elapsed
                logger.debug(f"告警 {alert_id} 图片上传跳过：MinIO清空后等待期内（还需等待 {wait_remaining:.1f} 秒）")
                return None
    
    try:
        # 检查本地文件是否存在
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"告警图片文件不存在: {image_path}")
            return None
        
        # 等待文件写入完成（文件大小稳定）
        file_size = wait_for_file_stable(image_path, max_wait_seconds=5, check_interval=0.1)
        if file_size is None or file_size == 0:
            logger.warning(f"告警图片文件不可用或大小为0: {image_path} (等待文件稳定后)")
            return None
        
        # 获取MinIO客户端
        minio_client = ModelService.get_minio_client()
        
        # 存储桶名称
        bucket_name = 'alert-images'
        
        # 确保存储桶存在
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"创建MinIO存储桶: {bucket_name}")
        
        # 生成对象名称：使用日期目录结构，格式：YYYY/MM/DD/alert_{alert_id}_{device_id}_{filename}
        file_name = os.path.basename(image_path)
        file_ext = os.path.splitext(file_name)[1] or '.jpg'
        now = datetime.now()
        object_name = f"{now.year}/{now.month:02d}/{now.day:02d}/alert_{alert_id}_{device_id}_{now.strftime('%Y%m%d%H%M%S')}{file_ext}"
        
        # 读取文件内容到内存，确保文件完整性
        # 使用二进制模式读取，在文件大小稳定后读取，避免文件在读取过程中被修改
        max_retries = 3
        retry_count = 0
        file_content = None
        
        while retry_count < max_retries:
            try:
                with open(image_path, 'rb') as file_data:
                    # 读取完整文件内容到内存
                    file_content = file_data.read()
                    
                    # 验证读取的数据大小是否与文件大小一致
                    if len(file_content) == file_size:
                        # 读取成功，跳出重试循环
                        break
                    else:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.debug(f"告警图片文件读取大小不匹配（重试 {retry_count}/{max_retries}）: 期望 {file_size} 字节，实际读取 {len(file_content)} 字节，等待文件稳定后重试...")
                            time.sleep(0.2)  # 等待200ms后重试
                            # 重新等待文件稳定（文件可能还在写入）
                            new_size = wait_for_file_stable(image_path, max_wait_seconds=2, check_interval=0.1)
                            if new_size and new_size > 0:
                                file_size = new_size
                                # 重置重试计数，因为文件大小变化了，需要重新读取
                                retry_count = 0
                            else:
                                logger.debug(f"文件大小检测失败，继续重试...")
                        else:
                            logger.warning(f"告警图片文件读取不完整（已重试 {max_retries} 次）: 期望 {file_size} 字节，实际读取 {len(file_content)} 字节")
                            return None
            except (IOError, OSError) as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.debug(f"告警图片文件读取失败（重试 {retry_count}/{max_retries}）: {str(e)}，等待后重试...")
                    time.sleep(0.2)
                else:
                    logger.warning(f"告警图片文件读取失败（已重试 {max_retries} 次）: {str(e)}")
                    return None
        
        if file_content is None or len(file_content) != file_size:
            logger.warning(f"告警图片文件读取失败: {image_path}")
            return None
        
        # 使用put_object上传文件内容（从内存流上传，避免文件被修改的问题）
        data_stream = BytesIO(file_content)
        minio_client.put_object(
            bucket_name,
            object_name,
            data_stream,
            length=len(file_content),
            content_type='image/jpeg' if file_ext.lower() in ['.jpg', '.jpeg'] else 'image/png' if file_ext.lower() == '.png' else 'application/octet-stream'
        )
        
        logger.debug(f"告警图片上传成功: {bucket_name}/{object_name}, 大小: {file_size} 字节")
        
        # 返回MinIO下载URL（用于存储到数据库）
        # 格式：/api/v1/buckets/{bucket_name}/objects/download?prefix={url_encoded_object_name}
        download_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(object_name, safe='')}"
        return download_url
        
    except S3Error as e:
        error_msg = str(e)
        logger.error(f"MinIO上传错误: {error_msg}")
        
        # 检查是否是 "stream having not enough data" 错误
        if "stream having not enough data" in error_msg.lower():
            logger.warning(f"检测到MinIO数据流错误，将删除alert-images存储桶下的所有图片")
            deleted_count = delete_all_alert_images_from_minio()
            logger.info(f"已清理告警图片存储桶，删除了 {deleted_count} 张图片")
        
        return None
    except Exception as e:
        error_msg = str(e)
        logger.error(f"上传告警图片到MinIO失败: {error_msg}", exc_info=True)
        
        # 检查是否是 "stream having not enough data" 错误
        if "stream having not enough data" in error_msg.lower():
            logger.warning(f"检测到MinIO数据流错误，将删除alert-images存储桶下的所有图片")
            deleted_count = delete_all_alert_images_from_minio()
            logger.info(f"已清理告警图片存储桶，删除了 {deleted_count} 张图片")
        
        return None


def process_alert_message(message: Dict):
    """
    处理告警消息：上传图片到MinIO并更新数据库
    注意：告警记录已经在alert_hook_service中先插入数据库，这里只负责上传图片
    
    Args:
        message: Kafka消息内容（字典格式）
    """
    try:
        alert_id = message.get('id')
        image_path = message.get('image_path')
        
        if not alert_id:
            logger.warning(f"告警消息缺少ID字段: {message}")
            return
        
        # 如果没有图片路径，跳过图片上传
        if not image_path:
            logger.debug(f"告警 {alert_id} 没有图片路径，跳过图片上传")
            return
        
        # 检查是否在清空后的等待期内（在数据库查询前检查，避免不必要的数据库操作）
        with _minio_cleanup_lock:
            if _last_minio_cleanup_time > 0:
                current_time = time.time()
                elapsed = current_time - _last_minio_cleanup_time
                if elapsed < _minio_cleanup_wait_seconds:
                    wait_remaining = _minio_cleanup_wait_seconds - elapsed
                    logger.debug(f"告警 {alert_id} 图片上传跳过：MinIO清空后等待期内（还需等待 {wait_remaining:.1f} 秒）")
                    return
        
        # 上传图片到MinIO（如果不在等待期内）
        device_id = message.get('device_id', 'unknown')
        minio_path = upload_image_to_minio(image_path, alert_id, device_id)
        
        if minio_path:
            # 在Flask应用上下文中执行数据库操作
            with current_app.app_context():
                # 查询告警记录（告警记录已经在alert_hook_service中先插入数据库）
                alert = Alert.query.get(alert_id)
                if not alert:
                    logger.warning(f"告警记录不存在: alert_id={alert_id}")
                    return
                
                # 更新数据库中的image_path
                alert.image_path = minio_path
                db.session.commit()
                logger.debug(f"告警 {alert_id} 图片路径已更新: {minio_path}")
        else:
            logger.warning(f"告警 {alert_id} 图片上传失败，保留原始路径: {image_path}")
                
    except Exception as e:
        logger.error(f"处理告警消息失败: {str(e)}", exc_info=True)
        # 确保数据库会话回滚
        try:
            with current_app.app_context():
                db.session.rollback()
        except:
            pass


def consume_alert_messages():
    """消费Kafka告警消息的主循环"""
    global _consumer_running
    
    logger.info("开始消费Kafka告警消息...")
    _consumer_running = True
    
    while _consumer_running:
        try:
            consumer = get_kafka_consumer()
            if consumer is None:
                # 消费者初始化失败，等待后重试
                time.sleep(10)
                continue
            
            # 消费消息（带超时，避免阻塞）
            for message in consumer:
                if not _consumer_running:
                    break
                
                try:
                    # 解析消息
                    message_value = message.value
                    if isinstance(message_value, dict):
                        logger.debug(f"收到告警消息: alert_id={message_value.get('id')}")
                        process_alert_message(message_value)
                    else:
                        logger.warning(f"收到非字典格式的消息: {type(message_value)}")
                except Exception as e:
                    logger.error(f"处理消息失败: {str(e)}", exc_info=True)
                    # 继续处理下一条消息，不中断消费
                    continue
                    
        except KafkaError as e:
            logger.error(f"Kafka消费错误: {str(e)}")
            # 重置消费者，下次重新初始化
            global _consumer
            if _consumer:
                try:
                    _consumer.close()
                except:
                    pass
                _consumer = None
            time.sleep(10)  # 等待后重试
        except Exception as e:
            logger.error(f"消费告警消息异常: {str(e)}", exc_info=True)
            time.sleep(10)  # 等待后重试
    
    logger.info("Kafka告警消息消费已停止")


def start_alert_consumer(app):
    """启动告警消息消费者线程"""
    global _consumer_thread, _consumer_running
    
    if _consumer_thread is not None and _consumer_thread.is_alive():
        logger.info("告警消息消费者线程已在运行")
        return
    
    # 在应用上下文中启动消费者
    def start_consumer():
        with app.app_context():
            consume_alert_messages()
    
    _consumer_thread = threading.Thread(target=start_consumer, daemon=True, name="AlertConsumer")
    _consumer_thread.start()
    logger.info("告警消息消费者线程已启动")


def stop_alert_consumer():
    """停止告警消息消费者"""
    global _consumer_running, _consumer, _consumer_thread
    
    logger.info("正在停止告警消息消费者...")
    _consumer_running = False
    
    if _consumer:
        try:
            _consumer.close()
        except:
            pass
        _consumer = None
    
    if _consumer_thread and _consumer_thread.is_alive():
        _consumer_thread.join(timeout=5)
    
    logger.info("告警消息消费者已停止")

