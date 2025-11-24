"""
帧排序器服务
接收来自多个模型实例的帧，使用滑动窗口排序后按顺序推送流

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
import subprocess
import base64
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的库
import cv2
import numpy as np

from app.services.frame_sorter_service import FrameBuffer

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[SORTER] %(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
frame_buffer: FrameBuffer = None
ffmpeg_process = None
output_url = None
server_ip = None
port = None
service_name = None


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


def init_ffmpeg(output_url: str, width: int = 1920, height: int = 1080, fps: int = 25):
    """初始化FFmpeg推流进程"""
    global ffmpeg_process
    
    command = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{width}x{height}',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-f', 'flv',
        output_url
    ]
    
    try:
        ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE)
        logger.info(f'FFmpeg推流进程已启动: {output_url}')
        return True
    except Exception as e:
        logger.error(f'启动FFmpeg失败: {str(e)}')
        return False


def flush_frames_loop():
    """定期刷新帧缓冲区，支持批量推送和超时滑动"""
    global frame_buffer, ffmpeg_process
    
    while True:
        try:
            if frame_buffer and frame_buffer.should_flush():
                # 批量获取可输出的帧（包含跳过的帧数信息）
                frames_with_skip = frame_buffer.flush_available_frames()
                
                if frames_with_skip:
                    # 记录跳过的帧数（只在第一批输出时记录）
                    total_skipped = 0
                    batch_frames = []
                    
                    for frame_info in frames_with_skip:
                        if isinstance(frame_info, tuple):
                            frame_data, skipped = frame_info
                            if skipped > 0:
                                total_skipped += skipped
                                logger.warning(f'批量推送前跳过了 {skipped} 个超时帧')
                            batch_frames.append(frame_data)
                        else:
                            # 兼容旧格式
                            batch_frames.append(frame_info)
                    
                    # 批量推送帧
                    for frame_data in batch_frames:
                        if ffmpeg_process and ffmpeg_process.stdin:
                            try:
                                # 解码JPEG图片
                                nparr = np.frombuffer(frame_data, np.uint8)
                                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                                if frame is not None:
                                    # 获取帧尺寸（首次需要初始化FFmpeg）
                                    if ffmpeg_process is None or ffmpeg_process.poll() is not None:
                                        height, width = frame.shape[:2]
                                        init_ffmpeg(output_url, width, height)
                                    
                                    if ffmpeg_process and ffmpeg_process.stdin:
                                        ffmpeg_process.stdin.write(frame.tobytes())
                                        ffmpeg_process.stdin.flush()
                            except Exception as e:
                                logger.error(f'推送帧失败: {str(e)}')
                    
                    if total_skipped > 0:
                        logger.info(f'批量推送了 {len(batch_frames)} 帧，跳过了 {total_skipped} 个超时帧')
                    elif len(batch_frames) > 0:
                        logger.debug(f'批量推送了 {len(batch_frames)} 帧')
            
            time.sleep(0.05)  # 每50ms检查一次，提高响应速度
            
        except Exception as e:
            logger.error(f'刷新帧缓冲区异常: {str(e)}')
            time.sleep(1)


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    stats = frame_buffer.get_stats() if frame_buffer else {}
    return jsonify({
        'status': 'healthy',
        'service_name': service_name,
        'buffer_stats': stats
    })


@app.route('/receive_frame', methods=['POST'])
def receive_frame():
    """接收帧"""
    global frame_buffer, ffmpeg_process
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 400,
                'msg': '请求体为空'
            }), 400
        
        frame_seq = data.get('frame_seq')
        frame_data_base64 = data.get('frame_data')
        instance_id = data.get('instance_id')
        width = data.get('width', 1920)
        height = data.get('height', 1080)
        
        if frame_seq is None or not frame_data_base64 or not instance_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数: frame_seq, frame_data, instance_id'
            }), 400
        
        # 解码base64图片
        try:
            frame_data = base64.b64decode(frame_data_base64)
        except Exception as e:
            logger.error(f'解码帧数据失败: {str(e)}')
            return jsonify({
                'code': 400,
                'msg': f'解码帧数据失败: {str(e)}'
            }), 400
        
        # 添加到缓冲区
        should_output = frame_buffer.add_frame(frame_seq, frame_data, instance_id)
        
        # 如果收到期望的帧，立即输出
        if should_output:
            next_frame = frame_buffer.get_next_frame()
            if next_frame and ffmpeg_process and ffmpeg_process.stdin:
                try:
                    # 初始化FFmpeg（如果未初始化）
                    if ffmpeg_process.poll() is not None:
                        init_ffmpeg(output_url, width, height)
                    
                    # 解码并推送帧
                    nparr = np.frombuffer(next_frame, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        ffmpeg_process.stdin.write(frame.tobytes())
                        ffmpeg_process.stdin.flush()
                except Exception as e:
                    logger.error(f'推送帧失败: {str(e)}')
        
        return jsonify({
            'code': 0,
            'msg': '帧接收成功',
            'data': {
                'frame_seq': frame_seq,
                'buffer_stats': frame_buffer.get_stats()
            }
        })
        
    except Exception as e:
        logger.error(f'接收帧失败: {str(e)}', exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@app.route('/stop', methods=['POST'])
def stop_sorter():
    """停止排序器"""
    global ffmpeg_process
    
    try:
        if ffmpeg_process:
            ffmpeg_process.stdin.close()
            ffmpeg_process.terminate()
            ffmpeg_process.wait(timeout=5)
        
        return jsonify({
            'code': 0,
            'msg': '排序器已停止'
        })
    except Exception as e:
        logger.error(f'停止排序器失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': f'停止失败: {str(e)}'
        }), 500


def main():
    """主函数"""
    global frame_buffer, output_url, server_ip, port, service_name
    
    # 从环境变量获取配置
    service_name = os.getenv('SERVICE_NAME')
    port = int(os.getenv('PORT', 9000))
    server_ip = os.getenv('SERVER_IP') or get_local_ip()
    output_url = os.getenv('OUTPUT_URL')
    window_size = int(os.getenv('WINDOW_SIZE', 10))
    batch_size = int(os.getenv('BATCH_SIZE', 5))  # 批量推送阈值
    frame_timeout = float(os.getenv('FRAME_TIMEOUT', 2.0))  # 单个帧超时时间（秒）
    
    if not service_name:
        logger.error('SERVICE_NAME环境变量未设置')
        sys.exit(1)
    
    if not output_url:
        logger.error('OUTPUT_URL环境变量未设置，排序器无法启动（需要推流地址）')
        logger.error('如果没有推流地址，排序器将不会启动')
        sys.exit(1)
    
    # 初始化帧缓冲区（支持批量推送和超时滑动）
    frame_buffer = FrameBuffer(
        window_size=window_size, 
        timeout=5.0,  # 整体超时时间
        batch_size=batch_size,  # 批量推送阈值
        frame_timeout=frame_timeout  # 单个帧超时时间
    )
    
    # 启动刷新线程
    flush_thread = threading.Thread(target=flush_frames_loop, daemon=True)
    flush_thread.start()
    
    logger.info(f'帧排序器服务启动: {service_name}')
    logger.info(f'接收地址: http://{server_ip}:{port}/receive_frame')
    logger.info(f'输出地址: {output_url}')
    logger.info(f'窗口大小: {window_size}')
    logger.info(f'批量推送阈值: {batch_size} 帧')
    logger.info(f'帧超时时间: {frame_timeout} 秒')
    
    # 启动Flask服务
    app.run(host='0.0.0.0', port=port, threaded=True, debug=False, use_reloader=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('收到中断信号，正在退出...')
        sys.exit(0)
    except Exception as e:
        logger.error(f'主函数异常: {str(e)}', exc_info=True)
        sys.exit(1)

