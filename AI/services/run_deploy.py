"""
最小化的模型部署服务模板
用于部署模型并提供推理接口

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
import multiprocessing
import uuid
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 添加当前目录到路径，以便导入模型相关代码
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================
# 全局异常处理器 - 确保所有异常都被记录
# ============================================
def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器，确保所有未捕获的异常都被记录"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 允许键盘中断正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    import traceback
    error_msg = f"❌ [SERVICES] 未捕获的异常: {exc_type.__name__}: {exc_value}"
    print(error_msg, file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("异常堆栈:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # 也尝试使用logger（如果已初始化）
    try:
        logger = logging.getLogger(__name__)
        logger.error(f"未捕获的异常: {exc_type.__name__}: {exc_value}")
        logger.error(traceback.format_exception(exc_type, exc_value, exc_traceback))
    except:
        pass

# 设置全局异常处理器
sys.excepthook = handle_exception

# ============================================
# 环境变量和系统配置初始化
# ============================================

# 加载环境变量配置文件
env_file = '.env'
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"✅ 已加载配置文件: {env_file} (覆盖模式)", file=sys.stderr)
else:
    print(f"⚠️  配置文件 {env_file} 不存在，使用系统环境变量", file=sys.stderr)

# 设置multiprocessing启动方法为'spawn'以支持CUDA
try:
    try:
        current_method = multiprocessing.get_start_method()
    except RuntimeError:
        current_method = None
    
    if current_method != 'spawn':
        multiprocessing.set_start_method('spawn', force=True)
        print(f"✅ 已设置multiprocessing启动方法为'spawn'（原方法: {current_method or '未设置'}）", file=sys.stderr)
    else:
        print(f"✅ multiprocessing启动方法已为'spawn'", file=sys.stderr)
except RuntimeError as e:
    try:
        current_method = multiprocessing.get_start_method()
        print(f"⚠️  无法设置multiprocessing启动方法: {str(e)}，当前方法: {current_method}", file=sys.stderr)
    except RuntimeError:
        print(f"⚠️  无法设置multiprocessing启动方法: {str(e)}", file=sys.stderr)

# 强制 ONNX Runtime 使用 CPU（在导入任何使用 ONNX Runtime 的模块之前设置）
os.environ['ORT_EXECUTION_PROVIDERS'] = 'CPUExecutionProvider'
print("✅ 已设置 ONNX Runtime 使用 CPU 执行提供者", file=sys.stderr)

# 如果未设置 CUDA_VISIBLE_DEVICES，临时隐藏 GPU
if 'CUDA_VISIBLE_DEVICES' not in os.environ:
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    print("⚠️  临时隐藏 GPU 设备以避免 onnxruntime-gpu 导入时的 CUDA 库加载错误", file=sys.stderr)

# 导入推理相关模块
ONNXInference = None
try:
    from app.utils.onnx_inference import ONNXInference
    print(f"[SERVICES] ✅ ONNX推理模块导入成功", file=sys.stderr)
except ImportError as e:
    print(f"[SERVICES] ⚠️  警告: 无法导入ONNX推理模块: {e}", file=sys.stderr)
except Exception as e:
    import traceback
    print(f"[SERVICES] ❌ 导入ONNX推理模块时发生异常: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

app = Flask(__name__)
CORS(app)

# 配置日志
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('flask').setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format='[SERVICES] %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True,
    stream=sys.stderr
)
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("🚀 模型部署服务 (Services Module) 启动")
logger.info("=" * 60)

# 全局变量
model = None
model_loaded = False
server_ip = None
port = None
nacos_client = None
nacos_service_name = None
ai_service_api = None  # AI模块API地址
mac_address = None  # MAC地址
process_id = None  # 进程ID


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


def get_mac_address():
    """获取MAC地址"""
    try:
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
    except:
        return 'unknown'


def get_ai_service_api():
    """获取AI模块API地址（优先从环境变量，其次从Nacos）"""
    global nacos_client
    
    # 方案1: 从环境变量获取
    ai_api = os.getenv('AI_SERVICE_API')
    if ai_api:
        # 确保URL格式正确
        if not ai_api.startswith('http://') and not ai_api.startswith('https://'):
            ai_api = f'http://{ai_api}'
        return ai_api
    
    # 方案2: 从Nacos获取
    try:
        ai_service_name = os.getenv('AI_SERVICE_NAME', 'model-server')
        if nacos_client:
            instances = nacos_client.list_naming_instance(
                service_name=ai_service_name,
                healthy_only=True
            )
            if instances and len(instances) > 0:
                # 随机选择一个实例
                import random
                instance = random.choice(instances)
                ip = instance.get('ip', '')
                port = instance.get('port', 5000)
                return f'http://{ip}:{port}'
    except Exception as e:
        logger.warning(f"从Nacos获取AI服务地址失败: {str(e)}")
    
    # 方案3: 默认值
    return 'http://localhost:5000'


def is_port_available(port, host='0.0.0.0'):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port, host='0.0.0.0', max_attempts=100):
    """从指定端口开始，自动递增寻找可用端口"""
    port = start_port
    attempts = 0
    
    while attempts < max_attempts:
        if is_port_available(port, host):
            return port
        port += 1
        attempts += 1
    
    logger.error(f"在 {max_attempts} 次尝试后仍未找到可用端口（从 {start_port} 开始）")
    return None


def load_model(model_path):
    """加载模型"""
    global model, model_loaded
    
    try:
        logger.info(f"开始加载模型: {model_path}")
        
        # 根据文件扩展名判断模型类型
        if model_path.endswith('.onnx'):
            # ONNX模型加载
            try:
                if ONNXInference is None:
                    error_msg = "onnxruntime未安装，无法加载ONNX模型。请运行: pip install onnxruntime"
                    logger.error(error_msg)
                    print(error_msg, file=sys.stderr)
                    return False
                model = ONNXInference(model_path)
                logger.info("✅ ONNX模型加载成功")
                model_loaded = True
                return True
            except Exception as e:
                error_msg = f"ONNX模型加载失败: {str(e)}"
                logger.error(error_msg)
                print(error_msg, file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                return False
        else:
            # PyTorch模型加载（.pt文件）
            try:
                from ultralytics import YOLO
                model = YOLO(model_path)
                logger.info("✅ YOLO模型加载成功")
                model_loaded = True
                return True
            except ImportError as e:
                error_msg = f"ultralytics未安装，无法加载YOLO模型: {str(e)}。请运行: pip install ultralytics"
                logger.error(error_msg)
                print(error_msg, file=sys.stderr)
                return False
            except Exception as e:
                error_msg = f"YOLO模型加载失败: {str(e)}"
                logger.error(error_msg)
                print(error_msg, file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                return False
        
    except Exception as e:
        error_msg = f"加载模型失败: {str(e)}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        model_loaded = False
        return False


def setup_nacos():
    """设置Nacos注册（可选）"""
    global nacos_client, nacos_service_name, server_ip, port
    
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
        
        # 构建Nacos服务名
        service_name = os.getenv('SERVICE_NAME', 'deploy_service')
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
    
    while True:
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


def send_ai_heartbeat():
    """向AI模块hook接口发送心跳"""
    global ai_service_api, server_ip, port, mac_address, process_id, nacos_service_name, nacos_client
    
    # 首次等待，确保服务已启动
    time.sleep(2)
    
    while True:
        try:
            # 如果AI服务地址未获取到，尝试重新获取
            if not ai_service_api:
                ai_service_api = get_ai_service_api()
                if not ai_service_api:
                    logger.warning("AI服务地址未获取到，等待10秒后重试...")
                    time.sleep(10)
                    continue
            
            # 从环境变量获取服务信息
            service_name = os.getenv('SERVICE_NAME', 'deploy_service')
            service_id = os.getenv('SERVICE_ID')
            model_id = os.getenv('MODEL_ID')
            model_version = os.getenv('MODEL_VERSION', 'V1.0.0')
            model_format = os.getenv('MODEL_FORMAT', 'pytorch')
            
            # 构建心跳数据
            heartbeat_data = {
                'service_name': service_name,
                'server_ip': server_ip,
                'port': port,
                'inference_endpoint': f'http://{server_ip}:{port}/inference',
                'mac_address': mac_address,
                'process_id': process_id,
                'model_version': model_version,
                'format': model_format
            }
            
            # 可选字段
            if service_id:
                try:
                    heartbeat_data['service_id'] = int(service_id)
                except:
                    pass
            
            if model_id:
                try:
                    heartbeat_data['model_id'] = int(model_id)
                except:
                    pass
            
            # 发送心跳请求
            heartbeat_url = f'{ai_service_api}/deploy/heartbeat'
            response = requests.post(
                heartbeat_url,
                json=heartbeat_data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"✅ 心跳上报成功: {service_name}@{server_ip}:{port}")
                    
                    # 检查是否需要停止服务
                    data = result.get('data', {})
                    if data.get('should_stop'):
                        logger.info("收到停止服务指令，准备停止服务...")
                        deregister_nacos()
                        os._exit(0)
                else:
                    logger.warning(f"心跳上报返回错误: {result.get('msg', '未知错误')}")
            else:
                logger.warning(f"心跳上报失败: HTTP {response.status_code}, 响应: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"心跳上报请求异常: {str(e)}")
        except Exception as e:
            logger.error(f"心跳上报异常: {str(e)}", exc_info=True)
        
        time.sleep(10)  # 每10秒发送一次心跳


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
        'service_name': os.getenv('SERVICE_NAME', 'deploy_service')
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
    try:
        logger.info("收到停止服务请求")
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
    global model, model_loaded
    
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
    global server_ip, port, nacos_client, ai_service_api, mac_address, process_id
    
    try:
        # 输出启动信息到stderr
        print("=" * 60, file=sys.stderr)
        print("🚀 模型部署服务启动中...", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
    except Exception as e:
        print(f"❌ [SERVICES] 输出启动信息失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    # 从环境变量获取配置
    try:
        service_name = os.getenv('SERVICE_NAME', 'deploy_service')
        
        # 安全地获取端口号
        try:
            port = int(os.getenv('PORT', 8000))
        except ValueError:
            error_msg = f"❌ [SERVICES] 无效的端口号: {os.getenv('PORT')}"
            print(error_msg, file=sys.stderr)
            sys.exit(1)
        
        model_path = os.getenv('MODEL_PATH')
        
        # 输出环境变量信息用于诊断
        print(f"[SERVICES] 服务名称: {service_name}", file=sys.stderr)
        print(f"[SERVICES] 模型路径: {model_path}", file=sys.stderr)
        print(f"[SERVICES] 端口: {port}", file=sys.stderr)
        
        server_ip = get_local_ip()
        print(f"[SERVICES] 服务器IP: {server_ip}", file=sys.stderr)
        
        # 获取MAC地址和进程ID
        mac_address = get_mac_address()
        process_id = os.getpid()
        print(f"[SERVICES] MAC地址: {mac_address}", file=sys.stderr)
        print(f"[SERVICES] 进程ID: {process_id}", file=sys.stderr)
    except Exception as e:
        error_msg = f"❌ [SERVICES] 获取配置信息失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    
    if not model_path:
        error_msg = "❌ [SERVICES] MODEL_PATH环境变量未设置，无法启动服务"
        try:
            logger.error(error_msg)
        except:
            pass
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # 验证模型文件是否存在
    if not os.path.exists(model_path):
        error_msg = f"❌ [SERVICES] 模型文件不存在: {model_path}"
        try:
            logger.error(error_msg)
        except:
            pass
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # 验证模型文件是否可读
    if not os.access(model_path, os.R_OK):
        error_msg = f"❌ [SERVICES] 模型文件不可读: {model_path}"
        try:
            logger.error(error_msg)
        except:
            pass
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # 加载模型
    try:
        logger.info(f"准备加载模型: {model_path}")
        print(f"[SERVICES] 准备加载模型: {model_path}", file=sys.stderr)
    except:
        print(f"[SERVICES] 准备加载模型: {model_path}", file=sys.stderr)
    
    if not load_model(model_path):
        error_msg = f"❌ [SERVICES] 模型加载失败: {model_path}，请检查模型文件是否完整或格式是否正确"
        try:
            logger.error(error_msg)
        except:
            pass
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    
    # 注册到Nacos（可选）
    try:
        setup_nacos()
    except Exception as e:
        error_msg = f"⚠️  [SERVICES] Nacos注册失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        try:
            logger.warning(error_msg)
        except:
            pass
    
    # 获取AI模块API地址
    try:
        ai_service_api = get_ai_service_api()
        print(f"[SERVICES] AI模块API地址: {ai_service_api}", file=sys.stderr)
        logger.info(f"AI模块API地址: {ai_service_api}")
    except Exception as e:
        error_msg = f"⚠️  [SERVICES] 获取AI模块API地址失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        try:
            logger.warning(error_msg)
        except:
            pass
    
    # 启动Nacos心跳线程（如果Nacos可用）
    if nacos_client:
        try:
            nacos_heartbeat_thread = threading.Thread(target=send_nacos_heartbeat, daemon=True)
            nacos_heartbeat_thread.start()
            logger.info("Nacos心跳线程已启动")
            print("[SERVICES] ✅ Nacos心跳线程已启动", file=sys.stderr)
        except Exception as e:
            error_msg = f"⚠️  [SERVICES] 启动Nacos心跳线程失败: {str(e)}"
            print(error_msg, file=sys.stderr)
            try:
                logger.warning(error_msg)
            except:
                pass
    
    # 启动AI模块心跳线程
    try:
        ai_heartbeat_thread = threading.Thread(target=send_ai_heartbeat, daemon=True)
        ai_heartbeat_thread.start()
        logger.info("AI模块心跳线程已启动")
        print("[SERVICES] ✅ AI模块心跳线程已启动", file=sys.stderr)
    except Exception as e:
        error_msg = f"⚠️  [SERVICES] 启动AI模块心跳线程失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        try:
            logger.warning(error_msg)
        except:
            pass
    
    # 注册退出处理
    atexit.register(deregister_nacos)
    
    # 注册信号处理
    def signal_handler(signum, frame):
        try:
            logger.info(f"收到信号 {signum}，正在关闭服务...")
        except:
            pass
        print(f"[SERVICES] 收到信号 {signum}，正在关闭服务...", file=sys.stderr)
        deregister_nacos()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 检查端口是否可用，如果不可用则自动查找可用端口
    host = '0.0.0.0'
    original_port = port
    try:
        logger.info(f"🔍 检查端口 {port} 是否可用...")
        print(f"[SERVICES] 🔍 检查端口 {port} 是否可用...", file=sys.stderr)
    except:
        print(f"[SERVICES] 🔍 检查端口 {port} 是否可用...", file=sys.stderr)
    
    try:
        if not is_port_available(port, host):
            try:
                logger.warning(f"⚠️  端口 {port} 已被占用，正在查找可用端口...")
            except:
                pass
            print(f"[SERVICES] ⚠️  端口 {port} 已被占用，正在查找可用端口...", file=sys.stderr)
            new_port = find_available_port(port, host)
            if new_port is None:
                error_msg = f"❌ [SERVICES] 无法找到可用端口（从 {port} 开始，已尝试100个端口）"
                try:
                    logger.error(error_msg)
                except:
                    pass
                print(error_msg, file=sys.stderr)
                sys.exit(1)
            port = new_port
            try:
                logger.info(f"✅ 已切换到可用端口: {port}")
            except:
                pass
            print(f"[SERVICES] ✅ 已切换到可用端口: {port}", file=sys.stderr)
        else:
            try:
                logger.info(f"✅ 端口 {port} 可用")
            except:
                pass
            print(f"[SERVICES] ✅ 端口 {port} 可用", file=sys.stderr)
        
        # 如果端口发生了变化，更新环境变量
        if port != original_port:
            os.environ['PORT'] = str(port)
            try:
                logger.info(f"已更新环境变量 PORT={port}")
            except:
                pass
            print(f"[SERVICES] 已更新环境变量 PORT={port}", file=sys.stderr)
    except Exception as e:
        error_msg = f"❌ [SERVICES] 端口检查失败: {str(e)}"
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    
    # 禁用 Flask 的默认日志输出
    try:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    except:
        pass
    
    # 启动Flask服务
    try:
        logger.info(f"部署服务启动: {service_name} on {server_ip}:{port}")
        logger.info("=" * 60)
        logger.info(f"🌐 服务地址: http://{server_ip}:{port}")
        logger.info(f"📊 健康检查: http://{server_ip}:{port}/health")
        logger.info(f"🔮 推理接口: http://{server_ip}:{port}/inference")
        logger.info("=" * 60)
        logger.info("🚀 正在启动Flask应用...")
    except:
        pass
    # 同时输出到stderr（确保关键信息都能看到）
    print("=" * 60, file=sys.stderr)
    print(f"[SERVICES] 部署服务启动: {service_name} on {server_ip}:{port}", file=sys.stderr)
    print(f"[SERVICES] 🌐 服务地址: http://{server_ip}:{port}", file=sys.stderr)
    print(f"[SERVICES] 📊 健康检查: http://{server_ip}:{port}/health", file=sys.stderr)
    print(f"[SERVICES] 🔮 推理接口: http://{server_ip}:{port}/inference", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("[SERVICES] 🚀 正在启动Flask应用...", file=sys.stderr)
    
    try:
        app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e) or "端口" in str(e):
            error_msg = f"❌ [SERVICES] 端口 {port} 启动失败: {str(e)}\n💡 请检查是否有其他进程在使用该端口"
            try:
                logger.error(error_msg)
            except:
                pass
            print(error_msg, file=sys.stderr)
        else:
            error_msg = f"❌ [SERVICES] 服务启动失败: {str(e)}"
            try:
                logger.error(error_msg)
            except:
                pass
            print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        try:
            deregister_nacos()
        except:
            pass
        sys.exit(1)
    except KeyboardInterrupt:
        try:
            logger.info("收到中断信号，正在关闭服务...")
        except:
            pass
        print("[SERVICES] 收到中断信号，正在关闭服务...", file=sys.stderr)
        try:
            deregister_nacos()
        except:
            pass
        sys.exit(0)
    except Exception as e:
        error_msg = f"❌ [SERVICES] 服务启动异常: {str(e)}"
        try:
            logger.error(error_msg)
        except:
            pass
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        try:
            deregister_nacos()
        except:
            pass
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SERVICES] 收到中断信号，正在退出...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        import traceback
        error_msg = f"❌ [SERVICES] 主函数异常: {str(e)}"
        print(error_msg, file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)

