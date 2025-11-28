"""
自动抽帧服务 - 定时从所有在线摄像头的RTSP/RTMP流中抽帧并保存到抓拍空间
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import threading
import cv2
import uuid
import io
import subprocess
import numpy as np
from datetime import datetime

from models import Device
from app.services.snap_space_service import get_minio_client, get_snap_space_by_device_id, create_snap_space_for_device
from app.services.camera_service import _monitor
from app.utils.ip_utils import check_ip_reachable

logger = logging.getLogger(__name__)

# 全局线程控制
_extraction_thread = None
_extraction_stop_event = threading.Event()
_app_instance = None


def extract_frame_from_rtsp(device, snap_space):
    """从RTSP流中抽帧并保存到抓拍空间
    
    Args:
        device: Device对象
        snap_space: SnapSpace对象
    
    Returns:
        bool: 是否成功
    """
    try:
        # 检查设备是否有源地址
        if not device.source:
            logger.warning(f"设备 {device.id} 没有源地址，跳过抽帧")
            return False
        
        source = device.source.strip()
        source_lower = source.lower()
        
        # 判断是否是RTMP流
        if source_lower.startswith('rtmp://'):
            # 使用FFmpeg从RTMP流中抽帧
            try:
                logger.debug(f"设备 {device.id} 开始从RTMP流抽帧: {source}")
                # 使用FFmpeg从RTMP流中抽取一帧并输出为JPEG格式
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', source,  # RTMP流地址
                    '-vframes', '1',  # 只抽取1帧
                    '-f', 'image2',  # 输出格式为图片
                    '-vcodec', 'mjpeg',  # 使用MJPEG编码
                    '-q:v', '2',  # 高质量
                    'pipe:1'  # 输出到标准输出
                ]
                
                # 执行FFmpeg命令并捕获输出
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(timeout=10)  # 10秒超时
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
                    logger.error(f"设备 {device.id} RTMP流抽帧失败: {error_msg}")
                    return False
                
                if not stdout:
                    logger.error(f"设备 {device.id} RTMP流抽帧失败: 未获取到图像数据")
                    return False
                
                # 将FFmpeg输出的JPEG数据解码为OpenCV图像
                image_array = np.frombuffer(stdout, np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                if frame is None:
                    logger.error(f"设备 {device.id} RTMP流抽帧失败: 图像解码失败")
                    return False
                
                logger.debug(f"设备 {device.id} RTMP流读取成功，帧大小: {frame.shape if frame is not None else 'None'}")
            except subprocess.TimeoutExpired:
                logger.error(f"设备 {device.id} RTMP流抽帧超时")
                return False
            except Exception as e:
                logger.error(f"设备 {device.id} RTMP流抽帧异常: {str(e)}", exc_info=True)
                return False
        else:
            # 从RTSP流中抽帧（使用OpenCV）
            logger.debug(f"设备 {device.id} 开始连接RTSP流: {source}")
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                logger.error(f"设备 {device.id} 无法打开RTSP流: {source}")
                return False
            
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲区，获取最新帧
            
            # 设置超时时间（5秒）
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error(f"设备 {device.id} RTSP流读取失败（ret=False），源地址: {source}")
                return False
            
            if frame is None:
                logger.error(f"设备 {device.id} RTSP流读取失败（frame=None），源地址: {source}")
                return False
            
            logger.debug(f"设备 {device.id} RTSP流读取成功，帧大小: {frame.shape if frame is not None else 'None'}")
        
        # 获取MinIO客户端
        try:
            minio_client = get_minio_client()
            logger.debug(f"设备 {device.id} MinIO客户端获取成功")
        except Exception as e:
            logger.error(f"设备 {device.id} 获取MinIO客户端失败: {str(e)}", exc_info=True)
            return False
        
        bucket_name = snap_space.bucket_name
        space_code = snap_space.space_code
        logger.debug(f"设备 {device.id} 使用bucket: {bucket_name}, 空间代码: {space_code}")
        
        # 确保bucket存在
        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                logger.info(f"创建MinIO bucket: {bucket_name}")
            else:
                logger.debug(f"设备 {device.id} MinIO bucket已存在: {bucket_name}")
        except Exception as e:
            logger.error(f"设备 {device.id} 检查/创建MinIO bucket失败: {str(e)}", exc_info=True)
            return False
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{uuid.uuid4().hex[:8]}_{timestamp}.jpg"
        device_folder = f"{device.id}/"
        object_name = f"{device_folder}{unique_filename}"
        
        # 编码图片
        logger.debug(f"设备 {device.id} 开始编码图片")
        success, encoded_image = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            logger.error(f"设备 {device.id} 图片编码失败")
            return False
        
        # 上传到MinIO
        image_bytes = encoded_image.tobytes()
        logger.debug(f"设备 {device.id} 图片编码成功，大小: {len(image_bytes)} 字节，准备上传到: {bucket_name}/{object_name}")
        try:
            minio_client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(image_bytes),
                length=len(image_bytes),
                content_type='image/jpeg'
            )
            logger.info(f"设备 {device.id} 抽帧成功，已保存到: {bucket_name}/{object_name}")
            return True
        except Exception as minio_error:
            logger.error(f"设备 {device.id} MinIO上传失败: {str(minio_error)}", exc_info=True)
            logger.error(f"设备 {device.id} MinIO上传失败详情 - bucket: {bucket_name}, object: {object_name}, 大小: {len(image_bytes)}")
            return False
        
    except Exception as e:
        logger.error(f"设备 {device.id} 抽帧失败: {str(e)}", exc_info=True)
        return False


def check_and_update_device_status(device):
    """检查设备状态，如果访问不到则设为离线
    
    Args:
        device: Device对象
    
    Returns:
        bool: 设备是否在线
    """
    try:
        # 如果是RTMP流，默认在线
        if device.source and device.source.strip().lower().startswith('rtmp://'):
            return True
        
        # 检查IP是否可达
        if device.ip:
            is_reachable = check_ip_reachable(device.ip)
            if not is_reachable:
                # IP不可达，更新监控状态为离线
                _monitor.update(device.id, device.ip)
                logger.warning(f"设备 {device.id} (IP: {device.ip}) 不可达，状态设为离线")
                return False
            else:
                # IP可达，更新监控状态为在线
                _monitor.update(device.id, device.ip)
                return True
        else:
            # 没有IP地址，尝试从RTSP流判断
            try:
                cap = cv2.VideoCapture(device.source)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ret, _ = cap.read()
                cap.release()
                
                if not ret:
                    logger.warning(f"设备 {device.id} RTSP流不可访问，状态设为离线")
                    return False
                return True
            except Exception as e:
                logger.warning(f"设备 {device.id} RTSP流检查失败: {str(e)}，状态设为离线")
                return False
    except Exception as e:
        logger.error(f"检查设备 {device.id} 状态失败: {str(e)}", exc_info=True)
        return False


def process_online_cameras(app):
    """处理所有在线摄像头的抽帧任务
    
    Args:
        app: Flask应用实例
    """
    try:
        with app.app_context():
            # 查询所有设备
            devices = Device.query.all()
            
            if not devices:
                logger.debug("没有找到任何设备")
                return
            
            processed_count = 0
            success_count = 0
            offline_count = 0
            
            for device in devices:
                try:
                    # 检查设备是否开启了自动抓拍（默认不开启）
                    auto_snap_enabled = getattr(device, 'auto_snap_enabled', False)
                    if not auto_snap_enabled:
                        # 设备未开启自动抓拍，跳过
                        continue
                    
                    # 检查设备是否在线
                    is_online = _monitor.is_online(device.id) if device.ip else False
                    
                    # 如果监控中没有该设备，尝试添加
                    if device.ip and not _monitor.is_watching(device.id):
                        is_online = check_and_update_device_status(device)
                    elif device.ip:
                        # 已经在监控中，直接检查状态
                        is_online = _monitor.is_online(device.id)
                    
                    # 如果设备不在线，跳过
                    if not is_online:
                        # 再次检查设备状态（可能刚上线）
                        is_online = check_and_update_device_status(device)
                        if not is_online:
                            offline_count += 1
                            continue
                    
                    processed_count += 1
                    
                    # 获取或创建抓拍空间
                    snap_space = get_snap_space_by_device_id(device.id)
                    if not snap_space:
                        # 自动创建抓拍空间
                        try:
                            snap_space = create_snap_space_for_device(device.id, device.name)
                            logger.info(f"为设备 {device.id} 自动创建抓拍空间: {snap_space.space_code}")
                        except Exception as e:
                            logger.error(f"为设备 {device.id} 创建抓拍空间失败: {str(e)}")
                            continue
                    
                    # 从RTSP流抽帧并保存
                    logger.info(f"开始为设备 {device.id} ({device.name}) 抽帧，源地址: {device.source}")
                    result = extract_frame_from_rtsp(device, snap_space)
                    if result:
                        success_count += 1
                        logger.info(f"设备 {device.id} ({device.name}) 抽帧成功")
                    else:
                        # 抽帧失败，检查设备状态（extract_frame_from_rtsp内部已记录详细错误）
                        logger.warning(f"设备 {device.id} ({device.name}) 抽帧失败，检查设备状态")
                        check_and_update_device_status(device)
                        
                except Exception as e:
                    logger.error(f"处理设备 {device.id} 失败: {str(e)}", exc_info=True)
            
            logger.info(f"定时抽帧任务完成: 处理={processed_count}, 成功={success_count}, 离线={offline_count}, 总数={len(devices)}")
            
    except Exception as e:
        logger.error(f"处理在线摄像头抽帧任务失败: {str(e)}", exc_info=True)


def auto_frame_extraction_worker():
    """自动抽帧工作线程（每分钟执行一次）"""
    logger.info("自动抽帧线程已启动，每分钟执行一次")
    
    while not _extraction_stop_event.is_set():
        try:
            # 执行抽帧任务
            if _app_instance:
                process_online_cameras(_app_instance)
            else:
                logger.warning("Flask应用实例未设置，跳过本次抽帧任务")
            
            # 等待60秒（1分钟）
            _extraction_stop_event.wait(60)
            
        except Exception as e:
            logger.error(f"自动抽帧线程异常: {str(e)}", exc_info=True)
            # 发生异常时等待一段时间再继续
            _extraction_stop_event.wait(60)
    
    logger.info("自动抽帧线程已停止")


def start_auto_frame_extraction(app=None):
    """启动自动抽帧线程
    
    Args:
        app: Flask应用实例（可选，如果提供则用于应用上下文）
    """
    global _extraction_thread, _app_instance
    
    if _app_instance is None and app is not None:
        _app_instance = app
    
    if _extraction_thread is not None and _extraction_thread.is_alive():
        logger.warning("自动抽帧线程已在运行")
        return
    
    _extraction_stop_event.clear()
    _extraction_thread = threading.Thread(
        target=auto_frame_extraction_worker,
        daemon=True,
        name="AutoFrameExtraction"
    )
    _extraction_thread.start()
    logger.info("自动抽帧线程启动成功")


def stop_auto_frame_extraction():
    """停止自动抽帧线程"""
    global _extraction_thread
    
    if _extraction_thread is None or not _extraction_thread.is_alive():
        return
    
    _extraction_stop_event.set()
    _extraction_thread.join(timeout=5.0)
    logger.info("自动抽帧线程已停止")

