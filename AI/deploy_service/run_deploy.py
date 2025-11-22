"""
独立的Flask部署服务
用于部署模型并提供推理接口
"""
import os
import sys
import time
import threading
import logging
import uuid
import socket
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加父目录到路径，以便导入模型相关代码
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
model = None
model_loaded = False
service_id = None
service_name = None
server_ip = None
port = None
ai_service_api = None
heartbeat_thread = None
heartbeat_stop_event = threading.Event()


def get_mac_address():
    """获取MAC地址"""
    try:
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
    except:
        return 'unknown'


def get_local_ip():
    """获取本地IP地址"""
    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
            for addr in addrs:
                ip = addr['addr']
                if ip != '127.0.0.1' and not ip.startswith('169.254.'):
                    return ip
    except:
        pass
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def load_model(model_path):
    """加载模型"""
    global model, model_loaded
    
    try:
        logger.info(f"开始加载模型: {model_path}")
        
        # 根据文件扩展名判断模型类型
        if model_path.endswith('.onnx'):
            # ONNX模型加载
            try:
                import onnxruntime as ort
                model = ort.InferenceSession(model_path)
                logger.info("ONNX模型加载成功")
            except ImportError:
                logger.error("onnxruntime未安装，无法加载ONNX模型")
                return False
        else:
            # PyTorch模型加载（.pt文件）
            try:
                from ultralytics import YOLO
                model = YOLO(model_path)
                logger.info("YOLO模型加载成功")
            except Exception as e:
                logger.error(f"YOLO模型加载失败: {str(e)}")
                return False
        
        model_loaded = True
        return True
        
    except Exception as e:
        logger.error(f"加载模型失败: {str(e)}")
        model_loaded = False
        return False


def send_heartbeat():
    """发送心跳"""
    global service_id, server_ip, port, ai_service_api
    
    while not heartbeat_stop_event.is_set():
        try:
            if service_id and ai_service_api:
                data = {
                    'service_id': service_id,
                    'server_ip': server_ip,
                    'port': port,
                    'inference_endpoint': f"http://{server_ip}:{port}/inference",
                    'mac_address': get_mac_address()
                }
                
                response = requests.post(
                    f"{ai_service_api}/heartbeat",
                    json=data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.debug("心跳发送成功")
                else:
                    logger.warning(f"心跳发送失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"心跳发送异常: {str(e)}")
        
        time.sleep(30)  # 每30秒发送一次心跳


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loaded,
        'service_id': service_id,
        'service_name': service_name
    })


@app.route('/inference', methods=['POST'])
def inference():
    """推理接口"""
    global model, model_loaded
    
    if not model_loaded or model is None:
        return jsonify({
            'code': 500,
            'msg': '模型未加载'
        }), 500
    
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'msg': '未找到文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 400,
                'msg': '未选择文件'
            }), 400
        
        # 保存临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        try:
            # 执行推理
            if hasattr(model, 'predict'):  # YOLO模型
                results = model.predict(temp_file.name)
                
                # 处理结果
                predictions = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        predictions.append({
                            'class': int(box.cls),
                            'confidence': float(box.conf),
                            'bbox': box.xyxy[0].tolist() if hasattr(box.xyxy, '__len__') else box.xyxy.tolist()
                        })
                
                return jsonify({
                    'code': 0,
                    'msg': '推理成功',
                    'data': {
                        'predictions': predictions,
                        'image_path': temp_file.name
                    }
                })
            else:
                # ONNX模型推理（简化实现）
                return jsonify({
                    'code': 500,
                    'msg': 'ONNX模型推理暂未实现'
                }), 500
                
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"推理失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'推理失败: {str(e)}'
        }), 500


def main():
    """主函数"""
    global service_id, service_name, server_ip, port, ai_service_api, heartbeat_thread
    
    # 从环境变量获取配置
    service_id = os.getenv('SERVICE_ID')
    service_name = os.getenv('SERVICE_NAME', 'deploy_service')
    port = int(os.getenv('PORT', 8000))
    model_path = os.getenv('MODEL_PATH')
    ai_service_api = os.getenv('AI_SERVICE_API', 'http://localhost:5000/model/deploy_service')
    
    server_ip = get_local_ip()
    
    if not model_path:
        logger.error("MODEL_PATH环境变量未设置")
        sys.exit(1)
    
    if not service_id:
        logger.error("SERVICE_ID环境变量未设置")
        sys.exit(1)
    
    # 加载模型
    if not load_model(model_path):
        logger.error("模型加载失败，退出")
        sys.exit(1)
    
    # 启动心跳线程
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    logger.info("心跳线程已启动")
    
    # 启动Flask服务
    logger.info(f"部署服务启动: {service_name} on {server_ip}:{port}")
    app.run(host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    main()

