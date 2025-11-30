"""
抽帧器服务模板工程
用于从视频流中按配置的间隔抽帧

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import time
import threading
import logging
import socket
import atexit
import signal
import uuid
import argparse
import cv2
import subprocess
import numpy as np
import io
import requests
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# 添加VIDEO模块路径以便导入模型
video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, video_root)

# 导入VIDEO模块的模型
from models import db, AlgorithmTask, Device, FrameExtractor

# ============================================
# 全局异常处理器
# ============================================
def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    import traceback
    error_msg = f"❌ [FRAME_EXTRACTOR] 未捕获的异常: {exc_type.__name__}: {exc_value}"
    print(error_msg, file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    try:
        logger = logging.getLogger(__name__)
        logger.error(f"未捕获的异常: {exc_type.__name__}: {exc_value}")
        logger.error(traceback.format_exception(exc_type, exc_value, exc_traceback))
    except:
        pass

sys.excepthook = handle_exception

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

# ============================================
# 环境变量和系统配置初始化
# ============================================
env_file = '.env'
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"✅ 已加载配置文件: {env_file}", file=sys.stderr)
else:
    print(f"⚠️  配置文件 {env_file} 不存在，使用系统环境变量", file=sys.stderr)

app = Flask(__name__)
CORS(app)

# 配置日志
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('flask').setLevel(logging.WARNING)

# 获取服务ID
service_id = os.getenv('SERVICE_ID', 'unknown')
task_id = os.getenv('TASK_ID')  # 算法任务ID
extractor_id = os.getenv('EXTRACTOR_ID')  # 抽帧器ID

# 日志目录
log_path = os.getenv('LOG_PATH')
if log_path:
    service_log_dir = log_path
else:
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logs_base_dir = os.path.join(video_root, 'logs')
    service_log_dir = os.path.join(logs_base_dir, f'frame_extractor_{service_id}')
os.makedirs(service_log_dir, exist_ok=True)

# 创建日志格式
log_format = '[FRAME_EXTRACTOR] %(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

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
logger.info("=" * 60)
logger.info("🚀 抽帧器服务启动")
logger.info(f"任务ID: {task_id}")
logger.info(f"抽帧器ID: {extractor_id}")
logger.info(f"日志目录: {service_log_dir}")
logger.info("=" * 60)

# 全局变量
db_session = None
task = None
extractor = None
devices = []
running = False
stop_event = threading.Event()
video_service_api = None
server_ip = None
port = None
process_id = os.getpid()

# ============================================
# 数据库连接
# ============================================
def init_database():
    """初始化数据库连接"""
    global db_session
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL环境变量未设置")
    
    # 创建数据库引擎
    engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)
    session_factory = sessionmaker(bind=engine)
    db_session = scoped_session(session_factory)
    
    logger.info("数据库连接初始化成功")


# ============================================
# 心跳上报
# ============================================
def get_video_service_api():
    """获取VIDEO服务API地址"""
    # 优先从环境变量获取
    api_url = os.getenv('VIDEO_SERVICE_API')
    if api_url:
        return api_url.rstrip('/')
    
    # 从数据库配置获取（如果有的话）
    # 这里可以添加从数据库读取配置的逻辑
    
    # 默认使用本地地址
    default_port = os.getenv('VIDEO_SERVICE_PORT', '6000')
    return f'http://localhost:{default_port}'


def send_heartbeat():
    """向VIDEO模块发送心跳"""
    global video_service_api, server_ip, port, process_id, extractor_id, task_id, service_log_dir
    
    # 首次等待，确保服务已启动
    time.sleep(2)
    
    while not stop_event.is_set():
        try:
            # 如果VIDEO服务地址未获取到，尝试重新获取
            if not video_service_api:
                video_service_api = get_video_service_api()
                if not video_service_api:
                    logger.warning("VIDEO服务地址未获取到，等待10秒后重试...")
                    time.sleep(10)
                    continue
            
            # 获取服务器IP
            if not server_ip:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(('8.8.8.8', 80))
                    server_ip = s.getsockname()[0]
                    s.close()
                except:
                    server_ip = '127.0.0.1'
            
            # 获取端口
            if not port:
                port = int(os.getenv('PORT', 8001))
            
            # 强制要求 extractor_id
            if not extractor_id:
                logger.warning("EXTRACTOR_ID 环境变量未设置，无法发送心跳")
                time.sleep(60)
                continue
            
            try:
                extractor_id_int = int(extractor_id)
            except (ValueError, TypeError):
                logger.error(f"EXTRACTOR_ID 无效: {extractor_id}，必须是数字")
                time.sleep(60)
                continue
            
            # 构建心跳数据
            heartbeat_data = {
                'extractor_id': extractor_id_int,
                'server_ip': server_ip,
                'port': port,
                'process_id': process_id,
                'log_path': service_log_dir,
                'task_id': int(task_id) if task_id else None
            }
            
            # 发送心跳请求
            heartbeat_url = f'{video_service_api}/api/v1/algorithm_task/heartbeat/extractor'
            response = requests.post(
                heartbeat_url,
                json=heartbeat_data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.debug(f"✅ 心跳上报成功: extractor_id={extractor_id_int}@{server_ip}:{port}")
                else:
                    logger.warning(f"心跳上报返回错误: {result.get('msg', '未知错误')}")
            else:
                logger.warning(f"心跳上报失败: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.debug(f"心跳上报请求异常: {str(e)}")
        except Exception as e:
            logger.error(f"心跳上报异常: {str(e)}", exc_info=True)
        
        # 每5秒发送一次心跳
        time.sleep(5)

# ============================================
# 抽帧逻辑
# ============================================
def extract_frame_from_stream(device, extractor_config):
    """从视频流中抽帧
    
    Args:
        device: Device对象
        extractor_config: FrameExtractor配置对象
    
    Returns:
        bool: 是否成功
    """
    try:
        if not device.source:
            logger.warning(f"设备 {device.id} 没有源地址，跳过抽帧")
            return False
        
        source = device.source.strip()
        source_lower = source.lower()
        
        # 判断流类型并抽帧
        if source_lower.startswith('rtmp://'):
            # RTMP流使用FFmpeg
            try:
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', source,
                    '-vframes', '1',
                    '-f', 'image2',
                    '-vcodec', 'mjpeg',
                    '-q:v', '2',
                    'pipe:1'
                ]
                
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(timeout=10)
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
                    logger.error(f"设备 {device.id} RTMP流抽帧失败: {error_msg}")
                    return False
                
                if not stdout:
                    logger.error(f"设备 {device.id} RTMP流抽帧失败: 未获取到图像数据")
                    return False
                
                image_array = np.frombuffer(stdout, np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                if frame is None:
                    logger.error(f"设备 {device.id} RTMP流抽帧失败: 图像解码失败")
                    return False
                
            except subprocess.TimeoutExpired:
                logger.error(f"设备 {device.id} RTMP流抽帧超时")
                return False
            except Exception as e:
                logger.error(f"设备 {device.id} RTMP流抽帧异常: {str(e)}", exc_info=True)
                return False
        else:
            # RTSP流使用OpenCV
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                logger.error(f"设备 {device.id} 无法打开RTSP流: {source}")
                return False
            
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                logger.error(f"设备 {device.id} RTSP流读取失败，源地址: {source}")
                return False
        
        # 这里可以添加保存帧的逻辑（保存到MinIO或本地）
        # 暂时只记录日志
        logger.info(f"设备 {device.id} 抽帧成功，帧大小: {frame.shape}")
        return True
        
    except Exception as e:
        logger.error(f"设备 {device.id} 抽帧失败: {str(e)}", exc_info=True)
        return False

# ============================================
# 抽帧工作线程
# ============================================
def frame_extraction_worker():
    """抽帧工作线程"""
    global task, extractor, devices
    
    logger.info("抽帧工作线程启动")
    
    frame_count = 0
    interval = extractor.interval if extractor else 1
    extractor_type = extractor.extractor_type if extractor else 'interval'
    
    while not stop_event.is_set():
        try:
            # 遍历所有设备进行抽帧
            for device in devices:
                if stop_event.is_set():
                    break
                
                # 根据抽帧器类型决定抽帧间隔
                if extractor_type == 'interval':
                    # 按帧间隔：每N帧抽一次
                    frame_count += 1
                    if frame_count % interval == 0:
                        extract_frame_from_stream(device, extractor)
                else:
                    # 按时间间隔：每N秒抽一次
                    extract_frame_from_stream(device, extractor)
                    time.sleep(interval)
            
            # 如果按帧间隔，需要短暂休眠避免CPU占用过高
            if extractor_type == 'interval':
                time.sleep(0.1)  # 100ms
                
        except Exception as e:
            logger.error(f"抽帧工作线程异常: {str(e)}", exc_info=True)
            time.sleep(1)
    
    logger.info("抽帧工作线程停止")

# ============================================
# Flask路由
# ============================================
@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'task_id': task_id,
        'extractor_id': extractor_id,
        'running': running
    })

@app.route('/stop', methods=['POST'])
def stop_service():
    """停止服务"""
    try:
        global running
        logger.info("收到停止服务请求")
        stop_event.set()
        running = False
        
        return jsonify({
            'code': 0,
            'msg': '服务正在停止'
        })
    except Exception as e:
        logger.error(f"停止服务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'停止服务失败: {str(e)}'
        }), 500

# ============================================
# 主函数
# ============================================
def main():
    """主函数"""
    global task, extractor, devices, running
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='抽帧器服务')
    parser.add_argument('--task-id', type=int, help='算法任务ID')
    parser.add_argument('--extractor-id', type=int, help='抽帧器ID')
    args = parser.parse_args()
    
    # 优先使用命令行参数，其次使用环境变量
    task_id_value = args.task_id or task_id
    extractor_id_value = args.extractor_id or extractor_id
    
    if not task_id_value:
        error_msg = "❌ TASK_ID环境变量或--task-id参数未设置"
        print(error_msg, file=sys.stderr)
        logger.error(error_msg)
        sys.exit(1)
    
    # 初始化数据库
    try:
        init_database()
    except Exception as e:
        error_msg = f"❌ 数据库初始化失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        logger.error(error_msg)
        sys.exit(1)
    
    # 从数据库加载任务和配置
    try:
        task = db_session.query(AlgorithmTask).filter_by(id=task_id_value).first()
        if not task:
            error_msg = f"❌ 算法任务不存在: task_id={task_id_value}"
            print(error_msg, file=sys.stderr)
            logger.error(error_msg)
            sys.exit(1)
        
        # 获取抽帧器配置
        if task.extractor_id:
            extractor = db_session.query(FrameExtractor).filter_by(id=task.extractor_id).first()
            if not extractor:
                logger.warning(f"抽帧器不存在: extractor_id={task.extractor_id}")
        elif extractor_id_value:
            extractor = db_session.query(FrameExtractor).filter_by(id=extractor_id_value).first()
            if not extractor:
                logger.warning(f"抽帧器不存在: extractor_id={extractor_id_value}")
        
        # 获取关联的设备列表
        devices = task.devices if task.devices else []
        
        logger.info(f"加载任务成功: task_id={task_id_value}, task_name={task.task_name}")
        logger.info(f"抽帧器配置: extractor_id={extractor.id if extractor else None}")
        logger.info(f"设备数量: {len(devices)}")
        
    except Exception as e:
        error_msg = f"❌ 加载任务配置失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        logger.error(error_msg, exc_info=True)
        sys.exit(1)
    
    # 启动抽帧工作线程
    try:
        running = True
        stop_event.clear()
        worker_thread = threading.Thread(target=frame_extraction_worker, daemon=True)
        worker_thread.start()
        logger.info("抽帧工作线程已启动")
    except Exception as e:
        error_msg = f"❌ 启动抽帧工作线程失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        logger.error(error_msg, exc_info=True)
        sys.exit(1)
    
    # 启动心跳上报线程
    try:
        heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        heartbeat_thread.start()
        logger.info("心跳上报线程已启动")
    except Exception as e:
        logger.warning(f"启动心跳上报线程失败: {str(e)}")
    
    # 注册退出处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭服务...")
        stop_event.set()
        running = False
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 启动Flask服务
    try:
        port = int(os.getenv('PORT', 8001))
        host = '0.0.0.0'
        
        logger.info(f"抽帧器服务启动: {host}:{port}")
        logger.info("=" * 60)
        
        app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
        stop_event.set()
        running = False
        sys.exit(0)
    except Exception as e:
        error_msg = f"❌ 服务启动异常: {str(e)}"
        logger.error(error_msg, exc_info=True)
        stop_event.set()
        running = False
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[FRAME_EXTRACTOR] 收到中断信号，正在退出...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        import traceback
        error_msg = f"❌ [FRAME_EXTRACTOR] 主函数异常: {str(e)}"
        print(error_msg, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

