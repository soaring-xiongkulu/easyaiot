#!/usr/bin/env python3
"""
推流转发服务程序
用于批量推送多个摄像头实时画面，无需AI推理

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
import cv2
import requests
import json
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 全局变量
TASK_ID = int(os.getenv('TASK_ID', '0'))
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
VIDEO_SERVICE_PORT = os.getenv('VIDEO_SERVICE_PORT', '6000')
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:48080')

# 数据库会话
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db_session = scoped_session(SessionLocal)

# 全局变量
stop_event = threading.Event()
task_config = None
# 摄像头流连接（VideoCapture对象）
device_caps = {}  # {device_id: cv2.VideoCapture}
# 摄像头推送进程（FFmpeg进程）
device_pushers = {}  # {device_id: subprocess.Popen}
# 设备流信息
device_streams = {}  # {device_id: {'rtsp_url': str, 'rtmp_url': str, 'device_name': str}}
# 线程锁
device_locks = {}  # {device_id: threading.Lock()}
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


def get_bitrate_for_quality(quality: str, custom_bitrate: Optional[str] = None) -> str:
    """根据质量设置获取码率"""
    if custom_bitrate:
        return custom_bitrate
    
    quality_map = {
        'low': '512k',
        'medium': '1M',
        'high': '2M'
    }
    return quality_map.get(quality, '1M')


def start_ffmpeg_pusher(device_id: str):
    """启动FFmpeg推流进程"""
    if device_id not in device_streams:
        logger.error(f"设备 {device_id} 流信息不存在")
        return None
    
    stream_info = device_streams[device_id]
    rtsp_url = stream_info['rtsp_url']
    rtmp_url = stream_info['rtmp_url']
    device_name = stream_info['device_name']
    
    # 获取码率
    bitrate = get_bitrate_for_quality(task_config.output_quality, task_config.output_bitrate)
    
    # 构建FFmpeg命令
    ffmpeg_cmd = [
        'ffmpeg',
        '-rtsp_transport', 'tcp',
        '-i', rtsp_url,
        '-an',  # 禁用音频
        '-c:v', 'libx264',
        '-b:v', bitrate,
        '-preset', 'veryfast',
        '-tune', 'zerolatency',
        '-f', 'flv',
        '-loglevel', 'error',
        rtmp_url
    ]
    
    try:
        logger.info(f"🚀 启动FFmpeg推流: 设备={device_name} ({device_id})")
        logger.info(f"   输入: {rtsp_url}")
        logger.info(f"   输出: {rtmp_url}")
        logger.info(f"   码率: {bitrate}")
        
        pusher_process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        # 等待一小段时间，检查进程是否立即退出
        time.sleep(1)
        if pusher_process.poll() is not None:
            stderr_output = pusher_process.stderr.read().decode('utf-8', errors='ignore')
            logger.error(f"❌ FFmpeg进程立即退出: 设备={device_name} ({device_id})")
            logger.error(f"   错误信息: {stderr_output}")
            return None
        
        logger.info(f"✅ FFmpeg推流启动成功: 设备={device_name} ({device_id}), PID={pusher_process.pid}")
        return pusher_process
        
    except Exception as e:
        logger.error(f"❌ 启动FFmpeg推流失败: 设备={device_name} ({device_id}), 错误={str(e)}", exc_info=True)
        return None


def stream_forward_worker(device_id: str):
    """推流转发工作线程"""
    logger.info(f"📺 推流转发线程启动 [设备: {device_id}]")
    
    if not task_config or not hasattr(task_config, 'device_streams'):
        logger.error(f"任务配置未加载，设备 {device_id} 推流转发线程退出")
        return
    
    device_stream_info = task_config.device_streams.get(device_id)
    if not device_stream_info:
        logger.error(f"设备 {device_id} 流信息不存在，推流转发线程退出")
        return
    
    rtsp_url = device_stream_info.get('rtsp_url')
    rtmp_url = device_stream_info.get('rtmp_url')
    device_name = device_stream_info.get('device_name', device_id)
    
    if not rtsp_url or not rtmp_url:
        logger.error(f"设备 {device_id} 流地址配置不完整，推流转发线程退出")
        return
    
    pusher_process = None
    retry_count = 0
    max_retries = 5
    retry_interval = 5  # 重试间隔（秒）
    
    while not stop_event.is_set():
        try:
            # 启动或重启FFmpeg推流进程
            if pusher_process is None or pusher_process.poll() is not None:
                if pusher_process is not None:
                    logger.warning(f"⚠️  FFmpeg进程异常退出，准备重启: 设备={device_name} ({device_id})")
                    pusher_process = None
                
                # 检查重试次数
                if retry_count >= max_retries:
                    logger.error(f"❌ 达到最大重试次数，停止推流: 设备={device_name} ({device_id})")
                    break
                
                pusher_process = start_ffmpeg_pusher(device_id)
                if pusher_process:
                    device_pushers[device_id] = pusher_process
                    retry_count = 0  # 重置重试计数
                else:
                    retry_count += 1
                    logger.warning(f"⚠️  启动FFmpeg失败，{retry_interval}秒后重试 ({retry_count}/{max_retries}): 设备={device_name} ({device_id})")
                    time.sleep(retry_interval)
                    continue
            
            # 等待一段时间后检查进程状态
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ 推流转发线程异常: 设备={device_name} ({device_id}), 错误={str(e)}", exc_info=True)
            time.sleep(retry_interval)
    
    # 清理资源
    if pusher_process and pusher_process.poll() is None:
        try:
            pusher_process.terminate()
            pusher_process.wait(timeout=5)
        except:
            try:
                pusher_process.kill()
            except:
                pass
    
    if device_id in device_pushers:
        del device_pushers[device_id]
    
    logger.info(f"📺 推流转发线程退出 [设备: {device_id}]")


def send_heartbeat():
    """发送心跳"""
    global heartbeat_thread
    
    while not stop_event.is_set():
        try:
            if not task_config:
                time.sleep(5)
                continue
            
            # 计算活跃流数量
            active_streams = 0
            for device_id, pusher in device_pushers.items():
                if pusher and pusher.poll() is None:
                    active_streams += 1
            
            # 发送心跳
            heartbeat_url = f"{GATEWAY_URL}/video/stream-forward/heartbeat"
            data = {
                'task_id': TASK_ID,
                'server_ip': get_local_ip(),
                'port': int(VIDEO_SERVICE_PORT),
                'process_id': os.getpid(),
                'log_path': os.path.join(video_root, 'logs', f'stream_forward_task_{TASK_ID}'),
                'active_streams': active_streams
            }
            
            try:
                response = requests.post(
                    heartbeat_url,
                    json=data,
                    timeout=5,
                    headers={'X-Authorization': f'Bearer {os.getenv("JWT_TOKEN", "")}'}
                )
                if response.status_code == 200:
                    logger.debug(f"✅ 心跳发送成功: active_streams={active_streams}")
                else:
                    logger.warning(f"⚠️  心跳发送失败: HTTP {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️  心跳发送异常: {str(e)}")
            
            time.sleep(5)  # 每5秒发送一次心跳
            
        except Exception as e:
            logger.error(f"❌ 心跳线程异常: {str(e)}", exc_info=True)
            time.sleep(5)


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
    logger.info("=" * 60)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 加载任务配置
    if not load_task_config():
        logger.error("❌ 加载任务配置失败，服务退出")
        return
    
    device_streams = task_config.device_streams
    
    # 为每个设备创建锁
    for device_id in device_streams.keys():
        device_locks[device_id] = threading.Lock()
    
    # 启动推流转发线程
    worker_threads = []
    for device_id in device_streams.keys():
        thread = threading.Thread(
            target=stream_forward_worker,
            args=(device_id,),
            daemon=True
        )
        thread.start()
        worker_threads.append(thread)
        logger.info(f"✅ 启动推流转发线程: 设备={device_id}")
    
    # 启动心跳线程
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    logger.info("✅ 心跳线程启动")
    
    logger.info("=" * 60)
    logger.info("推流转发服务运行中...")
    logger.info(f"活跃设备数: {len(device_streams)}")
    logger.info("=" * 60)
    
    try:
        # 主循环
        while not stop_event.is_set():
            time.sleep(1)
            
            # 检查所有工作线程是否还在运行
            alive_threads = [t for t in worker_threads if t.is_alive()]
            if len(alive_threads) == 0:
                logger.warning("⚠️  所有推流转发线程已退出")
                break
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，准备退出...")
    finally:
        # 停止所有线程
        logger.info("正在停止推流转发服务...")
        stop_event.set()
        
        # 等待所有工作线程结束
        for thread in worker_threads:
            thread.join(timeout=10)
        
        # 停止所有FFmpeg进程
        for device_id, pusher in device_pushers.items():
            if pusher and pusher.poll() is None:
                try:
                    pusher.terminate()
                    pusher.wait(timeout=5)
                except:
                    try:
                        pusher.kill()
                    except:
                        pass
        
        logger.info("推流转发服务已停止")


if __name__ == '__main__':
    main()

