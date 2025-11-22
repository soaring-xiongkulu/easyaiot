"""
独立的Flask部署服务
用于部署模型并提供推理接口
支持Nacos注册、日志上报、停止/重启接口
"""
import os
import sys
import time
import threading
import logging
import uuid
import socket
import requests
import atexit
import signal
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加当前目录到路径，以便导入模型相关代码
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入推理相关模块
ONNXInference = None
try:
    from app.utils.onnx_inference import ONNXInference
    from app.utils.yolo_validator import validate_yolo_model
except ImportError as e:
    print(f"警告: 无法导入推理模块: {e}")

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
model_id = None
model_version = None
model_format = None
nacos_service_name = None  # Nacos注册的服务名
server_ip = None
port = None
ai_service_api = None
heartbeat_thread = None
heartbeat_stop_event = threading.Event()
log_report_thread = None
log_report_stop_event = threading.Event()
nacos_client = None
shutdown_flag = threading.Event()


def get_mac_address():
    """获取MAC地址"""
    try:
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
    except:
        return 'unknown'


def get_local_ip():
    """获取本地IP地址"""
    # 方案1: 环境变量优先
    if ip := os.getenv('POD_IP'):
        return ip
    
    # 方案2: 多网卡探测
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
    
    # 方案3: 原始方式
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def get_ai_module_instance():
    """从Nacos获取AI模块实例列表，随机选择一个"""
    global nacos_client
    
    try:
        if not nacos_client:
            # 如果Nacos客户端未初始化，尝试初始化
            from nacos import NacosClient
            nacos_server = os.getenv('NACOS_SERVER', 'localhost:8848')
            namespace = os.getenv('NACOS_NAMESPACE', '')
            username = os.getenv('NACOS_USERNAME', 'nacos')
            password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')
            
            nacos_client = NacosClient(
                server_addresses=nacos_server,
                namespace=namespace,
                username=username,
                password=password
            )
        
        # AI模块的服务名（从环境变量获取，默认是model-server）
        ai_service_name = os.getenv('AI_SERVICE_NAME', 'model-server')
        
        # 获取服务实例列表
        instances = nacos_client.list_naming_instance(
            service_name=ai_service_name,
            healthy_only=True
        )
        
        if not instances or len(instances) == 0:
            logger.warning(f"未找到AI模块实例: {ai_service_name}")
            return None
        
        # 随机选择一个实例
        import random
        selected_instance = random.choice(instances)
        
        # 构建URL
        ip = selected_instance.get('ip', '')
        port = selected_instance.get('port', 5000)
        ai_url = f"http://{ip}:{port}"
        
        logger.info(f"从Nacos获取到AI模块实例: {ai_url} (共{len(instances)}个实例)")
        return ai_url
        
    except Exception as e:
        logger.error(f"从Nacos获取AI模块实例失败: {str(e)}")
        # 如果Nacos获取失败，使用环境变量中的默认值
        default_ai_url = os.getenv('AI_SERVICE_API', 'http://localhost:5000')
        logger.warning(f"使用默认AI模块地址: {default_ai_url}")
        return default_ai_url


def load_model(model_path):
    """加载模型"""
    global model, model_loaded
    
    try:
        logger.info(f"开始加载模型: {model_path}")
        
        # 根据文件扩展名判断模型类型
        if model_path.endswith('.onnx'):
            # ONNX模型加载
            try:
                model = ONNXInference(model_path)
                logger.info("ONNX模型加载成功")
                model_loaded = True
                return True
            except ImportError:
                logger.error("onnxruntime未安装，无法加载ONNX模型")
                return False
            except Exception as e:
                logger.error(f"ONNX模型加载失败: {str(e)}")
                return False
        else:
            # PyTorch模型加载（.pt文件）
            try:
                from ultralytics import YOLO
                model = YOLO(model_path)
                logger.info("YOLO模型加载成功")
                model_loaded = True
                return True
            except Exception as e:
                logger.error(f"YOLO模型加载失败: {str(e)}")
                return False
        
    except Exception as e:
        logger.error(f"加载模型失败: {str(e)}")
        model_loaded = False
        return False


