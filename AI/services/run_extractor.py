"""
抽帧器服务
从视频/RTSP流中抽帧，并通过负载均衡发送到多个推理器进行推理
推理完成后，推理器会将结果发送到排序器进行排序

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
import base64
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import deque
import cv2
import numpy as np

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[EXTRACTOR] %(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
camera_name = None
input_source = None
input_type = None
service_name = None
frame_skip = 1
current_frame_index = 0
frame_index_lock = threading.Lock()
inference_endpoints = []  # 推理器端点列表（负载均衡）
inference_endpoint_index = 0  # 当前使用的推理器索引（轮询）
inference_endpoint_lock = threading.Lock()
sorter_receive_url = None
extractor_id = None
server_ip = None
port = None
cap = None
extraction_thread = None
running = True


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


def get_next_inference_endpoint() -> str:
    """获取下一个推理器端点（轮询负载均衡）"""
    global inference_endpoint_index
    
    with inference_endpoint_lock:
        if not inference_endpoints:
            return None
        
        endpoint = inference_endpoints[inference_endpoint_index]
        inference_endpoint_index = (inference_endpoint_index + 1) % len(inference_endpoints)
        return endpoint


def update_inference_endpoints():
    """更新推理器端点列表（从数据库查询）"""
    global inference_endpoints, service_name, sorter_receive_url
    
    try:
        # 这里需要从数据库查询，但由于是独立进程，我们通过API查询
        # 或者通过环境变量传递，或者通过HTTP API查询
        # 暂时通过环境变量或API获取
        
        # 从主服务API获取推理器列表
        api_base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000')
        try:
            response = requests.get(
                f"{api_base_url}/api/v1/deploy/replicas",
                params={'service_name': service_name},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    services = data.get('data', [])
                    # 过滤出运行中的推理器
                    new_endpoints = [
                        s['inference_endpoint'] 
                        for s in services 
                        if s.get('status') == 'running' and s.get('inference_endpoint')
                    ]
                    if new_endpoints:
                        with inference_endpoint_lock:
                            inference_endpoints = new_endpoints
                            logger.info(f'更新推理器端点列表: {len(inference_endpoints)} 个推理器')
        except Exception as e:
            logger.warning(f'获取推理器列表失败: {str(e)}')
        
        # 获取排序器接收地址
        try:
            response = requests.get(
                f"{api_base_url}/api/v1/deploy/sorter",
                params={'service_name': service_name},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    sorter_data = data.get('data', {})
                    global sorter_receive_url
                    sorter_receive_url = sorter_data.get('receive_url')
                    logger.info(f'更新排序器接收地址: {sorter_receive_url}')
        except Exception as e:
            logger.warning(f'获取排序器地址失败: {str(e)}')
            
    except Exception as e:
        logger.error(f'更新推理器端点列表异常: {str(e)}')


def send_frame_to_inference(frame: np.ndarray, frame_index: int) -> bool:
    """
    将帧发送到推理器进行推理
    
    Args:
        frame: 帧数据（numpy数组）
        frame_index: 帧索引
    
    Returns:
        bool: 是否成功
    """
    global sorter_receive_url
    
    # 获取推理器端点
    inference_endpoint = get_next_inference_endpoint()
    if not inference_endpoint:
        logger.warning(f'没有可用的推理器端点，跳过帧 {frame_index}')
        return False
    
    try:
        # 将帧编码为JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        frame_bytes = buffer.tobytes()
        
        # 准备文件上传
        files = {
            'file': (f'frame_{frame_index}.jpg', frame_bytes, 'image/jpeg')
        }
        
        # 准备数据（如果sorter_receive_url为空，则不传递）
        data = {
            'conf_thres': '0.25',
            'iou_thres': '0.45',
            'frame_index': str(frame_index),  # 传递帧索引
        }
        
        # 如果排序器地址存在，传递给推理器（推理器会判断是否为视频/RTSP并发送到排序器）
        if sorter_receive_url:
            data['sorter_url'] = sorter_receive_url
        
        # 发送到推理器
        response = requests.post(
            inference_endpoint,
            files=files,
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                logger.debug(f'帧 {frame_index} 已发送到推理器: {inference_endpoint}')
                return True
            else:
                logger.warning(f'推理器返回错误: {result.get("msg")}')
                return False
        else:
            logger.warning(f'推理器请求失败: HTTP {response.status_code}')
            return False
            
    except Exception as e:
        logger.error(f'发送帧到推理器失败: {str(e)}')
        return False


def extract_frames():
    """抽帧主循环"""
    global cap, current_frame_index, running, frame_skip
    
    logger.info(f'开始抽帧: {input_source}, 类型: {input_type}, 抽帧间隔: {frame_skip}')
    
    # 打开视频源
    if input_type == 'rtsp':
        cap = cv2.VideoCapture(input_source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲区
    else:
        cap = cv2.VideoCapture(input_source)
    
    if not cap.isOpened():
        logger.error(f'无法打开视频源: {input_source}')
        return
    
    frame_count = 0
    
    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            logger.warning('无法读取帧，可能视频已结束')
            break
        
        # 抽帧策略：每frame_skip帧抽1帧
        if frame_count % frame_skip == 0:
            # 获取下一个帧索引
            with frame_index_lock:
                frame_index = current_frame_index
                current_frame_index += 1
            
            # 发送到推理器
            send_frame_to_inference(frame, frame_index)
        
        frame_count += 1
    
    if cap:
        cap.release()
    logger.info('抽帧结束')


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'camera_name': camera_name,
        'current_frame_index': current_frame_index,
        'inference_endpoints_count': len(inference_endpoints),
        'sorter_receive_url': sorter_receive_url
    })


@app.route('/start', methods=['POST'])
def start_extraction():
    """启动抽帧"""
    global extraction_thread, running
    
    if extraction_thread and extraction_thread.is_alive():
        return jsonify({
            'code': 400,
            'msg': '抽帧已在运行'
        }), 400
    
    running = True
    extraction_thread = threading.Thread(target=extract_frames, daemon=True)
    extraction_thread.start()
    
    return jsonify({
        'code': 0,
        'msg': '抽帧已启动'
    })


@app.route('/stop', methods=['POST'])
def stop_extraction():
    """停止抽帧"""
    global running, cap
    
    running = False
    if cap:
        cap.release()
    
    return jsonify({
        'code': 0,
        'msg': '抽帧已停止'
    })


@app.route('/update_endpoints', methods=['POST'])
def update_endpoints():
    """更新推理器端点列表"""
    update_inference_endpoints()
    return jsonify({
        'code': 0,
        'msg': '端点列表已更新',
        'data': {
            'inference_endpoints': inference_endpoints,
            'sorter_receive_url': sorter_receive_url
        }
    })


def send_heartbeat():
    """发送心跳"""
    global extractor_id, current_frame_index
    
    api_base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000')
    
    while running:
        try:
            requests.post(
                f"{api_base_url}/api/v1/deploy/extractor/heartbeat",
                json={
                    'extractor_id': extractor_id,
                    'camera_name': camera_name,
                    'current_frame_index': current_frame_index,
                    'status': 'running'
                },
                timeout=5
            )
        except Exception as e:
            logger.warning(f'发送心跳失败: {str(e)}')
        
        time.sleep(30)  # 每30秒发送一次心跳


def check_extractor_enabled():
    """检查抽帧器是否启用"""
    global extractor_id, camera_name
    try:
        api_base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000')
        response = requests.get(
            f"{api_base_url}/model/deploy_service/extractor/{camera_name}",
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                data = result.get('data', {})
                return data.get('is_enabled', False)
    except Exception as e:
        logger.warning(f'检查抽帧器启用状态失败: {str(e)}')
    return False


def main():
    """主函数"""
    global camera_name, input_source, input_type, service_name, frame_skip
    global extractor_id, server_ip, port, running, current_frame_index
    
    # 从环境变量获取配置
    extractor_id = int(os.getenv('EXTRACTOR_ID', 0))
    camera_name = os.getenv('CAMERA_NAME')
    port = int(os.getenv('PORT', 9100))
    server_ip = os.getenv('SERVER_IP') or get_local_ip()
    input_source = os.getenv('INPUT_SOURCE')
    input_type = os.getenv('INPUT_TYPE', 'rtsp')
    service_name = os.getenv('SERVICE_NAME')
    frame_skip = int(os.getenv('FRAME_SKIP', 1))
    sorter_receive_url_env = os.getenv('SORTER_RECEIVE_URL', '')
    
    if not camera_name:
        logger.error('CAMERA_NAME环境变量未设置')
        sys.exit(1)
    
    if not input_source:
        logger.error('INPUT_SOURCE环境变量未设置')
        sys.exit(1)
    
    if not service_name:
        logger.error('SERVICE_NAME环境变量未设置')
        sys.exit(1)
    
    # 检查抽帧器是否启用
    is_enabled = check_extractor_enabled()
    if not is_enabled:
        logger.info(f'抽帧器 {camera_name} 未启用，服务将启动但不进行抽帧')
        running = False  # 关闭抽帧标志
    
    # 从数据库读取current_frame_index（如果extractor_id有效）
    if extractor_id > 0:
        try:
            api_base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000')
            response = requests.get(
                f"{api_base_url}/model/deploy_service/extractor/{camera_name}",
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    data = result.get('data', {})
                    # 如果当前输入源是视频则从头抽帧，如果是rtsp流也是取当前流去抽帧
                    if input_type == 'video':
                        current_frame_index = 0  # 视频从头抽帧
                        logger.info('视频输入，帧索引重置为0')
                    else:
                        # RTSP保持当前索引（从当前流开始）
                        current_frame_index = data.get('current_frame_index', 0)
                        logger.info(f'RTSP输入，从数据库读取帧索引: {current_frame_index}')
                    # 更新排序器地址
                    if not sorter_receive_url_env and data.get('sorter_receive_url'):
                        global sorter_receive_url
                        sorter_receive_url = data.get('sorter_receive_url')
        except Exception as e:
            logger.warning(f'从数据库读取帧索引失败: {str(e)}，使用默认值0')
    
    # 更新排序器地址（如果环境变量中有）
    if sorter_receive_url_env:
        global sorter_receive_url
        sorter_receive_url = sorter_receive_url_env
    
    # 启动时更新推理器端点列表
    update_inference_endpoints()
    
    # 启动心跳线程
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    
    # 定期更新推理器端点列表（每5分钟）
    def periodic_update():
        while True:
            time.sleep(300)  # 5分钟
            if running:
                update_inference_endpoints()
    
    update_thread = threading.Thread(target=periodic_update, daemon=True)
    update_thread.start()
    
    # 定期检查抽帧器启用状态（每30秒）
    def check_enabled_periodic():
        global running
        while True:
            time.sleep(30)  # 每30秒检查一次
            is_enabled_now = check_extractor_enabled()
            if not is_enabled_now and running:
                logger.info(f'抽帧器 {camera_name} 已关闭，停止抽帧')
                running = False
            elif is_enabled_now and not running:
                logger.info(f'抽帧器 {camera_name} 已开启，开始抽帧')
                running = True
                # 重新启动抽帧线程
                extraction_thread = threading.Thread(target=extract_frames, daemon=True)
                extraction_thread.start()
    
    check_enabled_thread = threading.Thread(target=check_enabled_periodic, daemon=True)
    check_enabled_thread.start()
    
    logger.info(f'抽帧器服务启动: {camera_name}')
    logger.info(f'输入源: {input_source} ({input_type})')
    logger.info(f'服务名称: {service_name}')
    logger.info(f'抽帧间隔: {frame_skip}')
    logger.info(f'当前帧索引: {current_frame_index}')
    logger.info(f'推理器数量: {len(inference_endpoints)}')
    logger.info(f'排序器地址: {sorter_receive_url}')
    logger.info(f'抽帧器启用状态: {is_enabled}')
    
    # 自动启动抽帧（如果服务启动且抽帧器已启用）
    if running and is_enabled:
        extraction_thread = threading.Thread(target=extract_frames, daemon=True)
        extraction_thread.start()
        logger.info('抽帧线程已自动启动')
    else:
        logger.info('抽帧线程未启动（抽帧器未启用）')
    
    # 启动Flask服务
    app.run(host='0.0.0.0', port=port, threaded=True, debug=False, use_reloader=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('收到中断信号，正在退出...')
        running = False
        if cap:
            cap.release()
        sys.exit(0)
    except Exception as e:
        logger.error(f'主函数异常: {str(e)}', exc_info=True)
        sys.exit(1)

