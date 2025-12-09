#!/usr/bin/env python3
"""
推流转发服务程序
用于批量推送多个摄像头实时画面，无需AI推理

架构：
- 缓流器：每个摄像头从RTSP读取帧，放入各自的缓流器队列
- 抽帧器：1个共享线程从所有摄像头的缓流器队列抽帧，放入各自的抽帧队列
- 推流器：1个共享线程从所有摄像头的抽帧队列获取帧，推送到各自的RTMP

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import time
import threading
import logging
import subprocess
import signal
import queue
import cv2
import numpy as np
import requests
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, video_root)

# 导入VIDEO模块的模型
from models import db, StreamForwardTask, Device

# Flask应用实例（延迟创建）
_flask_app = None

def get_flask_app():
    """获取Flask应用实例"""
    global _flask_app
    if _flask_app is None:
        from flask import Flask
        app = Flask(__name__)
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_size': 10,
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10,
            }
        }
        db.init_app(app)
        _flask_app = app
    return _flask_app

# 加载环境变量
load_dotenv()

# ============================================
# 自定义日志处理器
# ============================================
class DailyRotatingFileHandler(logging.FileHandler):
    """按日期自动切换的日志文件处理器"""
    
    def __init__(self, log_dir, filename_pattern='%Y-%m-%d.log', encoding='utf-8'):
        self.log_dir = log_dir
        self.filename_pattern = filename_pattern
        self.current_date = datetime.now().date()
        self.current_file_path = None
        self._update_file_path()
        super().__init__(self.current_file_path, encoding=encoding)
    
    def _update_file_path(self):
        """更新当前日志文件路径"""
        today = datetime.now().date()
        if today != self.current_date or self.current_file_path is None:
            self.current_date = today
            filename = datetime.now().strftime(self.filename_pattern)
            self.current_file_path = os.path.join(self.log_dir, filename)
    
    def emit(self, record):
        """发送日志记录，如果日期变化则切换文件"""
        if datetime.now().date() != self.current_date:
            self.close()
            self._update_file_path()
            self.baseFilename = self.current_file_path
            if self.stream:
                self.stream.close()
                self.stream = None
            self.stream = self._open()
        
        super().emit(record)

# 配置日志
# 先获取日志目录（video_root在文件开头已定义）
log_path = os.getenv('LOG_PATH')
if log_path:
    service_log_dir = log_path
else:
    # video_root在文件开头已定义
    service_log_dir = os.path.join(video_root, 'logs', f'stream_forward_task_{os.getenv("TASK_ID", "0")}')
os.makedirs(service_log_dir, exist_ok=True)

# 保存日志目录到全局变量，供心跳上报使用
SERVICE_LOG_DIR = service_log_dir

# 创建日志格式
log_format = '[STREAM_FORWARD] [%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

# 创建根logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()

# 创建文件handler
file_handler = DailyRotatingFileHandler(service_log_dir, filename_pattern='%Y-%m-%d.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# 同时输出到stderr
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

# 全局变量
TASK_ID = int(os.getenv('TASK_ID', '0'))
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
VIDEO_SERVICE_PORT = os.getenv('VIDEO_SERVICE_PORT', '6000')
# GATEWAY_URL 已不再用于心跳上报，心跳上报直接使用 localhost:VIDEO_SERVICE_PORT
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:48080')

# 数据库会话
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db_session = scoped_session(SessionLocal)

# 配置参数
SOURCE_FPS = int(os.getenv('SOURCE_FPS', '15'))  # 源流帧率
TARGET_WIDTH = int(os.getenv('TARGET_WIDTH', '640'))  # 目标宽度
TARGET_HEIGHT = int(os.getenv('TARGET_HEIGHT', '360'))  # 目标高度
TARGET_RESOLUTION = (TARGET_WIDTH, TARGET_HEIGHT)
EXTRACT_INTERVAL = int(os.getenv('EXTRACT_INTERVAL', '5'))  # 抽帧间隔（每N帧抽1帧）
# 计算实际推流帧率（抽帧后的帧率）
TARGET_FPS = max(1, SOURCE_FPS // EXTRACT_INTERVAL)  # 实际推流帧率，至少1fps
BUFFER_QUEUE_SIZE = int(os.getenv('BUFFER_QUEUE_SIZE', '50'))  # 缓流器队列大小

# FFmpeg编码参数
FFMPEG_PRESET_ENV = os.getenv('FFMPEG_PRESET', 'ultrafast')
FFMPEG_PRESET = FFMPEG_PRESET_ENV.strip() if FFMPEG_PRESET_ENV and FFMPEG_PRESET_ENV.strip() else 'ultrafast'
FFMPEG_VIDEO_BITRATE_ENV = os.getenv('FFMPEG_VIDEO_BITRATE', '500k')
FFMPEG_VIDEO_BITRATE = FFMPEG_VIDEO_BITRATE_ENV.strip() if FFMPEG_VIDEO_BITRATE_ENV and FFMPEG_VIDEO_BITRATE_ENV.strip() else '500k'
FFMPEG_THREADS_ENV = os.getenv('FFMPEG_THREADS', None)
FFMPEG_THREADS = None if not FFMPEG_THREADS_ENV or FFMPEG_THREADS_ENV.strip() == '' else FFMPEG_THREADS_ENV.strip()
FFMPEG_GOP_SIZE_ENV = os.getenv('FFMPEG_GOP_SIZE', None)
FFMPEG_GOP_SIZE = int(FFMPEG_GOP_SIZE_ENV) if FFMPEG_GOP_SIZE_ENV else (SOURCE_FPS * 2)

# 全局变量
stop_event = threading.Event()
task_config = None
# 优化后的队列架构：使用两个队列避免帧反复进出
# 原始帧队列：存储从RTSP读取的原始帧（未处理）
raw_frame_queues = {}  # {device_id: queue.Queue}
# 已处理帧队列：存储抽帧器处理后的帧（已标记为需要推送）
processed_frame_queues = {}  # {device_id: queue.Queue}
# 摄像头流连接（VideoCapture对象）
device_caps = {}  # {device_id: cv2.VideoCapture}
# 摄像头推送进程（FFmpeg进程）
device_pushers = {}  # {device_id: subprocess.Popen}
# FFmpeg进程的stderr读取线程和错误信息
device_pusher_stderr_threads = {}  # {device_id: threading.Thread}
device_pusher_stderr_buffers = {}  # {device_id: list}
device_pusher_stderr_locks = {}  # {device_id: threading.Lock}
# 设备流信息
device_streams = {}  # {device_id: {'rtsp_url': str, 'rtmp_url': str, 'device_name': str}}
# 线程锁
device_locks = {}  # {device_id: threading.Lock()}
# 帧计数
frame_counts = {}  # {device_id: int}
# 心跳线程
heartbeat_thread = None


def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def load_task_config():
    """加载任务配置"""
    global task_config
    
    try:
        with get_flask_app().app_context():
            task = StreamForwardTask.query.get(TASK_ID)
            if not task:
                logger.error(f"推流转发任务不存在: TASK_ID={TASK_ID}")
                return False
            
            # 获取关联的设备
            devices = task.devices if task.devices else []
            if not devices:
                logger.error(f"推流转发任务没有关联的设备: TASK_ID={TASK_ID}")
                return False
            
            # 构建设备流信息
            device_streams_info = {}
            for device in devices:
                # 获取RTSP输入流地址
                rtsp_url = device.source
                if not rtsp_url:
                    logger.warning(f"设备 {device.id} 没有配置源地址，跳过")
                    continue
                
                # 获取RTMP输出流地址
                rtmp_url = device.rtmp_stream
                if not rtmp_url:
                    logger.warning(f"设备 {device.id} 没有配置RTMP输出地址，跳过")
                    continue
                
                device_streams_info[device.id] = {
                    'rtsp_url': rtsp_url,
                    'rtmp_url': rtmp_url,
                    'device_name': device.name or device.id
                }
            
            task_config = type('TaskConfig', (), {
                'task_id': task.id,
                'task_name': task.task_name,
                'output_format': task.output_format,
                'output_quality': task.output_quality,
                'output_bitrate': task.output_bitrate,
                'device_streams': device_streams_info
            })()
            
            logger.info(f"✅ 任务配置加载成功: task_id={TASK_ID}, task_name={task.task_name}, 设备数={len(device_streams_info)}")
            return True
            
    except Exception as e:
        logger.error(f"❌ 加载任务配置失败: {str(e)}", exc_info=True)
        return False


def check_rtmp_server_connection(rtmp_url: str) -> bool:
    """检查RTMP服务器是否可用"""
    try:
        # 从RTMP URL中提取主机和端口
        if not rtmp_url.startswith('rtmp://'):
            return False
        
        url_parts = rtmp_url.replace('rtmp://', '').split('/')
        host_port = url_parts[0]
        
        if ':' in host_port:
            host, port_str = host_port.split(':')
            try:
                port = int(port_str)
            except ValueError:
                port = 1935  # 默认RTMP端口
        else:
            host = host_port
            port = 1935  # 默认RTMP端口
        
        # 尝试连接RTMP服务器端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        return result == 0
    except Exception as e:
        logger.debug(f"检查RTMP服务器连接时出错: {str(e)}")
        return False


def read_ffmpeg_stderr(device_id: str, stderr_pipe, stderr_buffer: list, stderr_lock: threading.Lock):
    """读取FFmpeg进程的stderr输出"""
    try:
        for line in iter(stderr_pipe.readline, b''):
            if not line:
                break
            try:
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str:
                    with stderr_lock:
                        stderr_buffer.append(line_str)
                        # 只保留最近100行
                        if len(stderr_buffer) > 100:
                            stderr_buffer.pop(0)
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try:
            stderr_pipe.close()
        except:
            pass


def buffer_worker(device_id: str):
    """缓流器工作线程：为指定摄像头缓冲源流，从RTSP读取帧放入缓流器队列"""
    logger.info(f"💾 缓流器线程启动 [设备: {device_id}]")
    
    if not task_config or not hasattr(task_config, 'device_streams'):
        logger.error(f"任务配置未加载，设备 {device_id} 缓流器退出")
        return
    
    device_stream_info = task_config.device_streams.get(device_id)
    if not device_stream_info:
        logger.error(f"设备 {device_id} 流信息不存在，缓流器退出")
        return
    
    rtsp_url = device_stream_info.get('rtsp_url')
    device_name = device_stream_info.get('device_name', device_id)
    
    if not rtsp_url:
        logger.error(f"设备 {device_id} 输入流地址不存在，缓流器退出")
        return
    
    # 初始化帧计数
    if device_id not in frame_counts:
        frame_counts[device_id] = 0
    
    cap = None
    retry_count = 0
    max_retries = 5
    
    # 流畅度优化：基于时间戳的帧率控制（使用更精确的时间）
    frame_interval = 1.0 / SOURCE_FPS
    last_frame_time = time.perf_counter()  # 使用更高精度的时间
    
    while not stop_event.is_set():
        try:
            # 打开源流
            if cap is None or not cap.isOpened():
                stream_type = "RTSP" if rtsp_url.startswith('rtsp://') else "RTMP" if rtsp_url.startswith('rtmp://') else "流"
                
                logger.info(f"正在连接设备 {device_id} 的 {stream_type} 流: {rtsp_url} (重试次数: {retry_count})")
                
                try:
                    # 使用 FFmpeg 后端
                    if rtsp_url.startswith('rtmp://') or rtsp_url.startswith('rtsp://'):
                        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                    else:
                        cap = cv2.VideoCapture(rtsp_url)
                    
                    # 设置缓冲区大小为1，减少延迟
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # 设置超时参数
                    if rtsp_url.startswith('rtmp://') or rtsp_url.startswith('rtsp://'):
                        try:
                            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
                        except (AttributeError, cv2.error):
                            pass
                        try:
                            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
                        except (AttributeError, cv2.error):
                            pass
                    
                except Exception as e:
                    logger.error(f"设备 {device_id} 创建 VideoCapture 时出错: {str(e)}")
                    if cap is not None:
                        try:
                            cap.release()
                        except:
                            pass
                        cap = None
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ 设备 {device_id} 连接 {stream_type} 流失败，已达到最大重试次数 {max_retries}")
                        logger.info("等待30秒后重新尝试...")
                        time.sleep(30)
                        retry_count = 0
                    else:
                        logger.warning(f"设备 {device_id} 无法打开 {stream_type} 流，等待重试... ({retry_count}/{max_retries})")
                        time.sleep(2)
                    continue
                
                if not cap.isOpened():
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ 设备 {device_id} 连接 {stream_type} 流失败，已达到最大重试次数 {max_retries}")
                        logger.info("等待30秒后重新尝试...")
                        time.sleep(30)
                        retry_count = 0
                    else:
                        logger.warning(f"设备 {device_id} 无法打开 {stream_type} 流，等待重试... ({retry_count}/{max_retries})")
                        time.sleep(2)
                    if cap is not None:
                        try:
                            cap.release()
                        except:
                            pass
                        cap = None
                    continue
                
                retry_count = 0
                device_caps[device_id] = cap
                logger.info(f"✅ 设备 {device_id} {stream_type} 流连接成功")
            
            # 从源流读取帧
            ret, frame = cap.read()
            
            if not ret or frame is None:
                logger.warning(f"设备 {device_id} 读取源流帧失败，重新连接...")
                # 清理当前连接
                if cap is not None:
                    try:
                        cap.release()
                    except:
                        pass
                    cap = None
                    device_caps.pop(device_id, None)
                
                # 等待后重试连接
                time.sleep(1)
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"❌ 设备 {device_id} 读取帧失败次数过多，等待30秒后重新尝试...")
                    time.sleep(30)
                    retry_count = 0
                continue
            
            # 更新帧计数
            frame_counts[device_id] += 1
            frame_count = frame_counts[device_id]
            
            # 立即缩放到目标分辨率
            original_height, original_width = frame.shape[:2]
            if (original_width, original_height) != TARGET_RESOLUTION:
                frame = cv2.resize(frame, TARGET_RESOLUTION, interpolation=cv2.INTER_LINEAR)
            
            # 优化：将帧放入原始帧队列（不复制，直接使用）
            # 只在队列满时丢弃最旧的帧
            try:
                raw_frame_queues[device_id].put_nowait({
                    'frame': frame,  # 不复制，减少开销
                    'frame_number': frame_count,
                    'timestamp': time.time(),
                    'device_id': device_id
                })
            except queue.Full:
                # 队列满时，丢弃最旧的帧（保持队列大小）
                try:
                    raw_frame_queues[device_id].get_nowait()
                    raw_frame_queues[device_id].put_nowait({
                        'frame': frame,
                        'frame_number': frame_count,
                        'timestamp': time.time(),
                        'device_id': device_id
                    })
                except queue.Empty:
                    pass
            
            # 流畅度优化：基于时间戳的帧率控制（使用更精确的时间）
            current_time = time.perf_counter()
            elapsed = current_time - last_frame_time
            if elapsed < frame_interval:
                sleep_time = frame_interval - elapsed
                if sleep_time > 0.001:  # 只sleep超过1ms的情况
                    time.sleep(sleep_time)
            last_frame_time = time.perf_counter()
            
        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 缓流器异常: {str(e)}", exc_info=True)
            time.sleep(2)
    
    # 清理资源
    if cap is not None:
        try:
            cap.release()
        except:
            pass
        device_caps.pop(device_id, None)
    
    # 清理队列（如果还有未处理的帧）
    if device_id in raw_frame_queues:
        try:
            while True:
                raw_frame_queues[device_id].get_nowait()
        except queue.Empty:
            pass
    if device_id in processed_frame_queues:
        try:
            while True:
                processed_frame_queues[device_id].get_nowait()
        except queue.Empty:
            pass
    
    logger.info(f"💾 设备 {device_id} 缓流器线程停止")


def extractor_worker():
    """抽帧器工作线程：从原始帧队列获取帧，抽帧后放入已处理帧队列"""
    logger.info("📹 抽帧器线程启动（多摄像头并行）")
    
    while not stop_event.is_set():
        try:
            has_work = False
            # 遍历所有设备的原始帧队列
            for device_id, raw_queue in raw_frame_queues.items():
                try:
                    # 使用阻塞获取，超时0.1秒，减少轮询开销
                    frame_data = raw_queue.get(timeout=0.1)
                    frame = frame_data['frame']
                    frame_number = frame_data['frame_number']
                    timestamp = frame_data['timestamp']
                    device_id_from_data = frame_data.get('device_id', device_id)
                    
                    has_work = True
                    
                    # 抽帧：根据抽帧间隔决定是否处理
                    if frame_number % EXTRACT_INTERVAL == 0:
                        # 需要推送的帧，放入已处理帧队列
                        try:
                            processed_frame_queues[device_id].put_nowait({
                                'frame': frame,  # 不复制，直接使用
                                'frame_number': frame_number,
                                'timestamp': timestamp,
                                'device_id': device_id_from_data
                            })
                            if frame_number % (EXTRACT_INTERVAL * 10) == 0:
                                logger.debug(f"✅ 抽帧器 [{device_id_from_data}]: 帧号 {frame_number} 已处理")
                        except queue.Full:
                            # 已处理队列满时，丢弃最旧的帧
                            try:
                                processed_frame_queues[device_id].get_nowait()
                                processed_frame_queues[device_id].put_nowait({
                                    'frame': frame,
                                    'frame_number': frame_number,
                                    'timestamp': timestamp,
                                    'device_id': device_id_from_data
                                })
                            except queue.Empty:
                                pass
                    # 不需要推送的帧直接丢弃（不放入已处理队列）
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"❌ 设备 {device_id} 抽帧器异常: {str(e)}", exc_info=True)
            
            # 如果本轮没有工作，短暂休眠
            if not has_work:
                time.sleep(0.01)  # 10ms
            
        except Exception as e:
            logger.error(f"❌ 抽帧器异常: {str(e)}", exc_info=True)
            time.sleep(0.1)
    
    logger.info("📹 抽帧器线程停止")


def pusher_worker():
    """推流器工作线程：从已处理帧队列获取帧，推送到各自的RTMP"""
    logger.info("📺 推流器线程启动（多摄像头并行）")
    
    # 为每个设备初始化推送进程
    device_pusher_processes = {}  # {device_id: subprocess.Popen}
    # 为每个设备记录最后推送时间，用于帧率控制
    device_last_push_time = {}  # {device_id: float}
    
    # 计算每帧的时间间隔（基于实际推流帧率）
    push_frame_interval = 1.0 / TARGET_FPS if TARGET_FPS > 0 else 0.1
    # 队列积压阈值：如果队列中积压超过1秒的帧，丢弃旧帧保持实时性
    # 这样可以避免画面延迟过大，同时保持流畅
    max_queue_seconds = 1.0
    max_queue_frames = max(2, int(TARGET_FPS * max_queue_seconds))  # 至少保留2帧
    
    while not stop_event.is_set():
        try:
            has_work = False
            # 遍历所有设备的已处理帧队列
            for device_id, processed_queue in processed_frame_queues.items():
                try:
                    # 检查队列积压情况，如果积压太多，丢弃旧帧保持实时性
                    queue_size = processed_queue.qsize()
                    if queue_size > max_queue_frames:
                        # 队列积压过多，丢弃旧帧，只保留最新的几帧
                        # 这样可以避免画面延迟过大，同时保持流畅播放
                        dropped_count = 0
                        target_size = max(1, max_queue_frames // 2)  # 保留一半，至少1帧
                        while processed_queue.qsize() > target_size:
                            try:
                                processed_queue.get_nowait()
                                dropped_count += 1
                            except queue.Empty:
                                break
                        if dropped_count > 0:
                            logger.debug(f"设备 {device_id} 队列积压，已丢弃 {dropped_count} 帧旧帧以保持实时性 (队列大小: {queue_size} -> {processed_queue.qsize()})")
                    
                    # 使用非阻塞获取，避免一次性处理太多帧
                    try:
                        frame_data = processed_queue.get_nowait()
                    except queue.Empty:
                        continue
                    frame = frame_data['frame']
                    frame_number = frame_data['frame_number']
                    device_id_from_data = frame_data.get('device_id', device_id)
                    
                    has_work = True
                    
                    # 获取设备流信息
                    device_stream_info = task_config.device_streams.get(device_id_from_data) if task_config else None
                    if not device_stream_info:
                        continue
                    
                    rtmp_url = device_stream_info.get('rtmp_url')
                    device_name = device_stream_info.get('device_name', device_id_from_data)
                    
                    if not rtmp_url:
                        continue
                    
                    # 获取或创建推送进程
                    pusher_process = device_pusher_processes.get(device_id_from_data)
                    
                    # 如果进程不存在或已退出，启动新进程
                    if pusher_process is None or pusher_process.poll() is not None:
                        if pusher_process and pusher_process.poll() is not None:
                            # 获取错误信息
                            stderr_lines = []
                            if device_id_from_data in device_pusher_stderr_buffers:
                                with device_pusher_stderr_locks.get(device_id_from_data, threading.Lock()):
                                    stderr_lines = device_pusher_stderr_buffers[device_id_from_data].copy()
                                    device_pusher_stderr_buffers[device_id_from_data].clear()
                            
                            exit_code = pusher_process.returncode
                            logger.warning(f"⚠️  设备 {device_id_from_data} 推送进程异常退出 (退出码: {exit_code})")
                            
                            # 提取关键错误信息
                            if stderr_lines:
                                key_errors = []
                                for line in stderr_lines:
                                    line_lower = line.lower()
                                    if any(skip in line_lower for skip in ['version', 'copyright', 'built with', 'configuration:', 'libav']):
                                        continue
                                    if any(keyword in line_lower for keyword in ['error', 'failed', 'cannot', 'unable', 'invalid', 'connection refused', 'connection reset', 'timeout']):
                                        key_errors.append(line)
                                
                                if key_errors:
                                    logger.warning(f"   关键错误: {key_errors[-5:]}")
                        
                        # 停止旧进程
                        if pusher_process and pusher_process.poll() is None:
                            try:
                                pusher_process.stdin.close()
                                pusher_process.terminate()
                                pusher_process.wait(timeout=2)
                            except:
                                if pusher_process.poll() is None:
                                    pusher_process.kill()
                        
                        # 检查RTMP服务器连接
                        if not check_rtmp_server_connection(rtmp_url):
                            logger.warning(f"⚠️  设备 {device_id_from_data} RTMP服务器不可用: {rtmp_url}")
                            time.sleep(2)
                            continue
                        
                        # 构建FFmpeg命令（优化低延迟参数，使用实际推流帧率）
                        height, width = TARGET_HEIGHT, TARGET_WIDTH
                        ffmpeg_cmd = [
                            "ffmpeg",
                            "-y",
                            "-fflags", "nobuffer",
                            "-flags", "low_delay",  # 低延迟标志
                            "-f", "rawvideo",
                            "-vcodec", "rawvideo",
                            "-pix_fmt", "bgr24",
                            "-s", f"{width}x{height}",
                            "-r", str(TARGET_FPS),  # 使用实际推流帧率，而不是源流帧率
                            "-i", "-",
                            "-c:v", "libx264",
                            "-b:v", FFMPEG_VIDEO_BITRATE,
                            "-pix_fmt", "yuv420p",
                            "-preset", FFMPEG_PRESET,
                            "-tune", "zerolatency",  # 零延迟调优
                            "-g", str(FFMPEG_GOP_SIZE),
                            "-keyint_min", str(TARGET_FPS),  # 使用实际推流帧率
                            "-sc_threshold", "0",  # 禁用场景切换检测，降低延迟
                            "-f", "flv",
                        ]
                        
                        # 如果配置了线程数限制，添加线程参数
                        if FFMPEG_THREADS is not None and str(FFMPEG_THREADS).strip():
                            try:
                                threads_value = int(FFMPEG_THREADS)
                                if threads_value > 0:
                                    ffmpeg_cmd.extend(["-threads", str(threads_value)])
                            except (ValueError, TypeError):
                                pass
                        
                        # 添加输出地址
                        ffmpeg_cmd.append(rtmp_url)
                        
                        # 初始化stderr缓冲区
                        if device_id_from_data not in device_pusher_stderr_buffers:
                            device_pusher_stderr_buffers[device_id_from_data] = []
                            device_pusher_stderr_locks[device_id_from_data] = threading.Lock()
                        
                        try:
                            pusher_process = subprocess.Popen(
                                ffmpeg_cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                bufsize=0,
                                shell=False
                            )
                            
                            # 启动stderr读取线程
                            stderr_buffer = device_pusher_stderr_buffers[device_id_from_data]
                            stderr_lock = device_pusher_stderr_locks[device_id_from_data]
                            stderr_thread = threading.Thread(
                                target=read_ffmpeg_stderr,
                                args=(device_id_from_data, pusher_process.stderr, stderr_buffer, stderr_lock),
                                daemon=True
                            )
                            stderr_thread.start()
                            device_pusher_stderr_threads[device_id_from_data] = stderr_thread
                            
                            # 等待一小段时间，检查进程是否立即退出
                            time.sleep(0.5)
                            
                            if pusher_process.poll() is not None:
                                # 获取错误信息
                                time.sleep(0.3)
                                error_lines = []
                                with device_pusher_stderr_locks[device_id_from_data]:
                                    error_lines = device_pusher_stderr_buffers[device_id_from_data].copy()
                                    device_pusher_stderr_buffers[device_id_from_data].clear()
                                
                                exit_code = pusher_process.returncode
                                logger.error(f"❌ 设备 {device_id_from_data} 推送进程启动失败 (退出码: {exit_code})")
                                
                                if error_lines:
                                    key_errors = []
                                    for line in error_lines:
                                        line_lower = line.lower()
                                        if any(skip in line_lower for skip in ['version', 'copyright', 'built with', 'configuration:', 'libav']):
                                            continue
                                        if any(keyword in line_lower for keyword in ['error', 'failed', 'cannot', 'unable', 'invalid', 'connection refused', 'connection reset', 'timeout']):
                                            key_errors.append(line)
                                    
                                    if key_errors:
                                        logger.error(f"   关键错误: {key_errors[-5:]}")
                                
                                pusher_process = None
                                time.sleep(2)
                                continue
                            
                            device_pusher_processes[device_id_from_data] = pusher_process
                            device_pushers[device_id_from_data] = pusher_process
                            logger.info(f"✅ 设备 {device_id_from_data} 推送进程已启动 (PID: {pusher_process.pid})")
                            logger.info(f"   📺 推流地址: {rtmp_url}")
                            logger.info(f"   📐 推流参数: {TARGET_WIDTH}x{TARGET_HEIGHT} @ {TARGET_FPS} fps")
                            
                        except Exception as e:
                            logger.error(f"❌ 设备 {device_id_from_data} 启动推送进程失败: {str(e)}", exc_info=True)
                            pusher_process = None
                            time.sleep(2)
                            continue
                    
                    # 推送到RTMP流（添加基于时间戳的帧率控制，使画面更自然）
                    if pusher_process and pusher_process.poll() is None:
                        try:
                            # 基于时间戳的帧率控制，确保推送速度自然
                            current_time = time.perf_counter()
                            last_push_time = device_last_push_time.get(device_id_from_data, 0)
                            
                            # 计算距离上次推送的时间
                            elapsed = current_time - last_push_time
                            
                            # 如果距离上次推送时间太短，等待以保持自然帧率
                            # 这样可以避免一股脑推送所有积压的帧
                            if elapsed < push_frame_interval:
                                sleep_time = push_frame_interval - elapsed
                                if sleep_time > 0.001:  # 只sleep超过1ms的情况
                                    time.sleep(sleep_time)
                                    # 重新获取当前时间
                                    current_time = time.perf_counter()
                            
                            # 推送帧
                            pusher_process.stdin.write(frame.tobytes())
                            pusher_process.stdin.flush()
                            
                            # 更新最后推送时间
                            device_last_push_time[device_id_from_data] = current_time
                            
                            # 每次只处理一帧，然后继续循环，避免一次性推送太多
                            # 这样即使队列中有积压，也会按自然速度推送
                            
                        except (BrokenPipeError, OSError, IOError) as e:
                            # 管道错误，进程可能已退出
                            logger.error(f"❌ 设备 {device_id_from_data} 推送帧失败: {str(e)}")
                            # 检查进程是否真的退出了
                            if pusher_process.poll() is not None:
                                # 获取错误信息
                                stderr_lines = []
                                if device_id_from_data in device_pusher_stderr_buffers:
                                    with device_pusher_stderr_locks.get(device_id_from_data, threading.Lock()):
                                        stderr_lines = device_pusher_stderr_buffers[device_id_from_data].copy()
                                        device_pusher_stderr_buffers[device_id_from_data].clear()
                                
                                exit_code = pusher_process.returncode
                                logger.warning(f"⚠️  设备 {device_id_from_data} 推送进程异常退出 (退出码: {exit_code})")
                                
                                # 提取关键错误信息
                                if stderr_lines:
                                    key_errors = []
                                    for line in stderr_lines:
                                        line_lower = line.lower()
                                        if any(skip in line_lower for skip in ['version', 'copyright', 'built with', 'configuration:', 'libav']):
                                            continue
                                        if any(keyword in line_lower for keyword in ['error', 'failed', 'cannot', 'unable', 'invalid', 'connection refused', 'connection reset', 'timeout']):
                                            key_errors.append(line)
                                    
                                    if key_errors:
                                        logger.warning(f"   关键错误: {key_errors[-5:]}")
                                
                                pusher_process = None
                                device_pusher_processes.pop(device_id_from_data, None)
                                device_pushers.pop(device_id_from_data, None)
                        except Exception as e:
                            logger.error(f"❌ 设备 {device_id_from_data} 推送帧失败: {str(e)}")
                            # 检查进程状态
                            if pusher_process and pusher_process.poll() is not None:
                                pusher_process = None
                                device_pusher_processes.pop(device_id_from_data, None)
                                device_pushers.pop(device_id_from_data, None)
                
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"❌ 设备 {device_id} 推流器异常: {str(e)}", exc_info=True)
            
            # 如果本轮没有工作，短暂休眠
            # 注意：即使有工作，我们也只处理一帧就继续循环，确保推送速度自然
            if not has_work:
                time.sleep(0.01)  # 10ms
            else:
                # 即使有工作，也稍微休眠一下，避免CPU占用过高
                # 这样可以给其他设备处理的机会，同时保持推送速度自然
                time.sleep(0.001)  # 1ms
            
        except Exception as e:
            logger.error(f"❌ 推流器异常: {str(e)}", exc_info=True)
            time.sleep(0.1)
    
    # 清理所有推送进程
    for device_id, pusher_process in device_pusher_processes.items():
        if pusher_process:
            try:
                # 先关闭stdin
                if pusher_process.stdin:
                    try:
                        pusher_process.stdin.close()
                    except:
                        pass
                
                # 检查进程是否还在运行
                if pusher_process.poll() is None:
                    # 尝试优雅终止
                    try:
                        pusher_process.terminate()
                        pusher_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # 如果2秒内未结束，强制终止
                        if pusher_process.poll() is None:
                            pusher_process.kill()
                            pusher_process.wait()
                    except:
                        # 如果terminate失败，直接kill
                        if pusher_process.poll() is None:
                            try:
                                pusher_process.kill()
                                pusher_process.wait()
                            except:
                                pass
            except Exception as e:
                logger.warning(f"清理设备 {device_id} 推送进程时出错: {str(e)}")
    
    # 清理全局推送进程字典
    for device_id in list(device_pushers.keys()):
        device_pushers.pop(device_id, None)
    
    logger.info("📺 推流器线程停止")


def update_task_status(status: str = None, exception_reason: str = None):
    """更新任务状态到数据库
    
    Args:
        status: 状态值 [0:正常, 1:异常]
        exception_reason: 异常原因
    """
    try:
        with get_flask_app().app_context():
            task = StreamForwardTask.query.get(TASK_ID)
            if task:
                if status is not None:
                    task.status = status
                if exception_reason is not None:
                    task.exception_reason = exception_reason[:500]  # 限制长度
                db.session.commit()
                logger.debug(f"任务状态已更新: status={status}, exception_reason={exception_reason}")
    except Exception as e:
        logger.warning(f"更新任务状态失败: {str(e)}")


def send_heartbeat():
    """发送心跳到VIDEO服务"""
    try:
        import socket
        import os as os_module
        
        # 获取服务器IP
        server_ip = os_module.getenv('POD_IP', '')
        if not server_ip:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                server_ip = s.getsockname()[0]
                s.close()
            except:
                server_ip = 'localhost'
        
        # 获取进程ID
        process_id = os_module.getpid()
        
        # 构建日志路径
        log_path_for_heartbeat = SERVICE_LOG_DIR if 'SERVICE_LOG_DIR' in globals() else os.path.join(video_root, 'logs', f'stream_forward_task_{TASK_ID}')
        
        # 构建心跳URL（使用localhost，不依赖GATEWAY_URL）
        heartbeat_url = f"http://localhost:{VIDEO_SERVICE_PORT}/video/stream-forward/heartbeat"
        
        # 发送心跳
        response = requests.post(
            heartbeat_url,
            json={
                'task_id': TASK_ID,
                'server_ip': server_ip,
                'port': int(VIDEO_SERVICE_PORT),
                'process_id': process_id,
                'log_path': log_path_for_heartbeat
            },
            timeout=5
        )
        response.raise_for_status()
        logger.debug(f"心跳上报成功: task_id={TASK_ID}")
        # 心跳成功，更新状态为正常
        update_task_status(status=0, exception_reason=None)
    except Exception as e:
        logger.warning(f"心跳上报失败: {str(e)}")


def heartbeat_worker():
    """心跳上报工作线程"""
    logger.info("💓 心跳上报线程启动")
    while not stop_event.is_set():
        try:
            send_heartbeat()
            # 每10秒发送一次心跳
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(1)
        except Exception as e:
            logger.error(f"心跳上报线程异常: {str(e)}", exc_info=True)
            time.sleep(10)
    logger.info("💓 心跳上报线程停止")


def signal_handler(signum, frame):
    """信号处理函数"""
    logger.info(f"收到信号 {signum}，准备退出...")
    stop_event.set()


def main():
    """主函数"""
    global task_config, device_streams, heartbeat_thread
    
    logger.info("=" * 60)
    logger.info("推流转发服务启动")
    logger.info(f"任务ID: {TASK_ID}")
    logger.info(f"数据库URL: {DATABASE_URL}")
    logger.info(f"VIDEO服务端口: {VIDEO_SERVICE_PORT}")
    logger.info(f"心跳上报URL: http://localhost:{VIDEO_SERVICE_PORT}/video/stream-forward/heartbeat")
    logger.info(f"源流帧率: {SOURCE_FPS} fps")
    logger.info(f"抽帧间隔: 每 {EXTRACT_INTERVAL} 帧抽1帧")
    logger.info(f"实际推流帧率: {TARGET_FPS} fps (源流 {SOURCE_FPS} fps ÷ 抽帧间隔 {EXTRACT_INTERVAL})")
    logger.info(f"目标分辨率: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    logger.info("=" * 60)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 加载任务配置
    if not load_task_config():
        logger.error("❌ 加载任务配置失败，服务退出")
        update_task_status(status=1, exception_reason="加载任务配置失败")
        return
    
    # 服务启动成功，更新状态为正常
    update_task_status(status=0, exception_reason=None)
    
    device_streams = task_config.device_streams
    
    # 为每个设备创建队列和锁（优化后的双队列架构）
    # 已处理帧队列大小：根据实际推流帧率动态设置，缓冲约2-3秒的帧
    # 这样可以避免队列过大导致积压，同时保持一定的缓冲
    processed_queue_size = max(5, min(BUFFER_QUEUE_SIZE, int(TARGET_FPS * 3)))  # 最多3秒的缓冲
    
    for device_id in device_streams.keys():
        raw_frame_queues[device_id] = queue.Queue(maxsize=BUFFER_QUEUE_SIZE)
        processed_frame_queues[device_id] = queue.Queue(maxsize=processed_queue_size)
        device_locks[device_id] = threading.Lock()
        frame_counts[device_id] = 0
        logger.info(f"✅ 初始化设备 {device_id} 的队列和锁（双队列架构，已处理队列大小: {processed_queue_size}）")
    
    # 为每个摄像头启动独立的缓流器线程
    buffer_threads = []
    for device_id in device_streams.keys():
        thread = threading.Thread(
            target=buffer_worker,
            args=(device_id,),
            daemon=True
        )
        thread.start()
        buffer_threads.append(thread)
        logger.info(f"✅ 启动设备 {device_id} 的缓流器线程")
    
    # 启动共享的抽帧器线程（处理所有摄像头）
    extractor_thread = threading.Thread(target=extractor_worker, daemon=True)
    extractor_thread.start()
    logger.info("✅ 启动抽帧器线程（多摄像头并行）")
    
    # 启动共享的推流器线程（处理所有摄像头）
    pusher_thread = threading.Thread(target=pusher_worker, daemon=True)
    pusher_thread.start()
    logger.info("✅ 启动推流器线程（多摄像头并行）")
    
    # 启动心跳上报线程
    logger.info("💓 启动心跳上报线程...")
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    
    logger.info("=" * 60)
    logger.info("推流转发服务运行中...")
    logger.info(f"活跃设备数: {len(device_streams)}")
    logger.info("=" * 60)
    
    try:
        # 主循环
        while not stop_event.is_set():
            time.sleep(1)
            
            # 检查所有工作线程是否还在运行
            alive_buffer_threads = [t for t in buffer_threads if t.is_alive()]
            if len(alive_buffer_threads) == 0:
                logger.error("❌ 所有缓流器线程已退出，服务异常")
                update_task_status(status=1, exception_reason="所有缓流器线程已退出")
                break
            
            if not extractor_thread.is_alive():
                logger.error("❌ 抽帧器线程已退出，服务异常")
                update_task_status(status=1, exception_reason="抽帧器线程已退出")
                break
            
            if not pusher_thread.is_alive():
                logger.error("❌ 推流器线程已退出，服务异常")
                update_task_status(status=1, exception_reason="推流器线程已退出")
                break
            
            # 检查是否有活跃的推流进程
            active_pushers = sum(1 for p in device_pushers.values() if p and p.poll() is None)
            if active_pushers == 0 and len(device_pushers) > 0:
                # 有设备但没有活跃的推流进程，可能是异常情况
                logger.warning("⚠️  没有活跃的推流进程")
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，准备退出...")
    except Exception as e:
        logger.error(f"❌ 主循环异常: {str(e)}", exc_info=True)
        update_task_status(status=1, exception_reason=f"主循环异常: {str(e)[:450]}")
    finally:
        # 停止所有线程
        logger.info("正在停止推流转发服务...")
        stop_event.set()
        
        # 等待所有工作线程结束
        for thread in buffer_threads:
            thread.join(timeout=10)
        
        extractor_thread.join(timeout=10)
        pusher_thread.join(timeout=10)
        
        # 停止所有FFmpeg进程
        for device_id, pusher in list(device_pushers.items()):
            if pusher:
                try:
                    # 先关闭stdin
                    if pusher.stdin:
                        try:
                            pusher.stdin.close()
                        except:
                            pass
                    
                    # 检查进程是否还在运行
                    if pusher.poll() is None:
                        # 尝试优雅终止
                        try:
                            pusher.terminate()
                            pusher.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            # 如果5秒内未结束，强制终止
                            if pusher.poll() is None:
                                try:
                                    pusher.kill()
                                    pusher.wait()
                                except:
                                    pass
                        except:
                            # 如果terminate失败，直接kill
                            if pusher.poll() is None:
                                try:
                                    pusher.kill()
                                    pusher.wait()
                                except:
                                    pass
                except Exception as e:
                    logger.warning(f"停止设备 {device_id} FFmpeg进程时出错: {str(e)}")
        
        # 停止所有VideoCapture
        for device_id, cap in list(device_caps.items()):
            if cap is not None:
                try:
                    cap.release()
                except:
                    pass
            device_caps.pop(device_id, None)
        
        # 清理所有队列
        for device_id in list(raw_frame_queues.keys()):
            try:
                queue_obj = raw_frame_queues[device_id]
                while True:
                    queue_obj.get_nowait()
            except queue.Empty:
                pass
            raw_frame_queues.pop(device_id, None)
        
        for device_id in list(processed_frame_queues.keys()):
            try:
                queue_obj = processed_frame_queues[device_id]
                while True:
                    queue_obj.get_nowait()
            except queue.Empty:
                pass
            processed_frame_queues.pop(device_id, None)
        
        # 更新任务状态为已停止
        try:
            update_task_status(status=0, exception_reason=None)
        except Exception as e:
            logger.warning(f"更新任务停止状态失败: {str(e)}")
        
        logger.info("推流转发服务已停止")


if __name__ == '__main__':
    main()