def send_heartbeat():
    """发送心跳到主程序（通过Nacos获取AI模块实例）"""
    global service_id, service_name, server_ip, port, model_id, model_version, model_format
    
    while not heartbeat_stop_event.is_set():
        try:
            # 从Nacos获取AI模块实例
            ai_service_api = get_ai_module_instance()
            
            if ai_service_api:
                data = {
                    'server_ip': server_ip,
                    'port': port,
                    'inference_endpoint': f"http://{server_ip}:{port}/inference",
                    'mac_address': get_mac_address()
                }
                
                if service_name:
                    data['service_name'] = service_name
                if service_id:
                    data['service_id'] = service_id
                if model_id:
                    data['model_id'] = model_id
                if model_version:
                    data['model_version'] = model_version
                if model_format:
                    data['format'] = model_format
                
                try:
                    response = requests.post(
                        f"{ai_service_api}/model/deploy_service/heartbeat",
                        json=data,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('code') == 0 and result.get('data'):
                            returned_service_id = result.get('data', {}).get('service_id')
                            if returned_service_id:
                                service_id = returned_service_id
                        logger.debug("心跳发送成功")
                    else:
                        logger.warning(f"心跳发送失败: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"心跳发送请求异常: {str(e)}")
                    
        except Exception as e:
            logger.error(f"心跳发送异常: {str(e)}")
        
        time.sleep(30)  # 每30秒发送一次心跳


def send_log_to_main(log_content, log_level='INFO'):
    """上报日志到主程序（通过Nacos获取AI模块实例）"""
    global service_name
    
    try:
        # 从Nacos获取AI模块实例
        ai_service_api = get_ai_module_instance()
        
        if not ai_service_api:
            return
        
        # 构建日志上报数据
        log_data = {
            'service_name': service_name,
            'log': log_content,
            'level': log_level,
            'timestamp': datetime.now().isoformat()
        }
        
        # 发送日志到主程序
        try:
            response = requests.post(
                f"{ai_service_api}/model/deploy_service/logs",
                json=log_data,
                timeout=3
            )
            if response.status_code == 200:
                logger.debug("日志上报成功")
        except requests.exceptions.RequestException:
            # 如果日志上报接口不存在，静默失败（不影响主流程）
            pass
            
    except Exception as e:
        logger.debug(f"日志上报异常: {str(e)}")


class LogHandler(logging.Handler):
    """自定义日志处理器，用于上报日志到主程序"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_send_time = 0
        self._log_buffer = []
        self._buffer_lock = threading.Lock()
        self._buffer_size = 10  # 缓冲区大小
        self._flush_interval = 5  # 刷新间隔（秒）
        
        # 启动后台线程定期刷新缓冲区
        self._flush_thread = threading.Thread(target=self._periodic_flush, daemon=True)
        self._flush_thread.start()
    
    def emit(self, record):
        """发送日志记录"""
        try:
            log_message = self.format(record)
            log_level = record.levelname
            
            # 将日志添加到缓冲区
            with self._buffer_lock:
                self._log_buffer.append({
                    'message': log_message,
                    'level': log_level,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 如果缓冲区满了，立即刷新
                if len(self._log_buffer) >= self._buffer_size:
                    self._flush_buffer()
        except Exception:
            pass  # 避免日志上报失败影响主流程
    
    def _flush_buffer(self):
        """刷新缓冲区，上报所有日志"""
        with self._buffer_lock:
            if not self._log_buffer:
                return
            
            # 批量上报日志
            for log_item in self._log_buffer:
                send_log_to_main(log_item['message'], log_item['level'])
            
            self._log_buffer.clear()
    
    def _periodic_flush(self):
        """定期刷新缓冲区"""
        while not log_report_stop_event.is_set():
            time.sleep(self._flush_interval)
            self._flush_buffer()
    
    def close(self):
        """关闭处理器时刷新缓冲区"""
        self._flush_buffer()
        super().close()


def setup_nacos():
    """设置Nacos注册"""
    global nacos_client, nacos_service_name, server_ip, port, model_id, model_version, model_format
    
    try:
        from nacos import NacosClient
        
        # 获取Nacos配置
        nacos_server = os.getenv('NACOS_SERVER', 'localhost:8848')
        namespace = os.getenv('NACOS_NAMESPACE', '')
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')
        
        # 创建Nacos客户端
        nacos_client = NacosClient(
            server_addresses=nacos_server,
            namespace=namespace,
            username=username,
            password=password
        )
        
        # 构建Nacos服务名：model_{model_id}_{format}_{version}
        if model_id and model_version and model_format:
            nacos_service_name = f"model_{model_id}_{model_format}_{model_version}"
        else:
            # 如果缺少必要信息，使用service_name作为fallback
            logger.warning("缺少model_id/model_version/model_format，使用service_name作为Nacos服务名")
            nacos_service_name = service_name
        
        # 注册服务实例
        nacos_client.add_naming_instance(
            service_name=nacos_service_name,
            ip=server_ip,
            port=port,
            cluster_name="DEFAULT",
            healthy=True,
            ephemeral=True
        )
        
        logger.info(f"✅ 服务注册到Nacos成功: {nacos_service_name}@{server_ip}:{port}")
        return True
        
    except ImportError:
        logger.warning("nacos-sdk-python未安装，跳过Nacos注册")
        return False
    except Exception as e:
        logger.error(f"Nacos注册失败: {str(e)}")
        return False


def send_nacos_heartbeat():
    """发送Nacos心跳"""
    global nacos_client, nacos_service_name, server_ip, port
    
    while not heartbeat_stop_event.is_set():
        try:
            if nacos_client and nacos_service_name:
                nacos_client.send_heartbeat(
                    service_name=nacos_service_name,
                    ip=server_ip,
                    port=port
                )
        except Exception as e:
            logger.error(f"Nacos心跳发送异常: {str(e)}")
        
        time.sleep(5)  # 每5秒发送一次Nacos心跳


def deregister_nacos():
    """注销Nacos服务"""
    global nacos_client, nacos_service_name, server_ip, port
    
    try:
        if nacos_client and nacos_service_name:
            nacos_client.remove_naming_instance(
                service_name=nacos_service_name,
                ip=server_ip,
                port=port
            )
            logger.info(f"🔴 Nacos服务注销成功: {nacos_service_name}@{server_ip}:{port}")
    except Exception as e:
        logger.error(f"Nacos注销异常: {str(e)}")


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
        
        # 获取推理参数
        conf_thres = float(request.form.get('conf_thres', 0.25))
        iou_thres = float(request.form.get('iou_thres', 0.45))
        
        # 保存临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        try:
            # 执行推理
            # 检查是否为ONNX模型
            is_onnx = False
            if ONNXInference is not None:
                is_onnx = isinstance(model, ONNXInference)
            else:
                # 如果ONNXInference未导入，检查模型是否有detect方法且没有predict方法
                is_onnx = hasattr(model, 'detect') and not hasattr(model, 'predict')
            
            if is_onnx:
                # ONNX模型推理
                output_image, detections = model.detect(
                    temp_file.name,
                    conf_threshold=conf_thres,
                    iou_threshold=iou_thres,
                    draw=True
                )
                
                # 保存结果图片
                import cv2
                result_path = temp_file.name.replace(os.path.splitext(temp_file.name)[1], '_result.jpg')
                cv2.imwrite(result_path, output_image)
                
                return jsonify({
                    'code': 0,
                    'msg': '推理成功',
                    'data': {
                        'predictions': detections,
                        'result_image_path': result_path
                    }
                })
            elif hasattr(model, 'predict'):  # YOLO模型
                results = model.predict(
                    temp_file.name,
                    conf=conf_thres,
                    iou=iou_thres,
                    verbose=False
                )
                
                # 处理结果
                predictions = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        predictions.append({
                            'class': int(box.cls.item()),
                            'class_name': result.names[int(box.cls.item())],
                            'confidence': float(box.conf.item()),
                            'bbox': box.xyxy.tolist()[0]
                        })
                
                # 保存结果图片
                result_path = temp_file.name.replace(os.path.splitext(temp_file.name)[1], '_result.jpg')
                results[0].save(filename=result_path)
                
                return jsonify({
                    'code': 0,
                    'msg': '推理成功',
                    'data': {
                        'predictions': predictions,
                        'result_image_path': result_path
                    }
                })
            else:
                return jsonify({
                    'code': 500,
                    'msg': '不支持的模型类型'
                }), 500
                
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"推理失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'推理失败: {str(e)}'
        }), 500


@app.route('/stop', methods=['POST'])
def stop_service():
    """停止服务接口"""
    global shutdown_flag
    
    try:
        logger.info("收到停止服务请求")
        shutdown_flag.set()
        
        # 停止心跳线程
        heartbeat_stop_event.set()
        
        # 停止日志上报
        log_report_stop_event.set()
        
        # 注销Nacos
        deregister_nacos()
        
        # 延迟关闭，给响应时间
        def delayed_shutdown():
            time.sleep(1)
            os._exit(0)
        
        threading.Thread(target=delayed_shutdown, daemon=True).start()
        
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


@app.route('/restart', methods=['POST'])
def restart_service():
    """重启服务接口"""
    global model, model_loaded, model_id
    
    try:
        logger.info("收到重启服务请求")
        
        # 重新加载模型
        model_path = os.getenv('MODEL_PATH')
        if model_path:
            model_loaded = False
            model = None
            if load_model(model_path):
                return jsonify({
                    'code': 0,
                    'msg': '服务重启成功'
                })
            else:
                return jsonify({
                    'code': 500,
                    'msg': '模型重新加载失败'
                }), 500
        else:
            return jsonify({
                'code': 400,
                'msg': 'MODEL_PATH环境变量未设置'
            }), 400
            
    except Exception as e:
        logger.error(f"重启服务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'重启服务失败: {str(e)}'
        }), 500


def main():
    """主函数"""
    global service_id, service_name, model_id, model_version, model_format, server_ip, port, ai_service_api
    global heartbeat_thread, log_report_thread, nacos_client
    
    # 从环境变量获取配置
    service_id = os.getenv('SERVICE_ID')
    service_name = os.getenv('SERVICE_NAME', 'deploy_service')
    model_id = os.getenv('MODEL_ID')
    model_version = os.getenv('MODEL_VERSION', 'V1.0.0')
    model_format = os.getenv('MODEL_FORMAT', 'pytorch')  # 默认pytorch
    port = int(os.getenv('PORT', 8000))
    model_path = os.getenv('MODEL_PATH')
    # 不再使用固定的ai_service_api，改为从Nacos动态获取
    # ai_service_api = os.getenv('AI_SERVICE_API', 'http://localhost:5000/model/deploy_service')
    
    server_ip = get_local_ip()
    
    if not model_path:
        logger.error("MODEL_PATH环境变量未设置")
        sys.exit(1)
    
    if not service_name:
        logger.error("SERVICE_NAME环境变量未设置")
        sys.exit(1)
    
    # 添加日志处理器，用于上报日志到主程序
    log_handler = LogHandler()
    log_handler.setLevel(logging.INFO)
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    
    # 确保在程序退出时关闭日志处理器
    def cleanup_log_handler():
        log_handler.close()
    atexit.register(cleanup_log_handler)
    
    # 加载模型
    if not load_model(model_path):
        logger.error("模型加载失败，退出")
        sys.exit(1)
    
    # 注册到Nacos
    setup_nacos()
    
    # 启动心跳线程（发送到主程序）
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    logger.info("心跳线程已启动")
    
    # 启动Nacos心跳线程
    if nacos_client:
        nacos_heartbeat_thread = threading.Thread(target=send_nacos_heartbeat, daemon=True)
        nacos_heartbeat_thread.start()
        logger.info("Nacos心跳线程已启动")
    
    # 注册退出处理
    atexit.register(deregister_nacos)
    
    # 注册信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭服务...")
        deregister_nacos()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 启动Flask服务
    logger.info(f"部署服务启动: {service_name} on {server_ip}:{port}")
    try:
        app.run(host='0.0.0.0', port=port, threaded=True)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
        deregister_nacos()
        sys.exit(0)


if __name__ == '__main__':
    main()
