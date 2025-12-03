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
from pathlib import Path
from typing import Dict, Optional

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


def upload_image_to_minio(image_path: str, alert_id: int, device_id: str) -> Optional[str]:
    """
    上传告警图片到MinIO的alert-images存储桶
    
    Args:
        image_path: 本地图片路径
        alert_id: 告警ID
        device_id: 设备ID
    
    Returns:
        str: MinIO中的对象路径，如果失败返回None
    """
    try:
        # 检查本地文件是否存在
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"告警图片文件不存在: {image_path}")
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
        
        # 上传文件到MinIO
        minio_client.fput_object(bucket_name, object_name, image_path)
        logger.info(f"告警图片上传成功: {bucket_name}/{object_name}")
        
        # 返回MinIO对象路径（用于存储到数据库）
        return f"{bucket_name}/{object_name}"
        
    except S3Error as e:
        logger.error(f"MinIO上传错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"上传告警图片到MinIO失败: {str(e)}", exc_info=True)
        return None


def process_alert_message(message: Dict):
    """
    处理告警消息：上传图片到MinIO并更新数据库
    
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
        
        # 在Flask应用上下文中执行数据库操作
        with current_app.app_context():
            # 查询告警记录
            alert = Alert.query.get(alert_id)
            if not alert:
                logger.warning(f"告警记录不存在: alert_id={alert_id}")
                return
            
            # 如果已经上传过（image_path已经是MinIO路径），跳过
            if alert.image_path and (alert.image_path.startswith('alert-images/') or 'alert-images/' in alert.image_path):
                logger.debug(f"告警 {alert_id} 图片已上传到MinIO，跳过")
                return
            
            # 上传图片到MinIO
            device_id = message.get('device_id', 'unknown')
            minio_path = upload_image_to_minio(image_path, alert_id, device_id)
            
            if minio_path:
                # 更新数据库中的image_path
                alert.image_path = minio_path
                db.session.commit()
                logger.info(f"告警 {alert_id} 图片路径已更新: {minio_path}")
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

